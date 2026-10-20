import os, math, time
import numpy as np
import cv2
import rclpy
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import Image
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

GOAL_TIMEOUT = 150   # seconds allowed per waypoint

rclpy.init()
nav = BasicNavigator()
nav.set_parameters([Parameter("use_sim_time", Parameter.Type.BOOL, True)])

# ---- camera: always keep the latest image ----
latest = {"msg": None}
def on_image(msg):
    latest["msg"] = msg
nav.create_subscription(Image, "/camera/image_raw", on_image, qos_profile_sensor_data)

def save_photo(path):
    msg = latest["msg"]
    if msg is None:
        return False
    img = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.width, -1)
    if msg.encoding == "rgb8":
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, img)
    return True

def make_pose(x, y, yaw):
    p = PoseStamped()
    p.header.frame_id = "map"
    p.header.stamp = nav.get_clock().now().to_msg()
    p.pose.position.x = x
    p.pose.position.y = y
    p.pose.orientation.z = math.sin(yaw / 2.0)
    p.pose.orientation.w = math.cos(yaw / 2.0)
    return p

# ---- read the waypoints ----
waypoints = []
for line in open(os.path.expanduser("~/earthquake_ws/waypoints.txt")):
    if line.strip():
        x, y, yaw = map(float, line.split())
        waypoints.append((x, y, yaw))
print("Loaded", len(waypoints), "waypoints")

out_dir = os.path.expanduser("~/earthquake_ws/photos/run_" + time.strftime("%Y%m%d_%H%M%S"))
os.makedirs(out_dir, exist_ok=True)

for n, (x, y, yaw) in enumerate(waypoints, start=1):
    print("\n[%d/%d] Going to x=%.2f y=%.2f" % (n, len(waypoints), x, y))
    nav.goToPose(make_pose(x, y, yaw))
    start = time.time()
    while not nav.isTaskComplete():
        if time.time() - start > GOAL_TIMEOUT:
            print("   Too slow, cancelling this waypoint")
            nav.cancelTask()
            break
    result = nav.getResult()
    if result == TaskResult.SUCCEEDED:
        print("   Arrived.")
        t0 = time.time()
        while time.time() - t0 < 2.0:          # wait 2 s so the image is steady
            rclpy.spin_once(nav, timeout_sec=0.1)
        path = os.path.join(out_dir, "wp%d.png" % n)
        print("   Photo saved:" if save_photo(path) else "   No camera image received!", path)
    else:
        print("   Could not reach it (result:", result, "). Skipping photo.")

print("\nPatrol finished. Photos are in:", out_dir)
nav.destroy_node()
rclpy.shutdown()
