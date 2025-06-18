from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer
from pydantic.networks import IPvAnyAddress


class GetParamZabbixModel(BaseModel, validate_assignment=True):
    model_config = ConfigDict(from_attributes=True)

    output: str | list[str]
    filter: dict | None = None
    search: dict | None = None
    templateid: list[str] | None = None
    hostids: list[str] | None = None
    groupids: list[str] | None = None
    sortfield: str | None = None
    searchWildcardsEnabled: bool | None = None
    searchByAny: bool | None = None
    startSearch: bool | None = None
    selectHosts: Literal['extend', 'count'] | None = None
    selectHostGroups: Literal['extend'] | None = None
    selectInterfaces: Literal['extend', 'count'] | None = None


class InterfacesHostZabbixModel(BaseModel, validate_assignment=True):
    model_config = ConfigDict(from_attributes=True)

    type: int = 1
    main: int = 1
    useip: int = 1
    ip: IPvAnyAddress
    dns: str = ''
    port: str = '10050'

    @field_serializer('ip')
    def serialize_ip(self, ip: IPvAnyAddress, _info):
        return str(ip)


class GroupsHostZabbixModel(BaseModel, validate_assignment=True):
    model_config = ConfigDict(from_attributes=True)

    groupid: str


class TemplatesHostZabbixModel(BaseModel, validate_assignment=True):
    model_config = ConfigDict(from_attributes=True)

    templateid: str


class ParamCreateHostZabbixModel(BaseModel, validate_assignment=True):
    model_config = ConfigDict(from_attributes=True)

    host: str
    interfaces: list[InterfacesHostZabbixModel]
    groups: list[GroupsHostZabbixModel]
    templates: list[TemplatesHostZabbixModel]
