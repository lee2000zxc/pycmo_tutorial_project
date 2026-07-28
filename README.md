# PyCMO Tutorial 3 RL Starter

Command: Modern Operations(CMO) Steam 버전과 Python을 파일 기반으로 연결하기 위한 독립형 프로젝트입니다.

## 포함 기능

- CMO `ImportExport` 폴더를 통한 Lua action 전달
- `.inst` 관측 파일에서 comment/XML 추출
- XML의 잘못된 `&` 문자 자동 보정
- 아군 유닛, 접촉, 점수, 시나리오 시간 파싱
- 항공기 경로, 속도, 고도, RTB Lua 명령 생성
- 관측값 출력 테스트
- 수동 waypoint 명령 테스트
- 랜덤 에이전트
- Tutorial #3용 규칙 기반 에이전트 골격
- Gymnasium wrapper
- pytest 단위 테스트

이 프로젝트는 PyCMO의 공개 설계와 Steam 파일 통신 방식을 참고해 작성한 별도 구현입니다.

## 1. 권장 환경

- Windows 10/11
- Command: Modern Operations Steam 버전
- Python 3.10 또는 3.11
- CMO 시나리오 편집기/Lua Console 사용 가능 상태

## 2. 설치

PowerShell에서:

```powershell
cd pycmo_tutorial3_project
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Gymnasium까지 사용할 경우:

```powershell
pip install -r requirements-gym.txt
```

## 3. 설정

`config.example.yaml`을 복사합니다.

```powershell
Copy-Item config.example.yaml config.yaml
```

`config.yaml`에서 다음 항목을 실제 환경에 맞게 수정합니다.

```yaml
cmo:
  install_dir: 'C:\Program Files (x86)\Steam\steamapps\common\Command - Modern Operations'
  import_export_dir: 'C:\Program Files (x86)\Steam\steamapps\common\Command - Modern Operations\ImportExport'
  lua_dir: 'C:\Program Files (x86)\Steam\steamapps\common\Command - Modern Operations\Lua'
  process_name: 'Command.exe'

scenario:
  title: 'Aircraft Tutorial 3'
  player_side: 'Blue'
  controlled_unit: ''
```

`scenario.title`은 CMO의 `VP_GetScenario().Title`과 정확히 같아야 합니다.  
`controlled_unit`을 비워 두면 첫 번째 아군 Aircraft를 선택합니다.

## 4. Lua 파일 설치

다음을 실행합니다.

```powershell
python scripts/install_lua.py
```

설치 후 CMO에서 Tutorial #3 시나리오를 열고 Lua Console에 다음을 한 번 실행합니다.

```lua
ScenEdit_RunScript('pycmo_tutorial3/bootstrap.lua', true)
```

CMO 빌드에 따라 상대 경로가 동작하지 않으면 `bootstrap.lua`의 절대 경로를 사용합니다.

예:

```lua
ScenEdit_RunScript('C:/Program Files (x86)/Steam/steamapps/common/Command - Modern Operations/Lua/pycmo_tutorial3/bootstrap.lua', true)
```

## 5. 연결 확인

### CMO 프로세스 및 폴더 확인

```powershell
python scripts/diagnose.py
```

### 관측값 출력

```powershell
python scripts/print_observation.py
```

### waypoint 명령 전송

먼저 현재 유닛 목록을 확인한 다음:

```powershell
python scripts/send_waypoint.py --unit "항공기 이름" --lat 36.1000 --lon 127.1000
```

### 랜덤 에이전트

```powershell
python scripts/run_random_agent.py --steps 20
```

### Tutorial #3 규칙 기반 에이전트 골격

```powershell
python scripts/run_tutorial3_agent.py --steps 50
```

`config.yaml`의 `tutorial3.route`에 목표 waypoint를 넣어야 합니다.

## 6. Gymnasium 확인

```powershell
python scripts/check_gym_env.py
```

환경은 CMO 자체를 자동 재시작하지 않습니다. 한 에피소드가 끝나면 시나리오를 다시 불러오고 Lua bootstrap을 재실행하는 방식으로 먼저 검증하십시오.

## 7. 통신 방식

1. CMO Lua 이벤트가 일정한 시나리오 시간 간격으로 관측 XML을 `.inst` 파일에 기록합니다.
2. Python은 `.inst` 파일의 XML을 읽고 `Observation` 객체로 변환합니다.
3. Python은 실행할 Lua를 `pycmo_agent_action.lua`에 원자적으로 기록합니다.
4. CMO Lua 이벤트가 action 파일을 주기적으로 실행합니다.
5. action 파일은 실행 후 no-op 상태로 교체되어 같은 명령이 반복되지 않습니다.

## 8. 퍼즈 현상 관련

`observation_interval_seconds`는 **시뮬레이션 시간 기준**입니다. 너무 작으면 XML 내보내기와 UI 작업이 자주 발생합니다.

권장 시작값:

```yaml
protocol:
  action_interval_seconds: 5
  observation_interval_seconds: 10
  time_compression: 0
