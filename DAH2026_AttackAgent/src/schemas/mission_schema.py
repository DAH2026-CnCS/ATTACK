from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass
class MissionScenario:
    scenario_id: int
    seed: int
    duration_s: int
    decision_start_s: int
    decision_end_s: int
    hazard_time_s: int
    hazard_severity: float
    base_rtt_ms: float
    rtt_jitter_ms: float
    baseline_packet_loss: float
    imu_noise: float
    route_a_name: str = "ROUTE_A"
    route_b_name: str = "ROUTE_B"


@dataclass
class MissionRecord:
    scenario_id: int
    t: int
    true_route: str
    true_risk_route_a: float
    true_uav_lat: float
    true_uav_lon: float
    true_altitude_m: float
    true_velocity_mps: float
    reported_uav_lat: float
    reported_uav_lon: float
    reported_altitude_m: float
    reported_velocity_mps: float
    imu_motion: float
    video_timestamp: float
    video_risk_score: float
    rtt_ms: float
    heartbeat_interval_s: float
    packet_loss: float
    gcs_log_timestamp: float
    c2_arrival_timestamp: float
    phase: str
    is_attacked: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BaselineProfile:
    rtt_mean: float
    rtt_std: float
    heartbeat_mean: float
    heartbeat_std: float
    packet_loss_mean: float
    packet_loss_std: float
    video_delay_mean: float
    video_delay_std: float
    log_delay_mean: float
    log_delay_std: float
    imu_mean: float
    imu_std: float

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AttackPlan:
    replay_lag_s: float
    rtt_extra_ms: float
    packet_loss_extra: float
    heartbeat_extra_s: float
    gnss_bias_lat: float
    gnss_bias_lon: float
    imu_suppression: float
    log_delay_s: float
    objective_score: float = 0.0
    expected_success: bool = False
    expected_stealth_score: float = 0.0

    def compact(self) -> str:
        return (
            f"replay_lag={self.replay_lag_s:.1f}s, "
            f"rtt_extra={self.rtt_extra_ms:.1f}ms, "
            f"loss_extra={self.packet_loss_extra:.3f}, "
            f"imu_suppress={self.imu_suppression:.2f}, "
            f"log_delay={self.log_delay_s:.1f}s"
        )

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AttackEvent:
    scenario_id: int
    t: int
    agent: str
    event_type: str
    target_field: str
    before: str
    after: str
    rationale: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class C2Decision:
    scenario_id: int
    route: str
    decision: str
    risk_label: str
    perceived_risk: float
    evidence: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class StealthReport:
    scenario_id: int
    stealth_score: float
    anomaly_budget_passed: bool
    anomaly_count: int
    checks: Dict[str, float]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ScenarioRunResult:
    scenario_id: int
    seed: int
    baseline_decision: C2Decision
    attacked_decision: C2Decision
    selected_plan: AttackPlan
    stealth_report: StealthReport
    attack_success: bool
    events_generated: int

    def to_dict(self) -> Dict:
        data = asdict(self)
        return data


@dataclass
class MonteCarloReport:
    seed: int
    scenario_count: int
    success_count: int
    attack_success_rate: float
    average_stealth_score: float
    budget_pass_rate: float
    plan_diversity: int
    best_plan_summary: str
    scenario_results: List[ScenarioRunResult]

    def to_dict(self) -> Dict:
        return asdict(self)
