from __future__ import annotations

import math
import random
from typing import List

from schemas.mission_schema import MissionRecord, MissionScenario


class MissionContextAgent:
    """Generate synthetic UAV-GCS-C2-UGV joint reconnaissance scenarios.

    The agent does not connect to a real UAV/GCS. It creates reproducible mission
    streams that contain the same trust-flow elements used in the report:
    UAV telemetry, video risk, network delay, GCS log time, and C2 arrival time.
    """

    def generate_scenario(self, scenario_id: int, seed: int) -> MissionScenario:
        rng = random.Random(seed + scenario_id * 997)
        duration = rng.choice([90, 100, 110, 120])
        decision_start = rng.choice([55, 60, 65, 70])
        decision_end = min(duration - 5, decision_start + rng.choice([15, 18, 20]))
        hazard_time = decision_start - rng.choice([5, 8, 10, 12])
        hazard_severity = rng.uniform(0.78, 0.96)
        base_rtt = rng.uniform(42.0, 72.0)
        jitter = rng.uniform(4.0, 9.0)
        loss = rng.uniform(0.005, 0.025)
        imu_noise = rng.uniform(0.012, 0.028)
        return MissionScenario(
            scenario_id=scenario_id,
            seed=seed,
            duration_s=duration,
            decision_start_s=decision_start,
            decision_end_s=decision_end,
            hazard_time_s=hazard_time,
            hazard_severity=hazard_severity,
            base_rtt_ms=base_rtt,
            rtt_jitter_ms=jitter,
            baseline_packet_loss=loss,
            imu_noise=imu_noise,
        )

    def generate_records(self, scenario: MissionScenario) -> List[MissionRecord]:
        rng = random.Random(scenario.seed + scenario.scenario_id * 1733)
        records: List[MissionRecord] = []
        lat0 = 37.1000 + rng.uniform(-0.005, 0.005)
        lon0 = 127.1000 + rng.uniform(-0.005, 0.005)
        phase = "TRANSIT"

        for t in range(scenario.duration_s + 1):
            if t >= scenario.decision_start_s:
                phase = "C2_ROUTE_DECISION"
            elif t >= scenario.hazard_time_s:
                phase = "TARGET_RECON"

            progress = t / max(1, scenario.duration_s)
            true_lat = lat0 + 0.012 * progress + rng.gauss(0, 0.000015)
            true_lon = lon0 + 0.010 * progress + rng.gauss(0, 0.000015)
            altitude = 120 + 8 * math.sin(t / 13.0) + rng.gauss(0, 0.8)
            velocity = 11.5 + 0.8 * math.sin(t / 9.0) + rng.gauss(0, 0.15)
            imu_motion = abs(velocity / 38.0 + rng.gauss(0, scenario.imu_noise))

            if t < scenario.hazard_time_s:
                true_risk = max(0.06, rng.gauss(0.18, 0.035))
            else:
                ramp = min(1.0, (t - scenario.hazard_time_s) / 10.0)
                true_risk = min(0.99, 0.22 + ramp * scenario.hazard_severity + rng.gauss(0, 0.025))

            rtt = max(5.0, rng.gauss(scenario.base_rtt_ms, scenario.rtt_jitter_ms))
            heartbeat = max(0.8, rng.gauss(1.0, 0.08))
            packet_loss = min(0.18, max(0.0, rng.gauss(scenario.baseline_packet_loss, 0.004)))
            video_lag = max(0.0, rng.gauss(0.7, 0.18))
            log_lag = max(0.02, rng.gauss(0.35, 0.10))
            c2_lag = max(0.02, rng.gauss(0.45, 0.12))

            records.append(
                MissionRecord(
                    scenario_id=scenario.scenario_id,
                    t=t,
                    true_route=scenario.route_a_name,
                    true_risk_route_a=round(true_risk, 4),
                    true_uav_lat=round(true_lat, 7),
                    true_uav_lon=round(true_lon, 7),
                    true_altitude_m=round(altitude, 2),
                    true_velocity_mps=round(velocity, 2),
                    reported_uav_lat=round(true_lat + rng.gauss(0, 0.00001), 7),
                    reported_uav_lon=round(true_lon + rng.gauss(0, 0.00001), 7),
                    reported_altitude_m=round(altitude + rng.gauss(0, 0.5), 2),
                    reported_velocity_mps=round(velocity + rng.gauss(0, 0.1), 2),
                    imu_motion=round(imu_motion, 4),
                    video_timestamp=round(t - video_lag, 3),
                    video_risk_score=round(true_risk, 4),
                    rtt_ms=round(rtt, 2),
                    heartbeat_interval_s=round(heartbeat, 3),
                    packet_loss=round(packet_loss, 4),
                    gcs_log_timestamp=round(t + log_lag, 3),
                    c2_arrival_timestamp=round(t + c2_lag, 3),
                    phase=phase,
                    is_attacked=False,
                )
            )
        return records
