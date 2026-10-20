import sqlite3
import sys

db_path = sys.argv[1] if len(sys.argv) > 1 else "solemate.db"
conn = sqlite3.connect(db_path)

# 1. Did the device detect a fall in each session? Compare with reality.
print("1. Detected vs real, per session")
q1 = """
SELECT s.id, s.label, s.real_fall,
       COUNT(CASE WHEN e.event = 'fall' THEN 1 END)      AS detected,
       COUNT(CASE WHEN e.event = 'cancelled' THEN 1 END) AS cancelled,
       COUNT(CASE WHEN e.event = 'sos' THEN 1 END)       AS sos_sent
FROM sessions s
LEFT JOIN events e ON e.session_id = s.id
GROUP BY s.id
ORDER BY s.id;
"""
for row in conn.execute(q1):
    print("  ", row)

# 2. Summary: correct detections, missed falls, false alarms
print("\n2. Summary")
q2 = """
SELECT
  SUM(CASE WHEN real_fall = 1 AND detected > 0 THEN 1 ELSE 0 END) AS caught,
  SUM(CASE WHEN real_fall = 1 AND detected = 0 THEN 1 ELSE 0 END) AS missed,
  SUM(CASE WHEN real_fall = 0 AND detected > 0 THEN 1 ELSE 0 END) AS false_alarms,
  SUM(CASE WHEN real_fall = 0 THEN 1 ELSE 0 END)                  AS no_fall_sessions
FROM (
  SELECT s.id, s.real_fall,
         COUNT(CASE WHEN e.event = 'fall' THEN 1 END) AS detected
  FROM sessions s
  LEFT JOIN events e ON e.session_id = s.id
  GROUP BY s.id
);
"""
caught, missed, false_alarms, no_fall = conn.execute(q2).fetchone()
print(f"   caught={caught}, missed={missed}, false_alarms={false_alarms}")
if no_fall:
    print(f"   false-alarm rate = {false_alarms}/{no_fall} no-fall sessions")

# 3. Average pressure per sensor, per activity
print("\n3. Average pressure (heel, ball-in, ball-out, toe) by activity")
q3 = """
SELECT s.label,
       ROUND(AVG(r.p1)), ROUND(AVG(r.p2)), ROUND(AVG(r.p3)), ROUND(AVG(r.p4))
FROM readings r
JOIN sessions s ON s.id = r.session_id
GROUP BY s.label;
"""
for row in conn.execute(q3):
    print("  ", row)

# 4. Temperature range per session
print("\n4. Temperature range per session")
q4 = """
SELECT session_id, MIN(temp_c), MAX(temp_c), ROUND(AVG(temp_c), 1)
FROM readings
GROUP BY session_id;
"""
for row in conn.execute(q4):
    print("  ", row)

conn.close()