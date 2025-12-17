from novatel_client import NovatelClient
import time

gps = NovatelClient(max_yaw_dt=0.05)
gps.start()

while True:
    lat, lon, yaw = gps.get_pose()
    if lat is not None and yaw is not None:
        print(f"lat={lat:.8f}, lon={lon:.8f}, yaw={yaw:.2f}")
    time.sleep(0.02)
