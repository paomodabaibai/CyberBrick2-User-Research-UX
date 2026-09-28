"""Driver factory. Simulation mode NEVER imports machine or cb1_pwm.

The driver is chosen from the SAME config object the caller built its joint
model from - never from a global - so a simulation profile (sim_config) can
never select the hardware driver, and a hardware config can never silently
fall back to sim.

Board-side import chain stays free of os.path / sys.path juggling: modules
are uploaded flat to '/' and imported top-level.
"""


def create_driver(joint_model_ref, cfg):
    # cfg is required on purpose: driver selection must come from the same
    # configuration the controller was built with.
    if cfg.DRIVER == 'sim':
        from drivers.sim_driver import SimDriver
        return SimDriver()
    if cfg.DRIVER == 'cb1_pwm':
        from drivers import cb1_pwm
        return cb1_pwm.create(joint_model_ref, cfg)
    raise ValueError('unknown DRIVER %r' % cfg.DRIVER)
