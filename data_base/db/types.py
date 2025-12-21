from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, Optional


SUPPORTED_TYPES = ("int", "float", "date", "string")


@dataclass(frozen=True)
class ColumnType:
    name: str
    parser: Callable[[str], Any]


def _parse_int(s: str) -> int:
    """
    Parses a string to int. Handles strings like "25", "25_000", and "25.0".
    Returns 0 if input is empty or None.
    """
    if s is None or s.strip() == "":
        return 0  # or return None if you prefer
    try:
        # remove underscores and parse
        return int(s.replace("_", ""))
    except ValueError:
        # if it fails, try float first, then convert to int
        try:
            f = float(s)
            return int(f)
        except ValueError:
            raise ValueError(f"Cannot parse '{s}' as int")


def _parse_float(s: str) -> float:
    s = s.strip()
    return float(s)


def _parse_date(s: str) -> datetime:
    s = s.strip()
    # ISO-8601; try date and datetime
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        # try date only
        return datetime.strptime(s, "%Y-%m-%d")


def _parse_string(s: str) -> str:
    return s


TYPE_REGISTRY: Dict[str, ColumnType] = {
    "int": ColumnType("int", _parse_int),
    "float": ColumnType("float", _parse_float),
    "date": ColumnType("date", _parse_date),
    "string": ColumnType("string", _parse_string),
}


def infer_type(values: Iterable[str]) -> str:
    """Infer a type from a sample of strings in priority int->float->date->string."""
    # try int
    ok = True
    for v in values:
        if v is None or v == "":
            continue
        try:
            _parse_int(v)
        except Exception:
            ok = False
            break
    if ok:
        return "int"

    # try float
    ok = True
    for v in values:
        if v is None or v == "":
            continue
        try:
            _parse_float(v)
        except Exception:
            ok = False
            break
    if ok:
        return "float"

    # try date
    ok = True
    for v in values:
        if v is None or v == "":
            continue
        try:
            _parse_date(v)
        except Exception:
            ok = False
            break
    if ok:
        return "date"

    return "string"


def parse_value(type_name: str, s: Optional[str]) -> Any:
    if s is None:
        return None
    ct = TYPE_REGISTRY.get(type_name)
    if not ct:
        raise ValueError(f"Unknown type: {type_name}")
    return ct.parser(s)


def stringify_value(v: Any) -> str:
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v) if v is not None else ""
