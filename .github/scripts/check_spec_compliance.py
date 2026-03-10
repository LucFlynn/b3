"""
Spec Compliance Checker
Compares files changed in a PR against the spec's allowed file list.
Flags any file modifications not authorized by the spec.

Usage: python check_spec_compliance.py <changed_files.txt>
Output: writes report to /tmp/spec_compliance_report.md
"""

import sys
import os
import re
from pathlib import Path


def find_spec_file():
    """Look for a spec file in the repo. Check multiple locations."""
    candidates = [
        "SPEC.md",
        "spec.md", 
        "docs/SPEC.md",
        ".github/SPEC.md",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def extract_allowed_files(spec_content):
    """
    Parse the spec to find files that are explicitly mentioned as okay to change.
    
    Looks for file paths in sections like:
    - "Files Likely Touched"
    - "Files to Create/Modify"
    - "What to change"
    - "Create:" / "Modify:" lists
    
    Extracts anything that looks like a file path:
    - Contains a / and ends with a file extension
    - Or starts with backend/, frontend/, .github/, scripts/, etc.
    """
    allowed = set()
    
    # Known project directories — anything starting with these is a file path
    known_prefixes = [
        "backend/", "frontend/", "pixel/", "slack_bot/",
        "scripts/", ".github/", "docs/", "db/",
        "test_site/", "mocks/",
    ]
    
    # Known file extensions
    file_extensions = [
        ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yml", ".yaml",
        ".md", ".sh", ".sql", ".css", ".html", ".toml", ".cfg", ".txt",
        ".env", ".gitignore", ".dockerignore",
    ]
    
    # Also look for specific known files
    known_files = [
        "ARCHITECTURE.md", "CLAUDE.md", "AGENT.md", "SPEC.md",
        "docker-compose.yml", "Dockerfile", "Makefile",
        ".gitignore", "requirements.txt", "package.json",
    ]
    
    for line in spec_content.split("\n"):
        stripped = line.strip().lstrip("-").lstrip("*").lstrip("#").strip()
        stripped = stripped.strip("`").strip()
        
        # Remove common prefixes from bullet points
        for prefix in ["Create:", "Modify:", "Update:", "Add:", "Change:", "Edit:"]:
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix):].strip()
        
        # Check for file paths
        for token in stripped.split():
            # Clean up markdown formatting
            token = token.strip("`").strip("*").strip("_").strip(",").strip(")")
            
            # Remove trailing description after " —" or " -" or " ("
            token = token.split(" —")[0].split(" —")[0]
            
            # Check if it looks like a known project file
            for prefix in known_prefixes:
                if token.startswith(prefix):
                    allowed.add(token)
                    break
            
            # Check if it's a known standalone file
            if token in known_files:
                allowed.add(token)
            
            # Check if it has a file extension and a directory separator
            for ext in file_extensions:
                if token.endswith(ext) and "/" in token:
                    allowed.add(token)
                    break
    
    return allowed


def extract_do_not_modify(spec_content):
    """
    Look for files explicitly marked as DO NOT modify.
    These are hard blocks — flag them as critical if changed.
    """
    blocked = set()
    
    # Look for "Do NOT modify" or "No changes to" sections
    in_blocked_section = False
    
    for line in spec_content.split("\n"):
        lower = line.lower().strip()
        
        # Detect blocked sections
        if any(phrase in lower for phrase in [
            "do not modify", "do not touch", "do not change",
            "no changes to", "don't modify", "don't touch",
            "do not create new", "do not rebuild",
        ]):
            in_blocked_section = True
            continue
        
        # End of blocked section (empty line or new header)
        if in_blocked_section and (lower == "" or lower.startswith("#")):
            in_blocked_section = False
            continue
        
        if in_blocked_section:
            # Extract file paths or keywords from blocked items
            stripped = line.strip().lstrip("-").lstrip("*").strip()
            for token in stripped.split():
                token = token.strip("`").strip("*")
                if "/" in token and any(token.endswith(ext) for ext in [".py", ".ts", ".tsx", ".js", ".yml"]):
                    blocked.add(token)
            
            # Also check for keyword-based blocks
            keyword_blocks = {
                "pixel": ["pixel/"],
                "slack bot": ["slack_bot/"],
                "auth": ["middleware.ts", "security.py"],
                "clerk": ["middleware.ts", "@clerk"],
                "docker": ["Dockerfile", "docker-compose.yml"],
                "deployment": ["deploy_backend.sh", "deploy_frontend.sh"],
            }
            for keyword, paths in keyword_blocks.items():
                if keyword in lower:
                    for p in paths:
                        blocked.add(p)
    
    return blocked


