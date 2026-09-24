/* collaboration.js - real-time room sync via Socket.IO.
 *
 * Broadcasts code changes and cursor positions to everyone in the room,
 * updates the collaborators panel and remote cursors.
 *
 * Honest limitation: this is simple "last-change-wins" sync, not a CRDT.
 * Two people editing the exact same spot simultaneously may overwrite
 * each other - we document this clearly.
 */

(function () {
    "use strict";

    var APP = window.APP;
    var socket = null;
    var remoteCursors = {};   // sid -> decoration ids

    try {
        socket = window.io();
    } catch (e) {
        console.error("Socket.IO client missing", e);
        return;
    }
    window.SOCKET = socket;

    /* ---- Join room ----
     * We join through our own "room_join" event so the server can also
     * send us the current code + member list (nice for newcomers).
     */
    socket.on("connect", function () {
        socket.emit("room_join", { code: APP.roomCode, user: APP.user });
    });

    socket.on("room_joined", function (data) {
        if (typeof data.code === "string" && data.code.length > 0 && window.VS) {
            window.VS.setCode(data.code);
        }
        if (data.members) { renderMembers(data.members); }
    });

    socket.on("members_update", function (data) {
        renderMembers(data.members || []);
    });

    /* Receive code edited by someone else in the room. */
    socket.on("code_update", function (data) {
        if (!window.VS) { return; }
        var editor = window.VS.getEditor();
        if (!editor) { return; }
        var cursorPos = editor.getPosition();   // remember cursor before setValue
        window.VS.setCode(data.content || "");
        if (cursorPos) { editor.setPosition(cursorPos); }
        toast("Code updated by " + (data.by || "teammate"));
    });

    /* Receive a cursor position from a teammate. */
    socket.on("cursor_update", function (data) {
        if (!window.VS) { return; }
        var monaco = window.VS.getMonaco();
        var editor = window.VS.getEditor();
        if (!monaco || !editor) { return; }
        drawRemoteCursor(data);
    });

    socket.on("room_error", function (data) {
        toast(data.msg || "Room error");
    });

    socket.on("connect_error", function () {
        toast("Socket connection failed - collaboration disabled");
    });

    /* ---- Send code changes (debounced by editor.js) ---- */
    document.addEventListener("vibe:code-changed", function (e) {
        if (!socket || !socket.connected) { return; }
        socket.emit("code_change", {
            code: APP.roomCode,
            content: e.detail.code,
            language: e.detail.language || APP.language,
            user: APP.user
        });
    });

    /* ---- Send cursor moves ---- */
    document.addEventListener("vibe:cursor-moved", function (e) {
        if (!socket || !socket.connected || !APP.roomCode) { return; }
        socket.emit("cursor_move", {
            code: APP.roomCode,
            name: APP.user.username,
            line: e.detail.line,
            column: e.detail.column
        });
    });

    /* ---- Collaborators panel ---- */
    function renderMembers(members) {
        var box = document.getElementById("members-list");
        if (!box) { return; }
        document.getElementById("members-count").textContent = members.length;
        document.getElementById("online-count").textContent = members.length + " online";

        box.innerHTML = "";
        if (!members.length) {
            box.innerHTML = "<p style='color:var(--muted);'>No one else online yet.<br>Share the room link!</p>";
            return;
        }
        members.forEach(function (m) {
            var row = document.createElement("div");
            row.className = "member-row";
            var dot = document.createElement("span");
            dot.className = "member-dot";
            var name = document.createElement("span");
            name.textContent = m.name || "Guest";
            var self = m.id === (APP.user ? APP.user.id : null);
            if (self) { name.textContent += " (you)"; }
            row.appendChild(dot);
            row.appendChild(name);
            box.appendChild(row);
        });
    }

    /* ---- Remote cursors (Monaco decorations) ----
     * Each teammate gets a colored vertical line + name label at their
     * live cursor position.
     */
    var colors = ["#ff6b6b", "#34d399", "#fbbf24", "#7c5cff", "#22d3ee", "#f472b6"];

    function drawRemoteCursor(data) {
        var monaco = window.VS.getMonaco();
        var editor = window.VS.getEditor();
        var model = editor.getModel();
        if (!data.line || !data.column || data.id === socket.id) { return; }

        var range = new monaco.Range(data.line, data.column, data.line, data.column);
        var color = colors[(data.id || "").length % colors.length];

        var deco = editor.deltaDecorations(
            (remoteCursors[data.id] && remoteCursors[data.id].deco) || [],
            [{
                range: range,
                options: {
                    isWholeLine: false,
                    className: "remote-cursor",
                    beforeContentClassName: "remote-cursor-part",
                    hoverMessage: { value: data.name }
                }
            }]
        );

        // Label widget
        if (remoteCursors[data.id]) {
            editor.removeContentWidget(remoteCursors[data.id].widget);
        }
        var widget = {
            getId: function () { return "cur-" + data.id; },
            getDomNode: function () {
                if (!widget._node) {
                    var node = document.createElement("span");
                    node.className = "remote-label";
                    node.style.background = color;
                    node.style.color = "#000";
                    node.textContent = data.name;
                    widget._node = node;
                }
                return widget._node;
            },
            getPosition: function () {
                return { position: range.getStartPosition(), preference: [monaco.editor.ContentWidgetPositionPreference.ABOVE] };
            }
        };
        editor.addContentWidget(widget);
        remoteCursors[data.id] = { deco: deco, widget: widget };

        // Prevent infinite accumulation: cap total remote cursors
        var keys = Object.keys(remoteCursors);
        if (keys.length > 12) {
            var oldest = keys[0];
            editor.removeContentWidget(remoteCursors[oldest].widget);
            editor.deltaDecorations(remoteCursors[oldest].deco, []);
            delete remoteCursors[oldest];
        }
    }

})();

/* ---- Shared helpers used by multiple scripts ---- */
function toast(msg) {
    var el = document.getElementById("toast");
    if (!el) { return; }
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { el.classList.remove("show"); }, 2200);
}

function togglePanel(head) {
    var body = head.parentElement.querySelector(".panel-body");
    head.classList.toggle("collapsed");
    if (body) {
        body.style.height = head.classList.contains("collapsed") ? "0" : "";
        body.style.padding = head.classList.contains("collapsed") ? "0 12px" : "";
        body.style.overflow = "hidden";
    }
}