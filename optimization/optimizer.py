from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Union, Any, Optional

from optimization.type import Quadruple, Operand, QuadrupleOp, quadrupleOpType, QuadrupleOpType, OperandType, \
    commutative


@dataclass
class DAGNode:
    value: Operand | None
    op: QuadrupleOp | None = field(default=None)
    const: bool = field(default=False)
    var_refs: set[Operand] = field(default_factory=set)
    left: Union['DAGNode', None] = field(default=None)
    right: Union['DAGNode', None] = field(default=None)

    def __post_init__(self):
        self.const = self.value is not None and self.op is None

    def add_ref(self, operand: Operand):
        self.var_refs.add(operand)

    def rm_ref(self, operand: Operand):
        self.var_refs.discard(operand)

    def __hash__(self):
        return hash((self.value, self.op, self.const))

    def __str__(self):
        if self.op:
            return f"(op: {self.op}, const: {self.const}, var_refs: {self.var_refs}, left: {self.left}, right: {self.right})"
        else:
            return f"(value: {self.value}, const: {self.const}, var_refs: {self.var_refs})"


class LocalOptimizer:

    def __init__(self):
        self.__ref_table: dict[Operand, DAGNode] = {}  # var ref table
        self.__op_table: dict[tuple[int | None, QuadrupleOp, int | None], DAGNode] = {}  # op ref table
        self._CALC_MAP: dict[QuadrupleOp, Callable[[Quadruple], Operand]] = {    # op calculation function table
            # QuadrupleOp.ASSIGN: LocalOptimizer,

            QuadrupleOp.MINUS: self.__minus,
            QuadrupleOp.B_NOT: self.__b_not,

            QuadrupleOp.ADD: self.__add,
            QuadrupleOp.SUB: self.__sub,
            QuadrupleOp.MUL: self.__mul,
            QuadrupleOp.DIV: self.__div,
            QuadrupleOp.MOD: self.__mod,
            QuadrupleOp.B_AND: self.__b_and,
            QuadrupleOp.B_OR: self.__b_or,
            QuadrupleOp.B_XOR: self.__b_xor,
            QuadrupleOp.SHL: self.__shl,
            QuadrupleOp.SHR: self.__shr,
        }

        self._OPT_MAP: dict[QuadrupleOp, Callable[[Quadruple], Optional[DAGNode]]] = {
            QuadrupleOp.ADD: self.__opt_add,
            QuadrupleOp.SUB: self.__opt_sub,
            QuadrupleOp.MUL: self.__opt_mul,
            QuadrupleOp.DIV: self.__opt_div,
            QuadrupleOp.MOD: self.__opt_mod,
            QuadrupleOp.B_AND: self.__opt_b_and,
            QuadrupleOp.B_OR: self.__opt_b_or,
            QuadrupleOp.B_XOR: self.__opt_b_xor,
            QuadrupleOp.SHL: self.__opt_shl,
            QuadrupleOp.SHR: self.__opt_shr,
        }


    def __opt_add(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __opt_sub(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __opt_mul(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __opt_div(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __opt_mod(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __opt_b_and(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __opt_b_or(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __opt_b_xor(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __opt_shl(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __opt_shr(self, quadruple: Quadruple) -> DAGNode | None:
        return None

    def __get_binary_dag_op(self, quadruple: Quadruple) -> tuple[Any, Any, OperandType]:
        """
        a universal function for binary operations, get operands from quadruple,
        translate to operands.value in DAG(will expand variables)
        :param quadruple: the quadruple needs calculation
        :return: value and type
        """
        a, b = quadruple.get_binary_operand()
        a, b = self.__ref_table[a].value, self.__ref_table[b].value
        typ = a.type
        if a.type == OperandType.FLOAT or b.type == OperandType.FLOAT:
            typ = OperandType.FLOAT
        return a.value, b.value, typ


    # all function below is calculation function
    def __minus(self, quadruple: Quadruple) -> Operand:
        x = quadruple.get_unary_operand()
        x = self.__ref_table[x].value
        return Operand(-x.value, x.type)

    def __b_not(self, quadruple: Quadruple) -> Operand:
        a = quadruple.get_unary_operand()
        a = self.__ref_table[a].value
        return Operand(~a.value, a.type)

    def __add(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a + b, typ)

    def __sub(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a - b, typ)

    def __mul(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a * b, typ)

    def __div(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a / b, typ)

    def __mod(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a % b, typ)

    def __b_and(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a & b, typ)

    def __b_or(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a | b, typ)

    def __b_xor(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a ^ b, typ)

    def __shl(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a << b, typ)

    def __shr(self, quadruple: Quadruple) -> Operand:
        a, b, typ = self.__get_binary_dag_op(quadruple)
        return Operand(a >> b, typ)


    def __clear(self):
        self.__ref_table.clear()
        self.__op_table.clear()

    def __get_or_insert_ref(self, operand: Operand) -> DAGNode:
        """
        if operand exists than share it, or make one.
        this function ensure that this DAGNode will be added or already existed in ref_table
        :param operand: a constant or variable operand
        :return: a dag node, maby shared or maked.
        """
        if operand is None:
            raise TypeError("Operand can't be None")

        node = self.__ref_table.get(operand, None)

        if node is None:
            if operand.is_const:
                node = DAGNode(value=operand)
            else:
                node = DAGNode(value=None, var_refs={operand})

            self.__ref_table[operand] = node
        return node

    def __get_or_insert_op(self, operand1, op, operand2):
        """
        same as above, this function is mainly responsible for op_table
        meanwhile, this function ensure that commutative operations' order will be ignored
        :param operand1: a variable or None
        :param op: must not be ASSIGN
        :param operand2: a variable or None
        :return: a dag node
        """
        if operand1 is None and operand2 is None:
            raise TypeError("Operand can't be None")

        dag1, dag2 = id(self.__ref_table[operand1]), id(self.__ref_table[operand2])

        node = self.__op_table.get((dag1, op, dag2), None)

        if node is None and op in commutative:
            node = self.__op_table.get((dag2, op, dag1), None)

        if node is None:
            node_l = None if operand1 is None else self.__get_or_insert_ref(operand1)
            node_r = None if operand2 is None else self.__get_or_insert_ref(operand2)
            node = DAGNode(value=None, op=op, left=node_l, right=node_r)
            self.__op_table[(dag1, op, dag2)] = node

        return node

    def __build_node(self, quadruple: Quadruple) -> DAGNode:
        """
        this function is the first step of local optimation.
        it ensures all rvalues will be defined
        :return: a newly constructed DAGNode, if having multi newly constructed nodes, return last one
        """
        operands = quadruple.get_binary_operand()
        temp = None
        for op in operands:
            if op is None:
                continue

            temp = self.__get_or_insert_ref(op)

        return temp

    def __handle_const_unary(self, quadruple: Quadruple) -> DAGNode:
        """
        calculate constant
        :return:
        """
        operand = quadruple.get_unary_operand()
        result_operand = None

        if self.__ref_table[operand].const:
            result_operand = self._CALC_MAP[quadruple.op](quadruple)

        return self.__get_or_insert_ref(result_operand)

    def __handle_const_binary(self, quadruple: Quadruple) -> DAGNode | None:
        """
        calculate constant
        :return:
        """
        operand1, operand2 = quadruple.get_binary_operand()

        if not self.__ref_table[operand1].const or not self.__ref_table[operand2].const:
            return None

        result_operand = self._CALC_MAP[quadruple.op](quadruple)

        return self.__get_or_insert_ref(result_operand)

    def __handle_const(self, quadruple: Quadruple, op) -> DAGNode | None:  # calculate known value
        """
        the second step of local optimization, if it's non const, this function will return None
        """

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

        if node is not None:
            node.const = True

        return node

    def __handle_common_unary(self, quadruple: Quadruple) -> DAGNode | None:
        """
        generate calculating node
        """
        operand = quadruple.get_unary_operand()
        if self.__ref_table[operand].const:
            return None
        return self.__get_or_insert_op(None, quadruple.op, operand)

    def __handle_common_binary(self, quadruple: Quadruple) -> DAGNode | None:
        operand1, operand2 = quadruple.get_binary_operand()
        if self.__ref_table[operand1].const and self.__ref_table[operand2].const:
            return None

        node = None # optimation needed

        if node is None:
            node = self.__get_or_insert_op(operand1, quadruple.op, operand2)

        return node

    def __handle_common(self, quadruple: Quadruple, op):  # remove common expression
        """
        this function is the third step of local optimization. if it's all constant expression, it will return None
        """
        node = None
        match op:
            case QuadrupleOpType.NON_OPERATION:
                pass

            case QuadrupleOpType.UNARY_OPERATION:
                node = self.__handle_common_unary(quadruple)

            case QuadrupleOpType.BINARY_OPERATION:
                node = self.__handle_common_binary(quadruple)

            case _:
                raise NotImplementedError()

        return node

    def __handle_redundant(self, formula: Quadruple, node: DAGNode):  # remove redundant expression
        """
        this function is the forth step of local optimization.
        this function will guarantee that any variable bind to only one node.
        """
        lv = formula.get_lvalue()
        if lv in self.__ref_table:
            self.__ref_table[lv].rm_ref(lv)
            if len(self.__ref_table[lv].var_refs) == 0:
                del self.__ref_table[lv]

        node.add_ref(lv)
        self.__ref_table[lv] = node

    @staticmethod
    def __set_node(origin, new):
        # get new return new
        return new if new is not None else origin

    def __get_dags(self) -> list[DAGNode]:
        in_degree: dict[DAGNode, int] = {}
        result = []
        for item in set(self.__ref_table.values()):
            if item.left:
                in_degree[item.left] = in_degree.get(item.left, 0) + 1

            if item.right:
                in_degree[item.right] = in_degree.get(item.right, 0) + 1

            in_degree[item] = in_degree.get(item, 0)

        for k, v in in_degree.items():
            if v == 0 and len(k.var_refs) > 0:
                result.append(k)

        return result

    def to_dag(self, formulas: list[Quadruple]) -> list[DAGNode]:
        for quadruple in formulas:
            op = quadrupleOpType[quadruple.op]
            node = self.__build_node(quadruple)
            node = LocalOptimizer.__set_node(node, self.__handle_const(quadruple, op))
            node = LocalOptimizer.__set_node(node, self.__handle_common(quadruple, op))

            self.__handle_redundant(quadruple, node)

        dags = self.__get_dags()
        self.__clear()

        return dags

    def optimize(self, formulas: list[Quadruple], lives: set | None = None):

        dags = self.to_dag(formulas)

        result = []

        def is_lived(v3):
            return lives is not None and v3 not in lives

        def add_quadruple(v1, v2, node):

            if not v1 and not v2:
                if not node.value:
                    return

                for v3 in node.var_refs:
                    if is_lived(v3):
                        continue
                    v3 = Operand(v3, OperandType.VARIABLE)
                    result.append(Quadruple(QuadrupleOp.ASSIGN, node.value, None, v3))

                return

            if v1 is None:
                v1 = v2

            if node.op is None:
                raise RuntimeError("Node Op is None")

            refs_iter = iter(node.var_refs)
            calc_var = Operand(next(refs_iter), OperandType.VARIABLE)
            result.append(Quadruple(node.op, v1, v2, calc_var))

            for v3 in refs_iter:
                if is_lived(v3):
                    continue
                v3 = Operand(v3, OperandType.VARIABLE)
                result.append(Quadruple(QuadrupleOp.ASSIGN, calc_var, None, v3))


        def dfs(node: DAGNode):
            if node is None:
                return None
            v1 = dfs(node.left)
            v2 = dfs(node.right)


            if not v1 and not v2:
                if node.value:
                    result_node = Operand(node.value, node.value.type)
                else:
                    result_node = Operand(next(iter(node.var_refs)), OperandType.VARIABLE)
            else:
                result_node = Operand(next(iter(node.var_refs)), OperandType.VARIABLE)
            add_quadruple(v1, v2, node)
            return result_node

        for dag in dags:
            dfs(dag)

        return result
