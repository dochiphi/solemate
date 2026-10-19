# Python model of the fall-detection logic in firmware/hardware/Solemate.ino
IMPACT_G = 2.5
STILL_LOW = 0.8
STILL_HIGH = 1.2
STILL_TIME_S = 2.0     # firmware: STILL_TIME = 2000 ms
GIVE_UP_TIME_S = 15.0  # firmware: GIVE_UP_TIME = 15000 ms


def detect_fall(samples):
    """
    samples: list of (time_s, accel_g) tuples, sorted by time.
    Returns True if the firmware logic would detect a fall.
    """
    watching = False
    counting = False
    impact_time = 0.0
    still_start = 0.0

    for t, g in samples:
        if not watching:
            if g > IMPACT_G:
                watching = True
                counting = False
                impact_time = t
        else:
            is_still = STILL_LOW <= g <= STILL_HIGH
            if is_still:
                if not counting:
                    counting = True
                    still_start = t
                if t - still_start > STILL_TIME_S:
                    return True
            else:
                counting = False
            if t - impact_time > GIVE_UP_TIME_S:
                watching = False

    return False