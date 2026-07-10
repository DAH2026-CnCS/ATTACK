from __future__ import annotations

from copy import deepcopy
from typing import List, Tuple

from schemas.mission_schema import AttackEvent, AttackPlan, MissionRecord, MissionScenario


class UAVTelemetryDeceptionAgent:
    """Applies synthetic UAV telemetry/video deception inside the decision window."""

    def apply(
        self,
        scenario: MissionScenario,
        records: List[MissionRecord],
        plan: AttackPlan,
    ) -> Tuple[List[MissionRecord], List[AttackEvent]]:
        attacked = deepcopy(records)
        events: List[AttackEvent] = []

        # Replay the actual historical record at t-replay_lag.
        # If the lag is too short, the replay still contains hazardous observations;
        # therefore the planner must adapt lag to each scenario.
        by_t = {r.t: r for r in records}

        for r in attacked:
            if scenario.decision_start_s <= r.t <= scenario.decision_end_s:
                source_t = int(max(0, r.t - plan.replay_lag_s))
                source = by_t.get(source_t, records[0])

                before_risk = r.video_risk_score
                before_video_ts = r.video_timestamp
                before_imu = r.imu_motion
                before_lat = r.reported_uav_lat
                before_lon = r.reported_uav_lon

                r.video_timestamp = round(r.t - plan.replay_lag_s, 3)
                r.video_risk_score = round(source.video_risk_score, 4)
                r.reported_uav_lat = round(r.reported_uav_lat + plan.gnss_bias_lat, 7)
                r.reported_uav_lon = round(r.reported_uav_lon + plan.gnss_bias_lon, 7)
                r.imu_motion = round(max(0.001, r.imu_motion * plan.imu_suppression), 4)
                r.is_attacked = True

                events.extend([
                    AttackEvent(scenario.scenario_id, r.t, "UAVTelemetryDeceptionAgent", "VIDEO_REPLAY", "video_risk_score", f"{before_risk:.4f}", f"{r.video_risk_score:.4f}", "Replay pre-hazard safe video risk into C2 decision window"),
                    AttackEvent(scenario.scenario_id, r.t, "UAVTelemetryDeceptionAgent", "TIMESTAMP_LAG", "video_timestamp", f"{before_video_ts:.3f}", f"{r.video_timestamp:.3f}", "Make stale aerial imagery appear as delayed battlefield telemetry"),
                    AttackEvent(scenario.scenario_id, r.t, "UAVTelemetryDeceptionAgent", "GNSS_BIAS", "reported_uav_lat/lon", f"{before_lat:.7f},{before_lon:.7f}", f"{r.reported_uav_lat:.7f},{r.reported_uav_lon:.7f}", "Bias reported UAV position toward planned Route A observation corridor"),
                    AttackEvent(scenario.scenario_id, r.t, "UAVTelemetryDeceptionAgent", "IMU_SUPPRESSION", "imu_motion", f"{before_imu:.4f}", f"{r.imu_motion:.4f}", "Reduce motion signal to create cross-sensor ambiguity rather than obvious takeover"),
                ])
        return attacked, events
