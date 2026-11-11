"""Published API with persistent fixture runner/proof composition; strictly offline."""

from pathlib import Path

from integration.service import FixtureRun
from pieces.backend.app import create_app as backend_app
from pieces.proof.proof import Proof


def create_app(*, service=None):
    from fastapi.responses import JSONResponse

    service = service if service is not None else FixtureRun(Path(".goldgraft/pushed-integration"))
    app = backend_app(proof=Proof(), views=service)

    @app.middleware("http")
    async def offline_boundary(request, call_next):
        if request.url.path.startswith(("/pp/webhook/", "/gh/webhook")):
            response = JSONResponse(
                {
                    "type": "about:blank",
                    "title": "UNQUALIFIED callback verification",
                    "status": 503,
                },
                status_code=503,
                media_type="application/problem+json",
            )
        else:
            response = await call_next(request)
        response.headers["X-GoldGraft-Evidence-Class"] = "scripted"
        return response

    return app


app = create_app()
