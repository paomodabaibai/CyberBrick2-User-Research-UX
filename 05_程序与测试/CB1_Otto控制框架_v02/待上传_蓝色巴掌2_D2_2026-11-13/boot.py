# Custom receiver boot. Official app and rc_config retained for rollback.
import sys
if '/app' not in sys.path: sys.path.append('/app')
