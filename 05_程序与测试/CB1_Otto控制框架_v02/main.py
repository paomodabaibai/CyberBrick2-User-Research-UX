"""CB1 receiver startup: Otto continuous remote mode (v05).

On power-up the receiver waits for the remote link, then enables stance
by itself and stays ready until power-off. Controls:
    hold sticks FORWARD   -> walk forward (both sticks = straight)
    hold ONE stick only   -> forward with an arc (asymmetric hip stride)
    pull sticks BACK      -> walk backward
    release everything    -> ramp down and stand
The ONLY stop is the physical power switch. Attack stick (ch2) reserved.
"""
import otto_session

otto_session.run()
