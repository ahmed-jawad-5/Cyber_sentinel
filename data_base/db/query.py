from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

@dataclass
class Condition:
    column:str 
    op:str #these are the operations 
    value:any 
    def evl(self,row:Dict[str,Any])->bool:
        rv=row.get(self.column)
        if self.op =="eq":
            return rv == self.value
        if self.op == "lt":
            return rv is not None and rv < self.value
        if self.op == "le":
            return rv is not None and rv <= self.value
        if self.op == "gt":
            return rv is not None and rv > self.value
        if self.op == "ge":
            return rv is not None and rv >= self.value
        raise ValueError(f"Unknown op {self.op}")
@dataclass
class Filter:
    conditions:List[Condition]
    def match(self, row: Dict[str, Any]) -> bool:
        return all(c.evl(row) for c in self.conditions)

    def get_eq(self) -> List[Condition]:
        return [c for c in self.conditions if c.op == "eq"]
    def get_range_on(self,column):
        lo = None
        hi = None
        lo_inc = True
        hi_inc = False
        for c in self.conditions:
            if c.column != column:
                continue
            if c.op == "gt":
                lo = c.value if lo is None or c.value > lo else lo
                lo_inc = False
            elif c.op == "ge":
                lo = c.value if lo is None or c.value > lo else lo
                lo_inc = True
            elif c.op == "lt":
                hi = c.value if hi is None or c.value < hi else hi
                hi_inc = False
            elif c.op == "le":
                hi = c.value if hi is None or c.value < hi else hi
                hi_inc = True
        return lo, hi, lo_inc, hi_inc
    
def parse_kv(s: str) -> Tuple[str, str]:
    if "=" not in s:
        raise ValueError("Expected key=value")
    k, v = s.split("=", 1)
    return k.strip(), v.strip()



"""
    lt -> less the 
    le -> less equal to 
    gt -> grater then 
    ge -> grater then eq to 
    eq -> equal 
    lo_inc -> include lower bond 
    hi_inc -> include higher bond 
    
"""