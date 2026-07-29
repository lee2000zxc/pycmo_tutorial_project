# PyCMO 기반 CMO 강화학습 프로젝트 사용 가이드

## 1. 개요

이 프로젝트는 **Command: Modern Operations(CMO) Steam 버전**과 Python을 연결하고, CMO 시나리오를 **Gymnasium 환경**으로 감싼 뒤 **Stable-Baselines3의 PPO 알고리즘**을 적용하기 위한 예제 프로젝트입니다.

전체 구조는 다음과 같습니다.

```text
CMO 시나리오
    ↓
Lua 주기 이벤트
    ↓
관측 XML을 .inst 파일로 내보냄
    ↓
Python이 XML을 파싱
    ↓
Gymnasium observation 생성
    ↓
PPO가 action 선택
    ↓
Python이 Lua action 파일 생성
    ↓
CMO Lua 이벤트가 action 실행
```

현재 구현은 다음 기능을 포함합니다.

- CMO 시나리오 상태를 XML 형태로 내보내기
- 아군 항공기 상태 파싱
- 적 contact 상태 파싱
- 항공기 자동 출격
- 8방향 waypoint 이동
- 가장 가까운 contact 자동 공격
- Gymnasium 환경
- PPO 학습 및 평가
- 거리 기반 reward shaping
- XML 부분 쓰기 오류 재시도
- Windows 파일 잠금 충돌 재시도

---

## 2. 개발 및 실행 환경

권장 환경은 다음과 같습니다.

```text
운영체제: Windows 10 또는 Windows 11
CMO: Command: Modern Operations Steam 버전
Python: 3.10 또는 3.11 권장
Lua: CMO 내장 Lua 5.4
강화학습: Gymnasium + Stable-Baselines3
```

Python 3.12에서도 실행될 수 있지만, 일부 패키지 호환성을 고려하면 Python 3.10 또는 3.11을 권장합니다.

---

## 3. 프로젝트 구조

```text
pycmo_tutorial3_project/
├─ config.yaml
├─ config.example.yaml
├─ requirements.txt
├─ requirements-gym.txt
├─ requirements-rl.txt
├─ README.md
│
├─ cmo_tutorial/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ models.py
│  ├─ inst.py
│  ├─ parser.py
│  ├─ actions.py
│  ├─ protocol.py
│  ├─ environment.py
│  ├─ gym_env.py
│  └─ agents.py
│
├─ lua/
│  ├─ bootstrap.lua
│  ├─ init.lua
│  ├─ pycmo_lib.lua
│  └─ pycmo_agent_action.lua
│
├─ scripts/
│  ├─ install_lua.py
│  ├─ diagnose.py
│  ├─ print_observation.py
│  ├─ random_rl_rollout.py
│  ├─ check_rl_env.py
│  ├─ train_ppo.py
│  └─ evaluate_ppo.py
│
├─ outputs/
│  └─ ppo/
│
└─ tests/
```

---

## 4. Python 환경 설치

### 4.1 가상환경 생성

PowerShell에서 프로젝트 폴더로 이동합니다.

```powershell
cd C:\Users\etri\pycmo_tutorial3_project
```

Python Launcher인 `py`가 설치되어 있지 않다면 다음처럼 `python`을 사용합니다.

```powershell
python -m venv .venv
```

### 4.2 PowerShell 실행 정책 문제

다음과 같은 오류가 발생할 수 있습니다.

```text
이 시스템에서 스크립트를 실행할 수 없으므로 Activate.ps1 파일을 로드할 수 없습니다.
```

현재 PowerShell 창에서만 실행 정책을 완화합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

가상환경을 활성화합니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

정상적으로 활성화되면 다음처럼 표시됩니다.

```text
(.venv) PS C:\Users\etri\pycmo_tutorial3_project>
```

실행 정책을 변경하고 싶지 않다면 가상환경 Python을 직접 사용할 수도 있습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-rl.txt
```

### 4.3 의존성 설치

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-rl.txt
```

