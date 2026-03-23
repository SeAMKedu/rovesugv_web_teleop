from dataclasses import dataclass


@dataclass
class DriveCommand:
    env: str
    direction: str
