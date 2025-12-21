from __future__ import annotations
import csv
import json
import os
from typing import Any, Dict, Iterable, List, Optional
from .table import Table
from .types import infer_type, parse_value, stringify_value
from .query import Condition, Filter

class Database:
    def __init__(self,root :str="dbdata")->None:
        self.root = root
        self.tables :Dict[str,Table]={}
        os.makedirs(self.root, exist_ok=True)
    def metadata_path(self)->str:
        return os.path.join(self.root,"database.json")
    def table_data_path(self, table_name: str) -> str:
        return os.path.join(self.root, f"{table_name}.jsonl")
    def save(self) -> None:
        # Save rows as JSONL and write metadata
        meta = {
            "tables": {},
        }
        for name, table in self.tables.items():
            # write data
            data_path = self.table_data_path(name)
            with open(data_path, "w", encoding="utf-8") as f:
                for row in table.all_rows():
                    # stringify datetime
                    enc = {k: stringify_value(v) for k, v in row.items()}
                    f.write(json.dumps(enc) + "\n")
            meta["tables"][name] = {
                "schema": table.schema,
                "primary_key": table.primary_key,
                "sorted_indexes": table.sorted_indexes,
            }
        with open(self.metadata_path(), "w", encoding="utf-8") as mf:
            json.dump(meta, mf, indent=2)

    def load(self) -> None:
        path = self.metadata_path()
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as mf:
            meta = json.load(mf)
        for name, tmeta in meta.get("tables", {}).items():
            table = Table(
                name=name,
                schema=tmeta["schema"],
                primary_key=tmeta["primary_key"],
                sorted_indexes=tmeta.get("sorted_indexes", []),
            )
            # load rows
            data_path = self.table_data_path(name)
            if os.path.exists(data_path):
                with open(data_path, "r", encoding="utf-8") as f:
                    for line in f:
                        raw = json.loads(line)
                        # parse using schema
                        row = {col: parse_value(table.schema[col], raw.get(col)) for col in table.schema}
                        table.insert(row)
            self.tables[name] = table

    def create_table(self, name: str, schema: Dict[str, str], primary_key: str, sorted_indexes: Optional[List[str]] = None) -> Table:
        if name in self.tables:
            raise ValueError(f"Table {name} already exists")
        # If PK not inside CSV, auto-create it
        if primary_key not in schema:
            print(f"⚠ Primary key '{primary_key}' not found in CSV header — auto-generating it.")
            schema[primary_key] = "int"   # define type

        sorted_indexes = sorted_indexes or []
        table = Table(name=name, schema=schema, primary_key=primary_key, sorted_indexes=sorted_indexes)
        self.tables[name] = table
        return table

    def import_csv(
        self,
        table_name: str,
        csv_path: str,
        primary_key: str,
        sorted_indexes: Optional[List[str]] = None,
        sample_rows_for_inference: int = 200,
    ) -> Table:
        # Read header and sample to infer schema
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            if not header:
                raise ValueError("CSV has no header")
            # sample for inference
            samples: Dict[str, List[str]] = {h: [] for h in header}
            rows_cache: List[Dict[str, str]] = []
            for i, row in enumerate(reader):
                rows_cache.append(row)
                for h in header:
                    samples[h].append(row.get(h, ""))
                if i + 1 >= sample_rows_for_inference:
                    break
        # infer schema
        schema: Dict[str, str] = {}
        for h in header:
            schema[h] = infer_type(samples[h])
        # infer schema
        schema: Dict[str, str] = {}
        for h in header:
            schema[h] = infer_type(samples[h])

        # if PK doesn't exist in CSV, add it
        if primary_key not in schema:
            print(f"Primary key '{primary_key}' not in CSV, adding it automatically.")
            schema[primary_key] = "int"  # or "auto" type

        table = self.create_table(table_name, schema, primary_key, sorted_indexes)
        # re-open to stream insert
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                parsed = {col: parse_value(schema[col], row.get(col)) for col in schema}
                table.insert(parsed)
        return table

    def table(self, name: str) -> Table:
        t = self.tables.get(name)
        if not t:
            raise ValueError(f"Unknown table {name}")
        return t

 