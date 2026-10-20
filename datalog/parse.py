def parse_line(line):
    """
    Turns one line from the ESP32 into a Python dict.

    Data line example:
      F:1.02,T:31.5,P1:120,P2:85,P3:0,P4:40,C:0,S:OK,ST:12
      -> {"type": "reading", "g": 1.02, "temp_c": 31.5, ...}

    Event line example:
      !!! FALL DETECTED !!!
      -> {"type": "event", "event": "fall"}

    Returns None for lines we don't care about.
    """
    line = line.strip()

    events = {
        ">> Impact detected": "impact",
        "!!! FALL DETECTED !!!": "fall",
        ">> No fall": "no_fall",
        "*** SENDING SOS ***": "sos",
        ">> Alert cancelled from app": "cancelled",
    }
    if line in events:
        return {"type": "event", "event": events[line]}

    if not line.startswith("F:"):
        return None

    try:
        fields = dict(part.split(":", 1) for part in line.split(","))
        return {
            "type": "reading",
            "g": float(fields["F"]),
            "temp_c": float(fields["T"]),
            "p1": int(fields["P1"]),
            "p2": int(fields["P2"]),
            "p3": int(fields["P3"]),
            "p4": int(fields["P4"]),
            "countdown": int(fields["C"]),
            "status": fields["S"],
            "steps": int(fields["ST"]),
        }
    except (KeyError, ValueError):
        return None  # broken or cut-off line