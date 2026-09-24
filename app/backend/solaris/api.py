"""App FastAPI del backend."""

from fastapi import FastAPI

from solaris import __version__

app = FastAPI(title="Solaris backend", version=__version__)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
