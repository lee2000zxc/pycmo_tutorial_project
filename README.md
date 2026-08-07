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
cd pycmo_tutorial_project
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
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

기본 설정에서는 CMO 상태를 유지한 채 Python 상태만 초기화합니다. `auto_reset.enabled: true`를 사용하면 에피소드 사이에 `File → Load Recent`의 첫 시나리오를 자동으로 다시 불러올 수 있습니다.

## 7. 통신 방식

> `bootstrap.lua`는 학습/에이전트 연결을 시작할 때만 실행합니다. 일반 플레이 중 실행하면 Python이 없어도 CMO의 반복 observation/action 이벤트가 계속 동작해 Pulse Time이 크게 증가할 수 있습니다. 일반 플레이로 돌아갈 때는 `python scripts\shutdown_bridge.py` 또는 `shutdown.lua`를 실행하십시오.

`auto_reset.reload_on_first_reset: true`이면 `train_ppo.py` 시작 시 첫 reset부터 `File → Load Recent`의 첫 저장본을 불러오고, 목표 배속을 설정한 뒤 시뮬레이션을 재생합니다. 일반 플레이 저장본과 별도로 RL 시작용 저장본을 만드십시오. RL 시작용 저장본에는 bootstrap으로 생성된 PyCMO 이벤트가 포함되어 있어야 하며 `File → Load Recent`의 첫 항목이어야 합니다.

시나리오 종료 시 CMO가 `Scenario End` 창을 띄우면 Python이 창을 감지해 Enter로 닫고 episode를 종료한 뒤 자동 reset합니다. 빌드나 언어 설정에 따라 제목이 다르면 `auto_reset.scenario_end_window_title`을 실제 창 제목 일부로 변경하십시오.

1. CMO Lua 이벤트가 일정한 시나리오 시간 간격으로 관측 XML을 `.inst` 파일에 기록합니다.
2. Python은 `.inst` 파일의 XML을 읽고 `Observation` 객체로 변환합니다.
3. Python은 실행할 Lua를 `pycmo_agent_action.lua`에 원자적으로 기록합니다.
4. CMO Lua 이벤트가 action 파일을 주기적으로 실행합니다.
5. action 파일에는 세션별 고유 ID와 증가 sequence가 포함됩니다. CMO Lua 전역 상태가 이미 처리한 ID를 기억하므로 같은 파일을 다시 읽어도 명령은 한 번만 실행됩니다.

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

학습을 `Ctrl+C`로 중단하거나 정상 종료하면 환경의 `close()`가 bridge 종료 action을 보내 반복 observation/action 이벤트를 제거합니다. 강제 종료로 정리가 수행되지 않았으면 CMO Lua Console에서 다음을 실행합니다.

Python에서 종료 action을 보낼 수도 있습니다.

```powershell
python scripts\shutdown_bridge.py
```

```lua
ScenEdit_RunScript('C:/Program Files (x86)/Steam/steamapps/common/Command - Modern Operations/Lua/pycmo_tutorial3/shutdown.lua', true)
```


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

각 episode가 끝나면 reward가 콘솔에 출력되고 `outputs/ppo/episode_rewards.csv`에 누적됩니다.

```text
[Episode] 3 | reward=104.352100 | length=200 | total_timesteps=600
```

PowerShell에서 최근 결과를 확인할 수 있습니다.

```powershell
Import-Csv outputs\ppo\episode_rewards.csv |
    Select-Object -Last 20 |
    Format-Table episode, total_timesteps, reward, length
```

TensorBoard에서는 `episode/reward`, `episode/length`, `rollout/ep_rew_mean`을 확인합니다.

```powershell
tensorboard --logdir outputs\ppo\tensorboard
```

### 보상과 에피소드 초기화

보상은 기본 step penalty에 contact 탐지, 목표와의 거리 변화, CMO 점수 변화, 연료 소모를 반영합니다. `target_success_distance_km`가 0보다 클 때만 목표 거리 접근을 성공으로 사용합니다. 점수 증가만으로는 격추나 episode 성공으로 판정하지 않습니다.

`rl.soft_reset: true`는 Python의 에피소드 step, 이전 목표 거리, 이전 연료량만 초기화합니다. CMO 상태까지 초기화하는 반복 학습에는 Steam UI 기반 자동 로드를 사용할 수 있습니다.

```yaml
auto_reset:
  enabled: true
  reload_on_first_reset: true
  scenario_window_title: 'Flight Tutorial - AAW 1 - Simple Air Intercept'
  restart_timeout_seconds: 60
  menu_delay_seconds: 1
  target_time_compression: 5
```

자동 로드를 사용하기 전에 CMO에서 `bootstrap.lua`를 실행한 상태로 시나리오를 저장하고, 해당 파일이 `File → Load Recent` 목록 맨 위에 있는지 확인해야 합니다. 그래야 다시 불러온 시나리오에도 관측·행동 이벤트가 남아 있습니다. `reload_on_first_reset: true`이므로 `train_ppo.py`가 시작될 때 수행하는 첫 `env.reset()`부터 최근 시나리오를 다시 불러옵니다.

현재 `rl.max_episode_steps: 100`으로 설정되어 있어 정상 진행 중에는 100번째 step에서 에피소드가 잘리고, PPO가 다음 `reset()`을 호출할 때 시나리오를 자동으로 다시 불러옵니다. 시나리오 자체가 종료되거나 성공·실패 terminal 조건이 먼저 발생하면 해당 시점에 조기 reset됩니다.

`Side selection and briefing` 탐색이나 화면 좌표 클릭은 사용하지 않습니다. 최근 시나리오를 직접 불러온 뒤 CMO 창에서 `Enter`로 1배속을 설정하고 Numpad `+` 키를 두 번 보내 5배속으로 변경한 다음 `Space`로 시뮬레이션을 시작합니다. Python 에이전트는 새 observation에서 `scenario.controlled_unit`으로 지정된 항공기를 다시 선택합니다. 이름을 비워 두면 첫 번째 아군 Aircraft를 선택합니다.

학습 전에 자동 로드만 따로 시험할 수 있습니다.

```powershell
python scripts\restart_scenario.py
```

이 기능은 [duyminh1998/pycmo Steam 데모](https://github.com/duyminh1998/pycmo)의 UI 자동화 방식을 참고했습니다.
