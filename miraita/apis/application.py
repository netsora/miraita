from fastapi import FastAPI

from entari_plugin_server import server

from miraita.version import __version__

from .routers import router as api_router


__description__ = """
**A program that provide API services for [Miraita](https://github.com/KomoriDev/miraita). 🚀**

Project:
  - Miraita: [KomoriDev/miraita](https://github.com/KomoriDev/miraita)

"""  # noqa: E501

app: FastAPI = FastAPI(
    debug=False,
    title="Miraita API",
    description=__description__,
    version=__version__,
    openapi_url="/docs/openapi.json",
    redoc_url="/docs",
    root_path="/api",
    docs_url=None,
    contact={
        "name": "Komorebi",
        "email": "mute231010@gmail.com",
    },
)
app.include_router(api_router, prefix="/v1")


server.replace_app(app)  # type: ignore
