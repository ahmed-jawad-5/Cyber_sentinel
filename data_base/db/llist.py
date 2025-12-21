from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Generator, Optional


# -----------------------------
# Row Node
# -----------------------------
@dataclass
class RowNode:
    """A single row in the doubly linked list."""
    rid: int
    row: Dict[str, Any]
    prev: Optional["RowNode"] = None
    next: Optional["RowNode"] = None


# -----------------------------
# Doubly Linked List Structure
# -----------------------------
class LinkedList:
    """A minimal doubly linked list for row storage."""

    def __init__(self) -> None:
        self.head: Optional[RowNode] = None
        self.tail: Optional[RowNode] = None
        self._size: int = 0

    # ----------------------------------------
    # Insert (append to tail)
    # ----------------------------------------
    def append(self, rid: int, row: Dict[str, Any]) -> RowNode:
        """Append a new row to the end of the list and return its node."""
        node = RowNode(rid=rid, row=row)

        if self.tail is None:
            # Empty list
            self.head = self.tail = node
        else:
            # Normal append
            node.prev = self.tail
            self.tail.next = node
            self.tail = node

        self._size += 1
        return node

    # ----------------------------------------
    # Remove
    # ----------------------------------------
    def remove_node(self, node: RowNode) -> None:
        """Remove a given node from the list."""
        if node.prev:
            node.prev.next = node.next
        else:
            # Removing head
            self.head = node.next

        if node.next:
            node.next.prev = node.prev
        else:
            # Removing tail
            self.tail = node.prev

        node.prev = node.next = None
        self._size -= 1

    # ----------------------------------------
    # Size
    # ----------------------------------------
    def __len__(self) -> int:
        return self._size

    # ----------------------------------------
    # Iteration
    # ----------------------------------------
    def iter_nodes(self) -> Generator[RowNode, None, None]:
        """Iterate through nodes."""
        cur = self.head
        while cur is not None:
            yield cur
            cur = cur.next

    def iter_rows(self) -> Generator[Dict[str, Any], None, None]:
        """Iterate through row dictionaries only."""
        for node in self.iter_nodes():
            yield node.row

    def iter_rid_rows(self) -> Generator[tuple[int, Dict[str, Any]], None, None]:
        """Iterate as (rid, row) pairs."""
        cur = self.head
        while cur is not None:
            yield cur.rid, cur.row
            cur = cur.next

    # ----------------------------------------
    # Clear list (optional utility)
    # ----------------------------------------
    def clear(self) -> None:
        """Remove all nodes (used during table load/reset)."""
        cur = self.head
        while cur:
            nxt = cur.next
            cur.prev = cur.next = None
            cur = nxt
        self.head = self.tail = None
        self._size = 0

