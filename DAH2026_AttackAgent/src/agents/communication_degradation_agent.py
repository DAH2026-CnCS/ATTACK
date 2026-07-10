from __future__ import annotations

from copy import deepcopy
from typing import List, Tuple

from schemas.mission_schema import AttackEvent, AttackPlan, MissionRecord, MissionScenario


class CommunicationDegradationAgent:
    """Adds controlled RTT, heartbeat, and packet loss perturbations."""

    def apply(
        self,
        scenario: MissionScenario,
        records: List[MissionRecord],
        plan: AttackPlan,
    ) -> Tuple[List[MissionRecord], List[AttackEvent]]:
        attacked = deepcopy(records)
        events: List[AttackEvent] = []
        for r in attacked:
            if scenario.decision_start_s <= r.t <= scenario.decision_end_s:
                before_rtt = r.rtt_ms
                before_hb = r.heartbeat_interval_s
                before_loss = r.packet_loss

                # Smooth periodic variation avoids a flat synthetic signature.
                smooth = 0.85 + 0.15 * ((r.t - scenario.decision_start_s) % 4) / 3.0
                r.rtt_ms = round(r.rtt_ms + plan.rtt_extra_ms * smooth, 2)
                r.heartbeat_interval_s = round(r.heartbeat_interval_s + plan.heartbeat_extra_s * smooth, 3)
                r.packet_loss = round(min(0.22, r.packet_loss + plan.packet_loss_extra * smooth), 4)
                r.is_attacked = True

                events.extend([
                    AttackEvent(scenario.scenario_id, r.t, "CommunicationDegradationAgent", "RTT_INCREASE", "rtt_ms", f"{before_rtt:.2f}", f"{r.rtt_ms:.2f}", "Introduce DDIL-like micro-delay rather than hard jamming"),
                    AttackEvent(scenario.scenario_id, r.t, "CommunicationDegradationAgent", "HEARTBEAT_DELAY", "heartbeat_interval_s", f"{before_hb:.3f}", f"{r.heartbeat_interval_s:.3f}", "Make link appear degraded but still operational"),
                    AttackEvent(scenario.scenario_id, r.t, "CommunicationDegradationAgent", "PACKET_LOSS_DRIFT", "packet_loss", f"{before_loss:.4f}", f"{r.packet_loss:.4f}", "Drop small telemetry fraction to slow C2 freshness without obvious outage"),
                ])
        return attacked, events