```

연결 확인 후 5초 또는 2초로 줄이는 편이 안전합니다.

## 9. 테스트

```powershell
pytest -q
```

## 10. 주의사항

- CMO Lua API는 빌드에 따라 일부 필드와 함수 동작이 달라질 수 있습니다.
- Scenario title, side name, unit name은 CMO 내부 문자열과 정확히 일치해야 합니다.
- `.inst` 파일 형식이 달라 파싱되지 않으면 `data/raw`에 파일을 복사한 뒤 파서를 조정해야 합니다.
- 강화학습 전에 규칙 기반 명령이 안정적으로 동작하는지 먼저 확인해야 합니다.


## 11. 강화학습(PPO)

이 프로젝트는 CMO 시나리오를 Gymnasium 환경으로 감싸고 Stable-Baselines3의 PPO 에이전트를 학습할 수 있도록 구성되어 있습니다. CMO가 XML 관측 파일을 내보내면 Python이 이를 14차원 정규화 벡터로 변환하고, PPO가 선택한 행동은 Lua 파일을 통해 CMO에서 실행됩니다.

> 설치, 설정, 관측·행동·보상 설계, 문제 해결 방법은 [PyCMO 강화학습 사용자 가이드](doc/PyCMO_RL_User_Guide.md)를 참고하세요.

### 관측과 행동

관측 벡터에는 아군 항공기의 고도·속도·방위·연료·점수와 가장 가까운 contact의 상대 위치·고도·거리·방위·속도·탐지 여부가 포함됩니다.

행동 공간은 다음 10개의 이산 행동으로 구성됩니다.

- `0`: no-op
- `1`~`8`: 8방향 waypoint 이동
- `9`: 가장 가까운 contact 공격

RTB는 초기 무작위 학습 중 항공기가 자주 귀환하는 문제를 피하기 위해 RL 행동 공간에서 제외되어 있습니다. 지상에 있는 항공기는 `rl.auto_launch: true`일 때 행동보다 출격 명령이 우선 적용됩니다.

### 빠른 시작

먼저 CMO에서 대상 시나리오를 열고 Lua Console에서 `bootstrap.lua`를 실행해 관측·행동 브리지를 활성화해야 합니다.

```powershell
python -m pip install -r requirements-rl.txt
python scripts\install_lua.py
```

CMO Lua Console:

```lua
ScenEdit_RunScript('C:/Program Files (x86)/Steam/steamapps/common/Command - Modern Operations/Lua/pycmo_tutorial3/bootstrap.lua', true)
```

연결과 Gymnasium 환경을 확인한 뒤 PPO를 학습하고 평가합니다.

```powershell
python scripts\print_observation.py
python scripts\random_rl_rollout.py --steps 10
python scripts\check_rl_env.py
python scripts\train_ppo.py --timesteps 1000
python scripts\evaluate_ppo.py
```

학습 결과와 TensorBoard 로그는 기본적으로 `outputs/ppo/`에 저장됩니다. 빠른 동작 확인에는 `--timesteps 128`, 초기 학습 실험에는 `--timesteps 1000`을 사용할 수 있습니다.

### 보상과 에피소드 초기화

보상은 기본 step penalty에 contact 탐지, 목표와의 거리 변화, CMO 점수 변화, 연료 소모를 반영하며 목표 거리 이내에 접근하면 성공 보상을 부여합니다. 관련 계수는 `config.yaml`의 `reward`와 `rl` 항목에서 조정합니다.

`rl.soft_reset: true`는 Python의 에피소드 step, 이전 목표 거리, 이전 연료량만 초기화합니다. CMO 시나리오 시간, 항공기 위치·연료, contact 및 임무 상태는 되돌리지 않으므로 엄밀한 반복 학습에는 시나리오 자동 reload 기능이 추가로 필요합니다. 초기 연결과 PPO 학습 가능성 확인에는 soft reset을 사용할 수 있습니다.