`requirements-rl.txt`에는 일반적으로 다음 패키지가 들어갑니다.

```text
-r requirements-gym.txt
stable-baselines3>=2.0
tensorboard
```

---

## 5. config.yaml 설정

프로젝트의 `config.yaml`을 실제 CMO 설치 환경에 맞게 수정합니다.

```yaml
cmo:
  install_dir: 'C:\Program Files (x86)\Steam\steamapps\common\Command - Modern Operations'
  import_export_dir: 'C:\Program Files (x86)\Steam\steamapps\common\Command - Modern Operations\ImportExport'
  lua_dir: 'C:\Program Files (x86)\Steam\steamapps\common\Command - Modern Operations\Lua'
  process_name: 'Command.exe'

scenario:
  title: 'Flight Tutorial - AAW 1 - Simple Air Intercept'
  player_side: 'Blue'
  controlled_unit: ''

auto_reset:
  enabled: false
  reload_on_first_reset: true
  scenario_window_title: 'Flight Tutorial - AAW 1 - Simple Air Intercept'
  restart_timeout_seconds: 60
  menu_delay_seconds: 1
  target_time_compression: 5

protocol:
  action_filename: 'pycmo_agent_action.lua'
  action_interval_seconds: 5
  observation_interval_seconds: 5
  observation_timeout_seconds: 60
  poll_interval_seconds: 0.2
  time_compression: 0

reward:
  score_delta_scale: 1.0
  step_penalty: -0.01
  success_bonus: 100.0
  failure_penalty: -100.0

rl:
  waypoint_step_deg: 0.03
  max_episode_steps: 200
  target_success_distance_km: 20.0
  max_target_distance_km: 300.0
  distance_progress_scale: 0.2
  contact_reward: 0.02
  no_contact_penalty: -0.05
  fuel_penalty_scale: 2.0
  auto_launch: true
  soft_reset: true
```

### 주요 설정 설명

| 설정 | 설명 |
|---|---|
| `scenario.title` | CMO 내부 시나리오 제목과 정확히 일치해야 함 |
| `player_side` | Python이 제어할 Side 이름 |
| `controlled_unit` | 특정 항공기 이름. 빈 값이면 첫 번째 아군 Aircraft 선택 |
| `action_interval_seconds` | CMO가 action Lua 파일을 실행하는 간격 |
| `observation_interval_seconds` | 관측 XML을 내보내는 간격 |
| `time_compression` | CMO 시간 압축 코드 |
| `waypoint_step_deg` | 방향 action 1회당 waypoint 이동량 |
| `max_episode_steps` | 정상 진행 시 자동 로드 전까지 실행할 최대 step 수 |
| `target_success_distance_km` | 표적 접근 성공 거리 |
| `auto_launch` | 지상 항공기를 자동 출격시킬지 여부 |
| `soft_reset` | CMO 시나리오 초기화 없이 Python 내부 episode만 초기화 |
| `auto_reset.enabled` | reset 시 `File → Load Recent`의 첫 시나리오 자동 로드 |
| `reload_on_first_reset` | `train_ppo.py` 시작 시 첫 reset부터 자동 로드할지 여부 |
| `scenario_window_title` | Windows에서 활성화할 CMO 시나리오 창 제목 |
| `target_time_compression` | 로드 후 적용할 배속. 지원 값은 1, 2, 5 |

---

## 6. CMO Lua 파일 설치

Python에서 Lua 파일을 CMO 설치 경로로 복사합니다.

```powershell
python scripts\install_lua.py
```

설치 후 다음 폴더가 생성됩니다.

```text
C:\Program Files (x86)\Steam\steamapps\common\Command - Modern Operations\Lua\pycmo_tutorial3\
```

주요 파일:

```text
bootstrap.lua
init.lua
pycmo_lib.lua
pycmo_agent_action.lua
runtime_config.lua
```

