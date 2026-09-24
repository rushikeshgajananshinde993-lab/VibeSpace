"""VibeSpace - Code Runner.

Safely (for a student project) executes user code:

    - HTML/CSS/JavaScript : rendered in the browser preview panel (client-side)
    - Python  : run in a subprocess with timeout + output limits
    - Java    : compiled with javac and run, IF a JDK is installed
    - C#      : compiled with .NET and run, IF the .NET SDK is installed

Honest notes (also in VIVA_GUIDE.md):
  1. This is a final-year demonstration, NOT a production sandbox.
  2. If Java/.NET is missing, we report clearly - we never fake output.
  3. We never use os.system() - only subprocess with argument lists.
"""

import os
import subprocess
import sys
import tempfile
import uuid

import config

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def _truncate(text, limit=None):
    limit = limit or config.MAX_OUTPUT_CHARS
    if text is None:
        return ""
    text = str(text)
    if len(text) > limit:
        return text[:limit] + "\n...[output truncated]"
    return text


def _run_command(cmd, timeout=None, cwd=None):
    """Run a command, capture stdout/stderr. Never via a shell."""
    timeout = timeout or config.CODE_TIMEOUT_SECONDS
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            creationflags=CREATE_NO_WINDOW,
        )
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": _truncate(result.stdout),
            "stderr": _truncate(result.stderr),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "Timeout: the code ran for more than %d seconds and was stopped." % timeout,
        }
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": "Program not found: %s" % exc,
        }


def _workspace_file(subdir, name):
    folder = os.path.join(config.BASE_DIR, config.WORKSPACE_FOLDER, subdir)
    os.makedirs(folder, exist_ok=True)
    return folder, os.path.join(folder, name)


# ---------------------------------------------------------------------------
# Individual language runners
# ---------------------------------------------------------------------------
def run_python(code):
    folder, path = _workspace_file("python", "script_%s.py" % uuid.uuid4().hex[:6])
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    return _run_command([sys.executable, path], timeout=config.CODE_TIMEOUT_SECONDS)


def run_java(code):
    javac = _tool("javac")
    java = _tool("java")
    if not javac or not java:
        return {
            "ok": False,
            "stdout": "",
            "stderr": "Java execution is unavailable because a JDK is not installed on this computer.",
        }
    token = uuid.uuid4().hex[:6]
    folder = os.path.join(config.BASE_DIR, config.WORKSPACE_FOLDER, "java", "Run_%s" % token)
    os.makedirs(folder, exist_ok=True)
    main_file = os.path.join(folder, "Main.java")
    with open(main_file, "w", encoding="utf-8") as f:
        f.write(code)

    compile_result = _run_command(["javac", "Main.java"], cwd=folder)
    if not compile_result["ok"]:
        return {
            "ok": False,
            "stdout": "",
            "stderr": "Java compilation failed:\n" + compile_result["stderr"] +
                      compile_result["stdout"],
        }
    run_result = _run_command(["java", "Main"], cwd=folder,
                              timeout=config.CODE_TIMEOUT_SECONDS)
    run_result["lang_note"] = "Java (compiled with javac, then executed)"
    return run_result


def run_csharp(code):
    dotnet = _tool("dotnet")
    if not dotnet:
        return {
            "ok": False,
            "stdout": "",
            "stderr": "C# execution is unavailable because the .NET SDK is not installed on this computer.",
        }

    token = uuid.uuid4().hex[:6]
    folder = os.path.join(config.BASE_DIR, config.WORKSPACE_FOLDER, "csharp", "Proj_%s" % token)
    os.makedirs(folder, exist_ok=True)

    with open(os.path.join(folder, "Program.cs"), "w", encoding="utf-8") as f:
        f.write(code)

    csproj = (
        "<Project Sdk=\"Microsoft.NET.Sdk\">\n"
        "  <PropertyGroup>\n"
        "    <OutputType>Exe</OutputType>\n"
        "    <TargetFramework>net10.0</TargetFramework>\n"
        "    <Nullable>disable</Nullable>\n"
        "    <ImplicitUsings>enable</ImplicitUsings>\n"
        "  </PropertyGroup>\n"
        "</Project>\n"
    )
    with open(os.path.join(folder, "Proj_%s.csproj" % token), "w", encoding="utf-8") as f:
        f.write(csproj)

    run_result = _run_command([dotnet, "run", "--project", folder],
                              timeout=min(config.CODE_TIMEOUT_SECONDS + 10, 30))
    if not run_result["ok"]:
        # Network-restore issues vs code errors: keep message honest
        err = run_result["stderr"] + "\n" + run_result["stdout"]
        if "NU" in err and "restore" in err.lower():
            run_result["stderr"] = ("C# build/restore could not complete. "
                                    "First run of .NET may need internet once.\n" + err)
        return run_result
    run_result["lang_note"] = "C# (compiled with .NET SDK, then executed)"
    return run_result


def _tool(name):
    from shutil import which
    return which(name)


# ---------------------------------------------------------------------------
# Public dispatch
# ---------------------------------------------------------------------------
def run_code(language, code):
    """Dispatch code to the correct runner. Returns a dict for JSON response."""
    if not isinstance(code, str):
        return {"ok": False, "stdout": "", "stderr": "Code must be text."}
    if len(code) > config.MAX_CODE_CHARS:
        return {
            "ok": False,
            "stdout": "",
            "stderr": "Code is too large (limit is %d characters)." % config.MAX_CODE_CHARS,
        }

    language = (language or "python").lower()

    if language == "python":
        return run_python(code)
    if language == "java":
        return run_java(code)
    if language in ("csharp", "c#"):
        return run_csharp(code)

    # html/css/javascript run in the browser preview panel - handled client-side.
    return {
        "ok": True,
        "kind": "preview",
        "stdout": "",
        "stderr": "",
        "note": "HTML/CSS/JavaScript runs in the browser preview panel.",
    }


def tool_status():
    """Report which runtimes are available (used by demo/admin)."""
    return {
        "python": "available",
        "java": "available" if _tool("javac") and _tool("java") else "not installed",
        "dotnet": "available" if _tool("dotnet") else "not installed",
    }