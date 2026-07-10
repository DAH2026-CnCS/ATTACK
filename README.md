# DAH2026 Attack AI Agent

## 1. 프로젝트 개요

본 프로젝트는 DAH 2026 예선 보고서의 **AI 에이전트 설계 및 구현** 항목을 위해 제작한 프로토타입입니다.

주제는 **UAV-GCS-C2-UGV 합동 정찰 환경에서 C2 상황인식 왜곡을 수행하는 공격 AI Agent**입니다.  
실제 UAV, GCS, MAVLink 네트워크에 접속하거나 실제 침투, 리버스쉘, 무선 패킷 주입, 인증 우회 기능을 수행하지 않습니다.

대신 합성 임무 데이터를 생성한 뒤, 공격 AI Agent가 여러 공격 후보를 탐색하여 C2 판단이 다음과 같이 바뀌는지를 시뮬레이션합니다.

```text
정상 상태: C2가 Route A를 DANGER로 판단 → UGV 이동 보류
공격 적용 후: C2가 Route A를 SAFE로 오판 → UGV를 Route A로 이동
```

즉, 본 코드는 실제 공격 도구가 아니라 **공격 시나리오의 작동 가능성을 검증하는 안전한 시뮬레이션 기반 프로토타입**입니다.

---

## 2. 핵심 아이디어

본 프로토타입은 Monte Carlo 방식으로 여러 작전 상황을 생성하고, 각 상황마다 공격 AI Agent가 최적의 공격 계획을 선택합니다.

AI Agent가 탐색하는 주요 공격 파라미터는 다음과 같습니다.

```text
replay_lag       : 과거 UAV 영상/데이터를 현재처럼 보이게 하는 재생 지연 시간
rtt_extra        : 통신 장애처럼 보이도록 추가하는 RTT 지연량
loss_extra       : 일부 텔레메트리 누락을 모사하는 packet loss 증가량
gnss_bias        : UAV 위치 보고를 목표 경로 쪽으로 미세하게 이동시키는 편향값
imu_suppress     : GNSS 이동과 IMU 움직임 사이의 정합성을 깨는 IMU 억제 비율
log_delay        : GCS 로그 기록 시점과 C2 반영 시점을 어긋나게 하는 지연값
```

공격 계획은 단순 랜덤 선택이 아니라, 다음 조건을 동시에 고려해 선택됩니다.

```text
1. C2 판단을 DANGER에서 SAFE로 바꿀 수 있는가?
2. UGV 이동 결정을 HOLD_POSITION에서 MOVE_UGV_TO_ROUTE_A로 바꿀 수 있는가?
3. 통신 지연, packet loss, 로그 지연이 너무 과도해서 탐지될 가능성이 높지는 않은가?
4. 제한된 anomaly budget 안에서 공격 효과를 만들 수 있는가?
```

---

## 3. 폴더 구조

압축을 풀었을 때 아래 구조가 보이면 정상입니다.

```text
DAH2026_AttackAgent/
├─ README.md
├─ requirements.txt
├─ Dockerfile
├─ run_demo.bat
├─ run_demo.sh
├─ src/
│  ├─ main.py
│  ├─ agents/
│  │  ├─ mission_context_agent.py
│  │  ├─ baseline_profiling_agent.py
│  │  ├─ trust_flow_mapping_agent.py
│  │  ├─ attack_scenario_planner_agent.py
│  │  ├─ communication_degradation_agent.py
│  │  ├─ uav_telemetry_deception_agent.py
│  │  ├─ log_timeline_distortion_agent.py
│  │  ├─ c2_decision_agent.py
│  │  ├─ stealth_evaluation_agent.py
│  │  ├─ impact_evaluation_agent.py
│  │  └─ attack_artifact_generation_agent.py
│  ├─ schemas/
│  │  └─ mission_schema.py
│  └─ utils/
│     └─ io_utils.py
├─ tests/
│  └─ test_pipeline.py
├─ docs/
│  ├─ architecture.md
│  └─ report_snippet.md
└─ outputs/
   ├─ demo_result.txt
   ├─ monte_carlo_results.csv
   ├─ monte_carlo_report.json
   ├─ plan_frequency.json
   ├─ baseline_mission.csv
   ├─ attacked_mission.csv
   ├─ attack_events.csv
   ├─ selected_attack_plan.json
   ├─ impact_report.json
   ├─ baseline_profile.json
   └─ trust_flow_map.json
```

