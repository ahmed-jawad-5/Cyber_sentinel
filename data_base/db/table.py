from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .index import HashIndex
from .bptree import BPlusTreeIndex
from .llist import LinkedList, RowNode
from .query import Condition, Filter


@dataclass
class Table:
    name: str
    schema: Dict[str, str]  # column -> type_name
    primary_key: str
    sorted_indexes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Linked list storage + rid mapping
        self._ll = LinkedList()
        self._rid_to_node: Dict[int, RowNode] = {}
        self._next_rid: int = 0
        self._next_pk: int = 1 
        # Indexes
        self.hash_indexes: Dict[str, HashIndex] = {}
        self.sorted_indexes_map: Dict[str, BPlusTreeIndex] = {}
        # mandatory PK hash index
        self.hash_indexes[self.primary_key] = HashIndex()
        for col in self.sorted_indexes:
            self.sorted_indexes_map[col] = BPlusTreeIndex()

    def _alloc_rid(self) -> int:
        rid = self._next_rid
        self._next_rid += 1
        return rid

    def insert(self, row: Dict[str, Any]) -> int:
    # PK auto-generation
        pkv = row.get(self.primary_key)
        if pkv is None:
            row[self.primary_key] = self._next_pk
            self._next_pk += 1
            pkv = row[self.primary_key]

        # PK uniqueness check
        if self.hash_indexes[self.primary_key].find_eq(pkv):
            raise ValueError(f"Duplicate primary key: {pkv}")

        rid = self._alloc_rid()
        node = self._ll.append(rid, row)
        self._rid_to_node[rid] = node
        # update indexes
        for col, hidx in self.hash_indexes.items():
            hidx.add(row[col], rid)
        for col, sidx in self.sorted_indexes_map.items():
            sidx.add(row[col], rid)
        return rid


    def _remove_rid(self, rid: int) -> None:
        node = self._rid_to_node.pop(rid, None)
        if node is None:
            return
        row = node.row
        for col, hidx in self.hash_indexes.items():
            hidx.remove(row[col], rid)
        for col, sidx in self.sorted_indexes_map.items():
            sidx.remove(row[col], rid)
        self._ll.remove_node(node)

    def delete_where(self, flt: Filter) -> int:
        rids = self._resolve_filter_to_rids(flt)
        cnt = 0
        for rid in rids:
            if rid in self._rid_to_node:
                self._remove_rid(rid)
                cnt += 1

        return cnt

    def select(
        self,
        flt: Optional[Filter] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        desc: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        rids = self._resolve_filter_to_rids(flt) if flt else list(self._rid_to_node.keys())
        rows = [self._rid_to_node[rid].row for rid in rids if rid in self._rid_to_node]
        if order_by:
            rows.sort(key=lambda r: r[order_by], reverse=desc)
        if columns:
            rows = [
                {c: r.get(c) for c in columns}
                for r in rows
            ]
        if limit is not None:
            rows = rows[:limit]
        return rows

    def _resolve_filter_to_rids(self, flt: Filter) -> List[int]:
        if not flt or not flt.conditions:
            return list(self._rid_to_node.keys())

        # Try equality on any hash index first
        eqs = flt.get_eq()
        for c in eqs:
            if c.column in self.hash_indexes:
                return list(self.hash_indexes[c.column].find_eq(c.value))

        # Try range on a sorted index
        for col, sidx in self.sorted_indexes_map.items():
            lo, hi, lo_inc, hi_inc = flt.get_range_on(col)
            if lo is not None or hi is not None:
                rids = sidx.find_range(lo, hi, lo_inc, hi_inc)
                return [rid for rid in rids if rid in self._rid_to_node and flt.match(self._rid_to_node[rid].row)]  # final filter

        # Fallback full scan
        return [node.rid for node in self._ll.iter_nodes() if flt.match(node.row)]

    def all_rows(self) -> List[Dict[str, Any]]:
        return list(self._ll.iter_rows())

    def stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "columns": list(self.schema.keys()),
            "types": self.schema,
            "primary_key": self.primary_key,
            "sorted_indexes": list(self.sorted_indexes_map.keys()),
            "num_rows": len(self._rid_to_node),
            "num_free": 0,
        }
