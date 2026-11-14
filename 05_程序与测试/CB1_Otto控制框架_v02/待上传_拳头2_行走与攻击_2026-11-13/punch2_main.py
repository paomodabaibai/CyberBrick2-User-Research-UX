"""Continuous combined control; retain the installation guard."""
import os
import robot_remote
import punch2_remote_ready as profile


def start():
    if 'commissioning_hold' in os.listdir('/'):
        print('PUNCH2 installation hold; no outputs')
        return
    robot_remote.run_forever(profile)


if __name__ == '__main__':
    start()
