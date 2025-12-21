#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional

from db.storage import Database
from db.query import Condition, Filter, parse_kv
from db.types import parse_value


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Lightweight CSV-backed DB")
    p.add_argument("--db-path", default="dbdata", help="database root path")
    sub = p.add_subparsers(dest="cmd", required=True)

    pim = sub.add_parser("import", help="import a CSV into a new table")
    pim.add_argument("--csv", required=True, help="path to CSV file")
    pim.add_argument("--table", required=True, help="table name")
    pim.add_argument("--pk", required=True, help="primary key column")
    pim.add_argument("--sorted-indexes", default="", help="comma-separated column names")

    psel = sub.add_parser("select", help="select rows with optional filters")
    psel.add_argument("--table", required=True)
    psel.add_argument("--eq", action="append", default=[], help="col=val (repeatable)")
    psel.add_argument("--lt", action="append", default=[], help="col=val (repeatable)")
    psel.add_argument("--le", action="append", default=[], help="col=val (repeatable)")
    psel.add_argument("--gt", action="append", default=[], help="col=val (repeatable)")
    psel.add_argument("--ge", action="append", default=[], help="col=val (repeatable)")
    psel.add_argument("--columns", default="", help="comma-separated projection columns")
    psel.add_argument("--order-by", default=None)
    psel.add_argument("--desc", action="store_true")
    psel.add_argument("--limit", type=int, default=None)

    pins = sub.add_parser("insert", help="insert a row")
    pins.add_argument("--table", required=True)
    pins.add_argument("--set", action="append", required=True, help="col=val (repeatable)")

    pdel = sub.add_parser("delete", help="delete rows matching filters")
    pdel.add_argument("--table", required=True)
    pdel.add_argument("--eq", action="append", default=[], help="col=val (repeatable)")
    pdel.add_argument("--lt", action="append", default=[], help="col=val (repeatable)")
    pdel.add_argument("--le", action="append", default=[], help="col=val (repeatable)")
    pdel.add_argument("--gt", action="append", default=[], help="col=val (repeatable)")
    pdel.add_argument("--ge", action="append", default=[], help="col=val (repeatable)")

    pinfo = sub.add_parser("info", help="show table schema and index info")
    pinfo.add_argument("--table", required=True)

    psave = sub.add_parser("save", help="persist database to disk")

    pload = sub.add_parser("load", help="load database from disk")

    return p


def make_filter(args, schema: Dict[str, str]):
    conditions: List[Condition] = []
    for op in ("eq", "lt", "le", "gt", "ge"):
        items = getattr(args, op, []) or []
        for s in items:
            col, sval = parse_kv(s)
            if col not in schema:
                raise SystemExit(f"Unknown column: {col}")
            t = schema[col]
            v = parse_value(t, sval)
            conditions.append(Condition(column=col, op=op, value=v))
    return Filter(conditions)


def get_table_or_exit(db: Database, name: str):
    try:
        return db.table(name)
    except ValueError:
        available = sorted(db.tables.keys())
        hint = "; import a CSV first using: import --csv <file> --table <name> --pk <col>"
        if available:
            raise SystemExit(f"Unknown table: {name}. Available tables: {', '.join(available)}{hint}")
        raise SystemExit(f"Unknown table: {name}. No tables exist yet{hint}")


def cmd_import(db: Database, args: argparse.Namespace) -> None:
    sorted_indexes = [c for c in (args.sorted_indexes.split(",") if args.sorted_indexes else []) if c]
    tbl = db.import_csv(args.table, args.csv, args.pk, sorted_indexes)
    db.save()
    print(json.dumps({"ok": True, "table": tbl.stats()}, indent=2, default=str))


def cmd_select(db: Database, args: argparse.Namespace) -> None:
    tbl = get_table_or_exit(db, args.table)
    flt = make_filter(args, tbl.schema)
    cols = [c for c in (args.columns.split(",") if args.columns else []) if c] or None
    rows = tbl.select(
        flt=flt,
        columns=cols,
        order_by=args.order_by,
        desc=args.desc,
        limit=args.limit,
    )
    print(json.dumps(rows, indent=2, default=str))


def cmd_insert(db: Database, args: argparse.Namespace) -> None:
    tbl = get_table_or_exit(db, args.table)
    row: Dict[str, Any] = {}
    for s in args.set:
        col, sval = parse_kv(s)
        if col not in tbl.schema:
            raise SystemExit(f"Unknown column: {col}")
        row[col] = parse_value(tbl.schema[col], sval)
    rid = tbl.insert(row)
    db.save()
    print(json.dumps({"ok": True, "rid": rid}, indent=2))


def cmd_delete(db: Database, args: argparse.Namespace) -> None:
    tbl = get_table_or_exit(db, args.table)
    flt = make_filter(args, tbl.schema)
    cnt = tbl.delete_where(flt)
    db.save()
    print(json.dumps({"ok": True, "deleted": cnt}, indent=2))


def cmd_info(db: Database, args: argparse.Namespace) -> None:
    tbl = get_table_or_exit(db, args.table)
    print(json.dumps(tbl.stats(), indent=2))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    db = Database(root=args.db_path)
    # lazy load for all commands; create folder if missing handled in ctor
    if args.cmd != "import":
        db.load()
    if args.cmd == "import":
        cmd_import(db, args)
    elif args.cmd == "select":
        cmd_select(db, args)
    elif args.cmd == "insert":
        cmd_insert(db, args)
    elif args.cmd == "delete":
        cmd_delete(db, args)
    elif args.cmd == "info":
        cmd_info(db, args)
    elif args.cmd == "save":
        db.save()
        print(json.dumps({"ok": True}))
    elif args.cmd == "load":
        db.load()
        print(json.dumps({"ok": True, "tables": list(db.tables.keys())}))
    else:
        parser.error("unknown command")


if __name__ == "__main__":
    main()
