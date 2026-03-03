from enum import Enum


class TaskResult(Enum):
    UNKNOWN = 0
    SUCCEEDED = 1
    CANCELED = 2
    FAILED = 3


COMMAND_VELOCITY = {
    'KeyU': {'linearX': 0.5 ,'angularZ': 1.0},
    'KeyI': {'linearX': 0.5 ,'angularZ': 0.0},
    'KeyO': {'linearX': 0.5 ,'angularZ': -1.0},
    'KeyJ': {'linearX': 0.0 ,'angularZ': 1.0},
    'KeyK': {'linearX': 0.0 ,'angularZ': 0.0},
    'KeyL': {'linearX': 0.0 ,'angularZ': -1.0},
    'KeyM': {'linearX': -0.5 ,'angularZ': -1.0},
    'Comma': {'linearX': -0.5 ,'angularZ': 1.0},
    'Period': {'linearX': -0.5 ,'angularZ': 1.0},
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