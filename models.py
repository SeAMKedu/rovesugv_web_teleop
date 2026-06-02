from dataclasses import dataclass
from enum import Enum


class AlertType:
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


@dataclass
class Location:
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass
class Pose(Location):
    yaw: float = 0.0


@dataclass
class GPSWaypoint(Pose):
    pass


@dataclass
class EStop:
    is_triggered: bool = True


@dataclass
class NavigationData:
    goal_pose: Pose
    start_location: Location
    goal: str = "NA"
    is_nav2_active: bool = False
    is_running: bool = False

    def update_goal(self, new_goal: dict):
        self.goal = new_goal.get("goal", "NA")
        self.goal_pose.latitude = new_goal.get("latitude", 0.0)
        self.goal_pose.longitude = new_goal.get("longitude", 0.0)
        self.goal_pose.yaw = new_goal.get("yaw", 0.0)
        self.start_location.latitude = new_goal.get("startLat", 0.0)
        self.start_location.longitude = new_goal.get("startLon", 0.0)

    def reset_goal(self):
        self.goal = "NA"
        self.goal_pose.latitude = 0.0
        self.goal_pose.longitude =0.0
        self.goal_pose.yaw = 0.0
        self.start_location.latitude = 0.0
        self.start_location.longitude = 0.0


@dataclass
class AppData:
    e_stop: EStop
    navigation: NavigationData
    rover: Location


data = AppData(
    e_stop=EStop(),
    navigation=NavigationData(
        goal_pose=Pose(),
        start_location=Location(),
    ),
    rover=Location(),
)
