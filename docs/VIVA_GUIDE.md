# VIVA_GUIDE.md — Everything to explain in your exam

Read this a few times before the viva. Speak in simple sentences.
If you don't know something, say: "I can explain the part I built and tested."

---

## 1. Project Introduction

> "VibeSpace is a web-based collaborative coding platform. It combines
> real-time code collaboration, communication (chat), code execution,
> version history and offline AI-assisted code analysis in one
> application. Multiple developers join a room through a shareable link
> and build code together in a browser-based editor - the same Monaco
> editor used by VS Code."

## 2. Problem Statement

> "Developers usually edit code alone or need complex tools to
> collaborate in real time. Existing setups require installation,
> accounts and internet. VibeSpace solves this with a portable web
> application that runs from a pendrive, needs no internet, and lets
> people code together instantly by sharing a link."

## 3. Objectives

- Provide real-time collaborative coding in rooms
- Make it portable (runs from a pendrive)
- Work without internet and without paid AI APIs
- Offer code execution (HTML/Python/Java/C#)
- Provide offline AI-assisted code analysis
- Save and restore versions of code
- Provide an admin dashboard

## 4. Existing System

> "Existing systems like VS Code Live Share need installation and an
> account. Cloud IDEs need internet. They are not portable on a
> pendrive and not designed for a classroom demo."

## 5. Proposed System

> "A self-contained Flask web application that runs locally. Users
> register, create rooms, share links, collaborate, chat, run code,
> and get AI feedback - all without internet."

## 6. Features

- Register/Login/Logout with roles
- Room system with shareable links
- Real-time collaboration (Socket.IO)
- Three minimizable chat panels
- Code runner (HTML/CSS/JS preview, Python, Java, C#)
- Offline AI Code Watch + AI Review report
- Smart templates
- Version history (save/view/compare/restore)
- Admin dashboard

## 7. Technology Stack (and WHY - very common question)

- **Flask** → "A lightweight Python web framework for the backend/routes."
- **Flask-SocketIO** → "Real-time communication between browser and server."
- **SQLite** → "A lightweight file-based database, perfect for a portable project."
- **HTML/CSS/JavaScript** → "Frontend: structure, styling, behaviour."
- **Monaco Editor** → "The browser-based code editor engine used by VS Code."
- **Offline AI analyzer** → "Our own rule-based static analyzer - not a cloud API."

## 8. System Architecture

> "Client (browser: HTML/CSS/JS + Monaco) talks to the Flask server
> through HTTP for pages and through Socket.IO for real-time events.
> The server uses a database layer (SQLite) to store users, rooms,
> messages and versions. Code execution uses a controlled subprocess,
> and the AI analyzer is a separate module with detection rules."

Draw this diagram:
```
Browser -> Flask server -> SQLite
                  |
                  +-> code_runner (Python/Java/C#)
                  +-> ai_engine  (rule-based analysis)
```

## 9. Database Design

5 tables:
- `users` (id, username, email, password_hash, role, created_at)
- `rooms` (id, room_code, name, owner_id, created_at)
- `room_members` (id, room_id, user_id, joined_at)
- `messages` (id, room_id, user_id, message_type, content, created_at)
- `code_versions` (id, room_id, code, language, username, created_at)

> "Database file: `database/vibespace.db`."

## 10. Authentication

> "Passwords are hashed with Werkzeug (`generate_password_hash`) before
> being stored - never plain text. Login verifies the hash, then creates
> a secure session cookie. First registered user becomes admin."

## 11. Dashboard

> "After login the user sees: create room, join room with a code, my
> rooms, recent rooms, and the code-runner status of the computer."

## 12. Rooms

> "Creating a room generates a unique code like ABC123. The share link
> is `http://.../join/ABC123`. Anyone who opens the link joins the room.
> Membership is stored in the `room_members` table."

## 13. Socket.IO

> "Socket.IO keeps a continuous two-way connection open between the
> browser and server. When a user types, the server broadcasts the
> change to everyone else in the room. It powers collaboration, chat and
> cursor sharing."

## 14. Monaco Editor

> "Monaco is the open-source editor engine VS Code is built on. We
> bundle it locally in `static/monaco` so it works without internet."

## 15. Code Runner

> "- HTML/CSS/JS run directly in a browser preview iframe.
> - Python is executed in a subprocess with a timeout and output limit.
> - Java needs a JDK (compiled with javac). C# needs the .NET SDK.
> If Java/.NET is missing, we show a clear message - we never fake output."

## 16. AI Analyzer

> "It is NOT a cloud AI or LLM. It is a deterministic rule-based static
> analyzer we wrote. It checks for eval(), risky innerHTML, hard-coded
> passwords/API keys, unbalanced brackets, very long lines, duplicate
> code and similar real problems, and reports severity, line, problem,
> explanation and recommendation. It needs no API key and no internet."

## 17. Chat

> "Three chat panels: General, Code-Context and Media/Photos. All
> minimizable. Messages go through Socket.IO and are stored in the
> `messages` table. Media photos are sent as image data and shown in the
> panel."

## 18. Version History

> "We don't save every keystroke. Versions are saved manually (Save v
> button) and the latest code is kept in the room. Users can view,
> compare and restore any version. Stored in the `code_versions` table."

## 19. Admin

> "The admin panel (only for role=admin) shows users (ID, username,
> email, role, registration date - never passwords), all rooms, and
> statistics. The first registered user automatically becomes admin."

