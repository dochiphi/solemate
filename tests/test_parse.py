import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "datalog"))
from parse import parse_line


def test_data_line():
    item = parse_line("F:1.02,T:31.5,P1:120,P2:85,P3:0,P4:40,C:0,S:OK,ST:12")
    assert item["type"] == "reading"
    assert item["g"] == 1.02
    assert item["p1"] == 120
    assert item["status"] == "OK"
    assert item["steps"] == 12


def test_fall_event():
    assert parse_line("!!! FALL DETECTED !!!") == {"type": "event", "event": "fall"}


def test_cancel_event():
    assert parse_line(">> Alert cancelled from app")["event"] == "cancelled"


def test_line_with_newline_and_spaces():
    assert parse_line("  >> Impact detected\r\n")["event"] == "impact"


def test_cut_off_line_is_ignored():
    # serial lines can arrive broken at startup
    assert parse_line("F:1.02,T:31.5,P1:12") is None


def test_unrelated_line_is_ignored():
    assert parse_line("Ready, BLE advertising as 'Solemate'") is None