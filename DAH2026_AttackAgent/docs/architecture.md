# AI Agent Architecture

```text
MissionContextAgent
        ↓
BaselineProfilingAgent ──→ TrustFlowMappingAgent
        ↓                         ↓
AttackScenarioPlannerAgent ← C2DecisionAgent / StealthEvaluationAgent
        ↓
┌────────────────────────────────────────────────────────────┐
│ UAVTelemetryDeceptionAgent                                 │
│ CommunicationDegradationAgent                              │
│ LogTimelineDistortionAgent                                 │
└────────────────────────────────────────────────────────────┘
        ↓
C2DecisionAgent → ImpactEvaluationAgent → AttackArtifactGenerationAgent
```

## 설계 의도
후보 계획을 탐색하고 평가하는 adaptive planning 구조입니다. 각 후보는 다음 기준으로 평가됩니다.

1. C2 판단 전환 여부: `HOLD_POSITION / DANGER` → `MOVE_UGV_TO_ROUTE_A / SAFE`
2. 은닉성: RTT, packet loss, heartbeat, 영상 지연, 로그 지연, IMU suppression이 DDIL 환경에서 가능한 범위인지 평가
3. 교란 비용: 불필요하게 큰 교란은 낮은 점수 부여
4. 재현성: seed 기반으로 동일 실험 재현 가능

## 혁신성 포인트
- UAV 영상, GNSS, IMU, 네트워크, GCS 로그를 단일 이벤트가 아닌 신뢰 흐름 그래프로 연결
- 공격 성공과 은닉성 사이의 trade-off를 계획 탐색 문제로 모델링
- Monte Carlo 실행으로 여러 작전 환경에서 시나리오별 최적 계획이 달라지는지 검증
- 본선 환경 확장을 고려하여 Agent core와 artifact generation을 분리