---

## 7. bootstrap.lua 실행

CMO에서 시나리오를 연 뒤 Lua Console을 실행합니다.

```lua
ScenEdit_RunScript(
    'C:/Program Files (x86)/Steam/steamapps/common/Command - Modern Operations/Lua/pycmo_tutorial3/bootstrap.lua',
    true
)
```

한 줄로 실행하는 것이 안전합니다.

```lua
ScenEdit_RunScript('C:/Program Files (x86)/Steam/steamapps/common/Command - Modern Operations/Lua/pycmo_tutorial3/bootstrap.lua', true)
```

정상 출력 예:

```text
PyCMO runtime config loaded.
PyCMO Tutorial 3 bridge installed:
C:/Program Files (x86)/Steam/steamapps/common/Command - Modern Operations/Lua/pycmo_tutorial3/
```

---

## 8. 절대경로 처리

CMO의 `ScenEdit_RunScript()`는 현재 실행 중인 Lua 파일의 위치를 기준으로 상대경로를 처리하지 않을 수 있습니다.

따라서 `bootstrap.lua`는 `_scriptfolder_`를 이용해 현재 스크립트의 절대경로를 구합니다.

```lua
local folder = _scriptfolder_
folder = string.gsub(folder, "\\", "/")

if string.sub(folder, -1) ~= "/" then
    folder = folder .. "/"
end
```

이 경로를 이용해 다른 Lua 파일을 불러옵니다.

```lua
ScenEdit_RunScript(folder .. "runtime_config.lua", true)
ScenEdit_RunScript(folder .. "pycmo_lib.lua", true)
ScenEdit_RunScript(folder .. "init.lua", true)
```

---

## 9. runtime_config.lua 반환값 문제

CMO의 `ScenEdit_RunScript()`는 Lua 파일의 `return` 값을 그대로 전달하지 않고 `true` 또는 `false`를 반환할 수 있습니다.

따라서 다음 방식은 사용하지 않습니다.

```lua
local config = ScenEdit_RunScript(config_path, true)
```

대신 `runtime_config.lua`에서 전역 변수를 만듭니다.

```lua
PYCMO_RUNTIME_CONFIG = {
    action_filename = "pycmo_agent_action.lua",
    action_interval_seconds = 5,
    observation_interval_seconds = 5,
    time_compression = 0
}
```

`bootstrap.lua`에서는 다음처럼 읽습니다.

```lua
ScenEdit_RunScript(config_path, true)
local config = PYCMO_RUNTIME_CONFIG
```

---

## 10. CMO RegularTime interval 코드

CMO의 `RegularTime.Interval`에는 `"5sec"` 같은 문자열을 사용할 수 없습니다.

CMO 내부 interval 코드는 다음과 같습니다.

| 실제 시간 | Interval 코드 |
|---:|---:|
| 1초 | `"0"` |
| 5초 | `"1"` |
| 15초 | `"2"` |
| 30초 | `"3"` |
| 1분 | `"4"` |
| 5분 | `"5"` |
| 15분 | `"6"` |
| 30분 | `"7"` |
| 1시간 | `"8"` |

2초 간격은 지원되지 않으므로 1초 또는 5초를 사용해야 합니다.

---

## 11. CMO와 Python 통신 방식

### 11.1 Observation 통신

CMO Lua 이벤트가 주기적으로 다음 함수를 실행합니다.

```lua
PycmoExportScenarioToXML()
```

이 함수는 시나리오 시간, Side, 점수, unit, contact, 위치, 고도, 속도, 방위각, 연료, 출격 상태 등을 XML로 생성합니다.

XML은 CMO `ImportExport` 폴더의 `.inst` 파일에 저장됩니다.

### 11.2 Action 통신

Python은 다음 파일을 생성하거나 교체합니다.

```text
Lua\pycmo_tutorial3\pycmo_agent_action.lua
```