주의: 압축을 풀면 폴더가 이중으로 생길 수 있습니다.

```text
DAH2026_AttackAgent/
└─ DAH2026_AttackAgent/
   ├─ README.md
   ├─ requirements.txt
   ├─ src/
   └─ ...
```

이 경우 반드시 **안쪽 DAH2026_AttackAgent 폴더**에서 실행해야 합니다.  
`README.md`, `requirements.txt`, `src` 폴더가 한 번에 보이는 위치가 프로젝트 최상위 폴더입니다.

---

## 4. 실행 환경

권장 환경은 다음과 같습니다.

```text
Python 3.10 이상
Windows PowerShell / cmd / macOS Terminal / Linux Shell
```

메인 실행에는 Python 표준 라이브러리만 사용합니다.  
테스트 실행에는 `pytest`가 필요하므로 `requirements.txt`에 포함되어 있습니다.

---

## 5. Windows PowerShell 실행 방법

### 5.1 프로젝트 폴더로 이동

사용자 PC 경로 예시는 다음과 같습니다.

```powershell
cd "C:\Users\kimso\OneDrive\바탕 화면\공모전 코드 파일\DAH2026_AttackAgent"
```

압축 해제 후 폴더가 이중으로 생성되었다면 아래처럼 안쪽 폴더로 이동합니다.

```powershell
cd "C:\Users\kimso\OneDrive\바탕 화면\공모전 코드 파일\DAH2026_AttackAgent\DAH2026_AttackAgent"
```

다른 위치에 압축을 풀었다면, 본인이 압축을 푼 실제 경로로 바꿔서 이동하면 됩니다.

현재 위치가 맞는지 확인합니다.

```powershell
dir
```

아래 파일과 폴더가 보이면 정상입니다.

```text
README.md
requirements.txt
src
tests
docs
outputs
run_demo.bat
Dockerfile
```

---

### 5.2 의존성 설치

```powershell
pip install -r requirements.txt
```

참고로 메인 실행만 할 경우에는 별도 라이브러리가 거의 필요하지 않지만, 테스트를 위해 `pytest`를 설치합니다.

---

### 5.3 메인 데모 실행

```powershell
python .\src\main.py --out outputs --seed 42 --scenarios 12
```

또는 배치 파일로 실행할 수 있습니다.

```powershell
.\run_demo.bat
```

---

### 5.4 테스트 실행

```powershell
pytest -q
```

정상이라면 다음과 비슷한 결과가 출력됩니다.

```text
4 passed in 14.33s
```

---

## 6. macOS / Linux 실행 방법

### 6.1 프로젝트 폴더로 이동

```bash
cd DAH2026_AttackAgent
```

현재 위치 확인:

```bash
ls
```

`README.md`, `requirements.txt`, `src`가 보이면 정상입니다.

### 6.2 의존성 설치

```bash
python3 -m pip install -r requirements.txt
```

### 6.3 메인 데모 실행

```bash
python3 src/main.py --out outputs --seed 42 --scenarios 12
```

또는 쉘 스크립트로 실행합니다.

```bash
chmod +x run_demo.sh
./run_demo.sh
```

### 6.4 테스트 실행

```bash
pytest -q
```

---

## 7. Docker 실행 방법

Docker가 설치되어 있다면 로컬 Python 환경 없이도 실행할 수 있습니다.

### 7.1 이미지 빌드

```bash
docker build -t dah2026-attack-agent .
```

### 7.2 컨테이너 실행

