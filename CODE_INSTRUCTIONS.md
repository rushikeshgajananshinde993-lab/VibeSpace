# VibeSpace — How to Run in VS Code (Step by Step)

Follow these steps in order. Tick each checkbox as you complete it.

## BEFORE YOU START
- [ ] Pendrive connected
- [ ] Open the folder: in VS Code `File > Open Folder` and choose `D:\VibeSpace`

---

## STEP 1 — First time: install dependencies
1. Open VS Code Terminal: menu `Terminal > New Terminal`
2. Copy-paste this exact command and press Enter:

```
python -m pip install --no-index --find-links="vendor/wheels" -r requirements.txt
```

> What you should see: lines saying "Successfully installed Flask-3.1.3 ..."
> If pip is missing: run `python -m pip install --upgrade pip` (needs internet once).

## STEP 2 — Start the server
In the same terminal, run:

```
python server.py --host 127.0.0.1 --port 5566
```

> What you should see:
> ```
> Database : D:\VibeSpace\database\vibespace.db
> Server   : http://127.0.0.1:5566
> ```
> The terminal stays busy (that is correct — it is the running server).

## STEP 3 — Open in browser
- Keep the terminal running
- Open browser and go to: **http://127.0.0.1:5566/**
- You should see the VibeSpace homepage.

## STEP 4 — Stop the server
- In VS Code Terminal press `Ctrl + C` then `Y`

---

## QUICKER WAY (after step 1 is done once)
1. Open VS Code: `Ctrl+Shift+P` and type `Tasks: Run Task`
2. Choose **Run VibeSpace server**
3. Open http://127.0.0.1:5566/

---

## Or press F5 (Debug)
1. Open `server.py`
2. Press `F5`
3. VS Code starts the server with debugging icons
4. Open http://127.0.0.1:5566/

---

## IF SOMETHING GOES WRONG

| Problem | Fix |
|---|---|
| `'python' is not recognized` | Python not installed / not in PATH. Install Python from python.org and tick "Add Python to PATH". |
| `ModuleNotFoundError: No module named 'flask'` | Run Step 1 again (dependencies). |
| `Address already in use` | Change port: use `--port 5567` instead of 5566. |
| Browser can't open page | The server window must stay running. Check terminal shows the Server line. |
| Chinese/weird text in terminal | That's normal VS Code terminal encoding; homepage is fine. |

---

## MEMORY TRICK FOR VIVA
"VibeSpace ko VS Code me chalaane ke liye hamen do commands chahiye:
1. `pip install` — dependencies (libraries) install karne ke liye
2. `python server.py` — server start karne ke liye
Server chalta hai to hum browser me http://127.0.0.1:5566/ kholte hain."