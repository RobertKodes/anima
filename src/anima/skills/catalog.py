"""Anima skill catalog — capabilities the being can learn during onboarding."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    id: str
    title: str
    capability: str
    summary: str
    config_flag: str
    slash: str
    examples: tuple[str, ...]


SKILLS: tuple[Skill, ...] = (
    Skill(
        id="web-fetch",
        title="Web fetch",
        capability="web_fetch",
        summary="Read a public page and bring the text back into conversation.",
        config_flag="allow_web_fetch",
        slash="/fetch <url>",
        examples=("fetch https://example.com", "read this page https://…"),
    ),
    Skill(
        id="web-crawl",
        title="Web crawl",
        capability="web_crawl",
        summary="Walk same-site links and collect short excerpts from several pages.",
        config_flag="allow_web_crawl",
        slash="/crawl <url>",
        examples=("crawl https://docs.example.com",),
    ),
    Skill(
        id="explore",
        title="Explore",
        capability="explore",
        summary="Summarize a seed page and list the links it offers.",
        config_flag="allow_explore",
        slash="/explore <url>",
        examples=("explore https://news.ycombinator.com", "what links are on https://…"),
    ),
)


def skill_by_capability(cap_id: str) -> Skill | None:
    for skill in SKILLS:
        if skill.capability == cap_id:
            return skill
    return None


def apply_skill_grants(cfg, *, fetch: bool = False, crawl: bool = False, explore: bool = False) -> None:
    cfg.allow_web_fetch = fetch
    cfg.allow_web_crawl = crawl
    cfg.allow_explore = explore


def granted_skills(cfg) -> list[Skill]:
    flags = {
        "allow_web_fetch": cfg.allow_web_fetch,
        "allow_web_crawl": cfg.allow_web_crawl,
        "allow_explore": cfg.allow_explore,
    }
    return [s for s in SKILLS if flags.get(s.config_flag)]
