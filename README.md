# VibeSpace

**AI-Assisted Real-Time Collaborative Coding Platform**

VibeSpace is a web-based collaborative coding platform that combines
real-time code collaboration, communication, code execution, version
history and offline AI-assisted code analysis in one application.

---

## Features (all working)

- Register / Login / Logout (sessions, roles)
- First registered user becomes **admin**
- Create coding rooms + **shareable link** (`/join/ABC123`)
- **Monaco editor** (same engine as VS Code) — offline, no internet
- **Real-time collaboration**: live text sync, collaborator presence,
  remote cursors (Socket.IO)
- **Three minimizable chat panels**: General, Code-Context, Media/Photos
- **Code runner**: HTML/CSS/JS (browser preview), Python (subprocess),
  Java (JDK) and C# (.NET) when installed
- **Offline AI Code Watch**: rule-based static analysis (no API key!)
- **AI Review report**: BUgS/SECURITY/QUALITY/COMPLEXITY/PERFORMANCE + score
- **Smart templates**: Python, HTML, Java, C#
- **Version history**: save, view, compare, restore
- **Admin dashboard**: users, rooms, stats

---

## Run it online (free, no payment) - GitHub Codespaces

[![Open in GitHub Codespaces](https://img.shields.io/badge/Open%20in%20Codespaces-181717?style=for-the-badge&logo=github&logoColor=white)](https://codespaces.new/rushikeshgajananshinde993-lab/VibeSpace)

1. Click the button above (or open the repo, click `Code` -> `Codespaces` -> `Create codespace`).
2. Wait for the setup to finish (2-3 min, automatic).
3. Open the forwarded **port 5566** link (it shows in the bottom-right "Remote/Ports" tab, or VS Code opens a notification).
   The public link looks like: `https://5566-<codespace>.app.github.dev/`
4. Share that link! Anyone can register, log in, create rooms and code together.

> Free on GitHub: 120 core-hours / month. The codespace pauses after ~30 min idle; clicking back in it wakes it up.

## How to run (locally / pendrive)

### Option A - Pendrive (recommended)
1. Insert pendrive
2. Open the `VibeSpace` folder
3. Double-click **`run.bat`**
4. Browser opens VibeSpace automatically

### Option B - VS Code
1. `File > Open Folder` → choose the `VibeSpace` folder
2. Terminal: install deps once
   ```
   python -m pip install --no-index --find-links="vendor/wheels" -r requirements.txt
   ```
3. Start server
   ```
   python server.py --host 127.0.0.1 --port 5566
   ```
4. Open http://127.0.0.1:5566/

> No internet is needed after the first setup. Everything (Monaco editor,
> dependencies, AI analyzer) is stored locally in the project.

---

## Project structure

```
VibeSpace/
├── run.bat            # pendrive launcher (env check + offline install)
├── requirements.txt
├── config.py          # single place for APP_NAME + settings
├── database.py        # SQLite layer
├── server.py          # Flask app + Socket.IO + all routes/APIs
├── ai_engine.py       # offline rule-based code analyzer
├── code_runner.py     # Python/Java/C# execution
├── database/vibespace.db
├── workspace/         # temp files for code execution
├── vendor/wheels/     # offline dependency install
├── static/            # css, js, monaco (offline editor)
├── templates/         # HTML pages
└── docs/              # README, VIVA_GUIDE, DEMO_CHECKLIST, TROUBLESHOOTING
```

---

## Demo flow (recommended presentation)

1. Login → 2. Dashboard → 3. Create room → 4. Second browser joins →
5. Type together (cursors) → 6. Chat → 7. Run HTML preview →
8. Run Python → 9. AI Code Watch → 10. AI Review → 11. Save/Restore
version → 12. Admin panel → 13. Show database

---

## First user = admin

The very first account you register automatically becomes the **admin**,
so you can demonstrate the admin dashboard.

---

## Tech stack (viva-ready answers inside VIVA_GUIDE.md)

Python Flask · Flask-SocketIO · SQLite · HTML/CSS/JS · Monaco Editor ·
offline rule-based AI analyzer. No cloud APIs, no payment, no internet
required.

See `docs/VIVA_GUIDE.md` for full project documentation and 30+ exam
questions, `docs/DEMO_CHECKLIST.md` for presentation prep, and
`docs/TROUBLESHOOTING.md` for common problems.