"""Small validated environment profiles; no targets, uploads or live checks."""
from typing import Any, Literal

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


class RunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    profile_id: int = Field(gt=0)


class RunOut(BaseModel):
    run_id: int
    status: str
    assessment: dict[str, Any] | None = None
    coverage: dict[str, Any] = Field(default_factory=dict)
    scenarios: list[dict[str, Any]] = Field(default_factory=list)
    profile: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    notice: str
