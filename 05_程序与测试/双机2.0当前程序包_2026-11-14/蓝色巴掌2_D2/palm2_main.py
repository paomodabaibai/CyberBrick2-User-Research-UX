"""Blue 2.0 startup. A commissioning marker inhibits ALL robot outputs."""
import os
import robot_remote
import palm2_remote_ready as profile

def start():
    if 'commissioning_hold' in os.listdir('/'):
        print('PALM2 D2 INSTALLED; commissioning hold; no actuator outputs')
        return
    robot_remote.run_forever(profile)

if __name__ == '__main__':
    start()
