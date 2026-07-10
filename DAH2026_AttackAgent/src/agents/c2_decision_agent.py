from __future__ import annotations

import statistics
from typing import List

from schemas.mission_schema import BaselineProfile, C2Decision, MissionRecord, MissionScenario


def _avg(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


class C2DecisionAgent:
    """A transparent C2 decision model used only for prototype validation.

    It fuses video risk, network freshness, and sensor consistency to decide
    whether Route A is safe for UGV movement.
    """

    def decide(self, scenario: MissionScenario, records: List[MissionRecord], profile: BaselineProfile) -> C2Decision:
        window = [r for r in records if scenario.decision_start_s <= r.t <= scenario.decision_end_s]
        if not window:
            return C2Decision(scenario.scenario_id, "HOLD_POSITION", "HOLD_POSITION", "UNKNOWN", 1.0, ["no decision window"])

        video_risk = _avg([r.video_risk_score for r in window])
        rtt = _avg([r.rtt_ms for r in window])
        loss = _avg([r.packet_loss for r in window])
        video_delay = _avg([r.t - r.video_timestamp for r in window])
        log_delay = _avg([r.gcs_log_timestamp - r.t for r in window])

        # Consistency: GNSS indicates progress but IMU is too quiet. This is a weak suspicion signal,
        # intentionally not enough alone to stop the UGV in a noisy DDIL condition.
        lat_delta = window[-1].reported_uav_lat - window[0].reported_uav_lat
        lon_delta = window[-1].reported_uav_lon - window[0].reported_uav_lon
        imu_mean = _avg([r.imu_motion for r in window])
        movement_score = abs(lat_delta) + abs(lon_delta)
        sensor_mismatch = 1.0 if movement_score > 0.0012 and imu_mean < max(0.08, profile.imu_mean * 0.45) else 0.0

        # Communication penalty is bounded because the scenario assumes DDIL-like battlefield noise.
        # DDIL masking model: if telemetry arrives with mild network degradation,
        # C2 tends to interpret stale imagery as operational delay rather than immediate compromise.
        ddil_mask = max(0.0, min(0.75, (rtt - profile.rtt_mean) / 70.0 + max(0.0, loss - profile.packet_loss_mean) / 0.10))
        rtt_penalty = max(0.0, min(0.10, (rtt - (profile.rtt_mean + 4.0 * profile.rtt_std)) / 300.0))
        loss_penalty = max(0.0, min(0.10, (loss - (profile.packet_loss_mean + 0.08)) * 1.2))
        raw_stale_penalty = max(0.0, min(0.28, (video_delay - 9.0) / 38.0))
        stale_penalty = raw_stale_penalty * (1.0 - 0.65 * ddil_mask)
        log_penalty = max(0.0, min(0.06, (log_delay - 5.0) / 90.0))
        sensor_penalty = 0.08 * sensor_mismatch

        perceived_risk = min(1.0, max(0.0, video_risk + rtt_penalty + loss_penalty + stale_penalty + log_penalty + sensor_penalty))

        evidence = [
            f"video_risk={video_risk:.3f}",
            f"avg_rtt={rtt:.1f}ms",
            f"packet_loss={loss:.3f}",
            f"video_delay={video_delay:.1f}s",
            f"log_delay={log_delay:.1f}s",
            f"ddil_mask={ddil_mask:.2f}",
            f"sensor_mismatch={sensor_mismatch:.0f}",
            f"perceived_risk={perceived_risk:.3f}",
        ]

        if perceived_risk < 0.48:
            return C2Decision(scenario.scenario_id, "MOVE_UGV_TO_ROUTE_A", "MOVE", "SAFE", round(perceived_risk, 4), evidence)
        return C2Decision(scenario.scenario_id, "HOLD_POSITION", "HOLD_POSITION", "DANGER", round(perceived_risk, 4), evidence)
