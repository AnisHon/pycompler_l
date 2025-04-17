from collections.abc import Hashable

StateType = int
SymbolType = str | int

# 空
EPSILON = "@ε"
EMPTY_CHAR = EPSILON

class NodeInfo:
    __slots__ = ("accept", "label", "meta", "priority")
    def __init__(self, accept: bool, label: str = None, meta: Hashable = None, priority: int | None = None):
        self.accept = accept
        self.label: Hashable | None = label
        self.priority: int | None = priority
        self.meta = meta

    def __str__(self) -> str:
        return f"(accept: {self.accept}, label: {self.label}, meta: {self.meta})"

    def __repr__(self) -> str:
        return self.__str__()

NodeInfoMap = dict[StateType, NodeInfo]

# DFA 转移“矩阵”类型
DFAEdgeType = dict[tuple[StateType, SymbolType], StateType]

# NFA 转移“矩阵”类型
NFAEdgeType = dict[tuple[StateType, SymbolType], set[StateType]]
