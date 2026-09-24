/* chat.js - three minimizable chat panels (general + code + media).
 *
 * All messages go through Socket.IO: "chat_message" event. Media photos
 * are sent as data-URL images (base64) and stored in SQLite.
 */

(function () {
    "use strict";

    var APP = window.APP;
    var socket = window.SOCKET;

    if (!socket) { return; }

    var TYPE_TO_CONTAINER = {
        general: "chat-general",
        code: "chat-code",
        media: "chat-media"
    };

    function escText(s) {
        var d = document.createElement("div");
        d.textContent = s;
        return d.innerHTML;
    }

    window.sendChat = function (type, formOrContent) {
        if (typeof formOrContent === "string") {
            var content = formOrContent;
            if (type === "media_text") { type = "media"; }
            if (!content.trim()) { return; }
            socket.emit("chat_message", {
                code: APP.roomCode,
                type: type,
                content: content,
                user: APP.user
            });
            return;
        }
        var input = formOrContent.querySelector("input");
        var content = input.value.trim();
        if (!content) { return; }
        socket.emit("chat_message", {
            code: APP.roomCode,
            type: type,
            content: content,
            user: APP.user
        });
        input.value = "";
    };

    /* Receive new chat message */
    socket.on("chat_new", function (msg) {
        var containerId = TYPE_TO_CONTAINER[msg.message_type] || "chat-general";
        var box = document.getElementById(containerId);
        if (!box) { return; }

        var row = document.createElement("div");
        row.className = "chat-msg";
        var who = document.createElement("div");
        who.className = "chat-who";
        who.textContent = msg.username || "Guest";

        if (msg.message_type === "media" && /^data:image/.test(msg.content)) {
            var img = document.createElement("img");
            img.className = "chat-img";
            img.src = msg.content;
            img.alt = "Shared image";
            var cap = document.createElement("div");
            cap.className = "chat-text";
            cap.textContent = msg.content.split(",")[1] ? "[image]" : "";
            row.appendChild(who);
            row.appendChild(img);
        } else {
            var txt = document.createElement("div");
            txt.className = "chat-text";
            txt.textContent = msg.content;
            row.appendChild(who);
            row.appendChild(txt);
        }
        box.appendChild(row);
        box.scrollTop = box.scrollHeight;
    });

    /* Media upload -> data URL -> send as media chat message */
    var upload = document.getElementById("media-upload");
    if (upload) {
        upload.addEventListener("change", function () {
            var file = upload.files && upload.files[0];
            if (!file) { return; }
            if (file.size > 3 * 1024 * 1024) {
                toast("Image too large (max 3 MB)");
                return;
            }
            var reader = new FileReader();
            reader.onload = function (e) {
                socket.emit("chat_message", {
                    code: APP.roomCode,
                    type: "media",
                    content: e.target.result,
                    user: APP.user
                });
                toast("Photo sent");
            };
            reader.readAsDataURL(file);
            upload.value = "";
        });
    }
})();