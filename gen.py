#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Marcus Beauregard

"""A tiny static site generator: markdown posts + templates -> HTML."""
import os, sys, re, argparse

TITLE = "{{title}}"
BODY = "{{body}}"

def get_version():
    """Read the project version from pyproject.toml (no dependencies)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyproject.toml")
    try:
        with open(path, encoding="utf-8") as f:
            match = re.search(r'^version\s*=\s*"([^"]+)"', f.read(), re.M)
        if match:
            return match.group(1)
    except OSError:
        pass
    return "unknown"

def render(post_md, template):
    lines = post_md.strip().split("\n")
    out = []
    for line in lines:
        heading = re.match(r"^(#{1,6}) (.*)", line)
        if heading:
            level = len(heading.group(1))
            out.append("<h{0}>{1}</h{0}>".format(level, heading.group(2)))
        else:
            line = line.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            out.append("<p>" + line + "</p>")
    body = "\n".join(out)
    title = lines[0].lstrip("# ").strip()
    return template.replace(TITLE, title).replace(BODY, body)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--template", default="template.html")
    ap.add_argument("--version", action="version", version=get_version())
    args = ap.parse_args()
    try:
        tpl = open(args.template).read()
        os.makedirs(args.out, exist_ok=True)
        for fn in sorted(os.listdir(args.src)):
            path = os.path.join(args.src, fn)
            base, ext = os.path.splitext(fn)
            if ext.lower() != ".md" or not os.path.isfile(path):
                continue
            html = render(open(path).read(), tpl)
            open(os.path.join(args.out, base + ".html"), "w").write(html)
            print("built", fn)
        print("done")
    except Exception as exc:
        print("error: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
