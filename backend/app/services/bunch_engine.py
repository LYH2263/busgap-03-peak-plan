"""Bus bunching: planned headway vs actual arrival gaps."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime

@dataclass
class PeakWindow:
    """高峰窗口：起止分钟（相对当日 0 点）与高峰计划发车间隔。

    半开区间 [start_min, end_min)：到站时刻的「时*60+分」落在其中视为高峰内。
    """
    start_min: int
    end_min: int
    headway_min: float

    def contains(self, t: datetime) -> bool:
        minute = t.hour * 60 + t.minute
        return self.start_min <= minute < self.end_min

@dataclass
class GapEvent:
    stop_name: str
    earlier_trip: str
    later_trip: str
    gap_min: float
    planned_headway_min: float
    status: str
    suggestion: str
    period: str = ""  # "peak" / "offpeak"；线路未配置高峰时为 ""

def classify_gap(gap_min: float, planned_headway_min: float, bunch_threshold: float, large_threshold: float, period_label: str | None = None) -> tuple[str, str]:
    if gap_min < bunch_threshold:
        return ("bunching", f"间隔 {gap_min:.1f} 分钟低于串车阈值 {bunch_threshold}，建议后车缓行或抽稀。")
    if gap_min > large_threshold:
        return ("large_gap", f"间隔 {gap_min:.1f} 分钟超过大间隔阈值 {large_threshold}，建议前车减速或加发。")
    if period_label:
        return ("normal", f"间隔接近计划 {planned_headway_min:.1f} 分钟（{period_label}），保持即可。")
    return ("normal", f"间隔接近计划 {planned_headway_min:.1f} 分钟，保持即可。")

def detect_bunching(arrivals: list[dict], planned_headway_min: float, bunch_threshold: float, large_threshold: float, peak: PeakWindow | None = None) -> list[GapEvent]:
    by_stop: dict[str, list[dict]] = {}
    for a in arrivals:
        by_stop.setdefault(a["stop_name"], []).append(a)
    events: list[GapEvent] = []
    for stop, items in by_stop.items():
        items = sorted(items, key=lambda x: x["actual_arrive"])
        for i in range(1, len(items)):
            prev, cur = items[i - 1], items[i]
            gap_min = (cur["actual_arrive"] - prev["actual_arrive"]).total_seconds() / 60.0
            headway, label, period = planned_headway_min, None, ""
            if peak is not None:
                # 两班到站都落在高峰窗内才用高峰间隔，否则用平峰计划间隔
                if peak.contains(prev["actual_arrive"]) and peak.contains(cur["actual_arrive"]):
                    headway, label, period = peak.headway_min, "高峰", "peak"
                else:
                    label, period = "平峰", "offpeak"
            status, suggestion = classify_gap(gap_min, headway, bunch_threshold, large_threshold, label)
            events.append(GapEvent(stop, prev["trip_no"], cur["trip_no"], round(gap_min, 2), headway, status, suggestion, period))
    return events

def events_to_dicts(events: list[GapEvent]) -> list[dict]:
    return [asdict(e) for e in events]
