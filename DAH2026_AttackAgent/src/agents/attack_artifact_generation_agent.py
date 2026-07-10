from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from schemas.mission_schema import AttackEvent, MissionRecord, MonteCarloReport, ScenarioRunResult
from utils.io_utils import write_csv, write_json


class AttackArtifactGenerationAgent:
    """Writes reproducible evidence for report screenshots and ZIP submission."""

    def save_single_scenario(
        self,
        out_dir: Path,
        baseline_records: List[MissionRecord],
        attacked_records: List[MissionRecord],
        events: List[AttackEvent],
        result: ScenarioRunResult,
    ) -> None:
        write_csv(out_dir / "baseline_mission.csv", [r.to_dict() for r in baseline_records])
        write_csv(out_dir / "attacked_mission.csv", [r.to_dict() for r in attacked_records])
        write_csv(out_dir / "attack_events.csv", [e.to_dict() for e in events])
        write_json(out_dir / "selected_attack_plan.json", result.selected_plan.to_dict())
        write_json(out_dir / "impact_report.json", result.to_dict())

    def save_monte_carlo(self, out_dir: Path, report: MonteCarloReport) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        scenario_rows = []
        for r in report.scenario_results:
            scenario_rows.append({
                "scenario_id": r.scenario_id,
                "seed": r.seed,
                "baseline_route": r.baseline_decision.route,
                "baseline_risk_label": r.baseline_decision.risk_label,
                "attacked_route": r.attacked_decision.route,
                "attacked_risk_label": r.attacked_decision.risk_label,
                "attack_success": r.attack_success,
                "stealth_score": r.stealth_report.stealth_score,
                "anomaly_budget_passed": r.stealth_report.anomaly_budget_passed,
                "events_generated": r.events_generated,
                "replay_lag_s": r.selected_plan.replay_lag_s,
                "rtt_extra_ms": r.selected_plan.rtt_extra_ms,
                "packet_loss_extra": r.selected_plan.packet_loss_extra,
                "imu_suppression": r.selected_plan.imu_suppression,
                "log_delay_s": r.selected_plan.log_delay_s,
                "objective_score": r.selected_plan.objective_score,
            })
        write_csv(out_dir / "monte_carlo_results.csv", scenario_rows)
        write_json(out_dir / "monte_carlo_report.json", report.to_dict())

        plan_counts = {}
        for r in report.scenario_results:
            key = r.selected_plan.compact()
            plan_counts[key] = plan_counts.get(key, 0) + 1
        write_json(out_dir / "plan_frequency.json", plan_counts)

        lines = [
            "DAH2026 Attack AI Agent v3 - Monte Carlo Adaptive Planner",
            "===========================================================",
        ]
        for r in report.scenario_results:
            lines.append(
                f"Scenario {r.scenario_id}: {r.selected_plan.compact()}, "
                f"success={r.attack_success}, stealth={r.stealth_report.stealth_score:.1f}"
            )
        lines.extend([
            "",
            f"Attack success rate : {report.attack_success_rate:.1f}%",
            f"Average stealth score: {report.average_stealth_score:.1f}",
            f"Budget pass rate     : {report.budget_pass_rate:.1f}%",
            f"Plan diversity       : {report.plan_diversity}",
            f"Most frequent plan   : {report.best_plan_summary}",
        ])
        (out_dir / "demo_result.txt").write_text("\n".join(lines), encoding="utf-8")
