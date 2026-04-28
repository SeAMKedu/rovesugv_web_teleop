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
class EStop:
    trigger: str
    reset: str


@attrs.define
class Config:
    app: AppAddress
    estop_srv: EStop
    ros2_topics: ROS2Topics
    use_sim: bool
    

with open("config.yaml", "r") as config_file:
    cfg = yaml.safe_load(config_file)
    key = "sim" if cfg["use_sim"] else "robot"

    cfg["estop_srv"]["trigger"] = cfg[key]["estop_srv_trigger"]
    cfg["estop_srv"]["reset"] = cfg[key]["estop_srv_reset"]
    cfg["ros2_topics"]["battery"] = cfg[key]["battery_topic"]
    cfg["ros2_topics"]["odom"] = cfg[key]["odom_topic"]
    cfg["ros2_topics"]["nav_feedback"] = cfg[key]["nav_feedback_topic"]
    cfg["ros2_topics"]["navsatfix"] = cfg[key]["navsatfix_topic"]
    cfg["ros2_topics"]["planned_path"] = cfg[key]["planned_path_topic"]
    cfg["ros2_topics"]["teleop"] = cfg[key]["teleop_topic"]

    config = cattrs.structure(cfg, Config)
