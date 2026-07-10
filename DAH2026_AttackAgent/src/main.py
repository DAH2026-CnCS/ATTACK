from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import List, Tuple

from agents.attack_artifact_generation_agent import AttackArtifactGenerationAgent
from agents.attack_scenario_planner_agent import AttackScenarioPlannerAgent
from agents.baseline_profiling_agent import BaselineProfilingAgent
from agents.c2_decision_agent import C2DecisionAgent
from agents.impact_evaluation_agent import ImpactEvaluationAgent
from agents.mission_context_agent import MissionContextAgent
from agents.stealth_evaluation_agent import StealthEvaluationAgent
from agents.trust_flow_mapping_agent import TrustFlowMappingAgent
from schemas.mission_schema import MonteCarloReport, ScenarioRunResult
from utils.io_utils import write_json


def run_one_scenario(scenario_id: int, seed: int):
    mission_agent = MissionContextAgent()
    profile_agent = BaselineProfilingAgent()
    trust_agent = TrustFlowMappingAgent()
    planner = AttackScenarioPlannerAgent()
    c2 = C2DecisionAgent()
    stealth = StealthEvaluationAgent()
    impact = ImpactEvaluationAgent()

    scenario = mission_agent.generate_scenario(scenario_id=scenario_id, seed=seed)
    baseline_records = mission_agent.generate_records(scenario)
    profile = profile_agent.build_profile(baseline_records, warmup_until_s=scenario.hazard_time_s)
    trust_map = trust_agent.map_flow(scenario)

    baseline_decision = c2.decide(scenario, baseline_records, profile)
    selected_plan, attacked_records, events = planner.select_plan(scenario, baseline_records, profile)
    attacked_decision = c2.decide(scenario, attacked_records, profile)
    stealth_report = stealth.evaluate(scenario, attacked_records, profile)
    attack_success = impact.success(scenario, baseline_decision, attacked_decision)

    result = ScenarioRunResult(
        scenario_id=scenario.scenario_id,
        seed=seed,
        baseline_decision=baseline_decision,
        attacked_decision=attacked_decision,
        selected_plan=selected_plan,
        stealth_report=stealth_report,
        attack_success=attack_success,
        events_generated=len(events),
    )
    return scenario, baseline_records, attacked_records, events, profile, trust_map, result


def run_monte_carlo(seed: int, scenarios: int, out_dir: Path) -> MonteCarloReport:
    artifact = AttackArtifactGenerationAgent()
    results: List[ScenarioRunResult] = []

    # Save scenario 1 full artifacts as a detailed case study.
    first_payload = None
    for scenario_id in range(1, scenarios + 1):
        payload = run_one_scenario(scenario_id=scenario_id, seed=seed)
        scenario, baseline_records, attacked_records, events, profile, trust_map, result = payload
        results.append(result)
        if first_payload is None:
            first_payload = payload

    success_count = sum(1 for r in results if r.attack_success)
    avg_stealth = sum(r.stealth_report.stealth_score for r in results) / len(results)
    budget_pass = sum(1 for r in results if r.stealth_report.anomaly_budget_passed) / len(results) * 100.0
    plan_counter = Counter(r.selected_plan.compact() for r in results)
    most_common_plan = plan_counter.most_common(1)[0][0] if plan_counter else "N/A"

    report = MonteCarloReport(
        seed=seed,
        scenario_count=scenarios,
        success_count=success_count,
        attack_success_rate=round(success_count / len(results) * 100.0, 2),
        average_stealth_score=round(avg_stealth, 2),
        budget_pass_rate=round(budget_pass, 2),
        plan_diversity=len(plan_counter),
        best_plan_summary=most_common_plan,
        scenario_results=results,
    )

    artifact.save_monte_carlo(out_dir, report)
    if first_payload is not None:
        scenario, baseline_records, attacked_records, events, profile, trust_map, result = first_payload
        artifact.save_single_scenario(out_dir, baseline_records, attacked_records, events, result)
        write_json(out_dir / "baseline_profile.json", profile.to_dict())
        write_json(out_dir / "trust_flow_map.json", trust_map)
    return report


def print_report(report: MonteCarloReport, out_dir: Path) -> None:
    print("DAH2026 Attack AI Agent v3")
    print("==========================")
    print(f"Monte Carlo scenarios : {report.scenario_count}")
    print(f"Attack success rate   : {report.attack_success_rate:.1f}%")
    print(f"Average stealth score : {report.average_stealth_score:.1f}")
    print(f"Budget pass rate      : {report.budget_pass_rate:.1f}%")
    print(f"Plan diversity        : {report.plan_diversity}")
    print("")
    for r in report.scenario_results:
        print(
            f"Scenario {r.scenario_id}: {r.selected_plan.compact()}, "
            f"success={r.attack_success}, stealth={r.stealth_report.stealth_score:.1f}"
        )
    print("")
    print(f"Artifacts saved to    : {out_dir.resolve()}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="DAH2026 UAV-GCS-C2-UGV Attack AI Agent v3")
    p.add_argument("--out", default="outputs", help="output directory")
    p.add_argument("--seed", type=int, default=42, help="reproducible seed")
    p.add_argument("--scenarios", type=int, default=12, help="number of Monte Carlo scenarios")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    if args.scenarios < 1:
        raise ValueError("--scenarios must be >= 1")
    report = run_monte_carlo(seed=args.seed, scenarios=args.scenarios, out_dir=out_dir)
    print_report(report, out_dir)


if __name__ == "__main__":
    main()
