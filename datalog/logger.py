import argparse
import time

import db
from parse import parse_line


def lines_from_serial(port):
    import serial
    with serial.Serial(port, 115200, timeout=1) as ser:
        while True:
            yield ser.readline().decode(errors="ignore")


def lines_from_file(path):
    with open(path) as f:
        for line in f:
            yield line


def main():
    ap = argparse.ArgumentParser(description="Log Solemate data to SQLite")
    ap.add_argument("--label", required=True, help="e.g. walking, fake_fall")
    ap.add_argument("--real-fall", action="store_true", help="a fall was staged")
    ap.add_argument("--port", help="e.g. COM4 (real device)")
    ap.add_argument("--fake", help="text file of lines (no device)")
    ap.add_argument("--db", default="solemate.db")
    args = ap.parse_args()

    conn = db.connect(args.db)
    sid = db.start_session(conn, args.label, args.real_fall)
    print(f"Session {sid} started. Press Ctrl+C to stop.")

    source = lines_from_file(args.fake) if args.fake else lines_from_serial(args.port)
    start = time.time()
    count = 0
    fake_t = 0.0

    try:
        for line in source:
            item = parse_line(line)
            if item is None:
                continue
            if args.fake:
                # fake mode: pretend each data line is 0.5 s apart
                if item["type"] == "reading":
                    fake_t += 0.5
                t = fake_t
            else:
                t = time.time() - start
            db.save(conn, sid, t, item)
            count += 1
            if count % 20 == 0:
                conn.commit()
    except KeyboardInterrupt:
        pass
    finally:
        conn.commit()
        conn.close()
        print(f"Session {sid} saved, {count} lines logged.")


if __name__ == "__main__":
    main()