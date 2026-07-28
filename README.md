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


## 강화학습(PPO) 빠른 시작

```powershell
python -m pip install -r requirements-rl.txt
python scripts\install_lua.py
python scripts\random_rl_rollout.py --steps 10
python scripts\check_rl_env.py
python scripts\train_ppo.py --timesteps 1000
python scripts\evaluate_ppo.py
```

관측은 14차원 정규화 벡터이며, 가장 가까운 contact의 상대 위치·거리·방위·고도·속도를 포함합니다. 행동은 no-op, 8방향 waypoint, RTB의 10개 이산 행동입니다. 지상 항공기는 `rl.auto_launch: true`일 때 자동 출격합니다.

`rl.soft_reset: true`는 Python의 에피소드 통계만 초기화하며 CMO 시나리오 자체는 되돌리지 않습니다. 엄밀한 반복 학습을 위해서는 이후 CMO 시나리오 자동 재시작 브리지를 추가해야 합니다. 초기 연결 및 PPO 학습 가능성 확인에는 soft reset을 사용할 수 있습니다.
