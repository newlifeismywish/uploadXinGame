from typing import Optional

from config import AppConfig


class JobState:
    def __init__(self):
        self.current_step = None  # type: Optional[str]
        self.parsed_count = 0
        self.success_count = 0
        self.failed_count = 0
        self.processed_files = []
        self.failed_files = []


class JobContext:
    def __init__(self, config, date, force=False, state=None):
        self.config = config  # type: AppConfig
        self.date = date
        self.force = force
        self.state = state or JobState()
