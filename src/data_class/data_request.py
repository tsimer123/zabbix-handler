from pydantic import BaseModel, ConfigDict


class ResultRequestModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: bool
    data: str | None = None
    error: str | None = None
