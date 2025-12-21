from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple, Set


@dataclass
class LeafNode:
    keys: List[Any] = field(default_factory=list)
    values: List[Set[int]] = field(default_factory=list)  # sets of rids per key
    next: Optional["LeafNode"] = None

    def insert(self, key: Any, rid: int) -> None:
        i = bisect_left(self.keys, key)
        if i < len(self.keys) and self.keys[i] == key:
            self.values[i].add(rid)
        else:
            self.keys.insert(i, key)
            self.values.insert(i, {rid})

    def remove(self, key: Any, rid: int) -> None:
        i = bisect_left(self.keys, key)
        if i < len(self.keys) and self.keys[i] == key:
            s = self.values[i]
            s.discard(rid)
            if not s:
                # remove the key entirely
                self.keys.pop(i)
                self.values.pop(i)


@dataclass
class InternalNode:
    keys: List[Any] = field(default_factory=list)
    children: List[object] = field(default_factory=list)  # nodes (InternalNode or LeafNode)

    def child_index(self, key: Any) -> int:
        # first child > key goes to index; equal keys descend to right child
        return bisect_right(self.keys, key)


class BPlusTreeIndex:
    """Simple in-memory B+ tree.

    - Order defines the maximum number of children per internal node (fanout).
    - We split nodes when keys exceed (order - 1) for internal, and the same limit for leaves.
    - Deletion only removes entries; no rebalancing/merge for simplicity.
    """

    def __init__(self, order: int = 32) -> None:
        self.order = max(4, order)
        self.max_keys = self.order - 1
        self.root: object = LeafNode()

    # ---------- helpers ----------
    def _find_leaf_with_path(self, key: Any) -> Tuple[LeafNode, List[Tuple[InternalNode, int]]]:
        node = self.root
        path: List[Tuple[InternalNode, int]] = []
        while isinstance(node, InternalNode):
            idx = node.child_index(key)
            path.append((node, idx))
            node = node.children[idx]
        return node, path

    def _split_leaf(self, leaf: LeafNode) -> Tuple[Any, LeafNode]:
        mid = len(leaf.keys) // 2
        new_leaf = LeafNode(
            keys=leaf.keys[mid:],
            values=leaf.values[mid:],
            next=leaf.next,
        )
        split_key = new_leaf.keys[0]
        leaf.keys = leaf.keys[:mid]
        leaf.values = leaf.values[:mid]
        leaf.next = new_leaf
        return split_key, new_leaf

    def _split_internal(self, node: InternalNode) -> Tuple[Any, InternalNode]:
        mid = len(node.keys) // 2
        promote_key = node.keys[mid]
        new_node = InternalNode(
            keys=node.keys[mid + 1 :],
            children=node.children[mid + 1 :],
        )
        node.keys = node.keys[:mid]
        node.children = node.children[: mid + 1]
        return promote_key, new_node

    def _insert_into_parent(
        self,
        left: object,
        key: Any,
        right: object,
        path: List[Tuple[InternalNode, int]],
    ) -> None:
        if not path:
            # create new root
            self.root = InternalNode(keys=[key], children=[left, right])
            return
        parent, idx = path.pop()
        parent.keys.insert(idx, key)
        parent.children.insert(idx + 1, right)
        if len(parent.keys) > self.max_keys:
            pk, new_right = self._split_internal(parent)
            self._insert_into_parent(parent, pk, new_right, path)

    # ---------- public API ----------
    def add(self, key: Any, rid: int) -> None:
        leaf, path = self._find_leaf_with_path(key)
        leaf.insert(key, rid)
        if len(leaf.keys) > self.max_keys:
            split_key, new_leaf = self._split_leaf(leaf)
            self._insert_into_parent(leaf, split_key, new_leaf, path)

    def remove(self, key: Any, rid: int) -> None:
        leaf, _ = self._find_leaf_with_path(key)
        leaf.remove(key, rid)
        # no rebalancing; optional future improvement

    def find_range(
        self,
        lo_key: Optional[Any],
        hi_key: Optional[Any],
        lo_inclusive: bool = True,
        hi_inclusive: bool = False,
    ) -> List[int]:
        # find starting leaf
        start_key = lo_key if lo_key is not None else (hi_key if hi_key is not None else None)
        if isinstance(self.root, LeafNode):
            leaf = self.root
            # fast path for single-leaf root
        else:
            if start_key is None:
                # descend to leftmost leaf
                node = self.root
                while isinstance(node, InternalNode):
                    node = node.children[0]
                leaf = node  # type: ignore[assignment]
            else:
                leaf, _ = self._find_leaf_with_path(start_key)

        # position within leaf
        if lo_key is None:
            i = 0
        else:
            i = bisect_left(leaf.keys, lo_key)
            if not lo_inclusive and i < len(leaf.keys) and i < len(leaf.keys) and i >= 0:
                # if equal and exclusive, step to next strictly greater
                if i < len(leaf.keys) and leaf.keys[i] == lo_key:
                    i += 1

        result: List[int] = []
        cur = leaf
        j = i
        while cur is not None:
            while j < len(cur.keys):
                k = cur.keys[j]
                # check upper bound
                if hi_key is not None:
                    if k > hi_key or (k == hi_key and not hi_inclusive):
                        return result
                # within range
                result.extend(cur.values[j])
                j += 1
            cur = cur.next
            j = 0
        return result
