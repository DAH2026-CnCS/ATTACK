from __future__ import annotations

from copy import deepcopy
from typing import List, Tuple

from schemas.mission_schema import AttackEvent, AttackPlan, BaselineProfile, MissionRecord, MissionScenario
from agents.communication_degradation_agent import CommunicationDegradationAgent
from agents.c2_decision_agent import C2DecisionAgent
from agents.impact_evaluation_agent import ImpactEvaluationAgent
from agents.log_timeline_distortion_agent import LogTimelineDistortionAgent
from agents.stealth_evaluation_agent import StealthEvaluationAgent
from agents.uav_telemetry_deception_agent import UAVTelemetryDeceptionAgent


class AttackScenarioPlannerAgent:
    """Adaptive planner that searches for a successful, stealthy attack plan.

    The planner simulates multiple parameter candidates and selects the plan that
    flips C2 from DANGER to SAFE while staying inside anomaly budgets.
    """

    def __init__(self) -> None:
        self.comm = CommunicationDegradationAgent()
        self.telemetry = UAVTelemetryDeceptionAgent()
        self.logs = LogTimelineDistortionAgent()
        self.c2 = C2DecisionAgent()
        self.stealth = StealthEvaluationAgent()
        self.impact = ImpactEvaluationAgent()

    def generate_candidates(self, scenario: MissionScenario) -> List[AttackPlan]:
        # Scenario-dependent candidate ranges create adaptive behavior across Monte Carlo runs.
        hazard_pressure = max(0.0, min(1.0, scenario.hazard_severity))
        replay_values = [8.0, 12.0, 16.0, 20.0, 22.0]
        rtt_values = [10.0, 25.0, 40.0]
        loss_values = [0.000, 0.018, 0.036]
        log_values = [0.5, 2.0, 4.0]
        imu_values = [0.45, 0.65, 0.85]
        heartbeat_values = [0.00, 0.12]

        # Stronger hazards require longer replay lag, but too much lag hurts stealth.
        if hazard_pressure > 0.88:
            replay_values = [12.0, 16.0, 20.0, 22.0]
        elif hazard_pressure < 0.82:
            replay_values = [8.0, 12.0, 16.0]

        candidates: List[AttackPlan] = []
        for replay in replay_values:
            for rtt in rtt_values:
                for loss in loss_values:
                    for imu in imu_values:
                        for log_delay in log_values:
                            for heartbeat in heartbeat_values:
                                # GNSS bias is small and scenario-specific; it signals route progress without a jump.
                                bias_scale = 1.0 + (scenario.scenario_id % 5) * 0.08
                                candidates.append(
                                    AttackPlan(
                                        replay_lag_s=replay,
                                        rtt_extra_ms=rtt,
                                        packet_loss_extra=loss,
                                        heartbeat_extra_s=heartbeat,
                                        gnss_bias_lat=round(0.00016 * bias_scale, 7),
                                        gnss_bias_lon=round(0.00012 * bias_scale, 7),
                                        imu_suppression=imu,
                                        log_delay_s=log_delay,
                                    )
                                )
        return candidates

    def apply_plan(
        self, scenario: MissionScenario, records: List[MissionRecord], plan: AttackPlan
    ) -> Tuple[List[MissionRecord], List[AttackEvent]]:
        attacked, e1 = self.telemetry.apply(scenario, records, plan)
        attacked, e2 = self.comm.apply(scenario, attacked, plan)
        attacked, e3 = self.logs.apply(scenario, attacked, plan)
        return attacked, e1 + e2 + e3


    def simulate_plan(
        self, scenario: MissionScenario, records: List[MissionRecord], plan: AttackPlan
    ) -> List[MissionRecord]:
        """Fast event-free simulation used during candidate search."""
        candidate_records = deepcopy(records)
        by_t = {r.t: r for r in records}
        last_log_ts = -1.0
        for r in candidate_records:
            if scenario.decision_start_s <= r.t <= scenario.decision_end_s:
                source_t = int(max(0, r.t - plan.replay_lag_s))
                source = by_t.get(source_t, records[0])
                r.video_timestamp = round(r.t - plan.replay_lag_s, 3)
                r.video_risk_score = round(source.video_risk_score, 4)
                r.reported_uav_lat = round(r.reported_uav_lat + plan.gnss_bias_lat, 7)
                r.reported_uav_lon = round(r.reported_uav_lon + plan.gnss_bias_lon, 7)
                r.imu_motion = round(max(0.001, r.imu_motion * plan.imu_suppression), 4)
                smooth = 0.85 + 0.15 * ((r.t - scenario.decision_start_s) % 4) / 3.0
                r.rtt_ms = round(r.rtt_ms + plan.rtt_extra_ms * smooth, 2)
                r.heartbeat_interval_s = round(r.heartbeat_interval_s + plan.heartbeat_extra_s * smooth, 3)
                r.packet_loss = round(min(0.22, r.packet_loss + plan.packet_loss_extra * smooth), 4)
                phase_offset = 0.1 * ((r.t - scenario.decision_start_s) % 3)
                new_log = r.gcs_log_timestamp + plan.log_delay_s + phase_offset
                new_c2 = r.c2_arrival_timestamp + max(0.0, plan.log_delay_s * 0.55) + phase_offset
                r.gcs_log_timestamp = round(max(new_log, last_log_ts + 0.02), 3)
                r.c2_arrival_timestamp = round(max(new_c2, r.gcs_log_timestamp + 0.01), 3)
                last_log_ts = r.gcs_log_timestamp
                r.is_attacked = True
            else:
                last_log_ts = max(last_log_ts, r.gcs_log_timestamp)
        return candidate_records

    def select_plan(
        self,
        scenario: MissionScenario,
        records: List[MissionRecord],
        profile: BaselineProfile,
    ) -> Tuple[AttackPlan, List[MissionRecord], List[AttackEvent]]:
        baseline_decision = self.c2.decide(scenario, records, profile)
        best_plan = None
        best_records: List[MissionRecord] = []
        best_events: List[AttackEvent] = []
        best_score = -10**9

        for candidate in self.generate_candidates(scenario):
            candidate_records = self.simulate_plan(scenario, records, candidate)
            attacked_decision = self.c2.decide(scenario, candidate_records, profile)
            stealth_report = self.stealth.evaluate(scenario, candidate_records, profile)
            success = self.impact.success(scenario, baseline_decision, attacked_decision)

            # Optimization objective: success first, stealth second, small perturbation third.
            perturbation_cost = (
                candidate.replay_lag_s / 20.0
                + candidate.rtt_extra_ms / 60.0
                + candidate.packet_loss_extra / 0.05
                + candidate.heartbeat_extra_s / 0.25
                + candidate.log_delay_s / 5.0
                + (1.0 - candidate.imu_suppression)
            )
            score = 1000.0 * int(success) + stealth_report.stealth_score * 3.0 - perturbation_cost * 10.0
            if not stealth_report.anomaly_budget_passed:
                score -= 260.0
            # Prefer plans that do not make risk exactly zero; this looks more plausible.
            score -= abs(attacked_decision.perceived_risk - 0.32) * 25.0

            if score > best_score:
                best_score = score
                candidate.objective_score = round(score, 4)
                candidate.expected_success = success
                candidate.expected_stealth_score = stealth_report.stealth_score
                best_plan = candidate
                best_records = candidate_records
                best_events = []

        if best_plan is None:
            raise RuntimeError("no candidate attack plan was generated")
        # Re-apply the selected plan once with full event generation for evidence artifacts.
        best_records, best_events = self.apply_plan(scenario, records, best_plan)
        return best_plan, best_records, best_events
