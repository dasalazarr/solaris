#!/usr/bin/env python3
"""Lint the Solaris living wiki (WikiSkill layout). Stdlib only.

Checks:
  - every page in wiki/<type-folder>/ has frontmatter with required keys and a valid status
  - page id matches the filename prefix and is unique
  - every [[ID]] (frontmatter links and body) resolves to a page or a milestone (M0..M9)
  - every evidence path exists (the part before '#')
  - every feature links to >=1 problem (P) and >=1 place (L)
  - every .claude/skills/<skill>/ has SKILL.md + PURPOSE.md and its [[ID]] links resolve
  - wiki/index.md lists every page (use --write-index to regenerate it)

Usage:
  python3 scripts/wiki_lint.py               # lint, exit 1 on errors
  python3 scripts/wiki_lint.py --write-index # regenerate wiki/index.md, then lint
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
PAGE_DIRS = ["problems", "features", "places", "opportunities", "hypotheses", "risks", "patterns", "decisions"]
REQUIRED = ["id", "type", "title", "status", "owner_role", "links", "evidence", "updated"]
STATUSES = {"idea", "validating", "planned", "building", "done", "parked", "rejected", "accepted", "superseded"}
ROLES = {"product", "dev", "security", "wiki"}
LINK_RE = re.compile(r"\[\[([A-Za-z0-9-]+)\]\]")
MILESTONE_RE = re.compile(r"^M\d$")

SECTION_TITLES = {
    "problems": "Problemas (P)",
    "features": "Features (F)",
    "places": "Lugares clave (L)",
    "opportunities": "Oportunidades (O)",
    "hypotheses": "Hipótesis (H)",
    "risks": "Riesgos (R)",
    "patterns": "Patrones aprendidos (PAT)",
    "decisions": "Decisiones (ADR)",
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm: dict = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key.strip()] = [v.strip().strip('"') for v in inner.split(",") if v.strip()] if inner else []
        else:
            fm[key.strip()] = val.strip('"')
    return fm, text[end + 5 :]


def load_pages() -> list[dict]:
    pages = []
    for d in PAGE_DIRS:
        for path in sorted((WIKI / d).glob("*.md")):
            fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
            pages.append({"path": path, "dir": d, "fm": fm, "body": body})
    return pages


def write_index(pages: list[dict]) -> None:
    lines = [
        "# Solaris — Índice de la wiki",
        "",
        "> Catálogo generado por `python3 scripts/wiki_lint.py --write-index`. No editar a mano.",
        "> Capa WIKI del modelo WikiSkill (ver [[ADR-0001]]). Evidencia en `raw/`, procedimientos en `.claude/skills/`.",
        "",
        "Otros ficheros de la wiki: [logs.md](logs.md) (log cronológico) · [skill-impact.md](skill-impact.md) (auditoría de propuestas) · [_templates/](_templates/).",
        "",
    ]
    for d in PAGE_DIRS:
        group = [p for p in pages if p["dir"] == d]
        if not group:
            continue
        lines += [f"## {SECTION_TITLES[d]}", "", "| ID | Título | Estado | Rol |", "|---|---|---|---|"]
        for p in group:
            fm = p["fm"]
            rel = p["path"].relative_to(WIKI).as_posix()
            lines.append(f"| [{fm.get('id')}]({rel}) | {fm.get('title')} | {fm.get('status')} | {fm.get('owner_role')} |")
        lines.append("")
    (WIKI / "index.md").write_text("\n".join(lines), encoding="utf-8")


def lint(pages: list[dict]) -> list[str]:
    errors: list[str] = []
    ids: dict[str, Path] = {}
    for p in pages:
        rel = p["path"].relative_to(ROOT)
        fm = p["fm"]
        missing = [k for k in REQUIRED if k not in fm]
        if missing:
            errors.append(f"{rel}: faltan claves de frontmatter {missing}")
            continue
        pid = fm["id"]
        if not p["path"].name.startswith(pid + "-"):
            errors.append(f"{rel}: el id '{pid}' no coincide con el nombre de fichero")
        if pid in ids:
            errors.append(f"{rel}: id duplicado '{pid}' (también en {ids[pid].relative_to(ROOT)})")
        ids[pid] = p["path"]
        if fm["status"] not in STATUSES:
            errors.append(f"{rel}: estado inválido '{fm['status']}'")
        if fm["owner_role"] not in ROLES:
            errors.append(f"{rel}: owner_role inválido '{fm['owner_role']}'")
        for ev in fm["evidence"]:
            if not (ROOT / ev.split("#")[0]).exists():
                errors.append(f"{rel}: la evidencia no existe: {ev}")

    for p in pages:
        rel = p["path"].relative_to(ROOT)
        fm = p["fm"]
        if "links" not in fm:
            continue
        refs = {LINK_RE.fullmatch(l).group(1) for l in fm["links"] if LINK_RE.fullmatch(l)}
        refs |= set(LINK_RE.findall(p["body"]))
        for r in sorted(refs):
            if r not in ids and not MILESTONE_RE.match(r):
                errors.append(f"{rel}: enlace roto [[{r}]]")
        if p["dir"] == "features":
            if not any(r.startswith("P") and r[1:].isdigit() for r in refs):
                errors.append(f"{rel}: la feature no enlaza ningún problema (P)")
            if not any(r.startswith("L") and r[1:].isdigit() for r in refs):
                errors.append(f"{rel}: la feature no enlaza ningún lugar clave (L)")

    index = WIKI / "index.md"
    if not index.exists():
        errors.append("wiki/index.md no existe (ejecuta con --write-index)")
    else:
        text = index.read_text(encoding="utf-8")
        for pid, path in ids.items():
            if path.relative_to(WIKI).as_posix() not in text:
                errors.append(f"wiki/index.md: falta {pid} (ejecuta con --write-index)")
    skills = ROOT / ".claude" / "skills"
    for sk in sorted(skills.glob("*/")):
        for req in ("SKILL.md", "PURPOSE.md"):
            if not (sk / req).exists():
                errors.append(f"{sk.relative_to(ROOT)}: falta {req}")
        for md in sorted(sk.glob("*.md")):
            for r in sorted(set(LINK_RE.findall(md.read_text(encoding="utf-8")))):
                if r not in ids and not MILESTONE_RE.match(r):
                    errors.append(f"{md.relative_to(ROOT)}: enlace roto [[{r}]]")
    for f in ("logs.md", "skill-impact.md"):
        if not (WIKI / f).exists():
            errors.append(f"wiki/{f} no existe")
    return errors


def main() -> int:
    pages = load_pages()
    if "--write-index" in sys.argv:
        write_index(pages)
    errors = lint(pages)
    if errors:
        print(f"wiki_lint: {len(errors)} error(es)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"wiki_lint: OK — {len(pages)} páginas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
