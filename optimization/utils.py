from optimization.type import Quadruple, QuadrupleOp, Operand

str_op_map = {
    "=": QuadrupleOp.ASSIGN,

    "m": QuadrupleOp.MINUS,
    "~": QuadrupleOp.B_NOT,

    "+": QuadrupleOp.ADD,
    "-": QuadrupleOp.SUB,
    "*": QuadrupleOp.MUL,
    "/": QuadrupleOp.DIV,
    "%": QuadrupleOp.REM,
    "&": QuadrupleOp.B_AND,
    "|": QuadrupleOp.B_OR,
    "^": QuadrupleOp.B_XOR,
    "<<": QuadrupleOp.SHL,
    ">>": QuadrupleOp.SHR,
}


def load_quadruple(lines: list[str]) -> list[Quadruple]:
    for line in lines:
        pattens = line.split(" ")

        if len(pattens) < 3:
            raise RuntimeError(f"Invalid quadruple: {line}")

        op = pattens[1]
        if op == "-" and len(pattens) == 3:
            op = "m"

        op = str_op_map[op]

        for item in pattens[3:]:
            operand = Operand(item, None)






