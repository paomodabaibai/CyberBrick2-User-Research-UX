"""Simulator: replay scripted operation, log everything, export CSV+SVG.

This is a software replay, not a physics simulation: it says nothing about
balance, friction, or how far the real robot would travel.
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import joint_model
import gait_planner
import controller
import input_adapter
import sim_config
from drivers import create_driver

PHASE_COLORS = {'prepare': '#ffd9a0', 'weight_shift': '#a0c8ff',
                'unload_swing': '#a0ffc8', 'land': '#ffb0b0',
                'stabilize': '#e0c0ff'}


class Simulator:
    def __init__(self, config_ref=None, tick_ms=None):
        # PC-only: default to the VIRTUAL profile so simulation can never
        # mask missing/uncalibrated hardware in the real config.
        self.cfg = config_ref or sim_config.virtual()
        self.tick_ms = tick_ms or self.cfg.LOOP_MS
        self.jm = joint_model.JointModel(self.cfg)
        self.planner = gait_planner.GaitPlanner(self.cfg)
        self.driver = create_driver(self.jm, self.cfg)
        self.rows = []
        self._pending = []
        self.controller = controller.Controller(
            self.cfg, self.jm, self.planner, self.driver,
            log=self._pending.append)

    def run_script(self, script, total_ms=None):
        """script: list of (t_ms, action, payload).

        actions: enable, recover, release, lever_left(v), lever_right(v),
                 stop_button(bool), link(bool). Values persist until changed.
        """
        ops = sorted(script, key=lambda o: o[0])
        left = right = 0.0
        stop = False
        link = True
        oi = 0
        t = 0
        end = total_ms if total_ms is not None else (
            ops[-1][0] + 2000 if ops else 2000)
        while t <= end:
            while oi < len(ops) and ops[oi][0] <= t:
                _, action, payload = ops[oi]
                if action == 'enable':
                    self.controller.enable()
                elif action == 'recover':
                    self.controller.recover()
                elif action == 'release':
                    self.controller.release_output()
                elif action == 'lever_left':
                    left = payload
                elif action == 'lever_right':
                    right = payload
                elif action == 'stop_button':
                    stop = payload
                elif action == 'link':
                    link = payload
                oi += 1
            inp = input_adapter.from_manual(left, right, stop, link, t)
            self.controller.update(inp, t)
            self._log(t, inp)
            t += self.tick_ms
        return self.rows

    def _log(self, t, inp):
        c = self.controller
        row = dict(
            t_ms=t, state=c.state, phase=c.phase or '',
            step_side=c.step_side or '', support_side=c.support_side or '',
            last_foot=c.last_foot or '', landed=c.landed,
            left=round(inp.left, 3), right=round(inp.right, 3),
            stop=inp.stop_pressed, connected=inp.connected,
            left_hip=round(c.pose[0], 3), right_hip=round(c.pose[1], 3),
            left_ankle=round(c.pose[2], 3), right_ankle=round(c.pose[3], 3),
            reason=c.reason or '', event='; '.join(self._pending))
        # Keep the SAME list object: controller.log is bound to its append.
        del self._pending[:]
        self.rows.append(row)

    # --- exports ----------------------------------------------------------
    def export_csv(self, path):
        if not self.rows:
            return
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(self.rows[0].keys()))
            w.writeheader()
            w.writerows(self.rows)

    def export_svg(self, joints_path, phases_path):
        os.makedirs(os.path.dirname(os.path.abspath(joints_path)),
                    exist_ok=True)
        self._svg_joints(joints_path)
        self._svg_phases(phases_path)

    def _svg_joints(self, path):
        series = [('left_hip', '#d62728'), ('right_hip', '#1f77b4'),
                  ('left_ankle', '#2ca02c'), ('right_ankle', '#9467bd')]
        w, h, m = 900, 430, 46
        ts = [r['t_ms'] for r in self.rows]
        t_max = max(ts) or 1
        vals = [abs(r[k]) for r in self.rows for k, _ in series]
        y_max = max(20.0, (max(vals) if vals else 0) + 2)

        def x(v):
            return m + v / float(t_max) * (w - 2 * m)

        def y(v):
            return h / 2 - v / y_max * (h / 2 - m - 10)
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" '
                 'height="%d" font-family="sans-serif">' % (w, h),
                 '<rect width="100%" height="100%" fill="white"/>',
                 '<text x="%d" y="22" font-size="14">v02 four-joint offsets '
                 'vs time (deg, relative to stance) - software replay, '
                 'NOT physics</text>' % m]
        for gv in range(-int(y_max) - 1, int(y_max) + 2, 5):
            parts.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" '
                         'stroke="#eee"/>' % (m, y(gv), w - m, y(gv)))
            parts.append('<text x="6" y="%.1f" font-size="11" fill="#666">'
                         '%d</text>' % (y(gv) + 4, gv))
        for i, (k, color) in enumerate(series):
            pts = ' '.join('%.1f,%.1f' % (x(r['t_ms']), y(r[k]))
                           for r in self.rows)
            parts.append('<polyline fill="none" stroke="%s" '
                         'stroke-width="1.6" points="%s"/>' % (color, pts))
            parts.append('<text x="%d" y="%d" font-size="12" fill="%s">%s'
                         '</text>' % (w - m - 230, 40 + 18 * i, color, k))
        for r in self.rows:
            if r['event']:
                parts.append('<line x1="%.1f" y1="30" x2="%.1f" y2="%d" '
                             'stroke="#333" stroke-dasharray="2,2"/>'
                             % (x(r['t_ms']), x(r['t_ms']), h - m))
                parts.append('<text x="%.1f" y="%d" font-size="9" '
                             'transform="rotate(50 %.1f %d)">%s</text>'
                             % (x(r['t_ms']) + 2, h - m + 12,
                                x(r['t_ms']) + 2, h - m + 12,
                                r['event'][:42]))
        parts.append('</svg>')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(parts))

    def _svg_phases(self, path):
        w, top, bh = 900, 54, 34
        ts = [r['t_ms'] for r in self.rows]
        t_max = max(ts) or 1
        h = top + 2 * (bh + 18) + 46

        def x(v):
            return 46 + v / float(t_max) * (w - 92)
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" '
                 'height="%d" font-family="sans-serif">' % (w, h),
                 '<rect width="100%" height="100%" fill="white"/>',
                 '<text x="46" y="24" font-size="14">phase / state timeline '
                 '(software replay)</text>']
        for key, lane, label in (('state', 0, 'state'),
                                 ('phase', 1, 'phase')):
            y = top + lane * (bh + 18)
            parts.append('<text x="6" y="%.1f" font-size="12">%s</text>'
                         % (y + bh / 2.0, label))
            prev, start = None, 0
            ext = self.rows + [None]
            for i, r in enumerate(ext):
                val = r[key] if r is not None else object()
                if prev is not None and (r is None or val != prev):
                    x0 = x(self.rows[start]['t_ms'])
                    x1 = x(self.rows[i - 1]['t_ms'])
                    fill = (PHASE_COLORS.get(prev, '#cccccc')
                            if key == 'phase' else
                            ('#ff9c9c' if prev == 'walking' else '#9db8e8'))
                    parts.append('<rect x="%.1f" y="%d" width="%.1f" '
                                 'height="%d" fill="%s" stroke="#999"/>'
                                 % (x0, y, max(1.0, x1 - x0), bh, fill))
                    if x1 - x0 > 42 and prev:
                        parts.append('<text x="%.1f" y="%.1f" font-size="10">'
                                     '%s</text>' % (x0 + 2, y + bh - 10, prev))
                if r is None or val != prev:
                    prev = val if r is not None else None
                    start = i
        for r in self.rows:
            if r['event']:
                parts.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" '
                             'stroke="#333" stroke-dasharray="2,2"/>'
                             % (x(r['t_ms']), top - 6, x(r['t_ms']),
                                h - 40))
                parts.append('<text x="%.1f" y="%d" font-size="9" '
                             'transform="rotate(45 %.1f %d)">%s</text>'
                             % (x(r['t_ms']) + 2, h - 28,
                                x(r['t_ms']) + 2, h - 28, r['event'][:44]))
        parts.append('</svg>')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(parts))
