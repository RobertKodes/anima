"""Experience pack manifest schema."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ExperienceSkill(BaseModel):
    capability: str
    grant: bool = True


class ExperienceMcp(BaseModel):
    id: str
    title: str = ""
    transport: Literal["stdio"] = "stdio"
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    optional: bool = True


class ExperienceChannel(BaseModel):
    kind: Literal["telegram", "discord", "web"]
    enabled: bool = False
    note: str = ""


class ExperiencePersonality(BaseModel):
    name_hint: str = ""
    tone: str = ""
    values: list[str] = Field(default_factory=list)
    self_description: str = ""
    strategy_hint: str = ""


class ExperienceCapabilities(BaseModel):
    web_fetch: bool | None = None
    web_crawl: bool | None = None
    explore: bool | None = None
    shell: bool | None = None


class ExperienceManifest(BaseModel):
    id: str
    title: str
    version: str = "1.0.0"
    author: str = "anima"
    summary: str = ""
    tags: list[str] = Field(default_factory=list)
    unique: str = ""
    skills: list[ExperienceSkill] = Field(default_factory=list)
    mcp: list[ExperienceMcp] = Field(default_factory=list)
    channels: list[ExperienceChannel] = Field(default_factory=list)
    personality: ExperiencePersonality = Field(default_factory=ExperiencePersonality)
    capabilities: ExperienceCapabilities = Field(default_factory=ExperienceCapabilities)

    @classmethod
    def from_toml(cls, raw: dict[str, Any]) -> ExperienceManifest:
        return cls.model_validate(raw)
