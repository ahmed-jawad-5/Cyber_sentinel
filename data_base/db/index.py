from __future__ import annotations
from bisect import bisect_left,bisect_right
from typing import Dict,List,Optional,Set,Tuple,Any 


# there are two classes one gives the hash index
# there is another class that gives the sorted index 

class HashIndex:
    def __init__(self):
        self.map:Dict[Any,Set[int]]={}
    def add (self,key,rid):
        self.map.setdefault(key, set()).add(rid)
    def remove(self,key,rid):
        s = self.map.get(key)
        if not s:
            return
        s.discard(rid)
        if not s:
            self.map.pop(key, None)
    def find_eq(self,key):
        return set(self.map.get(key, set()))
    


class SortedIndex:
    def __init__(self):
        self.keys=[]
        self.rids=[]
    # making a porivate function 
    # this just gives back the tuple  of the key and row id 
    def _key_tuple(self,key,rid):
        return (key,rid)
    def _pairs_keys(self) -> List[Tuple[Any, int]]:
        # virtual list for (key, rid) using current arrays
        return list(zip(self.keys, self.rids))
    ## these all are the public functions 
    def add(self,key:Any,rid:int)->None:
        kt= self._key_tuple(key,rid)
        i = bisect_left(self._pairs_keys(),kt)
        self.keys.insert(i, key)
        self.rids.insert(i, rid)
    def remove(self, key: Any, rid: int) -> None:
        # Find the range for this key and remove the exact rid
        left = bisect_left(self.keys, key)
        right = bisect_right(self.keys, key)
        for i in range(left, right):
            if self.rids[i] == rid:
                self.keys.pop(i)
                self.rids.pop(i)
                return

    def _pairs_keys(self) -> List[Tuple[Any, int]]:
        # virtual list for (key, rid) using current arrays
        return list(zip(self.keys, self.rids))

    def find_range(
        self,
        lo_key: Optional[Any],
        hi_key: Optional[Any],
        lo_inclusive: bool = True,
        hi_inclusive: bool = False,
    ) -> List[int]:
        # Determine lower bound
        if lo_key is None:
            li = 0
        else:
            li = bisect_left(self.keys, lo_key) if lo_inclusive else bisect_right(self.keys, lo_key)
        # Determine upper bound
        if hi_key is None:
            ri = len(self.keys)
        else:
            ri = bisect_right(self.keys, hi_key) if hi_inclusive else bisect_left(self.keys, hi_key)
        if li >= ri:
            return []
        return self.rids[li:ri]

