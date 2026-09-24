/* runner.js - built-in code runner.
 *
 * - HTML / CSS / JavaScript : runs in the browser preview iframe.
 * - Python / Java / C#      : POST to /api/run -> server executes in a
 *                             controlled subprocess (timeout, output limit).
 */

(function () {
    "use strict";

    var APP = window.APP;
    var LAST_OUTPUT = "";

    function busy(on) {
        var btn = document.getElementById("run-btn");
        if (btn) {
            btn.disabled = on;
            btn.textContent = on ? "Running..." : "Run";
        }
    }

    function showConsole() {
        document.querySelectorAll(".otab").forEach(function (t) {
            t.classList.toggle("active", t.dataset.tab === "console");
        });
        document.querySelectorAll(".output-view").forEach(function (v) {
            v.classList.toggle("active", v.id === "console-output");
        });
    }

    function showPreview() {
        document.querySelectorAll(".otab").forEach(function (t) {
            t.classList.toggle("active", t.dataset.tab === "preview");
        });
        document.querySelectorAll(".output-view").forEach(function (v) {
            v.classList.toggle("active", v.id === "preview-frame");
        });
    }

    function showAI() {
        document.querySelectorAll(".otab").forEach(function (t) {
            t.classList.toggle("active", t.dataset.tab === "ai");
        });
        document.querySelectorAll(".output-view").forEach(function (v) {
            v.classList.toggle("active", v.id === "ai-output");
        });
    }

    document.querySelectorAll(".otab").forEach(function (tab) {
        tab.addEventListener("click", function () {
            var which = this.dataset.tab;
            if (which === "console") { showConsole(); }
            else if (which === "preview") { showPreview(); }
            else if (which === "ai") { showAI(); }
        });
    });

    document.getElementById("clear-output-btn").addEventListener("click", function () {
        var c = document.getElementById("console-output");
        if (c) { c.textContent = ""; }
    });

    function writeOutput(text) {
        var c = document.getElementById("console-output");
        if (!c) { return; }
        c.textContent = text;
        c.scrollTop = c.scrollHeight;
        localStorage.setItem("vibes-last-output-" + APP.roomCode, text);
        showConsole();
    }

    function runPreview() {
        var code = window.VS.getCode();
        var iframe = document.getElementById("preview-frame");
        iframe.srcdoc = code;
        showPreview();
    }

    function runServer() {
        busy(true);
        var code = window.VS.getCode();
        fetch("/api/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ language: window.VS.language, code: code })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var out = "";
            out += "=== Output ===\n" + (data.stdout || "") + "\n";
            if (data.stderr) { out += "\n=== Errors / stderr ===\n" + data.stderr + "\n"; }
            if (data.note) { out += "\n" + data.note + "\n"; }
            if (data.ok && data.stdout === "" && data.stderr === "") { out += "(no output)\n"; }
            writeOutput(out);
        })
        .catch(function (err) {
            writeOutput("Run failed - is the server running?\n" + err);
        })
        .finally(function () { busy(false); });
    }

    document.getElementById("run-btn").addEventListener("click", function () {
        var lang = window.VS.language;
        if (lang === "html" || lang === "css" || lang === "javascript") {
            runPreview();
        } else {
            runServer();
        }
    });

    /* Expose for ai.js */
    window.RUNNER = { showConsole: showConsole, showPreview: showPreview, showAI: showAI };
})();