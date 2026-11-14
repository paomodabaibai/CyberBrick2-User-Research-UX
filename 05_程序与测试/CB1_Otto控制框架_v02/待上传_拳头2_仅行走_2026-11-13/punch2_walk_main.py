"""Installation marker blocks all outputs; otherwise run walking forever."""
import os
import robot_remote
import punch2_walk_ready as profile

def start():
    if 'commissioning_hold' in os.listdir('/'):
        print('PUNCH2 WALK INSTALLED; installation hold; no outputs')
        return
    robot_remote.run_forever(profile)

if __name__=='__main__':
    start()
