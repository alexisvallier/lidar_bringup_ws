#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from geometry_msgs.msg import TransformStamped
from mocap4r2_msgs.msg import RigidBodies
import tf2_ros
import tf2_py
from tf2_sensor_msgs.tf2_sensor_msgs import do_transform_cloud
from tf_transformations import quaternion_matrix
from rclpy.duration import Duration

class CloudToRigidBodyFrame(Node):
    def __init__(self):
        super().__init__('cloud_to_rigidbody_frame')

        self.world_frame = None

        # Input topic from LiDAR
        self.declare_parameter('input_cloud_topic', '/points_voxel')
        # Data topic from mocap (rigid body positions)
        self.declare_parameter('pose_topic', '/rigid_bodies')
        # Name of the robot rigid body / LiDAR frame (treat them as the same frame)
        # IMPORTANT: set this to exactly the LiDAR cloud frame_id (e.g. "hesai_lidar_link")
        self.declare_parameter('rigid_body_frame', 'hesai_lidar_link')
        self.declare_parameter('rigid_body_name', '2') 
        self.declare_parameter('output_cloud_topic', '/cloud_in_rb_frame')

        input_cloud_topic = self.get_parameter('input_cloud_topic').value
        pose_topic = self.get_parameter('pose_topic').value
        self.rigid_body_frame = self.get_parameter('rigid_body_frame').value
        self.rigid_body_name = self.get_parameter('rigid_body_name').value
        output_cloud_topic = self.get_parameter('output_cloud_topic').value

        self.time_offset = 0.0          # seconds (positive means LiDAR is ahead of TF)
        self.log_offset = True         # enable during calibration

        # TF buffer and listener/broadcaster
        self.tf_buffer = tf2_ros.Buffer(cache_time=Duration(seconds=30.0))
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # Subscriptions to LiDAR and mocap topics
        self.cloud_sub = self.create_subscription(
            PointCloud2, input_cloud_topic, self.cloud_callback, 10)
        self.pose_sub = self.create_subscription(
            RigidBodies, pose_topic, self.pose_callback, 10)

        # Publisher of transformed LiDAR data
        self.cloud_pub = self.create_publisher(PointCloud2, output_cloud_topic, 10)

        self.latest_pose = None
        self.get_logger().info("CloudToRigidBodyFrame node initialized")

    # Callback for mocap data
    def pose_callback(self, msg: RigidBodies):
        if len(msg.rigidbodies) == 0:
            self.get_logger().warn("RigidBodies received but empty")
            return

        rb = None
        for body in msg.rigidbodies:
            if body.rigid_body_name == self.rigid_body_name:
                rb = body
                break

        if rb is None:
            self.get_logger().warn_once(
                "Rigid body '{self.rigid_body_name}' not found in message"
            )
            return

        # Save frame info
        self.world_frame = msg.header.frame_id
        self.latest_pose = rb

        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        t.header.frame_id = msg.header.frame_id      # e.g. "optitrack_world"
        t.child_frame_id = self.rigid_body_frame     # e.g. "hesai_lidar_link"

        t.transform.translation.x = rb.pose.position.x
        t.transform.translation.y = rb.pose.position.y
        t.transform.translation.z = rb.pose.position.z
        t.transform.rotation = rb.pose.orientation

        self.tf_broadcaster.sendTransform(t)

    # Callback for LiDAR data
    def cloud_callback(self, cloud_msg: PointCloud2):
        if self.latest_pose is None:
            self.get_logger().warn("No pose received yet — skipping cloud.")
            return

        # World frame from mocap (e.g. "optitrack_world")
        world_frame = self.world_frame



        # --- Optional: log how old the cloud is relative to ROS time ---
        if self.log_offset:
            now = self.get_clock().now().nanoseconds * 1e-9
            self.get_logger().info(f"Cloud age vs now: {now - cloud_time:.3f} s")

        # --- Apply offset correction ---
        corrected_stamp = cloud_msg.header.stamp - Duration(seconds=self.time_offset)

        try:
            # Directly transform from world (optitrack) frame to LiDAR frame
            # Since rigid_body_frame ≡ LiDAR frame, we only need one transform
            transform_world = self.tf_buffer.lookup_transform(
                world_frame,                   # parent: world frame (e.g. "optitrack_world")
                cloud_msg.header.frame_id,     # child: LiDAR frame (e.g. "hesai_lidar_link")
                corrected_stamp,
                timeout=Duration(seconds=0.2)
            )

            cloud_in_world = do_transform_cloud(cloud_msg, transform_world)

            # Publish in world frame
            cloud_in_world.header.frame_id = world_frame
            self.cloud_pub.publish(cloud_in_world)

        except (tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f"Transform failed: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = CloudToRigidBodyFrame()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
