from dataclasses import dataclass, field
import os

from sources.base import SourceDef
from sources.wttj_jobs import SOURCE as WTTJ_JOBS


@dataclass(frozen=True)
class SourceConfig:
    id: str                        # e.g. "wttj_jobs" — used as source_id in the dedup key
    subject: str                   # "jobs" | "apartments" — report section label
    search_url: str
    criteria: str                  # evaluator system prompt for this source instance
    credentials_env: dict[str, str]  # e.g. {"email": "WTTJ_EMAIL", "password": "WTTJ_PASSWORD"} — env var NAMES, not values
    source_def: SourceDef
    max_pages: int = 5


@dataclass(frozen=True)
class UserConfig:
    id: str                        # e.g. "nhm" — used as user_id in the dedup key
    telegram_token_env: str
    telegram_chat_id_env: str
    sources: list[SourceConfig] = field(default_factory=list)


def validate_config(users: list[UserConfig]) -> None:
    missing = []
    for user in users:
        for var in (user.telegram_token_env, user.telegram_chat_id_env):
            if not os.getenv(var):
                missing.append(var)
        for source in user.sources:
            missing += [v for v in source.credentials_env.values() if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(sorted(set(missing)))}")


USERS: list[UserConfig] = [
    UserConfig(
        id="nhm",
        telegram_token_env="TELEGRAM_TOKEN",
        telegram_chat_id_env="TELEGRAM_CHAT_ID",
        sources=[
            SourceConfig(
                id="wttj_jobs",
                subject="jobs",
                search_url="https://www.welcometothejungle.com/fr/jobs-matches",
                criteria=WTTJ_JOBS.default_criteria,
                credentials_env={"email": "WTTJ_EMAIL", "password": "WTTJ_PASSWORD"},
                source_def=WTTJ_JOBS,
            ),
            # Bien'ici apartments: add a SourceConfig here once sources/bienici_apartments.py
            # is actually implemented (currently a NotImplementedError stub).
        ],
    ),
    # A second user (own credentials, own Telegram destination) goes here, e.g.:
    # UserConfig(
    #     id="alice",
    #     telegram_token_env="TELEGRAM_TOKEN",              # can share the same bot...
    #     telegram_chat_id_env="ALICE_TELEGRAM_CHAT_ID",     # ...pointed at a different chat
    #     sources=[
    #         SourceConfig(
    #             id="wttj_jobs",
    #             subject="jobs",
    #             search_url="https://www.welcometothejungle.com/fr/jobs-matches",
    #             criteria=WTTJ_JOBS.default_criteria,
    #             credentials_env={"email": "ALICE_WTTJ_EMAIL", "password": "ALICE_WTTJ_PASSWORD"},
    #             source_def=WTTJ_JOBS,
    #         ),
    #     ],
    # ),
]
