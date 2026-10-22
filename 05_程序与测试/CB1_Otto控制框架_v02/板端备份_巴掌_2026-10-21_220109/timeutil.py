"""Board-safe monotonic time helpers, shared by PC tests and board loop.

Board (MicroPython): time.ticks_ms + time.ticks_diff, which handle counter
wrap correctly on every port - use them verbatim.
PC (CPython): no ticks API, so now_ms() returns a 30-bit-masked monotonic
millisecond count and diff_ms() implements the same signed wrap-around
difference. The identical wrap semantics on both sides is the point: timing
tests written on the PC exercise the same edge cases the board will hit.
"""
import time

if hasattr(time, 'ticks_ms'):          # MicroPython
    def now_ms():
        return time.ticks_ms()

    def diff_ms(a, b):
        """Signed milliseconds a-b, wrap-safe."""
        return time.ticks_diff(a, b)
else:                                   # CPython
    _WRAP = 1 << 30                     # match the usual MicroPython width

    def now_ms():
        return int(time.monotonic() * 1000) & (_WRAP - 1)

    def diff_ms(a, b):
        d = (a - b) & (_WRAP - 1)
        return d - _WRAP if d >= _WRAP // 2 else d
