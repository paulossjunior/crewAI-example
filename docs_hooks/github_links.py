"""MkDocs hook: rewrite relative links that point outside docs_dir to GitHub.

Docs link to source files (e.g. ``../../src/dinner_crew/models.py``) that live
outside ``docs/`` and therefore are not part of the built site. This hook turns
those links into absolute GitHub URLs. Links that stay inside ``docs/`` are left
untouched so MkDocs can validate and resolve them as usual.
"""

from __future__ import annotations

import os
import re

REPO_URL = "https://github.com/paulossjunior/crewAI-example"
BRANCH = "main"

# Inline Markdown links/images: ](target) or ](target "title")
LINK_RE = re.compile(r'\]\((?P<target>[^)\s]+)(?P<title>\s+"[^"]*")?\)')
FENCE_RE = re.compile(r"^(\s*)(```|~~~)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def _rewrite(target: str, page_dir: str, docs_dir: str, repo_root: str) -> str:
    if target.startswith(("#", "/")) or SCHEME_RE.match(target):
        return target
    path, sep, anchor = target.partition("#")
    if not path:
        return target
    resolved = os.path.normpath(os.path.join(page_dir, path))
    if os.path.commonpath([resolved, docs_dir]) == docs_dir:
        return target  # inside docs/: keep relative
    rel = os.path.relpath(resolved, repo_root)
    if rel.startswith(".."):
        return target  # outside the repository: leave as is
    kind = "tree" if os.path.isdir(resolved) else "blob"
    url = f"{REPO_URL}/{kind}/{BRANCH}/{rel.replace(os.sep, '/')}"
    return url + (sep + anchor if sep else "")


def on_page_markdown(markdown, page, config, files):
    docs_dir = os.path.abspath(config["docs_dir"])
    repo_root = os.path.dirname(os.path.abspath(config["config_file_path"]))
    page_dir = os.path.dirname(os.path.join(docs_dir, page.file.src_path))

    out = []
    fence = None
    for line in markdown.splitlines(keepends=True):
        m = FENCE_RE.match(line)
        if m:
            if fence is None:
                fence = m.group(2)
            elif m.group(2) == fence:
                fence = None
            out.append(line)
            continue
        if fence is not None:
            out.append(line)
            continue
        out.append(
            LINK_RE.sub(
                lambda mo: "]("
                + _rewrite(mo.group("target"), page_dir, docs_dir, repo_root)
                + (mo.group("title") or "")
                + ")",
                line,
            )
        )
    return "".join(out)
