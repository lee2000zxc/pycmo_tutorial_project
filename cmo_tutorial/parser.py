from __future__ import annotations

import xml.etree.ElementTree as ET

from .models import (
    ContactState,
    Observation,
    SideState,
    UnitState,
)


def _text(
    node: ET.Element | None,
    tag: str,
    default: str | None = None,
) -> str | None:
    if node is None:
        return default

    child = node.find(tag)

    if child is None or child.text is None:
        return default

    value = child.text.strip()

    if value == "":
        return default

    return value


def _float(
    node: ET.Element | None,
    tag: str,
    default: float | None = None,
) -> float | None:
    value = _text(node, tag)

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(
    node: ET.Element | None,
    tag: str,
    default: int | None = None,
) -> int | None:
    value = _float(node, tag)

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def _bool(
    node: ET.Element | None,
    tag: str,
    default: bool | None = None,
) -> bool | None:
    value = _text(node, tag)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {
        "true",
        "1",
        "yes",
        "y",
        "on",
    }:
        return True

    if normalized in {
        "false",
        "0",
        "no",
        "n",
        "off",
    }:
        return False

    return default


def _parse_contacts(
    side_node: ET.Element,
) -> tuple[ContactState, ...]:
    contacts_node = side_node.find("Contacts")

    if contacts_node is None:
        return ()

    contacts: list[ContactState] = []

    for contact_node in list(contacts_node):
        guid = _text(
            contact_node,
            "ID",
            "",
        ) or ""

        # 공격 행동에는 contact GUID가 필요하다.
        # GUID가 비어 있어도 관측용으로는 보존하지만,
        # gym_env의 공격 대상 필터에서 제외된다.
        contacts.append(
            ContactState(
                guid=guid,
                name=_text(
                    contact_node,
                    "Name",
                ),
                contact_type=_text(
                    contact_node,
                    "Type",
                ),
                latitude=_float(
                    contact_node,
                    "Lat",
                ),
                longitude=_float(
                    contact_node,
                    "Lon",
                ),
                altitude_m=_float(
                    contact_node,
                    "CA",
                ),
                speed_kts=_float(
                    contact_node,
                    "CS",
                ),
            )
        )

    return tuple(contacts)


def _parse_fuel(
    unit_node: ET.Element,
) -> tuple[float | None, float | None]:
    fuel_node = unit_node.find("Fuel")

    if fuel_node is None:
        return None, None

    fuel_records = fuel_node.findall("FuelRec")

    if not fuel_records:
        return None, None

    current_total = 0.0
    maximum_total = 0.0
    current_found = False
    maximum_found = False

    # 여러 연료 탱크가 있을 수 있으므로 전체 합계를 사용한다.
    for record in fuel_records:
        current = _float(
            record,
            "CQ",
        )
        maximum = _float(
            record,
            "MQ",
        )

        if current is not None:
            current_total += current
            current_found = True

        if maximum is not None:
            maximum_total += maximum
            maximum_found = True

    return (
        current_total if current_found else None,
        maximum_total if maximum_found else None,
    )


def _parse_sides(
    root: ET.Element,
) -> tuple[SideState, ...]:
    sides_node = root.find("Sides")

    if sides_node is None:
        return ()

    sides: list[SideState] = []

    for side_node in sides_node.findall("Side"):
        sides.append(
            SideState(
                guid=_text(
                    side_node,
                    "ID",
                    "",
                ) or "",
                name=_text(
                    side_node,
                    "Name",
                    "",
                ) or "",
                total_score=_float(
                    side_node,
                    "TotalScore",
                    0.0,
                ) or 0.0,
                contacts=_parse_contacts(
                    side_node,
                ),
            )
        )

    return tuple(sides)


def _parse_units(
    root: ET.Element,
) -> tuple[UnitState, ...]:
    units_node = root.find("ActiveUnits")

    if units_node is None:
        return ()

    units: list[UnitState] = []

    for unit_node in list(units_node):
        fuel_current, fuel_maximum = _parse_fuel(
            unit_node
        )

        units.append(
            UnitState(
                guid=_text(
                    unit_node,
                    "ID",
                    "",
                ) or "",
                name=_text(
                    unit_node,
                    "Name",
                    "",
                ) or "",
                side=_text(
                    unit_node,
                    "Side",
                    "",
                ) or "",
                unit_type=unit_node.tag,
                dbid=_int(
                    unit_node,
                    "DBID",
                ),
                latitude=_float(
                    unit_node,
                    "Lat",
                ),
                longitude=_float(
                    unit_node,
                    "Lon",
                ),
                altitude_m=_float(
                    unit_node,
                    "CA",
                ),
                heading_deg=_float(
                    unit_node,
                    "CH",
                ),
                speed_kts=_float(
                    unit_node,
                    "CS",
                ),
                throttle=_text(
                    unit_node,
                    "Thr",
                ),
                fuel_current=fuel_current,
                fuel_max=fuel_maximum,
                is_operating=_bool(
                    unit_node,
                    "IsOperating",
                ),
                condition=_text(
                    unit_node,
                    "Condition",
                ),
                host_facility=_text(
                    unit_node,
                    "HostFacility",
                ),
            )
        )

    return tuple(units)


def parse_observation_xml(
    xml: str,
    scenario_ended: bool = False,
) -> Observation:
    if not isinstance(xml, str):
        raise TypeError(
            "xml은 문자열이어야 합니다."
        )

    xml = xml.strip()

    if not xml:
        raise ValueError(
            "빈 XML 문자열입니다."
        )

    # CMO가 파일을 쓰는 도중 읽은 경우를 명확하게 감지한다.
    if "</Scenario>" not in xml:
        raise ET.ParseError(
            "Scenario 종료 태그가 없습니다. "
            "CMO가 observation 파일을 쓰는 중일 수 있습니다."
        )

    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        # protocol.wait_for_new()에서 재시도할 수 있도록
        # ParseError를 그대로 전달한다.
        raise

    if root.tag != "Scenario":
        scenario_node = root.find(".//Scenario")

        if scenario_node is None:
            raise ValueError(
                f"Scenario 루트를 찾지 못했습니다. "
                f"현재 루트 태그: {root.tag}"
            )

        root = scenario_node

    sides = _parse_sides(root)
    units = _parse_units(root)

    return Observation(
        title=_text(
            root,
            "Title",
            "",
        ) or "",
        scenario_time=_int(
            root,
            "Time",
            0,
        ) or 0,
        start_time=_int(
            root,
            "StartTime",
        ),
        duration=_int(
            root,
            "Duration",
        ),
        status=_text(
            root,
            "Status",
        ),
        time_compression=_int(
            root,
            "TimeCompression",
        ),
        sides=sides,
        units=units,
        scenario_ended=bool(
            scenario_ended
        ),
    )