CMO Lua 이벤트는 이 파일을 주기적으로 실행합니다.

---

## 12. Observation 데이터 모델

### ContactState

```python
@dataclass(frozen=True)
class ContactState:
    guid: str
    name: str | None
    contact_type: str | None
    latitude: float | None
    longitude: float | None
    altitude_m: float | None
    speed_kts: float | None
```

공격 행동을 사용하려면 `guid`가 필요합니다.

### UnitState

```python
@dataclass(frozen=True)
class UnitState:
    guid: str
    name: str
    side: str
    unit_type: str
    dbid: int | None
    latitude: float | None
    longitude: float | None
    altitude_m: float | None
    heading_deg: float | None
    speed_kts: float | None
    throttle: str | None
    fuel_current: float | None
    fuel_max: float | None
    is_operating: bool | None
    condition: str | None
    host_facility: str | None
```

---

## 13. XML parser 핵심 처리

Parser는 다음을 처리해야 합니다.

- 빈 Contacts
- 여러 FuelRec 합산
- contact GUID
- IsOperating
- Condition
- HostFacility
- 파일 쓰기 도중 읽힌 불완전 XML

불완전 XML 확인:

```python
if "</Scenario>" not in xml:
    raise ET.ParseError(
        "Scenario 종료 태그가 없습니다."
    )
```

`protocol.py`는 `ET.ParseError` 발생 시 프로그램을 종료하지 않고 다시 읽어야 합니다.

---

## 14. Windows XML race condition 처리

CMO가 `.inst` 파일을 쓰는 도중 Python이 읽으면 다음 오류가 발생할 수 있습니다.

```text
xml.etree.ElementTree.ParseError: unclosed token
```

해결 방법:

1. 파일 크기와 수정 시간이 잠시 안정될 때까지 기다립니다.
2. `</Scenario>` 존재 여부를 검사합니다.
3. `ET.ParseError` 발생 시 재시도합니다.

```python
except (
    OSError,
    ValueError,
    ET.ParseError,
):
    time.sleep(
        self.config.protocol.poll_interval_seconds
    )
    continue
```

---

## 15. Windows action 파일 잠금 처리

CMO가 `pycmo_agent_action.lua`를 읽는 순간 Python이 파일을 교체하면 다음 오류가 발생할 수 있습니다.

```text
PermissionError: [WinError 5] 액세스가 거부되었습니다.
```

해결:

```python
for attempt in range(1, max_attempts + 1):
    try:
        os.replace(temporary, path)
        return
    except PermissionError:
        time.sleep(0.1)
```

권장 설정:

```yaml
action_interval_seconds: 5
observation_interval_seconds: 5
```

---

## 16. Gymnasium 환경

환경 클래스는 다음 API를 구현합니다.

```python
observation, info = env.reset()

observation, reward, terminated, truncated, info = env.step(action)
```

### Observation space

현재 관측 벡터는 14차원입니다.

```text
0  아군기 고도
1  아군기 속도
2  아군기 heading sin
3  아군기 heading cos
4  연료 비율
5  표적 상대 북쪽 위치
6  표적 상대 동쪽 위치
7  표적 상대 고도
8  표적 거리
9  표적 방위 sin
10 표적 방위 cos
11 표적 속도
12 contact 존재 여부
13 아군 점수
```

```python
self.observation_space = spaces.Box(
    low=-1.0,
    high=1.0,
    shape=(14,),
    dtype=np.float32,
)
```

상대 위치 계산:

```python
north_km = (
    target_latitude - own_latitude
) * 111.0

east_km = (
    target_longitude - own_longitude
) * 111.0 * math.cos(
    math.radians(own_latitude)
)
```

---

## 17. Action space

현재 권장 행동 공간은 10개입니다.

