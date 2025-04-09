from common.IdGenerator import id_generator
from common.type import StateType, NodeInfoMap, SymbolType, NodeInfo, NFAEdgeType, EPSILON



class NFA:
    def __init__(self):
        self.__nodes: NodeInfoMap = {}
        self.__edges: NFAEdgeType = {}

    @property
    def nodes(self) -> NodeInfoMap:
        return self.__nodes

    @property
    def edges(self) -> NFAEdgeType:
        return self.__edges

    def add_node(self, node: StateType, accept: bool = False, label: str = None, meta = None) -> None:
        """
        添加节点（状态）
        :param node: 状态名 int | str
        :param accept: 是否为接受状态（终态）
        :param label: 字符串标签
        :param meta: 元信息
        """
        self.nodes[node] = NodeInfo(accept=accept, label=label, meta=meta)

    def add_edge(self, origin: StateType, dest: StateType | set[StateType] | list[StateType], edge: SymbolType) -> None:
        """
        添加边（转移）
        :param origin: 初始节点（状态）
        :param dest: 目标节点（状态）
        :param edge: 边字符（转移）
        """

        if origin not in self.nodes:
            node = dest if origin not in self.nodes else origin
            raise RuntimeError("Unknown node: " + str(node))

        k = (origin, edge)
        if k not in self.edges:
            self.edges[k] = set()

        if isinstance(dest, StateType):
            self.edges[k].add(dest)
        elif isinstance(dest, set) or isinstance(dest, list):
            self.edges[k].update(dest)
        else :
            raise RuntimeError("Unknown dest type: " + str(dest))

    def translate_to(self, node: StateType, edge: SymbolType) -> set[StateType] | None:
        k = (node, edge)
        if k not in self.edges:
            return None
        return self.edges[k]

    def closure(self, nodes: set[StateType]) -> set[StateType]:
        """
        epsilon闭包运算
        :param nodes:
        :return:
        """
        result: set[StateType] = set()
        stack: [SymbolType] = list(nodes)

        while len(stack) > 0:
            node = stack.pop()

            # 如果已经遍历过，跳过
            if node in result:
                continue
            result.add(node)

            # epsilon转移
            connect_nodes = self.translate_to(node, EPSILON)

            if connect_nodes is not None:
                stack += connect_nodes

        return result


    def dfa_edge(self, nodes: set[StateType], edge: SymbolType) -> set[StateType]:
        """
        《现代编译原理》管这个弧转叫DFAEdge
        :param nodes: 参与弧度转的节点
        :param edge: 弧转边
        :return: 弧转后节点
        """
        result: set[StateType] = set()
        for item in nodes:
            t_nodes = self.translate_to(item, edge)
            if t_nodes is not None:
                result |= t_nodes

        return result

    def concat(self, new_nfa: 'NFA'):
        """
        拼接两个DFA，包括边和节点
        :param new_nfa:
        :return:
        """
        self.nodes.update(new_nfa.nodes)
        self.edges.update(new_nfa.edges)



def __translate_recursion(reg_text: str, pos: int, beg_state: StateType, generator) -> tuple[NFA, StateType]:

    nfa = NFA()






def __priority(op1, op2):
    """
    返回-1 0 1 op1 < op2 op1 = op2 op1 > op2
    :param op1:
    :param op2:
    :return:
    """
    # prior_matrix = {
    #     '(': {'(': -1,'[': -1,'|': 1, '*': 1, 'x': 1, ')': 0, ']': 0},
    #     '[': {'(': 0,'[': 0,'|': 0, '*': 0, 'x': 0, ')': 0, ']': 0},
    #     '|': {'(': 0,'[': 0,'|': 0, '*': 0, 'x': 0, ')': 0, ']': 0},
    #     '*': {'(': 0,'[': 0,'|': 0, '*': 0, 'x': 0, ')': 0, ']': 0},
    #     'x': {'(': 0,'[': 0,'|': 0, '*': 0, 'x': 0, ')': 0, ']': 0},
    #     ')': {'(': 0,'[': 0,'|': 0, '*': 0, 'x': 0, ')': 0, ']': 0},
    #     ']': {'(': 0,'[': 0,'|': 0, '*': 0, 'x': 0, ')': 0, ']': 0},
    # }


# def __calc()

#
# def translate_to_nfa(reg_text: str):
#     char_stack = []
#     op_stack = []
#
#
#     for c in reg_text:
#         if c == '(' or c == '[':
#             op_stack.append(c)
#         elif c == ')':
#             pass
#         elif c == ']':
#             pass
#         elif c == '|'  or c == '*':
#             if
#             char_stack.append(c)
#             pass
#         else:
#             char_stack.append(c)
#             if len(char_stack) > 0:
#                 op_stack.append('X')
#
#
#
#
#     pass


def test_nfa():
    # todo 测试代码
    nfa = NFA()
    nfa.add_node(0)
    nfa.add_node(1)
    nfa.add_node(2)
    nfa.add_node(3)
    nfa.add_node(4)
    nfa.add_node(5)
    nfa.add_node(6)
    nfa.add_node(7)
    # print(nfa.nodes.keys())

    nfa.add_edge(0, [0, 1, 2, 3], EPSILON)
    nfa.add_edge(1, [0, 1, 2, 3], EPSILON)
    nfa.add_edge(2, [0, 1, 2, 3], EPSILON)
    nfa.add_edge(2, [0, 1, 2, 3], 'a')
    nfa.add_edge(2, [0, 1, 2, 3], 'b')
    nfa.add_edge(3, [0, 1], 'a')
    # print(nfa.edges)

    print(nfa.closure({0, 1}))
    print(nfa.closure({1}))
    print(nfa.closure({2}))
    print(nfa.dfa_edge({3, 2}, 'a'))

    s1 = {3, 1, 2}
    s2 = set()
    s2.add(3)
    print(s2)
    s2.add(1)
    print(s2)
    s2.add(2)
    print(s2)
    print(s1)


    d = {frozenset(s1): "114514"}
    print(d[frozenset(s2)])