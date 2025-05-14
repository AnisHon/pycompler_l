from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from optimization.type import Quadruple, Operand, QuadrupleOp, quadrupleOpType, QuadrupleOpType, OperandType, \
    commutative


@dataclass
class DAGNode:
    value: Operand | None
    op: OperandType | None = field(default=None)
    const: bool = field(default=False)
    var_refs: set[Operand] = field(default_factory=set)
    left: 'DAGNode' | None = field(default=None)
    right: 'DAGNode' | None = field(default=None)

    def __post_init__(self):
        self.const = self.value.type != OperandType.VARIABLE and self.op is None

    def add_ref(self, operand: Operand):
        self.var_refs.add(operand)

    def rm_ref(self, operand: Operand):
        self.var_refs.discard(operand)

class Optimizer:

    _CALC_MAP: dict[QuadrupleOp, Callable[[Quadruple], Operand]] = {

    }

    def __init__(self):
        self.__ref_table: dict[Operand, DAGNode] = {} # var ref table
        self.__op_table: dict[tuple[DAGNode | None, QuadrupleOp, DAGNode | None], DAGNode] = {}  # op ref table


    def __clear(self):
        self.__ref_table.clear()
        self.__op_table.clear()

    def __get_or_insert_ref(self, operand: Operand) -> DAGNode:
        if operand is None:
            raise TypeError("Operand can't be None")

        node = self.__ref_table.get(operand, None)

        if node is None:
            node = DAGNode(value=operand)
            self.__ref_table[operand] = node
        return node

    def __get_or_insert_op(self, operand1, op, operand2):
        if operand1 is None and operand2 is None:
            raise TypeError("Operand can't be None")

        node = self.__op_table.get((operand1, op, operand2), None)

        if op in commutative:
            node = self.__op_table.get((operand2, op, operand1), None)

        if node is None:
            node_l = None if operand1 is None else self.__get_or_insert_ref(operand1)
            node_r = None if operand2 is None else self.__get_or_insert_ref(operand2)
            node = DAGNode(value=None, op=op, left=node_l, right=node_r)
            self.__op_table[(operand1, op, operand2)] = node

        return node


    def __build_node(self, quadruple: Quadruple) -> DAGNode:
        operands = quadruple.get_binary_operand()
        temp = None
        for op in operands:
            if op is None:
                continue

            temp = self.__get_or_insert_ref(op)

        return temp

    def __handle_const_unary(self, quadruple: Quadruple) -> DAGNode:
        operand = quadruple.get_unary_operand()
        result_operand = None
        if operand.is_const:
            result_operand = Optimizer._CALC_MAP[quadruple.op](quadruple)

        return self.__get_or_insert_ref(result_operand)


    def __handle_const_binary(self, quadruple: Quadruple) -> DAGNode:
        operand1, operand2 = quadruple.get_binary_operand()
        result_operand = None

        if operand1.is_const and operand2.is_const:
            result_operand = Optimizer._CALC_MAP[quadruple.op](quadruple)

        return self.__get_or_insert_ref(result_operand)


    def __handle_const(self, quadruple: Quadruple, op) -> DAGNode | None:  # calculate known value
        node = None
        match op:
            case QuadrupleOpType.NON_OPERATION:
                pass

            case QuadrupleOpType.UNARY_OPERATION:
               node = self.__handle_const_unary(quadruple)

            case QuadrupleOpType.BINARY_OPERATION:
                node = self.__handle_const_binary(quadruple)

            case _:
                raise NotImplementedError()

        return node

    def __handle_common_unary(self, quadruple: Quadruple) -> DAGNode:
        operand = quadruple.get_unary_operand()
        return self.__get_or_insert_op(None, quadruple.op, operand)


    def __handle_common_binary(self, quadruple: Quadruple) -> DAGNode:
        operand1, operand2 = quadruple.get_binary_operand()
        return self.__get_or_insert_op(operand1, quadruple.op, operand2)

    def __handle_common(self, quadruple: Quadruple, op):      # remove common expression
        node = None
        match op:
            case QuadrupleOpType.NON_OPERATION:
                pass

            case QuadrupleOpType.UNARY_OPERATION:
                node = self.__handle_const_unary(quadruple)

            case QuadrupleOpType.BINARY_OPERATION:
                node = self.__handle_const_binary(quadruple)

            case _:
                raise NotImplementedError()

        return node

    def __handle_redundant(self, formula: Quadruple, node: DAGNode):  # remove redundant expression
        lv = formula.get_lvalue()
        if lv in self.__ref_table:
            self.__ref_table[lv].rm_ref(lv)

        node.add_ref(lv)



    @staticmethod
    def __set_node(origin, new):
        return new if new is not None else origin

    def __get_dags(self) -> list[DAGNode]:
        in_degree: dict[DAGNode, int] = defaultdict(int)
        result = []
        for item in set(self.__ref_table.values()):
            if item.left:
                in_degree[item.left] += 1
            elif item.right:
                in_degree[item.right] += 1

        for k, v in in_degree.items():
            if v == 0:
                result.append(k)

        return result

    def to_dag(self, formulas: list[Quadruple]) -> list[DAGNode]:
        for quadruple in formulas:
            op = quadrupleOpType[quadruple.op]
            node = self.__build_node(quadruple)
            node = Optimizer.__set_node(node, self.__handle_const(quadruple, op))
            node = Optimizer.__set_node(node, self.__handle_const(quadruple, op))

            self.__handle_redundant(quadruple, node)

        dags = self.__get_dags()
        self.__clear()

        return dags


    def optimize(self, formulas: list[Quadruple]):
        pass