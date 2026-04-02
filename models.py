from dataclasses import dataclass


@dataclass
class GPSWaypoint:
    latitude: float
    longitude: float
    yaw: float