| Action | 의미 |
|---:|---|
| 0 | No-op |
| 1 | 북쪽 waypoint |
| 2 | 북동쪽 waypoint |
| 3 | 동쪽 waypoint |
| 4 | 남동쪽 waypoint |
| 5 | 남쪽 waypoint |
| 6 | 남서쪽 waypoint |
| 7 | 서쪽 waypoint |
| 8 | 북서쪽 waypoint |
| 9 | 가장 가까운 contact 공격 |

```python
self.action_space = spaces.Discrete(10)
```

RTB는 초기 RL action에서 제외하는 것을 권장합니다. 초기 정책은 무작위에 가까우므로 RTB가 포함되면 항공기가 자주 귀환·착륙합니다.

---

## 18. 자동 출격

아군기가 지상에 있으면 RL action보다 출격 명령을 우선합니다.

```python
if (
    self.config.rl.auto_launch
    and unit.is_operating is False
):
    return launch(
        self.config.scenario.player_side,
        unit.name,
    )
```

출격 명령 직후 바로 공중 상태가 되는 것은 아니며 출격 준비와 활주 시간이 필요합니다.

---

## 19. 공격 action

가장 가까운 contact에 대해 다음 Lua 명령을 생성합니다.

```lua
ScenEdit_AttackContact(
    attacker_guid,
    contact_guid,
    {
        mode = 0
    }
)
```

`mode = 0`은 자동 무장 선택 방식입니다.

CMO는 사거리, 식별 상태, WCS/ROE, 보유 무장, 교전 조건을 확인한 뒤 실제 발사를 수행합니다. 공격 action을 선택했다고 해서 항상 즉시 미사일이 발사되는 것은 아닙니다.

---

## 20. Reward 설계

현재 reward 구성:

```text
기본 step penalty
+ contact 탐지 보상
- contact 미탐지 패널티
+ 표적과 가까워진 거리
+ CMO 점수 변화
- 연료 소모
+ 성공 보상
```

```python
reward = step_penalty

if target_distance is None:
    reward += no_contact_penalty
else:
    reward += contact_reward
    progress = previous_distance - current_distance
    reward += distance_progress_scale * progress

reward += score_delta_scale * score_delta
reward -= fuel_penalty_scale * fuel_used
```

초기 성공 조건:

```python
success = (
    distance_km is not None
    and distance_km
    <= target_success_distance_km
)
```

초기 단계에서는 격추보다 표적에 일정 거리 이내 접근하는 것을 성공으로 두는 것이 학습이 쉽습니다.

---

## 21. Episode reset과 자동 로드

`soft_reset: true`는 Python 내부 상태만 초기화합니다.

초기화되는 항목:

```text
episode step
이전 표적 거리
이전 연료량
```

초기화되지 않는 항목:

```text
CMO 시나리오 시간
항공기 위치
연료
contact 상태
적 파괴 여부
미션 상태
```

CMO 상태까지 초기화하려면 `auto_reset.enabled: true`로 설정합니다. `reload_on_first_reset: true`이면 `train_ppo.py` 시작 시 Stable-Baselines3가 호출하는 첫 `reset()`부터 다음 순서로 동작합니다.

`max_episode_steps: 200`이면 200번째 `step()`이 `truncated=True`를 반환합니다. Stable-Baselines3는 이 신호를 받은 뒤 `reset()`을 호출하므로 `File → Load Recent` 자동 로드가 시작됩니다. 시나리오 종료나 성공·실패 terminal 조건이 먼저 발생하면 200 step 이전에도 reset될 수 있습니다.

자동화는 `Side selection and briefing` 창을 탐색하거나 클릭하지 않습니다. 최근 파일을 직접 불러온 뒤 CMO 시나리오 창을 활성화합니다. 이어서 `Enter`로 배속을 1배로 초기화하고 Numpad `+`를 두 번 입력해 5배속으로 변경한 뒤 `Space`로 시뮬레이션을 즉시 시작합니다. 일반 키보드의 `+`가 아니라 Windows `SendKeys`의 `{ADD}` 키 코드를 사용합니다. 최종 로드 성공 여부는 `protocol.observation_timeout_seconds` 동안 새로운 observation 파일이 생성되는지로 판단합니다.

