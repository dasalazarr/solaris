"""Lectura determinista de erp/seed.sql (ERP mock, M1-T3) para que el corpus cite datos reales.

No depende de docker: parsea los INSERT del seed versionado. El gate (check_corpus.py) sí
contrasta contra la base de datos viva.
"""
from __future__ import annotations

import re
from datetime import date
from functools import lru_cache
from pathlib import Path

SEED = Path(__file__).resolve().parents[2] / "erp" / "seed.sql"

_INSERT = re.compile(r"INSERT INTO erp\.(\w+) \(([^)]*)\) VALUES\n(.*?);\n", re.S)


def _parse_values(body: str) -> list[tuple]:
    rows, row, i, n = [], None, 0, len(body)
    while i < n:
        c = body[i]
        if c == "(" and row is None:
            row, i = [], i + 1
            continue
        if row is None:
            i += 1
            continue
        if c == "'":
            j, buf = i + 1, []
            while True:
                if body[j] == "'" and j + 1 < n and body[j + 1] == "'":
                    buf.append("'"); j += 2; continue
                if body[j] == "'":
                    break
                buf.append(body[j]); j += 1
            row.append("".join(buf)); i = j + 1
            continue
        if c in " ,\n":
            i += 1
            continue
        if c == ")":
            rows.append(tuple(row)); row = None; i += 1
            continue
        m = re.match(r"[^,)\s]+", body[i:])
        tok = m.group(0); i += len(tok)
        if tok == "NULL":
            row.append(None)
        elif tok in ("true", "false"):
            row.append(tok == "true")
        elif re.fullmatch(r"-?\d+", tok):
            row.append(int(tok))
        else:
            row.append(float(tok))
    return rows


def _coerce(v):
    if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return date.fromisoformat(v)
    return v


@lru_cache(maxsize=1)
def load() -> dict[str, list[dict]]:
    text = SEED.read_text(encoding="utf-8")
    out: dict[str, list[dict]] = {}
    for table, cols, body in _INSERT.findall(text):
        names = [c.strip() for c in cols.split(",")]
        out.setdefault(table, []).extend(
            {k: _coerce(v) for k, v in zip(names, r)} for r in _parse_values(body))
    return out


def by_key(table: str, key: str) -> dict:
    return {r[key]: r for r in load()[table]}


def lots_of(ref: str) -> list[dict]:
    return sorted((l for l in load()["lots"] if l["part_ref"] == ref), key=lambda l: l["production_date"])


def shipments_of(lot_code: str) -> list[dict]:
    return sorted((s for s in load()["shipments"] if s["lot_code"] == lot_code), key=lambda s: s["ship_date"])


def complaint_for_8d(eightd_id: str) -> dict:
    return next(c for c in load()["complaints"] if c["report_8d_id"] == eightd_id)
