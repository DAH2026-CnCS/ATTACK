from __future__ import annotations

import statistics
from typing import List

from schemas.mission_schema import BaselineProfile, MissionRecord


def _mean(values: List[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _std(values: List[float]) -> float:
    return statistics.stdev(values) if len(values) >= 2 else 0.0


class BaselineProfilingAgent:
    """Learns normal ranges before the attack window."""

    def build_profile(self, records: List[MissionRecord], warmup_until_s: int) -> BaselineProfile:
        base = [r for r in records if r.t < warmup_until_s]
        video_delay = [r.t - r.video_timestamp for r in base]
        log_delay = [r.gcs_log_timestamp - r.t for r in base]
        return BaselineProfile(
            rtt_mean=_mean([r.rtt_ms for r in base]),
            rtt_std=max(_std([r.rtt_ms for r in base]), 1.0),
            heartbeat_mean=_mean([r.heartbeat_interval_s for r in base]),
            heartbeat_std=max(_std([r.heartbeat_interval_s for r in base]), 0.03),
            packet_loss_mean=_mean([r.packet_loss for r in base]),
            packet_loss_std=max(_std([r.packet_loss for r in base]), 0.003),
            video_delay_mean=_mean(video_delay),
            video_delay_std=max(_std(video_delay), 0.05),
            log_delay_mean=_mean(log_delay),
            log_delay_std=max(_std(log_delay), 0.04),
            imu_mean=_mean([r.imu_motion for r in base]),
            imu_std=max(_std([r.imu_motion for r in base]), 0.01),
        )
