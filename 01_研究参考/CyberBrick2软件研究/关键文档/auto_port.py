"""
auto_port - CB2 runtime port auto-detection utility.

Usage: see knowledge/skill/cb2/cb2-auto-port/SKILL.md.

Public API:
    port_of(kind, index=0, raise_error_if_not_exist=True)  Main interface: returns port name (e.g. "A3")
    list_modules()                                          Returns {normalized kind: [port_name list sorted by port_id], ...}
    reset()                                                 Optional: clears local resolve / log cache (see "Hard limit" below)

Behavior summary:
- kind is compared against the module_name field from cyberbrick.Port.list(),
  both sides normalized (lowercase + strip "_" / "-" / spaces).
  So "HallSplit" / "hall_split" / "HALL-SPLIT" are equivalent.
- Real matches are sorted by port_id ascending, the index-th one is returned.
- If the device is not found:
    raise_error_if_not_exist=True  -> raises LookupError (default; the program
                                      stops with a clear error, so put port_of()
                                      calls at the top of the file to fail fast).
    raise_error_if_not_exist=False -> returns "" (empty string), useful when you
                                      only want to probe whether a device exists.
- Results for the same (kind, index) are cached; subsequent calls return
  immediately without printing again. Safe to call at high frequency.
- First call to port_of() / list_modules() automatically loads Port.list()
  from the board once. **Caller does NOT need to init at program start.**

Hard limit (detection only happens at soft-boot):
- cyberbrick.Port.list() only scans wiring once at CB2 power-on / soft-reset
  (machine.soft_reset / power cycle). Devices plugged or unplugged while running
  are NOT detected (hot-plug detection not yet implemented).
- reset() only clears auto_port's own local caches (_resolved / _logged),
  allowing first-time logs to print again;
  it does NOT re-read Port.list() (data won't change, re-reading is pointless).
- To recognize newly changed wiring, the ONLY way is [soft-reset + re-run entry .py],
  making firmware re-scan Port.list().
"""

import cyberbrick


_loaded = False
_modules = {}        # normalized kind -> [port_name, ...] (sorted by port_id ascending)
_resolved = {}       # cache: (norm_kind, index) -> port_name (or "")
_logged = set()      # (norm_kind, index) keys that have printed first-time log


def _norm(s):
    return ''.join(c for c in str(s).lower() if c not in ('_', '-', ' '))


def _load():
    """One-time lazy load: read firmware Port.list(), sort by port_id into _modules."""
    global _loaded, _modules
    entries = sorted(cyberbrick.Port.list(), key=lambda e: e.get('port_id', 0))
    _modules = {}
    for e in entries:
        port = e.get('port_name')
        if not port:
            continue
        mname = e.get('module_name')
        if not mname:
            continue
        _modules.setdefault(_norm(mname), []).append(port)
    _loaded = True


def reset():
    """Clear local resolve / log caches, allowing first-time logs to print again.

    Clears only auto_port's own two cache sets:
        _resolved   cached (kind, index) -> port mappings
        _logged     (kind, index) keys that have printed first-time log

    Does NOT re-read firmware Port.list() -- cyberbrick.Port.list() only scans
    wiring at CB2 power-on / soft-reset; calling this function while running
    cannot detect newly changed wiring. To recognize new wiring, do
    [soft-reset + re-run entry .py]. See module docstring "Hard limit" section.
    """
    global _resolved, _logged
    _resolved = {}
    _logged = set()


def port_of(kind, index=0, raise_error_if_not_exist=True):
    """Return the port name for the index-th device of the given kind (sorted by port_id ascending).

    Args:
        kind (str): Module type, matched against module_name case-insensitively
            (underscores, hyphens, spaces are ignored).
        index (int): Which same-type device, 0-based, sorted by port_id ascending.
        raise_error_if_not_exist (bool): When the device is not found on board,
            True raises LookupError (default); False returns "" (empty string).

    Returns: port name string (e.g. "A3"), or "" when not found and
        raise_error_if_not_exist=False.
    """
    if not _loaded:
        _load()
    key = (_norm(kind), index)
    if key in _resolved:
        return _resolved[key]
    ports = _modules.get(_norm(kind), [])
    if index < len(ports):
        port = ports[index]
        _resolved[key] = port
        if key not in _logged:
            print('auto_port: resolved {}(index={}) -> {} (detected on board)'.format(kind, index, port))
            _logged.add(key)
        return port
    if raise_error_if_not_exist:
        raise LookupError(
            'auto_port: {}(index={}) not detected on board'.format(kind, index)
        )
    _resolved[key] = ''
    if key not in _logged:
        print(
            'auto_port: {}(index={}) not detected on board, returning "" '
            '(raise_error_if_not_exist=False)'.format(kind, index)
        )
        _logged.add(key)
    return ''


def list_modules():
    """Debug helper: returns {normalized kind: [port_name list sorted by port_id], ...}."""
    if not _loaded:
        _load()
    return dict(_modules)
