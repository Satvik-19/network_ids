"""Small validated environment profiles; no targets, uploads or live checks."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    environment: Literal['home','lab','small_organisation','web_server']
    scale: Literal['1-10','10-50','50+'] = '1-10'
    exposure: Literal['internal','some_public','public'] = 'internal'
    services: list[Literal['web','ssh','ftp','database','file_sharing']] = Field(default_factory=list, max_length=5)

    @field_validator('services')
    @classmethod
    def canonical_services(cls, values):
        return sorted(set(values))


class ScenarioPlan(BaseModel):
    name: str
    reason: str
    available: bool
    flow_count: int
    purpose: str


class ProfileOut(BaseModel):
    id: int
    profile: ProfileRequest
    suite: list[ScenarioPlan]
    unsupported_services: list[str]
    unknown_attack_detection: str
    notice: str
