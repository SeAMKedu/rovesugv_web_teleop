import attrs
import cattrs
import yaml


@attrs.define
class AppAddress:
    host: str
    port: int


@attrs.define
class ROS2Topics:
    battery: str
    odom: str
    nav_feedback: str
    navsatfix: str
    planned_path: str
    teleop: str


@attrs.define
class StartPoint:
    latitude: float
    longitude: float


@attrs.define
class Config:
    app: AppAddress
    ros2_topics: ROS2Topics
    start_point: StartPoint
    use_sim: bool
    

with open("config.yaml", "r") as config_file:
    cfg = yaml.safe_load(config_file)
    key = "sim" if cfg["use_sim"] else "robot"
    
    cfg["ros2_topics"]["battery"] = cfg[key]["battery_topic"]
    cfg["ros2_topics"]["odom"] = cfg[key]["odom_topic"]
    cfg["ros2_topics"]["nav_feedback"] = cfg[key]["nav_feedback_topic"]
    cfg["ros2_topics"]["navsatfix"] = cfg[key]["navsatfix_topic"]
    cfg["ros2_topics"]["planned_path"] = cfg[key]["planned_path_topic"]
    cfg["ros2_topics"]["teleop"] = cfg[key]["teleop_topic"]
    cfg["start_point"]["latitude"] = cfg[key]["start_point"]["latitude"]
    cfg["start_point"]["longitude"] = cfg[key]["start_point"]["longitude"]

    config = cattrs.structure(cfg, Config)
