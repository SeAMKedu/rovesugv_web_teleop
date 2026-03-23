from enum import Enum

ROBOT_NAMESPACE = "myPanther"


class Environment(Enum):
    SIMULATION = "simulation"
    ROBOT = ROBOT_NAMESPACE


class EnvSimulation(Enum):
    TELEOPERATION_TOPIC = "/cmd_vel"


class EnvRobot(Enum):
    TELEOPERATION_TOPIC = f"/{ROBOT_NAMESPACE}/cmd_vel"


class TaskResult(Enum):
    UNKNOWN = 0
    SUCCEEDED = 1
    CANCELED = 2
    FAILED = 3


COMMAND_VELOCITY = {
    'forwardLeft': {'linearX': 0.5 ,'angularZ': 1.0},
    'forward': {'linearX': 0.5 ,'angularZ': 0.0},
    'forwardRight': {'linearX': 0.5 ,'angularZ': -1.0},
    'rotateLeft': {'linearX': 0.0 ,'angularZ': 1.0},
    'stop': {'linearX': 0.0 ,'angularZ': 0.0},
    'rotateRight': {'linearX': 0.0 ,'angularZ': -1.0},
    'backwardLeft': {'linearX': -0.5 ,'angularZ': -1.0},
    'backward': {'linearX': -0.5 ,'angularZ': 0.0},
    'backwardRight': {'linearX': -0.5 ,'angularZ': 1.0},
}

INIT_POINT_LAT = 62.789252
INIT_POINT_LON = 22.821627

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5000

NAV_TARGETS = {
    'automotiveLab': {
        'latitude': 62.790967500,
        'longitude': 22.821647222,
        'yaw': 0.0
    },
    'manufacturingLab': {
        'latitude': 62.789319444,
        'longitude': 22.821791111,
        'yaw': 0.7853981633974483,
    },
    'roboticsLab': {
        'latitude': 62.789201667,
        'longitude': 22.822063056,
        'yaw': -0.7853981633974483,
    },
}
NAV_TARGET_STOP = 'stop'