from optimization.type import Quadruple, QuadrupleOp, Operand, OperandType

str_op_map = {
    "=": QuadrupleOp.ASSIGN,

    "m": QuadrupleOp.MINUS,
    "~": QuadrupleOp.B_NOT,

    "+": QuadrupleOp.ADD,
    "-": QuadrupleOp.SUB,
    "*": QuadrupleOp.MUL,
    "/": QuadrupleOp.DIV,
    "%": QuadrupleOp.MOD,
    "&": QuadrupleOp.B_AND,
    "|": QuadrupleOp.B_OR,
    "^": QuadrupleOp.B_XOR,
    "<<": QuadrupleOp.SHL,
    ">>": QuadrupleOp.SHR,
}

def get_type(x: str):

    try:
        return int(x), OperandType.INTEGER
    except ValueError:
        pass

    try:
        return float(x), OperandType.FLOAT
    except ValueError:
        pass

    return x, OperandType.VARIABLE

def load_quadruple(lines: list[str]) -> list[Quadruple]:
    result = []
    for line in lines:
        pattens = line.split(" ")
        pattens = list(filter(lambda x: len(x) != 0, pattens))
        if len(pattens) == 0:
            continue
        if len(pattens) < 3:
            raise RuntimeError(f"Invalid quadruple: {line}")

        if len(pattens) == 4:
            op = pattens[2]
        elif len(pattens) == 3:
            op = pattens[1]
        else:
            op = pattens[3]


        if op == "-" and len(pattens) == 4:
            op = "m"

        op = str_op_map[op]

        lvalue = Operand(pattens[0], OperandType.VARIABLE)

        operands = []
        for item in pattens[2:]:
            value, typ = get_type(item)
            operands.append(Operand(value, typ))

        if len(operands) == 1:
            result.append(Quadruple(op, v1=operands[0], v2=None, v3=lvalue))
        elif len(operands) == 2:
            result.append(Quadruple(op, v1=operands[1], v2=None, v3=lvalue))
        else:
            result.append(Quadruple(op, v1=operands[0], v2=operands[2], v3=lvalue))


    return result





