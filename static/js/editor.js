/* editor.js - Monaco setup + toolbar controls for VibeSpace.
 *
 * Hotel Monaco locally (offline): we load loader.js from /static/monaco
 * and point the AMD loader at the local "vs" folder.
 */

(function () {
    "use strict";

    var APP = window.APP;
    var MONACO_PREFIX = "/static/monaco";
    var editorHost = document.getElementById("editor-host");

    var monaco = null;
    var editor = null;
    var applyingRemote = false;

    /* Expose a small event bus so other scripts can act after Monaco is ready. */
    var readyHandlers = [];
    window.afterMonacoReady = function (fn) {
        if (monaco) { fn(monaco, editor); } else { readyHandlers.push(fn); }
    };

    var languageMap = {
        python: "python",
        html: "html",
        css: "css",
        javascript: "javascript",
        java: "java",
        csharp: "csharp"
    };

    function monacoLanguage(lang) {
        return languageMap[lang] || "python";
    }

    function setLanguage(newLang) {
        APP.language = newLang;
        monaco.editor.setModelLanguage(editor.getModel(), monacoLanguage(newLang));
        document.getElementById("language-select").value = newLang;
    }

    function getCode() {
        return editor ? editor.getValue() : "";
    }

    window.VS = {
        getCode: getCode,
        setCode: function (code) {
            applyingRemote = true;
            editor.setValue(code);
            applyingRemote = false;
        },
        get language() { return APP.language; },
        getMonaco: function () { return monaco; },
        getEditor: function () { return editor; },
        isApplyingRemote: function () { return applyingRemote; },
        setLang: setLanguage
    };

    /* ---- Create Monaco editor ---- */
    window.require.config({ paths: { vs: MONACO_PREFIX + "/vs" } });
    window.require(["vs/editor/editor.main"], function () {
        monaco = window.monaco;

        editor = monaco.editor.create(editorHost, {
            value: APP.initialCode || "",
            language: monacoLanguage(APP.language),
            theme: "vs-dark",
            automaticLayout: true,
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: "on"
        });

        var debounceTimer = null;
        editor.onDidChangeModelContent(function () {
            if (applyingRemote) { return; }
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function () {
                var ev = new CustomEvent("vibe:code-changed", {
                    detail: { code: editor.getValue(), language: APP.language }
                });
                document.dispatchEvent(ev);
            }, 150);
        });

        editor.onDidChangeCursorPosition(function (e) {
            var ev = new CustomEvent("vibe:cursor-moved", {
                detail: { line: e.position.lineNumber, column: e.position.column }
            });
            document.dispatchEvent(ev);
        });

        readyHandlers.forEach(function (fn) { fn(monaco, editor); });
        readyHandlers = [];
    });

    /* ---- Toolbar: language selector ---- */
    document.getElementById("language-select").addEventListener("change", function () {
        setLanguage(this.value);
    });

    /* ---- Toolbar: template selector ---- */
    document.getElementById("template-select").addEventListener("change", function () {
        var lang = this.value;
        if (!lang) { return; }
        fetch("/api/template", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ language: lang })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.ok && window.VS) {
                window.VS.setCode(data.code);
                window.VS.setLang(data.language);
                toast("Template loaded: " + lang);
            }
        })
        .catch(function () { toast("Could not load template"); });
        this.value = "";
    });

    /* ---- Toolbar: save version ---- */
    document.getElementById("save-version-btn").addEventListener("click", function () {
        saveVersion();
    });

    /* ---- Copy link ---- */
    document.getElementById("copy-link-btn").addEventListener("click", function () {
        var link = window.location.origin + "/join/" + APP.roomCode;
        if (navigator.clipboard) {
            navigator.clipboard.writeText(link).then(function () {
                toast("Link copied: " + link);
            });
        } else {
            prompt("Copy this room link:", link);
        }
    });

    /* ---- Versions modal ---- */
    document.getElementById("versions-btn").addEventListener("click", function () {
        loadVersions();
    });

    window.VS.saveVersion = saveVersion;
    window.VS.loadVersions = loadVersions;

    function saveVersion() {
        fetch("/api/version/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ room_code: APP.roomCode, language: APP.language, code: getCode() })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.ok) {
                toast("Version saved");
                APP.versions = data.versions;
            } else {
                toast(data.error || "Save failed");
            }
        })
        .catch(function () { toast("Save failed - is server running?"); });
    }

    function loadVersions() {
        fetch("/api/room/" + APP.roomCode + "/versions")
        .then(function (r) { return r.json(); })
        .then(function (data) {
            renderVersions(data.versions || []);
            document.getElementById("versions-modal").style.display = "flex";
        })
        .catch(function () { toast("Could not load versions"); });
    }

    function renderVersions(versions) {
        var box = document.getElementById("versions-list");
        box.innerHTML = "";
        if (!versions.length) {
            box.innerHTML = "<p style='color:var(--muted)'>No versions saved yet. Use 'Save v'.</p>";
            return;
        }
        var table = document.createElement("table");
        table.style.width = "100%";
        table.style.borderCollapse = "collapse";

        var head = document.createElement("tr");
        ["Version", "User", "Language", "Time", "Actions"].forEach(function (h) {
            var th = document.createElement("th");
            th.textContent = h;
            th.style.cssText = "text-align:left;padding:8px;color:var(--muted)";
            head.appendChild(th);
        });
        table.appendChild(head);

        versions.forEach(function (v, i) {
            var tr = document.createElement("tr");
            tr.style.borderTop = "1px solid var(--border)";
            var cells = [ "#" + (versions.length - i), v.username || "-", v.language || "-", v.created_at || "-" ];
            cells.forEach(function (c) {
                var td = document.createElement("td");
                td.textContent = c;
                td.style.padding = "8px";
                tr.appendChild(td);
            });

            var actTd = document.createElement("td");
            actTd.style.padding = "8px";

            var view = makeBtn("View", function () { restoreVersion(v.id, false); });
            var restore = makeBtn("Restore", function () { restoreVersion(v.id, true); });
            var compare = makeBtn("Compare", function () { showDiff(v, versions); });
            actTd.appendChild(view);
            actTd.appendChild(restore);
            actTd.appendChild(compare);
            tr.appendChild(actTd);
            table.appendChild(tr);
        });
        box.appendChild(table);
    }

    function makeBtn(label, handler) {
        var b = document.createElement("button");
        b.className = "btn btn-xs";
        b.textContent = label;
        b.style.marginRight = "6px";
        b.addEventListener("click", handler);
        return b;
    }

    function restoreVersion(versionId, actuallyRestore) {
        fetch("/api/version/restore", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ version_id: versionId })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (data.ok) {
                window.VS.setCode(data.code);
                window.VS.setLang(data.language || window.VS.language);
                toast(actuallyRestore ? "Restored version into the editor" : "Loaded version into the editor");
            } else {
                toast(data.error || "Restore failed");
            }
        })
        .catch(function () { toast("Restore failed"); });
    }

    function showDiff(versionA, allVersions) {
        var b = document.getElementById("version-diff");
        b.style.display = "block";
        var latest = allVersions[0];
        if (!latest || latest.id === versionA.id) {
            document.getElementById("diff-text").textContent = "This version is the latest - no difference.";
            return;
        }
        var oldLines = (latest.code || "").split("\n");
        var newLines = (versionA.code || "").split("\n");
        var out = [];
        var max = Math.max(oldLines.length, newLines.length);
        for (var i = 0; i < max; i++) {
            var a = oldLines[i] === undefined ? "" : oldLines[i];
            var c = newLines[i] === undefined ? "" : newLines[i];
            if (a === c) {
                out.push("   " + a);
            } else {
                out.push("-  " + a);
                out.push("+  " + c);
            }
        }
        document.getElementById("diff-text").textContent = out.join("\n").slice(0, 8000);
    }
})();