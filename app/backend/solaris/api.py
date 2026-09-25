"""App FastAPI del backend."""

from fastapi import FastAPI

from solaris import __version__
from solaris.audit.api import router as audit_router
from solaris.auth.api import router as auth_router

app = FastAPI(title="Solaris backend", version=__version__)
app.include_router(auth_router)
app.include_router(audit_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
