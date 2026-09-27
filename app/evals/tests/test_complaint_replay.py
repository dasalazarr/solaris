"""Arnés sin LLM del parser (M3-T8): la señal del LLM sola nunca activa el aviso rojo."""

import json

import pytest
from solaris.settings import Settings

import complaint_replay as cr


@pytest.fixture
def settings():
    return Settings(_env_file=None)


def test_adversarial_model_signal_gives_zero_fp_and_keeps_case5(settings):
    res = cr.run([], settings)  # sin grabaciones: solo el peor caso sintético
    m = res["metrics"]["adversarial"]
    assert sum(m["clean_runs"].values()) == 4 and m["fp"] == 0
    assert m["legacy_fp"] == 4  # la regla anterior habría marcado los 4 limpios
    assert m["case5_runs"] == 1 and m["case5_3of3"] == 1 and m["leaks"] == 0


def test_recorded_0312_false_positive_is_now_review_note(settings, tmp_path):
    # Respuesta real de gemini del diagnóstico (declara S3, requisito legítimo del OEM).
    raw = json.dumps({**cr.EMPTY_OUT, "ignored_instructions": [
        {"source": "S3", "summary": "Instrucciones sobre el formato de las piezas."}]})
    f = tmp_path / "run.json"
    f.write_text(json.dumps({"items": [{"file": "C-OEMN-2026-0312.pdf", "llm_raw": raw}]}))
    res = cr.run([str(f)], settings)
    (it,) = [x for x in res["items"] if x["mode"] == "recorded"]
    assert not it["injection_suspected"] and it["legacy_suspected"]
    assert it["model_only"] == ["S3"] and it["leaks"] == []
