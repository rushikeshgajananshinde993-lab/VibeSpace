# Troubleshooting Guide

Simple fixes for the most common problems. Read the section that matches
your symptom.

---

## 1. Python not installed / `'python' is not recognized`

- You need Python 3.9 or newer.
- Install from https://www.python.org/downloads/
- During installation, **TICK "Add Python to PATH"** (very important).
- After install, re-open the terminal / re-try `run.bat`.

## 2. `pip` not available

- Very rare if Python is installed.
- Run once (needs internet): `python -m pip install --upgrade pip`

## 3. Dependency installation fails

- `run.bat` first tries the local `vendor/wheels` folder (offline, no internet).
- If the computer's Python version is not covered by the wheels
  (Python 3.9-3.14 are covered), it falls back to online install.
- If both fail, check internet is working, then:
  ```
  python -m pip install -r requirements.txt
  ```

## 4. Port already in use (server won't start)

- `run.bat` / the server automatically searches for a free port and shows
  the exact URL to open.
- In VS Code use a different port:
  ```
  python server.py --host 127.0.0.1 --port 5567
  ```
- Or find the program using the port and close it.

## 5. Java code won't run ("JDK not installed")

- Java execution genuinely needs a **JDK** (compiler). VibeSpace reports it
  honestly - it never fakes output.
- This computer DOES have Java 21, so the demo works here.
- On a computer without Java, show the honest message and demo the other
  languages instead. This is a documented limitation.

## 6. C# code won't run (".NET not installed")

- Same as Java: C# needs the **.NET SDK**.
- This computer has .NET 10, so it works on the demo machine.
- First C# run may need internet once (to restore the SDK packages).
  Subsequent runs work offline.

## 7. Database does not initialize

- The database is created automatically at `database/vibespace.db`.
- Make sure the `database/` folder exists inside the VibeSpace project.
- If `database/vibespace.db` partially exists and is corrupt, close all
  server windows, **rename** the `.db` file to `vibespace.db.old`
  (don't delete), and restart - a fresh database is created.

## 8. Permission denied / cannot write

- The pendrive project folder may be read-only or the computer restricts
  writing.
- Copy the `VibeSpace` folder to the computer's desktop and run from there.
- run.bat shows a "Write access" check warning if this is a problem.

## 9. Browser problem

- VibeSpace is tested on Chrome and Edge.
- If the page says "can't connect", the server is not running. Check the
  server terminal window is still open and shows no errors.

## 10. Pendrive drive letter changed (D: became E:)

- That's fine! VibeSpace never uses a fixed drive letter.
- Simply open the folder wherever the pendrive is mounted
  (e.g. `E:\VibeSpace`) and run `run.bat`.

## 11. Antivirus / script blocking

- Windows SmartScreen or antivirus may warn about `run.bat`.
- Click "More info" → "Run anyway" if it is our own file.
- If `run.bat` is blocked but VS Code works, run VS Code instead:
  `python server.py --host 127.0.0.1 --port 5566`

## 12. Monaco editor not loading (blank editor)

- The Monaco files are in `static/monaco/vs/`. run.bat checks this.
- If the folder is missing/corrupt, re-copy the project from the pendrive
  backup, or re-download monaco-editor (v0.52) and place `min/vs` into
  `static/monaco/vs/`.

## 13. Server does not start at all

1. Make sure you are inside the correct folder (`VibeSpace`).
2. Run from VS Code terminal:
   ```
   python server.py
   ```
3. Read the error printed in the terminal - it usually says exactly what is
   wrong (missing module, syntax error, port busy).
4. If a module is missing, reinstall dependencies (section 3).

## 14. Collaboration / chat not working (but pages load)

- Collaboration uses WebSockets. If the browser blocks WebSockets or the
  server uses a proxy, sync fails.
- For the demo, it's fine: many colleges allow localhost WebSockets.
- Refresh the page - if members list shows only you, open a **second
  browser window** on the same computer to test two users.

## 15. AI shows no findings on clean code

- That is correct and honest: the analyzer is rule-based. Clean code gets
  "No obvious issues detected". Write code with `eval()`, `innerHTML=`,
  a hard-coded password, or an unclosed bracket to demonstrate it firing.