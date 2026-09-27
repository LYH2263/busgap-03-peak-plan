from datetime import datetime, timedelta
from app.services.bunch_engine import PeakWindow, classify_gap, detect_bunching

def test_classify_bunching():
    assert classify_gap(2.0, 8.0, 3.0, 15.0)[0] == "bunching"

def test_classify_large():
    assert classify_gap(16.0, 8.0, 3.0, 15.0)[0] == "large_gap"

def test_classify_normal():
    assert classify_gap(8.0, 8.0, 3.0, 15.0)[0] == "normal"

def test_detect_bunching_events():
    base = datetime(2026, 1, 1, 8, 0)
    arrivals = [
        {"stop_name": "A", "trip_no": "T1", "actual_arrive": base},
        {"stop_name": "A", "trip_no": "T2", "actual_arrive": base + timedelta(minutes=2)},
        {"stop_name": "A", "trip_no": "T3", "actual_arrive": base + timedelta(minutes=20)},
    ]
    events = detect_bunching(arrivals, 8.0, 3.0, 15.0)
    assert len(events) == 2
    assert events[0].status == "bunching"
    assert events[1].status == "large_gap"

def test_classify_normal_with_period_label():
    status, text = classify_gap(5.0, 5.0, 3.0, 15.0, "高峰")
    assert status == "normal"
    assert "高峰" in text
    assert "5.0" in text

def test_peak_window_boundary():
    peak = PeakWindow(420, 540, 4.0)  # 07:00–09:00
    assert peak.contains(datetime(2026, 1, 1, 7, 0))
    assert peak.contains(datetime(2026, 1, 1, 8, 59))
    assert not peak.contains(datetime(2026, 1, 1, 9, 0))
    assert not peak.contains(datetime(2026, 1, 1, 6, 59))

def test_detect_with_peak_window():
    base = datetime(2026, 1, 1, 8, 0)  # 高峰 07:00–09:00，高峰间隔 4 分
    peak = PeakWindow(420, 540, 4.0)
    arrivals = [
        {"stop_name": "A", "trip_no": "T1", "actual_arrive": base},
        {"stop_name": "A", "trip_no": "T2", "actual_arrive": base + timedelta(minutes=5)},
        {"stop_name": "A", "trip_no": "T3", "actual_arrive": base + timedelta(hours=4)},
        {"stop_name": "A", "trip_no": "T4", "actual_arrive": base + timedelta(hours=4, minutes=6)},
    ]
    events = detect_bunching(arrivals, 8.0, 3.0, 15.0, peak)
    assert len(events) == 3
    # 两班都在高峰内：用高峰间隔，文案带「高峰」
    assert events[0].planned_headway_min == 4.0
    assert events[0].period == "peak"
    assert events[0].status == "normal"
    assert "高峰" in events[0].suggestion
    # 一班在高峰一班不在：按平峰
    assert events[1].planned_headway_min == 8.0
    assert events[1].period == "offpeak"
    # 两班都在高峰外：按平峰，文案带「平峰」
    assert events[2].planned_headway_min == 8.0
    assert events[2].period == "offpeak"
    assert events[2].status == "normal"
    assert "平峰" in events[2].suggestion

def test_detect_without_peak_unchanged():
    base = datetime(2026, 1, 1, 8, 0)
    arrivals = [
        {"stop_name": "A", "trip_no": "T1", "actual_arrive": base},
        {"stop_name": "A", "trip_no": "T2", "actual_arrive": base + timedelta(minutes=8)},
    ]
    events = detect_bunching(arrivals, 8.0, 3.0, 15.0)
    assert events[0].period == ""
    assert events[0].planned_headway_min == 8.0
    assert events[0].suggestion == "间隔接近计划 8.0 分钟，保持即可。"