새 observation을 읽으면 에이전트는 `scenario.controlled_unit`과 이름이 일치하는 아군 항공기를 다시 선택합니다. 이 설정이 빈 문자열이면 첫 번째 아군 Aircraft를 선택합니다.

```text
이전 관측·종료 파일 상태 기록
→ CMO File → Load Recent 메뉴 실행
→ 최근 시나리오 목록의 첫 파일 선택
→ Enter 입력으로 1배속 초기화
→ Numpad + 키 2회로 5배속 설정
→ Space 입력으로 시뮬레이션 시작
→ 저장된 PyCMO 이벤트가 새 관측 생성
→ controlled_unit 재선택
→ Python이 새 관측을 확인한 후 다음 episode 시작
```

자동 로드를 사용하기 전에 다음 준비가 필요합니다.

1. CMO에서 학습할 시나리오를 엽니다.
2. `bootstrap.lua`를 실행해 PyCMO 관측·행동 이벤트를 설치합니다.
3. 이벤트가 포함된 상태로 시나리오를 저장합니다.
4. 저장한 파일이 `File → Load Recent` 목록 맨 위에 있는지 확인합니다.
5. `config.yaml`에서 `auto_reset.enabled: true`로 설정합니다.

학습 전에 재시작 동작과 새 관측 생성을 독립적으로 확인합니다.

```powershell
python scripts\restart_scenario.py
```

