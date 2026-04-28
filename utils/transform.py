import rclpy
from rclpy.node import Node
from robot_localization.srv import ToLL


class Transform(Node):
    def __init__(self):
        super().__init__(node_name="location_node")
        self.client = self.create_client(srv_type=ToLL, srv_name="/toLL")

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for 'ToLL' servive...")

    def to_ll(self) -> ToLL.Response:
        """Transform (x=0, y=0, z=0) to (lat, long, alt)."""
        request = ToLL.Request()
        request.map_point.x = 0.0
        request.map_point.y = 0.0
        request.map_point.z = 0.0
        
        future = self.client.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response: ToLL.Response = future.result()

        return response
