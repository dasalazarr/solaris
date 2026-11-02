#!/usr/bin/env python3
"""Tests de las reglas de contrato de wiki_lint.py. Stdlib only.

Usage: python3 scripts/test_wiki_lint.py
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wiki_lint  # noqa: E402

CONTRACT = """---
rol: tester
responsable: {owner}
kpi: ["algo medible"]
reglas: [REG-EVID, REG-REV]
acciones_permitidas: ["leer"]
revision_requerida: ["publicar"]
ultima_evidencia: {evidence}
updated: 2026-11-02
---
"""


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "plan" / "contratos").mkdir(parents=True)
        (self.root / ".claude" / "agents").mkdir(parents=True)
        (self.root / ".claude" / "agents" / "tester.md").write_text("x")
        (self.root / "raw" / "sessions").mkdir(parents=True)
        (self.root / "raw" / "sessions" / "2026-11-01_tester_x.md").write_text("x")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, owner: str = "Diego", evidence: str = "raw/sessions/2026-11-01_tester_x.md", body: str | None = None) -> None:
        text = body if body is not None else CONTRACT.format(owner=owner, evidence=evidence)
        (self.root / "plan" / "contratos" / "tester.md").write_text(text)

    def run_lint(self, today: date = date(2026, 11, 2)) -> tuple[list[str], list[str]]:
        return wiki_lint.lint_contracts(self.root, today)

    def test_valid_contract(self) -> None:
        self.write()
        self.assertEqual(self.run_lint(), ([], []))

    def test_missing_kpi_fails(self) -> None:
        self.write(body=CONTRACT.format(owner="Diego", evidence="raw/sessions/2026-11-01_tester_x.md").replace('kpi: ["algo medible"]\n', ""))
        errors, _ = self.run_lint()
        self.assertTrue(any("kpi" in e for e in errors))

    def test_broken_evidence_fails(self) -> None:
        self.write(evidence="raw/sessions/2026-11-01_no-existe.md")
        errors, _ = self.run_lint()
        self.assertTrue(any("REG-EVID" in e for e in errors))

    def test_agent_as_owner_fails(self) -> None:
        self.write(owner="tester")
        errors, _ = self.run_lint()
        self.assertTrue(any("REG-REV" in e for e in errors))

    def test_stale_evidence_warns(self) -> None:
        self.write()
        errors, warnings = self.run_lint(today=date(2026, 12, 1))
        self.assertEqual(errors, [])
        self.assertTrue(any("REG-EVID-14" in w for w in warnings))


class RuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "diario").mkdir(parents=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def page(self, **fm: object) -> dict:
        return {"path": self.root / "wiki" / "x.md", "fm": fm}

    def test_ab_without_traffic_fails(self) -> None:
        errors = wiki_lint.lint_rules([self.page(experiment="ab", evidence=["raw/research/x.md"])], self.root)
        self.assertTrue(any("REG-AB" in e for e in errors))

    def test_ab_with_traffic_passes(self) -> None:
        errors = wiki_lint.lint_rules([self.page(experiment="ab", evidence=["raw/eval-runs/2026-12-01_trafico.md"])], self.root)
        self.assertEqual(errors, [])

    def test_market_insight_without_source_fails(self) -> None:
        errors = wiki_lint.lint_rules([self.page(origin="mercado", evidence=["docs/prd-landing.md"])], self.root)
        self.assertTrue(any("REG-CITA" in e for e in errors))

    def test_diario_without_marker_fails(self) -> None:
        (self.root / "docs" / "diario" / "2026-11-02-x.md").write_text("# Título\n\nTexto.\n")
        errors = wiki_lint.lint_rules([], self.root)
        self.assertTrue(any("REG-DIARIO" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
