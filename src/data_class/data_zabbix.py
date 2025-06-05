from typing import Literal

from pydantic import BaseModel, ConfigDict


class GetParamZabbixModel(BaseModel, validate_assignment=True):
    model_config = ConfigDict(from_attributes=True)

    output: str | list[str]
    filter: dict | None = None
    search: dict | None = None
    sortfield: str
    searchWildcardsEnabled: bool | None = None
    searchByAny: bool | None = None
    startSearch: bool | None = None
    selectHosts: Literal['extend', 'count'] | None = None
