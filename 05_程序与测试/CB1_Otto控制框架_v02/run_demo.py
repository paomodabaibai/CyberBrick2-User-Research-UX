"""One-command v02 demo: scripted remote session replayed end to end.

Usage:  python run_demo.py
Writes demo_log.csv, demo_joints.svg, demo_phases.svg into output/.
Software replay only - NOT a physics simulation, says nothing about balance.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulator import Simulator

# step total ~= 250+450+450+350+300 = 1800 ms per step
SCRIPT = [
    (0,    'enable',       None),          # explicit enable (no button needed)
    (200,  'lever_left',  0.9),           # first step: LEFT (done ~2000)
    (2300, 'lever_left',  0.0),           # recenter -> re-armed
    (2600, 'lever_right', 0.9),           # alternate step: RIGHT (done ~4400)
    (4700, 'lever_right', 0.0),
    (5000, 'lever_left',  0.9),           # third step LEFT (running until ~6800)
    (5400, 'lever_left',  0.0),           # recenter mid-step -> re-armed
    (5800, 'lever_right', 0.9),           # push while busy: dropped, never queued
    (7000, 'lever_right', 0.0),
    (7200, 'lever_left',  0.9),           # both levers forward...
    (7200, 'lever_right', 0.9),           # ...-> rejected_conflict, nothing pending
    (7600, 'lever_left',  0.0),
    (7600, 'lever_right', 0.0),
    (8000, 'lever_left',  0.9),           # same side as last foot -> rejected
    (8600, 'lever_left',  0.0),
    (9000, 'lever_right', 0.9),           # clean right step (running until ~10800)
    (10200, 'lever_right', 0.0),          # release lever, step keeps running
    (10500, 'stop_button', True),         # K4 stop mid-step: pose frozen, held
    (11000, 'stop_button', False),
    (12500, 'link', False),               # link loss -> FAULT
    (14000, 'link', True),                # reconnect does NOT auto-resume
    (14200, 'lever_right', 0.9),          # push during FAULT: rejected
    (14800, 'lever_right', 0.0),
]


def main():
    sim = Simulator()
    rows = sim.run_script(SCRIPT, total_ms=16000)
    sim.controller.recover()            # explicit operator action
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    sim.export_csv(os.path.join(out, 'demo_log.csv'))
    sim.export_svg(os.path.join(out, 'demo_joints.svg'),
                   os.path.join(out, 'demo_phases.svg'))
    events = [r for r in rows if r['event']]
    print('v02 demo replay finished: %d ticks, %d events'
          % (len(rows), len(events)))
    for r in events:
        print('  t=%6d  %-8s  %s' % (r['t_ms'], r['state'], r['event']))
    print('final state:', sim.controller.state)
    print('outputs: output/demo_log.csv, output/demo_joints.svg, '
          'output/demo_phases.svg')
    print('NOTE: software replay only - not physics, not a walking guarantee.')


if __name__ == '__main__':
    main()
