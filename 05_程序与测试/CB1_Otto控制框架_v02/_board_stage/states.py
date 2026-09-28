"""Machine states and step lifecycle for the whole robot."""

DISABLED = 'disabled'   # needs an explicit enable(); no step accepted
READY = 'ready'         # enabled, holding stance, can accept a step
WALKING = 'walking'     # executing a planned step trajectory
STOPPED = 'stopped'     # explicit stop: cancel action, HOLD last commanded pose
FAULT = 'fault'         # link loss or limit violation; explicit recover() only

# Notes carried into docs:
# - STOPPED/FAULT hold the last COMMANDED pose; that does not guarantee the
#   real robot is standing. release_output() is a separate driver action.
# - After FAULT, a reconnecting link never resumes walking by itself.
