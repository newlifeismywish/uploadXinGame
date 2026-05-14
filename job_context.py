from dataclasses import dataclass, field
from typing import Optional

from config import AppConfig


@dataclass
class JobState:
    current_step: Optional[str] = None

    parsed_count: int = 0
    success_count: int = 0
    failed_count: int = 0

    processed_files: list[str] = field(default_factory=list)
    failed_files: list[str] = field(default_factory=list)


@dataclass
class JobContext:
    config: AppConfig
    date: str
    force: bool = False
    state: JobState = field(default_factory=JobState)
