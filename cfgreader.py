import os
import pathlib

import attrs
import cattrs
import yaml

cwd = pathlib.Path(__file__).parent
filepath = os.path.join(cwd, "config", "app.yaml")


@attrs.define
class AddressInfo:
    host: str
    port: int


@attrs.define
class App:
    address: AddressInfo


@attrs.define
class Services:
    e_stop_reset: str
    e_stop_trigger: str


@attrs.define
class Topics:
    battery_status: str
    camera: str
    e_stop: str
    odom: str
    nav_feedback: str
    navsatfix: str
    planned_path: str
    teleop: str


@attrs.define
class Config:
    app: App
    services: Services
    topics: Topics
    use_sim: bool


with open(filepath, "r") as config_file:
    cfg = yaml.safe_load(config_file)
    key = "sim" if cfg["use_sim"] else "robot"

    cfg["services"] = {}
    cfg["services"]["e_stop_reset"] = cfg[key]["services"]["e_stop_reset"]
    cfg["services"]["e_stop_trigger"] = cfg[key]["services"]["e_stop_trigger"]

    cfg["topics"] = {}
    cfg["topics"]["battery_status"] = cfg[key]["topics"]["battery_status"]
    cfg["topics"]["camera"] = cfg[key]["topics"]["camera"]
    cfg["topics"]["e_stop"] = cfg[key]["topics"]["e_stop"]
    cfg["topics"]["odom"] = cfg[key]["topics"]["odom"]
    cfg["topics"]["nav_feedback"] =  cfg[key]["topics"]["nav_feedback"]
    cfg["topics"]["navsatfix"] = cfg[key]["topics"]["navsatfix"]
    cfg["topics"]["planned_path"] = cfg[key]["topics"]["planned_path"]
    cfg["topics"]["teleop"] = cfg[key]["topics"]["teleop"]

    config = cattrs.structure(cfg, Config)
