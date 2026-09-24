/* ai.js - Offline AI Code Watch.
 *
 * Sends the current code to /api/analyze (rule-based offline analyzer),
 * then shows the findings in the "AI Code Watch" output panel, sorted by
 * severity. Clicking a finding jumps the Monaco editor to that line.
 */

(function () {
    "use strict";

    var SEV_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 };
    var SEV_COLOR = { HIGH: "#f87171", MEDIUM: "#fbbf24", LOW: "#94a3b8" };

    function sw_displayCtrl() {
        // show the AI tab and focus it
        if (window.RUNNER) { window.RUNNER.showAI(); }
    }

    document.getElementById("analyze-btn").addEventListener("click", function () {
        var btn = this;
        var oldText = btn.textContent;
        btn.disabled = true;
        btn.textContent = "Analyzing...";

        fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ language: window.VS.language, code: window.VS.getCode() })
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            render(findings(data));
        })
        .catch(function () { sw_displayCtrl(); render([]); toast("Analyze failed"); })
        .finally(function () { btn.disabled = false; btn.textContent = oldText; });
    });

    function findings(data) {
        if (!data || !data.ok) { return []; }
        return (data.findings || []).slice().sort(function (a, b) {
            return (SEV_ORDER[a.severity] || 9) - (SEV_ORDER[b.severity] || 9);
        });
    }

    function render(items) {
        sw_displayCtrl();
        var box = document.getElementById("ai-output");
        if (!box) { return; }
        box.innerHTML = "";

        var header = document.createElement("div");
        header.className = "ai-header";
        header.textContent = "Offline AI Code Watch - " + items.length + " finding(s)";
        box.appendChild(header);

        if (!items.length) {
            var ok = document.createElement("p");
            ok.className = "ai-ok";
            ok.textContent = "No obvious issues detected by the rule-based analyzer.";
            box.appendChild(ok);
            return;
        }

        items.forEach(function (f) {
            var card = document.createElement("div");
            card.className = "ai-card";
            card.style.borderLeft = "4px solid " + (SEV_COLOR[f.severity] || "#999");

            var top = document.createElement("div");
            top.className = "ai-card-top";

            var sev = document.createElement("span");
            sev.className = "ai-sev";
            sev.textContent = f.severity;
            sev.style.color = SEV_COLOR[f.severity] || "#999";
            top.appendChild(sev);

            var prob = document.createElement("span");
            prob.className = "ai-prob";
            prob.textContent = f.problem;
            top.appendChild(prob);

            var lineBtn = document.createElement("button");
            lineBtn.className = "btn btn-xs btn-outline";
            lineBtn.textContent = "Line " + f.line;
            lineBtn.style.marginLeft = "auto";
            lineBtn.addEventListener("click", function () {
                if (window.VS) {
                    var editor = window.VS.getEditor();
                    var monaco = window.VS.getMonaco();
                    if (editor && monaco) {
                        editor.revealLineInCenter(f.line);
                        editor.setPosition({ lineNumber: f.line, column: 1 });
                        editor.focus();
                    }
                }
            });
            top.appendChild(lineBtn);
            card.appendChild(top);

            var expl = document.createElement("div");
            expl.className = "ai-expl";
            expl.textContent = f.explanation;
            card.appendChild(expl);

            var rec = document.createElement("div");
            rec.className = "ai-reco";
            rec.textContent = "Fix: " + f.recommendation;
            card.appendChild(rec);

            box.appendChild(card);
        });
    }
})();