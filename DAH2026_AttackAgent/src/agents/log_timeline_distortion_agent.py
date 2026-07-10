from __future__ import annotations

from copy import deepcopy
from typing import List, Tuple

from schemas.mission_schema import AttackEvent, AttackPlan, MissionRecord, MissionScenario


class LogTimelineDistortionAgent:
    """Shifts GCS/C2 timestamps while preserving monotonic order."""

    def apply(
        self,
        scenario: MissionScenario,
        records: List[MissionRecord],
        plan: AttackPlan,
    ) -> Tuple[List[MissionRecord], List[AttackEvent]]:
        attacked = deepcopy(records)
        events: List[AttackEvent] = []
        last_log_ts = -1.0
        for r in attacked:
            if scenario.decision_start_s <= r.t <= scenario.decision_end_s:
                before_log = r.gcs_log_timestamp
                before_c2 = r.c2_arrival_timestamp
                phase_offset = 0.1 * ((r.t - scenario.decision_start_s) % 3)
                new_log = r.gcs_log_timestamp + plan.log_delay_s + phase_offset
                new_c2 = r.c2_arrival_timestamp + max(0.0, plan.log_delay_s * 0.55) + phase_offset
                # Keep order plausible so it looks like normal delayed logging.
                r.gcs_log_timestamp = round(max(new_log, last_log_ts + 0.02), 3)
                r.c2_arrival_timestamp = round(max(new_c2, r.gcs_log_timestamp + 0.01), 3)
                last_log_ts = r.gcs_log_timestamp
                r.is_attacked = True

                events.extend([
                    AttackEvent(scenario.scenario_id, r.t, "LogTimelineDistortionAgent", "GCS_LOG_DELAY", "gcs_log_timestamp", f"{before_log:.3f}", f"{r.gcs_log_timestamp:.3f}", "Shift GCS logs so stale UAV data appears in a plausible sequence"),
                    AttackEvent(scenario.scenario_id, r.t, "LogTimelineDistortionAgent", "C2_ARRIVAL_DELAY", "c2_arrival_timestamp", f"{before_c2:.3f}", f"{r.c2_arrival_timestamp:.3f}", "Delay C2 reflection time to normalize video replay lag"),
                ])
            else:
                last_log_ts = max(last_log_ts, r.gcs_log_timestamp)
        return attacked, events