자동화는 [duyminh1998/pycmo Steam 데모](https://github.com/duyminh1998/pycmo)의 UI 재시작 방식을 참고합니다. CMO 메뉴와 팝업을 Windows 키 입력 및 마우스 클릭으로 조작하므로 다음 조건을 지켜야 합니다.

- 학습 중 CMO 창을 닫지 않습니다.
- `scenario_window_title`이 실제 창 제목과 일치해야 합니다.
- CMO 메뉴 구조가 달라진 빌드에서는 `scripts/restart_cmo_scenario.ps1`의 메뉴 키 순서를 조정해야 할 수 있습니다.

---

## 22. 환경 연결 확인

CMO 프로세스 및 경로 확인:

```powershell
python scripts\diagnose.py
```

Observation 출력:

```powershell
python scripts\print_observation.py
```

Contact GUID 확인 예:

```python
side = obs.side(cfg.scenario.player_side)

for contact in side.contacts:
    print(
        f"GUID={contact.guid}, "
        f"name={contact.name}, "
        f"type={contact.contact_type}, "
        f"lat={contact.latitude}, "
        f"lon={contact.longitude}"
    )
```

---

## 23. Random rollout 테스트

PPO 학습 전에 random action으로 환경을 확인합니다.

```powershell
python scripts\random_rl_rollout.py --steps 10
```

확인 항목:

- observation 파일 갱신
- action 파일 실행
- 자동 출격
- waypoint 변경
- contact 거리 계산
- 공격 action 실행
- XML ParseError 재시도
- WinError 5 재시도

---

## 24. Gymnasium 환경 검사

```powershell
python scripts\check_rl_env.py
```

내부적으로 `check_env()`를 실행합니다.

```python
from stable_baselines3.common.env_checker import check_env

check_env(
    env,
    warn=True,
    skip_render_check=True,
)
```

CMO 시나리오와 bootstrap이 실행 중이어야 합니다.

---

## 25. PPO 학습

짧은 테스트:

```powershell
python scripts\train_ppo.py --timesteps 128
```

조금 더 긴 테스트:

```powershell
python scripts\train_ppo.py --timesteps 1000
```

권장 초기 설정:

```python
model = PPO(
    policy="MlpPolicy",
    env=env,
    learning_rate=3e-4,
    n_steps=32,
    batch_size=32,
    n_epochs=5,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    verbose=1,
    tensorboard_log=str(tensorboard_dir),
    device="auto",
)
```

CMO는 한 step이 느리므로 `n_steps=2048` 같은 일반 기본값은 적합하지 않습니다.

---

## 26. PPO 로그 해석

예:

```text
total_timesteps: 64
entropy_loss: -2.3
approx_kl: 0.0002
explained_variance: -1.14
fps: 0
```

- `entropy_loss ≈ -2.3`: 행동 10개를 거의 균등하게 선택하는 초기 무작위 정책
- `explained_variance < 0`: critic이 아직 reward를 잘 예측하지 못함
- `fps = 0`: 한 step이 수 초 걸려 정수 FPS가 1 미만으로 표시됨

각 episode가 종료되면 `train_ppo.py`가 reward를 콘솔에 출력합니다.

```text
[Episode] 3 | reward=104.352100 | length=200 | total_timesteps=600
```

전체 이력은 `outputs/ppo/episode_rewards.csv`에 누적됩니다.

| 열 | 설명 |
|---|---|
| `episode` | resume 실행을 포함한 누적 episode 번호 |
| `total_timesteps` | episode 종료 시 모델의 누적 timestep |
| `reward` | 해당 episode의 reward 합계 |
| `length` | 해당 episode의 실제 step 수 |
| `elapsed_seconds` | 현재 학습 실행의 경과 시간 |

```powershell
Import-Csv outputs\ppo\episode_rewards.csv |
    Select-Object -Last 20 |
    Format-Table episode, total_timesteps, reward, length
```

TensorBoard에서는 `episode/reward`, `episode/length`, `rollout/ep_rew_mean`을 함께 비교합니다.

---

## 27. 학습 재개

```powershell
python scripts\train_ppo.py `
    --timesteps 1000 `
    --resume outputs\ppo\final_model.zip
```

행동 공간이 바뀌면 기존 모델을 사용할 수 없습니다.

```text
Discrete(9) → Discrete(10)
```

이 경우 새로 학습합니다.

```powershell
Rename-Item outputs\ppo outputs\ppo_old
python scripts\train_ppo.py --timesteps 256
```

---

## 28. 학습 모델 평가

```powershell
python scripts\evaluate_ppo.py
```

특정 모델 지정:

```powershell
python scripts\evaluate_ppo.py `
    --model outputs\ppo\final_model.zip `
    --steps 100
```

---

## 29. TensorBoard

```powershell
tensorboard --logdir outputs\ppo\tensorboard
```

주요 지표:

```text
rollout/ep_rew_mean
rollout/ep_len_mean
train/entropy_loss
train/value_loss
train/policy_gradient_loss
train/approx_kl
train/explained_variance
```

---

## 30. 자주 발생하는 오류

### `py` 명령을 찾을 수 없음

```powershell
python -m venv .venv
```

### Activate.ps1 실행 불가

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### bootstrap 내부 파일 경로 오류

`_scriptfolder_`를 이용한 절대경로를 사용합니다.

### config가 boolean으로 반환됨

`return {}` 대신 `PYCMO_RUNTIME_CONFIG` 전역 변수를 사용합니다.

### Can't parse Interval

`"5sec"`가 아니라 CMO interval 코드 `"1"`을 사용합니다.

### Observation timeout

```powershell
Get-Item "...\ImportExport\시나리오이름.inst" |
    Select-Object LastWriteTime, Length
```

수정 시간이 바뀌지 않으면 CMO observation 이벤트가 실행되지 않는 것입니다.

### PermissionError WinError 5

CMO와 Python의 action 파일 접근 충돌입니다. `os.replace()` 재시도와 5초 action interval을 사용합니다.

### XML unclosed token

CMO가 파일을 쓰는 도중 Python이 읽은 것입니다. 파일 안정화와 `ET.ParseError` 재시도를 적용합니다.

### 항공기가 계속 착륙함

RTB를 RL action에서 제거하고 필요 시 환경 안전 규칙으로 처리합니다.

### action 9에서 KeyError

`Discrete(10)`이면 action 9를 공격 action으로 별도 처리해야 합니다.

### `_nearest_contact()` 중복 정의

동일 메서드를 두 번 정의하면 아래쪽 함수가 위쪽 함수를 덮어씁니다. 반환 타입을 `(contact, distance)`로 통일합니다.

---

## 31. 현재 구현의 한계

1. 자동 reset이 CMO Steam UI와 화면 좌표에 의존
2. 단일 아군기 중심
3. 가장 가까운 contact만 사용
4. 무장 상태 observation 미포함
5. 실제 격추 여부 reward 미반영
6. contact 분류 불확실성 단순 처리
7. 파일 기반 통신으로 느린 step 속도
8. action과 observation 주기 비동기 가능성
9. 시나리오별 Lua 필드 차이 가능성

---

## 32. 향후 개선 방향

### 시나리오 자동 reset 안정화

```text
화면 좌표 기반 클릭 제거
→ Windows UI Automation으로 버튼 탐색
→ CMO 창·팝업 상태 진단 강화
→ 실패한 episode 재시작 복구
```

### 공격 observation 확장

```text
남은 미사일 수
무장 DBID
현재 교전 대상
발사 가능 거리
표적 식별 수준
WCS 상태
기체 damage
적군 생존 여부
```

### Reward 확장

```text
적 격추 +100
아군기 격추 -100
미사일 낭비 -5
유효 사거리 내 발사 +1
교전 후 생존 +20
RTB 성공 +30
```

### Surrogate 환경 사전학습

```text
Python 단순 전투 환경
→ PPO 사전학습
→ 동일 observation/action 유지
→ CMO fine-tuning
```

---

## 33. 권장 개발 순서

1. CMO 시나리오 수동 실행
2. bootstrap 설치 및 실행
3. `.inst` 관측 파일 생성 확인
4. unit/contact 출력 확인
5. waypoint action 확인
6. 자동 출격 확인
7. 공격 action 확인
8. random rollout 10 step
9. `check_env()` 실행
10. PPO 128 step 테스트
11. PPO 1000 step 테스트
12. reward 로그 분석
13. 자동 scenario reset 활성화 및 반복 검증
14. 격추 및 생존 reward 추가
15. 장기 학습 수행

---

## 34. 최소 실행 절차

```powershell
cd C:\Users\etri\pycmo_tutorial3_project
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-rl.txt
python scripts\install_lua.py
```

CMO Lua Console:

```lua
ScenEdit_RunScript('C:/Program Files (x86)/Steam/steamapps/common/Command - Modern Operations/Lua/pycmo_tutorial3/bootstrap.lua', true)
```

PowerShell:

```powershell
python scripts\print_observation.py
python scripts\random_rl_rollout.py --steps 10
python scripts\check_rl_env.py
python scripts\train_ppo.py --timesteps 128
```

---

## 35. 마무리

이 프로젝트는 CMO를 다음 강화학습 인터페이스로 변환합니다.

```text
CMO 상태 → Observation
Python/Lua 명령 → Action
시나리오 결과 → Reward
목표 달성/종료 → Episode termination
```

현재 구현 범위:

```text
CMO 파일 통신
+ XML 관측 파싱
+ 아군기 자동 출격
+ 방향 waypoint 행동
+ contact 공격 행동
+ 14차원 observation
+ reward shaping
+ Gymnasium wrapper
+ PPO 학습
+ Steam UI 기반 자동 scenario reset
```

연구 수준의 반복 학습으로 발전시키기 위해서는 **자동 scenario reset 안정화**, **무장 상태 observation**, **격추/생존 reward**, **복수 유닛 확장**이 다음 핵심 과제입니다.