def categorize_changes(changed_files, allowed_files, blocked_patterns):
    """Categorize each changed file as authorized, unauthorized, or critical."""
    authorized = []
    unauthorized = []
    critical = []  # files explicitly blocked by the spec
    
    # Always allowed — these are meta files that any PR might touch
    always_ok = {
        "SPEC.md", "spec.md",
        ".github/workflows/spec-compliance.yml",
        ".github/scripts/check_spec_compliance.py",
    }
    
    for filepath in changed_files:
        filepath = filepath.strip()
        if not filepath:
            continue
        
        # Always allowed files
        if filepath in always_ok:
            authorized.append((filepath, "always allowed"))
            continue
        
        # Check against critical/blocked patterns
        is_critical = False
        for blocked in blocked_patterns:
            if blocked in filepath:
                critical.append((filepath, f"blocked by spec (matches '{blocked}')"))
                is_critical = True
                break
        
        if is_critical:
            continue
        
        # Check against allowed files from spec
        is_allowed = False
        for allowed in allowed_files:
            # Exact match
            if filepath == allowed:
                is_allowed = True
                authorized.append((filepath, "in spec"))
                break
            # Directory match (spec says "backend/app/routers/" and file is in that dir)
            if allowed.endswith("/") and filepath.startswith(allowed):
                is_allowed = True
                authorized.append((filepath, f"in spec directory ({allowed})"))
                break
            # Partial match — file is referenced in the spec even if not exact
            if allowed in filepath or filepath in allowed:
                is_allowed = True
                authorized.append((filepath, f"likely match ({allowed})"))
                break
        
        if not is_allowed:
            unauthorized.append((filepath, "NOT in spec"))
    
    return authorized, unauthorized, critical


def generate_report(spec_file, authorized, unauthorized, critical, changed_count):
    """Generate a markdown report for the PR comment."""
    lines = []
    lines.append("# 🔍 Spec Compliance Check")
    lines.append("")
    
    if spec_file:
        lines.append(f"Spec file: `{spec_file}`")
    else:
        lines.append("⚠️ **No SPEC.md found in this branch.**")
        lines.append("")
        lines.append("Every feature branch should include a `SPEC.md` file listing which files")
        lines.append("are expected to be modified. Without a spec, all changes are flagged as unverified.")
        lines.append("")
        lines.append(f"This PR modifies **{changed_count} files** with no spec to check against.")
        lines.append("")
        lines.append("Add a `SPEC.md` to the root of this branch with a 'Files Likely Touched' section.")
        return "\n".join(lines)
    
    lines.append(f"Files changed: **{changed_count}**")
    lines.append("")
    
    # Critical violations — files explicitly blocked
    if critical:
        lines.append("## 🚨 CRITICAL — Blocked Files Modified")
        lines.append("")
        lines.append("These files are explicitly marked as **DO NOT MODIFY** in the spec:")
        lines.append("")
        for filepath, reason in critical:
            lines.append(f"- ❌ `{filepath}` — {reason}")
        lines.append("")
        lines.append("**Do NOT merge this PR until these changes are removed or the spec is updated.**")
        lines.append("")
    
    # Unauthorized changes
    if unauthorized:
        lines.append("## ⚠️ Unauthorized Changes")
        lines.append("")
        lines.append("These files were modified but are **not listed in the spec**:")
        lines.append("")
        for filepath, reason in unauthorized:
            lines.append(f"- ⚠️ `{filepath}` — {reason}")
        lines.append("")
        lines.append("Review these changes carefully. They may be necessary but were not planned.")
        lines.append("")
    
    # Authorized changes
    if authorized:
        lines.append("## ✅ Authorized Changes")
        lines.append("")
        for filepath, reason in authorized:
            lines.append(f"- ✅ `{filepath}` — {reason}")
        lines.append("")
    
    # Summary
    lines.append("---")
    lines.append("")
    
    if critical:
        lines.append("**Result: ❌ FAIL** — Critical files were modified that the spec explicitly blocks.")
    elif unauthorized:
        lines.append(f"**Result: ⚠️ WARNING** — {len(unauthorized)} file(s) changed outside the spec. Review before merging.")
    else:
        lines.append("**Result: ✅ PASS** — All changes match the spec.")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_spec_compliance.py <changed_files.txt>")
        sys.exit(1)
    
    # Read changed files
    changed_files_path = sys.argv[1]
    with open(changed_files_path, "r") as f:
        changed_files = [line.strip() for line in f.readlines() if line.strip()]
    
    print(f"Found {len(changed_files)} changed files")
    
    # Find and read spec
    spec_file = find_spec_file()
    
    if spec_file:
        print(f"Found spec: {spec_file}")
        with open(spec_file, "r") as f:
            spec_content = f.read()
        
        allowed_files = extract_allowed_files(spec_content)
        blocked_patterns = extract_do_not_modify(spec_content)
        
        print(f"Allowed files from spec: {len(allowed_files)}")
        for f in sorted(allowed_files):
            print(f"  + {f}")
        
        print(f"Blocked patterns from spec: {len(blocked_patterns)}")
        for f in sorted(blocked_patterns):
            print(f"  x {f}")
        
        authorized, unauthorized, critical = categorize_changes(
            changed_files, allowed_files, blocked_patterns
        )
    else:
        print("No spec file found")
        authorized = []
        unauthorized = [(f, "no spec to check against") for f in changed_files]
        critical = []
    
    # Generate report
    report = generate_report(
        spec_file, authorized, unauthorized, critical, len(changed_files)
    )
    
    # Write report
    report_path = "/tmp/spec_compliance_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\nReport written to {report_path}")
    print(report)
    
    # Exit with error code if critical violations found
    if critical:
        print("\n❌ CRITICAL: Blocked files were modified!")
        sys.exit(1)
    
    # Warning exit code for unauthorized but non-critical changes
    # (don't block the PR, just flag it)
    if unauthorized:
        print(f"\n⚠️ WARNING: {len(unauthorized)} unauthorized changes")
    else:
        print("\n✅ All changes match spec")


if __name__ == "__main__":
    main()
