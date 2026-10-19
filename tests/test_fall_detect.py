from fall_detect import detect_fall


def test_spike_then_still_is_fall():
    samples = [(0.0, 1.0), (0.1, 3.0), (0.2, 1.0), (1.2, 1.0), (2.3, 1.0)]
    assert detect_fall(samples) is True


def test_no_spike_is_not_fall():
    samples = [(0.0, 1.0), (1.0, 1.1), (2.0, 0.9), (3.0, 1.0)]
    assert detect_fall(samples) is False


def test_spike_then_moving_is_not_fall():
    # person gets up and keeps moving after the impact
    samples = [(0.0, 1.0), (0.1, 3.0), (0.5, 1.8), (1.0, 0.4), (1.5, 1.7), (2.5, 0.5)]
    assert detect_fall(samples) is False


def test_still_too_short_is_not_fall():
    # still for only 1.5 s, below the 2 s requirement
    samples = [(0.0, 1.0), (0.1, 3.0), (0.2, 1.0), (1.7, 1.0)]
    assert detect_fall(samples) is False


def test_spike_exactly_at_threshold_is_not_fall():
    # rule is "above 2.5 g", so exactly 2.5 g should not trigger
    samples = [(0.0, 1.0), (0.1, 2.5), (0.2, 1.0), (2.3, 1.0)]
    assert detect_fall(samples) is False

def test_still_exactly_2s_is_not_fall():
    # firmware uses "more than 2000 ms", so exactly 2.0 s is not enough
    samples = [(0.0, 1.0), (0.25, 3.0), (0.5, 1.0), (2.5, 1.0)]
    assert detect_fall(samples) is False


def test_band_edges_count_as_still():
    # 0.8 g and 1.2 g are inside the band (inclusive)
    samples = [(0.0, 1.0), (0.1, 3.0), (0.2, 0.8), (1.0, 1.2), (2.3, 0.8)]
    assert detect_fall(samples) is True


def test_just_outside_band_resets_timer():
    # 1.21 g breaks the stillness, so the 2 s timer restarts
    samples = [(0.0, 1.0), (0.1, 3.0), (0.2, 1.0), (1.0, 1.21), (1.1, 1.0), (2.3, 1.0)]
    assert detect_fall(samples) is False


def test_gives_up_after_15s():
    # keeps moving past 15 s after impact, then goes still: too late
    samples = [(0.0, 1.0), (0.1, 3.0), (5.0, 1.8), (10.0, 0.3), (15.5, 1.7),
               (16.0, 1.0), (19.0, 1.0)]
    assert detect_fall(samples) is False


def test_still_late_but_within_15s_is_fall():
    # moves for a while, then goes still before the 15 s give-up
    samples = [(0.0, 1.0), (0.1, 3.0), (5.0, 1.8), (10.0, 1.0), (12.5, 1.0)]
    assert detect_fall(samples) is True


def test_new_impact_after_give_up_is_detected():
    samples = [(0.0, 1.0), (0.1, 3.0), (15.5, 1.7),
               (20.0, 3.0), (20.1, 1.0), (22.5, 1.0)]
    assert detect_fall(samples) is True