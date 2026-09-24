"""VibeSpace - Offline AI-Assisted Code Analyzer.

This is NOT an LLM. It is a deterministic, rule-based static analysis
engine. It reads the code line by line and looks for real problems:

    - security issues (eval, innerHTML, shell execution, weak passwords)
    - bugs (unbalanced brackets, missing quotes, duplicate code)
    - style / quality issues (long functions, magic numbers)
    - complexity / performance concerns (deep nesting, long lists)

Every finding has: severity, category, line, problem, explanation,
recommendation. The review page groups these into the 7 required
sections. No internet, no API key, no external packages needed.
"""

import os
import re

# ---------------------------------------------------------------------------
# Smart templates (Phase 12)
# ---------------------------------------------------------------------------
TEMPLATES = {
    "python": {
        "label": "Python",
        "code": (
            "# Welcome to VibeSpace!\n"
            "def greet(name):\n"
            "    return f\"Hello, {name}!\"\n"
            "\n"
            "name = input(\"Enter your name: \")\n"
            "print(greet(name))\n"
        ),
    },
    "html": {
        "label": "HTML/CSS/JS",
        "code": (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            "    <title>VibeSpace Page</title>\n"
            "    <style>\n"
            "        body { font-family: sans-serif; background: #0f1117; color: #e6e9f2; }\n"
            "        h1 { color: #7c5cff; }\n"
            "    </style>\n"
            "</head>\n"
            "<body>\n"
            "    <h1>Hello from VibeSpace</h1>\n"
            "    <p>This is a live preview.</p>\n"
            '    <button onclick="document.getElementById(\'msg\').textContent = \'Clicked!\'">Click me</button>\n'
            '    <p id="msg"></p>\n'
            "</body>\n"
            "</html>\n"
        ),
    },
    "java": {
        "label": "Java",
        "code": (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(\"Hello from Java!\");\n"
            "    }\n"
            "}\n"
        ),
    },
    "csharp": {
        "label": "C#",
        "code": (
            "using System;\n"
            "\n"
            "class Program\n"
            "{\n"
            "    static void Main()\n"
            "    {\n"
            "        Console.WriteLine(\"Hello from C#!\");\n"
            "    }\n"
            "}\n"
        ),
    },
    "javascript": {
        "label": "JavaScript",
        "code": (
            '// JavaScript runs in the browser preview\n'
            'const greet = (name) => `Hello, ${name}!`;\n'
            'console.log(greet("VibeSpace"));\n'
            'document.body.innerHTML = "<h2>" + greet("User") + "</h2>";\n'
        ),
    },
    "css": {
        "label": "CSS",
        "code": (
            "body {\n"
            "    background-color: #0f1117;\n"
            "    color: #e6e9f2;\n"
            "}\n"
            ".btn {\n"
            "    background: #7c5cff;\n"
            "    padding: 10px 18px;\n"
            "    border-radius: 8px;\n"
            "}\n"
        ),
    },
}


# ---------------------------------------------------------------------------
# Finding factory
# ---------------------------------------------------------------------------
def _make(severity, category, line, problem, explanation, recommendation):
    return {
        "severity": severity,
        "category": category,
        "line": line,
        "problem": problem,
        "explanation": explanation,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Language helpers
# ---------------------------------------------------------------------------
def _is_python(lang):
    return lang == "python"


def _is_jsfam(lang):
    return lang in ("javascript", "html")


def _is_csharp(lang):
    return lang == "csharp"


def _is_java(lang):
    return lang == "java"


def _paren_balance(lines):
    """Check that ( [ { are balanced. Returns (ok, line_no, name)."""
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for idx, line in enumerate(lines, start=1):
        for ch in line:
            if ch in "([{":
                stack.append(ch)
            elif ch in ")]}":
                if not stack or stack[-1] != pairs[ch]:
                    return False, idx, "bracket"
                stack.pop()
    if stack:
        return False, len(lines), "bracket"
    return True, None, None


def _basic_checks(lines, lang):
    """Warn about line-length, tabs, trailing spaces, TODO, magic numbers."""
    findings = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.rstrip("\n")
        if len(stripped) > 120:
            findings.append(_make(
                "LOW", "code_quality", idx,
                "Very long line (%d characters)" % len(stripped),
                "Lines longer than 120 characters are hard to read and maintain.",
                "Break the line into smaller parts or wrap expressions.",
            ))
        if "\t" in stripped:
            findings.append(_make(
                "LOW", "code_quality", idx,
                "Tab character used for indentation",
                "Tabs can cause inconsistent indentation across editors.",
                "Use 4 spaces instead of tab characters.",
            ))
        if "TODO" in stripped or "FIXME" in stripped:
            findings.append(_make(
                "LOW", "code_quality", idx,
                "TODO / FIXME comment found",
                "Unfinished work must not remain in the final code.",
                "Complete the task or remove the TODO comment.",
            ))
        if "password" in stripped.lower() and ("=" in stripped) and ("input" not in stripped.lower()):
            if re.search(r"password\s*=\s*['\"]", stripped, re.IGNORECASE):
                findings.append(_make(
                    "HIGH", "security", idx,
                    "Hard-coded password detected",
                    "Credentials should never be written directly in source code.",
                    "Move passwords to environment variables.",
                ))
        if re.search(r"(api[_-]?key|secret|token)\s*=\s*['\"][^'\"]{3,}", stripped, re.IGNORECASE):
            findings.append(_make(
                "HIGH", "security", idx,
                "Hard-coded API key / secret detected",
                "Secrets in source code can be stolen and misused.",
                "Store secrets in environment variables or a secret manager.",
            ))
    return findings


def _security_checks(lines, lang):
    findings = []
    patterns = []
    if _is_python(lang):
        patterns = [
            (r"\beval\s*\(", "HIGH", "eval() is dangerous",
             "eval() executes any string as code, which is a major security risk.",
             "Avoid eval(); use safer alternatives like ast.literal_eval()."),
            (r"\bexec\s*\(", "HIGH", "exec() executes arbitrary code",
             "exec() can run code from untrusted input.",
             "Remove exec() usage; parse data instead of executing it."),
            (r"os\.system\s*\(", "HIGH", "Unsafe shell execution via os.system",
             "os.system runs a shell command directly, enabling command injection.",
             "Use subprocess.run with a list of arguments, never a shell string."),
            (r"subprocess\..*shell\s*=\s*True", "HIGH", "subprocess with shell=True",
             "shell=True allows shell metacharacters to be executed.",
             "Pass arguments as a list and set shell=False."),
            (r"INSERT INTO|SELECT |UPDATE |DELETE FROM", "MEDIUM", "Raw SQL query",
             "Building SQL with string concatenation can allow SQL injection.",
             "Use parameterized queries (cursor.execute('...', params))."),
            (r"input\s*\(", "LOW", "input() used without type check",
             "User input is always a string; bad for numeric logic.",
             "Wrap input() with int() or float() where needed."),
        ]
    elif _is_jsfam(lang):
        patterns = [
            (r"\beval\s*\(", "HIGH", "eval() is dangerous",
             "eval() executes any string as code, which is a major security risk.",
             "Remove eval(); use JSON.parse() for data."),
            (r"\.innerHTML\s*=", "HIGH", "innerHTML with dynamic content",
             "Assigning innerHTML with user-controlled data enables XSS attacks.",
             "Use textContent, or escape output before assigning innerHTML."),
            (r"document\.write\s*\(", "MEDIUM", "document.write is discouraged",
             "document.write is slow and unsafe when used with injected content.",
             "Use DOM manipulation APIs like createElement/appendChild."),
        ]
    elif _is_java(lang) or _is_csharp(lang):
        patterns = [
            (r"Runtime\.getRuntime\(\)\.exec|ProcessBuilder", "MEDIUM", "Process execution used",
             "Executing OS processes from Java/C# needs strict input validation.",
             "Validate/whitelist command arguments; never trust user input."),
            (r"static\s+String.*(SELECT |INSERT INTO)", "MEDIUM", "Raw SQL string",
             "Raw SQL strings risk SQL injection.",
             "Use PreparedStatement / parameterized SQL."),
        ]

    for idx, line in enumerate(lines, start=1):
        for pattern, severity, problem, explanation, recommendation in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(_make(
                    severity, "security", idx, problem, explanation, recommendation
                ))
    return findings


def _bug_checks(lines, lang):
    findings = []
    balanced, line_no, kind = _paren_balance(lines)
    if not balanced:
        findings.append(_make(
            "HIGH", "bug", line_no,
            "Unbalanced %s - brackets are not closed properly" % kind,
            "The opening and closing brackets ( ) [ ] { } do not match.",
            "Check the the line indicated and close all opened brackets.",
        ))

    # Unbalanced quotes (crude but useful): count odd double quotes per line
    quote_start = None
    for idx, line in enumerate(lines, start=1):
        # count unescaped double-quotes including triple-quoted strings approx
        bare = re.sub(r"\\\"", "", line)
        if bare.count("\"") % 2 == 1:
            findings.append(_make(
                "MEDIUM", "bug", idx,
                "Possible unclosed string - odd number of double quotes",
                "A string may be missing its closing quote on this line.",
                "Close the string with a matching double quote.",
            ))

    # duplicate lines (code smell)
    seen = {}
    for idx, line in enumerate(lines, start=1):
        s = line.strip()
        if len(s) < 12:
            continue
        seen.setdefault(s, []).append(idx)
    for s, idxs in seen.items():
        if len(idxs) >= 3:
            findings.append(_make(
                "LOW", "bug", idxs[0],
                "Repeated identical line (%d times)" % len(idxs),
                "Duplicated code is harder to maintain and often a copy-paste mistake.",
                "Refactor the repeated logic into a function or loop.",
            ))
    return findings


def _quality_checks(lines, lang):
    findings = []
    # functions / methods that are too long
    fn_indent = 0
    fn_start = 0
    fn_count = 0
    inside = False
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.match(r"^(def |public static void main|public static .*\(|class |function |=>)", stripped):
            inside = True
            fn_start = idx
            fn_count = 0
            fn_indent = len(line) - len(line.lstrip())
        elif inside and stripped:
            if len(line) - len(line.lstrip()) <= fn_indent and not stripped.startswith((")", "}", "]")):
                inside = False
                if fn_count > 40:
                    findings.append(_make(
                        "LOW", "code_quality", fn_start,
                        "Long function/block (%d lines)" % fn_count,
                        "Long functions are hard to read, test and maintain.",
                        "Split the function into smaller helper functions.",
                    ))
            else:
                fn_count += 1

    # comments ratio
    total = max(1, len([l for l in lines if l.strip()]))
    comments = len([l for l in lines if l.strip().startswith(("#", "//", "/*", "--"))])
    if total >= 15 and comments < 2:
        findings.append(_make(
            "LOW", "code_quality", 1,
            "No comments in a %d-line file" % total,
            "Complex code without comments is difficult for others to understand.",
            "Add short comments explaining the purpose of key blocks.",
        ))
    return findings


def _complexity_checks(lines, lang):
    findings = []
    # deep nesting
    max_depth = 0
    cur = 0
    for line in lines:
        if re.match(r"^\s", line):
            cur = len(line) - len(line.lstrip())
            if cur > 48:
                findings.append(_make(
                    "LOW", "complexity", 1,
                    "Deep indentation (over 48 spaces)",
                    "Very deep nesting makes code hard to follow.",
                    "Extract nested logic into functions.",
                ))
                break
    # suspicious infinite loops
    for idx, line in enumerate(lines, start=1):
        if re.search(r"\bwhile\s+True\b", line):
            # check for a break in the following 30 lines
            snippet = "".join(lines[idx:idx + 30])
            if "break" not in snippet:
                findings.append(_make(
                    "MEDIUM", "complexity", idx,
                    "while True loop with no visible break",
                    "This loop may never end (infinite loop risk).",
                    "Add a break condition or a counter that stops the loop.",
                ))
    # cycles
    for idx, line in enumerate(lines, start=1):
        if re.search(r"\bfor\s+.*\bin\b", line) and re.search(r"\bfor\s+.*\bin\b", "".join(lines[idx:idx + 5])):
            findings.append(_make(
                "LOW", "performance", idx,
                "Nested loop detected",
                "Nested loops can make the program very slow for large inputs.",
                "Try to reduce the number of nested loops.",
            ))
    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def analyze_code(code, language="python"):
    """Return a list of findings for the given code."""
    if not isinstance(code, str):
        return []
    lines = code.split("\n")
    findings = []
    findings += _basic_checks(lines, language)
    findings += _security_checks(lines, language)
    findings += _bug_checks(lines, language)
    findings += _quality_checks(lines, language)
    findings += _complexity_checks(lines, language)

    # clean duplicates (same line + same problem)
    seen = set()
    unique = []
    for f in findings:
        key = (f["line"], f["problem"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(f)
    unique.sort(key=lambda f: (f["line"], f["severity"]))
    return unique


def _group(findings):
    sections = {
        "SUMMARY": [],
        "BUGS": [],
        "SECURITY": [],
        "CODE_QUALITY": [],
        "COMPLEXITY": [],
        "PERFORMANCE": [],
        "RECOMMENDATIONS": [],
    }
    category_map = {
        "bug": "BUGS",
        "security": "SECURITY",
        "code_quality": "CODE_QUALITY",
        "complexity": "COMPLEXITY",
        "performance": "PERFORMANCE",
    }
    for f in findings:
        sections[category_map.get(f["category"], "CODE_QUALITY")].append(f)
        sections["RECOMMENDATIONS"].append(f["recommendation"])
    return sections


def review_code(code, language="python"):
    """Produce the full AI Review report (used by the review page)."""
    findings = analyze_code(code, language)
    sections = _group(findings)

    high = len([f for f in findings if f["severity"] == "HIGH"])
    med = len([f for f in findings if f["severity"] == "MEDIUM"])
    low = len([f for f in findings if f["severity"] == "LOW"])

    score = max(0, 100 - (high * 12 + med * 6 + low * 2))
    if not findings:
        score = 100

    if score >= 90:
        grade = "A - Excellent"
        verdict = "The code looks clean. Small improvements remain."
    elif score >= 75:
        grade = "B - Good"
        verdict = "Solid code with a few fixable issues."
    elif score >= 55:
        grade = "C - Needs Attention"
        verdict = "Several issues should be fixed before this is final."
    else:
        grade = "D - Critical"
        verdict = "Important problems found. Fix the high-severity items first."

    summary = {
        "total": len(findings),
        "high": high,
        "medium": med,
        "low": low,
        "score": score,
        "grade": grade,
        "verdict": verdict,
    }

    # human summary line
    if not findings:
        summary["summary_text"] = "No significant issues detected by the offline analyzer."
    else:
        summary["summary_text"] = (
            "The analyzer found %d issue(s): %d high, %d medium, %d low. "
            "The offline rule-based analyzer reviewed the code for security, "
            "bugs, style and performance." % (len(findings), high, med, low)
        )

    sections["SUMMARY"] = [
        {
            "problem": summary["summary_text"],
            "explanation": ("Overall quality score: %d/100 (%s). %s" % (score, grade, verdict)),
            "recommendation": (
                "Fix HIGH severity items first (security and bugs), "
                "then address MEDIUM, and finally LOW."
            ),
        }
    ]

    return {"summary": summary, "sections": sections, "findings": findings}


def get_language_list():
    return [{"id": k, "label": v["label"]} for k, v in TEMPLATES.items()]