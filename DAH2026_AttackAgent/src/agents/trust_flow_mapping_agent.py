from __future__ import annotations

from typing import Dict, List

from schemas.mission_schema import MissionScenario


class TrustFlowMappingAgent:
    """Builds an explainable map of which data affects C2 and UGV routing."""

    def map_flow(self, scenario: MissionScenario) -> Dict:
        return {
            "scenario_id": scenario.scenario_id,
            "attack_objective": "Flip C2 perception of Route A from DANGER to SAFE",
            "decision_window": [scenario.decision_start_s, scenario.decision_end_s],
            "trust_edges": [
                {"from": "UAV video frame", "to": "C2 route risk", "weight": 0.40},
                {"from": "UAV GNSS position", "to": "C2 route confirmation", "weight": 0.20},
                {"from": "IMU/altitude consistency", "to": "C2 sensor confidence", "weight": 0.15},
                {"from": "RTT/heartbeat/packet loss", "to": "C2 data freshness", "weight": 0.15},
                {"from": "GCS log timestamp", "to": "C2 timeline trust", "weight": 0.10},
            ],
            "manipulation_points": [
                "video_timestamp", "video_risk_score", "reported_uav_lat", "reported_uav_lon",
                "imu_motion", "rtt_ms", "heartbeat_interval_s", "packet_loss", "gcs_log_timestamp",
            ],
        }