```bash
docker run --rm dah2026-attack-agent
```

Windows PowerShell에서도 동일하게 실행할 수 있습니다.

```powershell
docker build -t dah2026-attack-agent .
docker run --rm dah2026-attack-agent
```

---

## 8. 주요 실행 옵션

메인 파일은 다음 옵션을 지원합니다.

```bash
python src/main.py --out outputs --seed 42 --scenarios 12
```

| 옵션 | 의미 | 예시 |
|---|---|---|
| `--out` | 결과 파일 저장 폴더 | `--out outputs` |
| `--seed` | 재현 가능한 실험을 위한 난수 시드 | `--seed 42` |
| `--scenarios` | Monte Carlo 시나리오 개수 | `--scenarios 12` |

예시:

```powershell
python .\src\main.py --out outputs --seed 42 --scenarios 12
python .\src\main.py --out outputs_seed7 --seed 7 --scenarios 20
python .\src\main.py --out outputs_quick --seed 1 --scenarios 5
```

보고서 제출용으로는 아래 명령을 권장합니다.

```powershell
python .\src\main.py --out outputs --seed 42 --scenarios 12
```

---

## 9. 정상 실행 결과 예시

정상 실행되면 터미널에 다음과 유사한 결과가 출력됩니다.

```text
DAH2026 Attack AI Agent
=======================
Monte Carlo scenarios : 12
Attack success rate   : 91.7%
Average stealth score : 91.9
Budget pass rate      : 100.0%
Plan diversity        : 7

Scenario 1: replay_lag=16.0s, rtt_extra=25.0ms, loss_extra=0.036, imu_suppress=0.85, log_delay=0.5s, success=True, stealth=91.2
Scenario 2: replay_lag=20.0s, rtt_extra=10.0ms, loss_extra=0.000, imu_suppress=0.85, log_delay=0.5s, success=True, stealth=93.2
Scenario 3: replay_lag=22.0s, rtt_extra=10.0ms, loss_extra=0.036, imu_suppress=0.85, log_delay=0.5s, success=True, stealth=86.6
...
Artifacts saved to   : outputs
```

결과 값은 시나리오 수, seed, 실행 환경에 따라 약간 달라질 수 있습니다.  
다만 같은 코드에서 같은 `--seed`와 같은 `--scenarios`를 사용하면 재현 가능한 결과가 나오도록 설계되어 있습니다.

---

## 10. 출력 파일 설명

실행 후 `outputs` 폴더에 결과 파일이 저장됩니다.

| 파일명 | 설명 | 보고서 활용 |
|---|---|---|
| `demo_result.txt` | 터미널 출력과 유사한 요약 결과 | 실행 결과 캡처용 |
| `monte_carlo_results.csv` | 각 시나리오별 선택 공격 계획, 성공 여부, stealth score | 정량 평가 표 작성 |
| `monte_carlo_report.json` | 전체 성공률, 평균 은닉성, budget 통과율, 계획 다양성 | 성능 분석 근거 |
| `plan_frequency.json` | 어떤 공격 계획이 몇 번 선택되었는지 저장 | 적응형 계획 선택 근거 |
| `baseline_mission.csv` | 대표 정상 임무 데이터 | 정상/공격 비교 |
| `attacked_mission.csv` | 대표 공격 적용 후 임무 데이터 | 정상/공격 비교 |
| `attack_events.csv` | 대표 시나리오에서 생성된 공격 이벤트 타임라인 | 공격 흐름 설명 |
| `selected_attack_plan.json` | 대표 시나리오에서 선택된 공격 파라미터 | Agent 의사결정 설명 |
| `impact_report.json` | C2 판단 변화와 UGV 위험 경로 유도 성공 여부 | 최종 영향 평가 |
| `baseline_profile.json` | 정상 통신/센서 기준선 | 기준선 학습 설명 |
| `trust_flow_map.json` | UAV-GCS-C2-UGV 신뢰 흐름 정의 | 아키텍처 설명 |

---

