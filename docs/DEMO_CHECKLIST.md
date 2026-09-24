# Demo Checklist

Use this before and during your presentation so nothing is forgotten.

---

## BEFORE PRESENTATION

- [ ] Pendrive connected
- [ ] Correct project folder open (`VibeSpace`)
- [ ] Launcher works (`run.bat`)
- [ ] Environment check passes
- [ ] Server starts
- [ ] Browser opens automatically
- [ ] Database loads (`database/vibespace.db` exists)
- [ ] Login works
- [ ] Room creation works
- [ ] Second user can join (second browser window)
- [ ] Collaboration works
- [ ] Chat works
- [ ] HTML preview works
- [ ] Python execution works
- [ ] AI analyzer works
- [ ] Review works
- [ ] Version history works
- [ ] Restore works
- [ ] Admin works
- [ ] User data can be demonstrated

---

## PRACTICE FLOW (do this 3 times before presenting)

1. Start server
2. Register account (note: FIRST account becomes admin → use it for admin demo)
3. Login
4. Dashboard → Create a Room
5. Copy the share link
6. Open a **second browser window** (Incognito) → paste link → join
7. In both windows: type code together → watch cursors + live sync
8. Open each chat panel, send a message; send a photo in Media chat
9. Write HTML → Run → Preview tab shows the page
10. Write Python (`print("Hello")`) → Run → Console shows output
    (Java / C# also demo if runtime installed - this PC has both)
11. Click **AI** → findings appear; click a finding → jumps to line
12. Click **Review** → full report with score
13. Save versions (press "Save v" a few times) → **Versions** → Restore an old one
14. Open **Admin** panel (top right) → show users table (no passwords!)
15. Optional: open `database/vibespace.db` with a viewer to show the table

---

## DURING PRESENTATION TIPS

- Keep the server running - never close the terminal window.
- Have two browser windows open and ready before you start.
- Internet OFF is fine - everything is local.
- If Java/C# is missing on a random computer, say honestly:
  "Java execution requires a JDK; on this computer it is/isn't installed."
- The AI is rule-based, not a cloud LLM. Say so proudly - it works offline.

---

## BACKUP PLAN (if the computer is very restricted)

- Copy the whole `VibeSpace` folder to the Desktop instead of running
  from the pendrive (avoids permission problems).
- If `run.bat` is blocked, use VS Code:
  `python server.py --host 127.0.0.1 --port 5566`