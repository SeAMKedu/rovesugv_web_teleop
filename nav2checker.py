import sys
import time

import rclpy
import socketio
import socketio.exceptions
from rclpy.node import Node
from std_srvs.srv import Trigger


class Nav2Checker(Node):
    """docstring"""

    def __init__(self):
        super().__init__(node_name="nav2_checker")
    

    def check_nav2_state(self):
        """Check if the Navigation 2 stack is active."""
        service_name = "/lifecycle_manager_navigation/is_active"
        client = self.create_client(Trigger, service_name)
        request = Trigger.Request()
        future = client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        response: Trigger.Response = future.result()
        if not response:
            return False
        return response.success


def main():
    try:
        sio_client = socketio.SimpleClient()
        sio_client.connect("http://127.0.0.1:5000")
    except socketio.exceptions as error:
        print(f"[ERROR] {error}")
        sys.exit(1)

    rclpy.init()
    node = Nav2Checker()

    while True:
        try:
            is_active = node.check_nav2_state()
            print(f"Nav2 is active: {is_active}")
            sio_client.emit("on_nav2_state", is_active)
            time.sleep(10)
        except KeyboardInterrupt:
            break

    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == "__main__":
    main()