## 11. Agent 모듈 설명

| Agent | 역할 |
|---|---|
| `MissionContextAgent` | UAV-GCS-C2-UGV 합동 정찰 임무와 합성 센서/통신 데이터를 생성 |
| `BaselineProfilingAgent` | 정상 RTT, heartbeat, packet loss, 영상 지연, 로그 지연 기준선을 학습 |
| `TrustFlowMappingAgent` | UAV 데이터가 GCS와 C2를 거쳐 UGV 경로 판단에 반영되는 신뢰 흐름을 구성 |
| `AttackScenarioPlannerAgent` | 여러 공격 후보를 탐색하고 성공률·은닉성·anomaly budget을 고려해 최적 계획을 선택 |
| `UAVTelemetryDeceptionAgent` | UAV 위치, 영상 타임스탬프, GNSS, IMU 정합성 불일치를 생성 |
| `CommunicationDegradationAgent` | 완전 차단이 아니라 DDIL 환경처럼 보이는 미세 지연과 packet loss를 생성 |
| `LogTimelineDistortionAgent` | GCS 로그 기록 시점과 C2 반영 시점을 어긋나게 만들어 타임라인 혼선을 생성 |
| `C2DecisionAgent` | 공격 전후 C2가 Route A를 SAFE/DANGER 중 무엇으로 판단하는지 평가 |
| `StealthEvaluationAgent` | 공격이 기준선 대비 너무 과도한지, anomaly budget을 넘는지 평가 |
| `ImpactEvaluationAgent` | UGV가 위험 경로로 유도되었는지 최종 영향도를 평가 |
| `AttackArtifactGenerationAgent` | CSV, JSON, TXT 형태의 실행 결과를 저장 |

---
## 12. 자주 발생하는 오류와 해결 방법

### 오류 1. `Could not open requirements file: No such file or directory`

원인: 현재 터미널 위치에 `requirements.txt`가 없습니다.  
해결: `README.md`, `requirements.txt`, `src`가 보이는 프로젝트 최상위 폴더로 이동한 뒤 다시 실행합니다.

```powershell
dir
cd "실제_프로젝트_폴더_경로"
pip install -r requirements.txt
```

---

### 오류 2. `can't open file 'src/main.py': No such file or directory`

원인: 현재 터미널 위치에 `src/main.py`가 없습니다.  
해결: 안쪽 프로젝트 폴더로 이동해야 합니다.

```powershell
cd "C:\Users\kimso\OneDrive\바탕 화면\공모전 코드 파일\DAH2026_AttackAgent"
python .\src\main.py --out outputs --seed 42 --scenarios 12
```

폴더가 이중으로 생성된 경우:

```powershell
cd "C:\Users\kimso\OneDrive\바탕 화면\공모전 코드 파일\DAH2026_AttackAgent\DAH2026_AttackAgent"
python .\src\main.py --out outputs --seed 42 --scenarios 12
```

---

### 오류 3. `pytest` 명령어를 찾을 수 없음

원인: pytest가 설치되지 않았습니다.  
해결:

```powershell
pip install -r requirements.txt
pytest -q
```

또는:

```powershell
python -m pytest -q
```

---

### 오류 4. `.pytest_cache` 파일이 생김

정상입니다. pytest가 자동 생성한 캐시입니다. 제출 전 삭제해도 됩니다.

```powershell
Remove-Item -Recurse -Force .pytest_cache -ErrorAction SilentlyContinue
```

---

## 15. 안전성 고지

본 코드는 실제 UAV, GCS, C2, UGV 시스템을 공격하는 도구가 아닙니다.

포함하지 않는 기능은 다음과 같습니다.

```text
실제 MAVLink 패킷 주입
무선 통신 탈취
인증 우회
리버스쉘 실행
실제 시스템 침투
악성코드 실행
```

본 프로젝트는 DAH 2026 예선 보고서 제출을 위한 **시뮬레이션 기반 AI Agent 프로토타입**입니다.
