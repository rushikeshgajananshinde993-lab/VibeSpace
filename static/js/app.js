/* VibeSpace - small frontend helper used on every page */

(function () {
    "use strict";

    // Hide any alert after a few seconds automatically.
    document.addEventListener("DOMContentLoaded", function () {
        var alerts = document.querySelectorAll(".alert");
        alerts.forEach(function (alert) {
            setTimeout(function () {
                alert.style.transition = "opacity 0.5s";
                alert.style.opacity = "0";
                setTimeout(function () { alert.remove(); }, 500);
            }, 5000);
        });
    });
})();