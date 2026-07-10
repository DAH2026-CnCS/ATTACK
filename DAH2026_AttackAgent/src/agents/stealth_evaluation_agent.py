from __future__ import annotations

import statistics
from typing import Dict, List

from schemas.mission_schema import BaselineProfile, MissionRecord, MissionScenario, StealthReport


def _avg(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


class StealthEvaluationAgent:
    """Evaluates whether synthetic perturbations stay within a plausible DDIL budget."""

    def evaluate(self, scenario: MissionScenario, records: List[MissionRecord], profile: BaselineProfile) -> StealthReport:
        window = [r for r in records if scenario.decision_start_s <= r.t <= scenario.decision_end_s]
        if not window:
            return StealthReport(scenario.scenario_id, 0.0, False, 99, {})

        avg_rtt = _avg([r.rtt_ms for r in window])
        avg_loss = _avg([r.packet_loss for r in window])
        avg_hb = _avg([r.heartbeat_interval_s for r in window])
        avg_video_delay = _avg([r.t - r.video_timestamp for r in window])
        avg_log_delay = _avg([r.gcs_log_timestamp - r.t for r in window])
        avg_imu = _avg([r.imu_motion for r in window])

        # Normalized excess over a plausible operational threshold.
        checks: Dict[str, float] = {
            "rtt_excess": max(0.0, (avg_rtt - (profile.rtt_mean + 4.5 * profile.rtt_std)) / 80.0),
            "packet_loss_excess": max(0.0, (avg_loss - (profile.packet_loss_mean + 0.090)) / 0.070),
            "heartbeat_excess": max(0.0, (avg_hb - 1.65) / 0.80),
            "video_delay_excess": max(0.0, (avg_video_delay - 20.0) / 18.0),
            "log_delay_excess": max(0.0, (avg_log_delay - 6.0) / 8.0),
            "imu_suppression_excess": max(0.0, ((profile.imu_mean * 0.25) - avg_imu) / max(0.001, profile.imu_mean)),
        }
        anomaly_count = sum(1 for v in checks.values() if v > 0.0)
        hard_penalty = sum(min(1.0, v) for v in checks.values())
        # Soft penalty rewards realistic low-amplitude perturbations but does not make
        # stealth look artificially perfect. Even stealthy replay and micro-delay leave
        # some measurable footprint in a C2 audit trail.
        soft_penalty = (
            max(0.0, avg_rtt - profile.rtt_mean) / max(1.0, profile.rtt_std * 12.0)
            + avg_loss / 0.30
            + max(0.0, avg_hb - profile.heartbeat_mean) / 1.4
            + avg_video_delay / 42.0
            + avg_log_delay / 18.0
            + max(0.0, profile.imu_mean - avg_imu) / max(0.001, profile.imu_mean) * 0.45
        )
        stealth_score = max(0.0, 100.0 - hard_penalty * 16.0 - soft_penalty * 9.0 - anomaly_count * 2.5)
        return StealthReport(
            scenario_id=scenario.scenario_id,
            stealth_score=round(stealth_score, 2),
            anomaly_budget_passed=stealth_score >= 72.0 and anomaly_count <= 3,
            anomaly_count=anomaly_count,
            checks={k: round(v, 4) for k, v in checks.items()},
        )
