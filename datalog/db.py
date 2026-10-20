import sqlite3
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT,
    label       TEXT,     -- what you did: walking, fake_fall, sitting...
    real_fall   INTEGER   -- 1 if a real (staged) fall happened, 0 if not
);
CREATE TABLE IF NOT EXISTS readings (
    session_id  INTEGER,
    t_s         REAL,     -- seconds since the session started
    g REAL, temp_c REAL,
    p1 INTEGER, p2 INTEGER, p3 INTEGER, p4 INTEGER,
    countdown INTEGER, status TEXT, steps INTEGER
);
CREATE TABLE IF NOT EXISTS events (
    session_id  INTEGER,
    t_s         REAL,
    event       TEXT      -- impact, fall, no_fall, sos, cancelled
);
"""


def connect(path="solemate.db"):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def start_session(conn, label, real_fall):
    cur = conn.execute(
        "INSERT INTO sessions (started_at, label, real_fall) VALUES (?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), label, int(real_fall)),
    )
    conn.commit()
    return cur.lastrowid


def save(conn, session_id, t_s, item):
    if item["type"] == "reading":
        conn.execute(
            "INSERT INTO readings VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (session_id, t_s, item["g"], item["temp_c"],
             item["p1"], item["p2"], item["p3"], item["p4"],
             item["countdown"], item["status"], item["steps"]),
        )
    elif item["type"] == "event":
        conn.execute(
            "INSERT INTO events VALUES (?,?,?)",
            (session_id, t_s, item["event"]),
        )