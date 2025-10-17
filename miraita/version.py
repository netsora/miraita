from importlib.metadata import metadata

from pydantic import BaseModel, ConfigDict


class Metadata(BaseModel):
    name: str
    version: str
    summary: str

    model_config = ConfigDict(extra="allow")


__metadata__ = Metadata(**metadata("miraita").json)  # type: ignore

__version__ = __metadata__.version
