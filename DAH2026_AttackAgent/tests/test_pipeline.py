from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from main import run_monte_carlo, run_one_scenario


def test_single_scenario_succeeds_or_produces_decision():
    scenario, baseline, attacked, events, profile, trust_map, result = run_one_scenario(1, 42)
    assert result.baseline_decision.risk_label == "DANGER"
    assert result.attacked_decision.risk_label in {"SAFE", "DANGER"}
    assert result.events_generated == len(events)
    assert "trust_edges" in trust_map


def test_monte_carlo_outputs_are_reasonable(tmp_path):
    report = run_monte_carlo(seed=42, scenarios=4, out_dir=tmp_path)
    assert report.scenario_count == 4
    assert 0 <= report.attack_success_rate <= 100
    assert report.average_stealth_score >= 60
    assert (tmp_path / "monte_carlo_results.csv").exists()
    assert (tmp_path / "demo_result.txt").exists()


def test_plan_can_vary_across_scenarios(tmp_path):
    report = run_monte_carlo(seed=42, scenarios=8, out_dir=tmp_path)
    assert report.plan_diversity >= 2


def test_report_artifacts_include_case_study(tmp_path):
    run_monte_carlo(seed=7, scenarios=3, out_dir=tmp_path)
    assert (tmp_path / "baseline_mission.csv").exists()
    assert (tmp_path / "attacked_mission.csv").exists()
    assert (tmp_path / "selected_attack_plan.json").exists()
    assert (tmp_path / "impact_report.json").exists()