## 20. Security

- Passwords hashed, never plain text
- Sessions protected with a random secret key
- Chat content displayed safely (no raw HTML injection)
- Code execution in a subprocess with timeout + output limits (no os.system)
- Input validation on registration

## 21. Portability

> "Everything is inside one `VibeSpace` folder: code, database, Monaco,
> dependencies (as local wheels). No absolute paths. It runs from any
> drive letter. run.bat detects Python and installs dependencies from
> local wheels if there is no internet."

## 22. Limitations (be honest - examiners respect this)

1. Java execution requires a JDK; C# requires the .NET SDK.
2. Code execution is a demo, not a production sandbox.
3. Offline AI analysis is rule-based, not an LLM.
4. Collaboration is simple last-change-wins sync, not a CRDT.
5. Portable execution can be limited by computer permissions/antivirus.
6. Very large images/files have size limits.

## 23. Future Scope

- Add a real CRDT (like Yjs) for perfect conflict-free sync
- Add voice/video calls (WebRTC)
- Add a real sandboxed container for safer code execution
- Add optional cloud LLM for advanced AI review
- Export projects / connect to Git

---

# 30+ Common Viva Questions (short answers)

**1. What is VibeSpace?**
A web app for real-time collaborative coding with chat, code execution,
version history and offline AI analysis.

**2. Why did you choose Flask?**
It is a lightweight Python web framework, easy to learn, explain and extend.

**3. Why SQLite?**
It is a lightweight file-based database, ideal for a portable student project
with no installation.

**4. What is Socket.IO?**
It enables real-time two-way communication between browser and server, used
for collaboration and chat.

**5. What is Monaco?**
The browser-based code editor engine used by VS Code; we bundle it locally.

**6. How does login work?**
The form submits the username/password, Flask verifies the stored hash, then
creates a session.

**7. Where is user data stored?**
In the local SQLite database at `database/vibespace.db`, in the `users` table.

**8. How are passwords protected?**
They are hashed (one-way) with Werkzeug before storing; plain text is never
saved and never shown.

**9. How does room creation work?**
A unique room code is generated, a row is inserted into `rooms`, and the
creator becomes a member; a share link is produced.

**10. How does collaboration work?**
Users connect via Socket.IO. When one types, the server broadcasts the change
to everyone else in the same room.

**11. Is it a CRDT?**
No. It is simple last-change-wins synchronization - suitable for this demo,
and we document that honestly.

**12. How does chat work?**
Browser sends the message via Socket.IO; server stores it in `messages` and
broadcasts it to the room.

**13. Why three chat panels?**
General chat, code-context chat, and media/photos - each has a clear purpose.

**14. How does code execution work?**
HTML/CSS/JS run in a browser iframe; Python, Java and C# run in a controlled
subprocess with timeout and output limits.

**15. Is there a risk with running code?**
We never use os.system, we enforce timeout and output limits; but a
production-grade sandbox would need stronger isolation - a documented limit.

**16. What is the AI analyzer?**
An offline rule-based static analyzer that detects real issues like eval(),
unsafe innerHTML, hard-coded passwords and syntax problems.

**17. Is the AI a real LLM?**
No. It is rule-based so the demo works 100% offline without an API key.

**18. What if Java is not installed?**
Java execution reports an honest message; we never fake output.

**19. What if .NET is not installed?**
Same as Java - C# execution shows a clear message.

**20. What if there is no internet?**
Almost everything works: Monaco, database, AI analyzer, Python runner, and
dependencies install from local wheels.

**21. What are the project limitations?**
Java/C# need their runtimes; execution is not a hard sandbox; AI is
rule-based; collaboration is not a full CRDT.

**22. Why is the project portable?**
Everything lives in one folder with local wheels and local assets, uses
relative paths, and works from any drive letter on a pendrive.

**23. How does version history work?**
Versions are explicitly saved to `code_versions`; the user can view,
compare or restore any saved version.

**24. How is the admin created?**
The first registered user automatically gets the admin role.

**25. Can the examiner see the database?**
Yes - through the admin panel (users without passwords) or by opening the
`database/vibespace.db` file.

**26. What tables are in the database?**
users, rooms, room_members, messages, code_versions.

**27. What is a session?**
A small server-set cookie that remembers who is logged in.

**28. How did you test the project?**
By registering two accounts (or using two browser windows), joining the same
room, typing together, running code, and saving/restoring versions.

**29. What is a subprocess?**
Running another program (like the Python interpreter) as a separate process
from our server with control over time and output.

**30. What is the future scope?**
Real CRDT sync, WebRTC calls, container sandboxing, optional cloud AI and Git
integration.

**31. Why use JavaScript on the frontend?**
To make the page interactive and to communicate with the server in real time.

**32. What is the difference between GET and POST?**
GET requests data (e.g. open a page); POST sends data (e.g. submit a form).

**33. What is a foreign key?**
It links a row in one table to a row in another (e.g. room_members.room_id →
rooms.id).

**34. How do you run the project from a pendrive?**
Double-click `run.bat`; it checks the environment, installs dependencies from
local wheels, starts the server and opens the browser.

**35. Did you use any paid service?**
No. Everything - Flask, Socket.IO, Monaco, SQLite - is free and open source.

**36. What did YOU personally build?**
The whole application: Flask backend, SQLite schema, Socket.IO events,
Monaco integration, code runner, the rule-based AI analyzer, chat, version
history, admin panel and the launcher.