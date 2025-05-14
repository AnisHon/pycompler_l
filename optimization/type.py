from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

class QuadrupleOpType(Enum):
    NON_OPERATION = auto()
    UNARY_OPERATION = auto()
    BINARY_OPERATION = auto()


class QuadrupleOp(Enum):
    # non-operation (op, v1, _, v3)
    ASSIGN = auto()     # v3 = v1

    # unary operation (op, v1, _, v3)
    MINUS = auto()      # v3 = -v1
    B_NOT = auto()      # v3 = ~v1

    # binary operation (op, v1, v2, v3)
    ADD = auto()        # v3 = v1 + v2
    SUB = auto()        # v3 = v1 - v2
    MUL = auto()        # v3 = v1 * v2
    DIV = auto()        # v3 = v1 / v2
    REM = auto()        # v3 = v1 % v2

    B_AND = auto()      # v3 = v1 & v2
    B_OR = auto()       # v3 = v1 | v2
    B_XOR = auto()      # v3 = v1 ^ v2

    SHL = auto()        # v3 = v1 << v2
    SHR = auto()        # v3 = v1 >> v2

class OperandType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    POINTER = auto()
    VARIABLE = auto()

@dataclass
class Operand:
    value: Any
    type: OperandType

    @property
    def is_const(self):
        return self.type != OperandType.VARIABLE

@dataclass
class Quadruple:
    op: QuadrupleOp
    v1: Operand | None
    v2: Operand | None
    v3: Operand

    def get_non_operand(self) -> Operand:
        return self.v1

    def get_unary_operand(self) -> Operand:
        return self.v1

    def get_binary_operand(self) -> tuple[Operand, Operand]:
        return self.v1, self.v2

    def get_lvalue(self):
        return self.v3

quadrupleOpType = {
    QuadrupleOp.ASSIGN: QuadrupleOpType.NON_OPERATION,

    QuadrupleOp.MINUS: QuadrupleOpType.UNARY_OPERATION,
    QuadrupleOp.B_NOT: QuadrupleOpType.UNARY_OPERATION,

    QuadrupleOp.ADD: QuadrupleOpType.BINARY_OPERATION,
    QuadrupleOp.SUB: QuadrupleOpType.BINARY_OPERATION,
    QuadrupleOp.MUL: QuadrupleOpType.BINARY_OPERATION,
    QuadrupleOp.DIV: QuadrupleOpType.BINARY_OPERATION,
    QuadrupleOp.REM: QuadrupleOpType.BINARY_OPERATION,
    QuadrupleOp.B_AND: QuadrupleOpType.BINARY_OPERATION,
    QuadrupleOp.B_OR: QuadrupleOpType.BINARY_OPERATION,
    QuadrupleOp.B_XOR: QuadrupleOpType.BINARY_OPERATION,
    QuadrupleOp.SHL: QuadrupleOpType.BINARY_OPERATION,
    QuadrupleOp.SHR: QuadrupleOpType.BINARY_OPERATION,

}

commutative = frozenset({
    QuadrupleOp.ADD,
    QuadrupleOp.MUL,
    QuadrupleOp.B_AND,
    QuadrupleOp.B_OR,
    QuadrupleOp.B_XOR,
})



