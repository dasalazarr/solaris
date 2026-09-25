"""M2-T8 (security): todo secreto de Settings se borra de los textos del audit, incluidos los de
M4-T1 (JWT, solaris_app, contraseñas de demo). Caso real: un usuario escribe su contraseña en el
campo de usuario y el login fallido guarda `attempted_user` en un audit que no se puede borrar."""

from pydantic import SecretStr

from solaris.audit.redact import REDACTED, redact_payload, scrub_text
from solaris.settings import Settings

SECRETS = {
    "auth_jwt_secret": "jwt-secret-0123456789abcdef0123456789",
    "solaris_app_password": "app-pass-0123456789abcd",
    "demo_password_inaki_calidad": "demo-pass-inaki-0123456789",
    "demo_password_jon_it": "demo-pass-jon-0123456789",
    "openrouter_api_key": "or-key-without-sk-prefix-0123",
}


def _settings() -> Settings:
    return Settings(_env_file=None, **{k: SecretStr(v) for k, v in SECRETS.items()})


def test_every_secretstr_field_is_scrubbed():
    s = _settings()
    for value in SECRETS.values():
        out = scrub_text(f"antes {value} después", s)
        assert value not in out
        assert REDACTED in out


def test_password_typed_as_username_is_not_stored():
    s = _settings()
    payload = {"action": "login", "outcome": "denied",
               "attempted_user": SECRETS["demo_password_inaki_calidad"]}
    assert SECRETS["demo_password_inaki_calidad"] not in str(redact_payload(payload, s))
