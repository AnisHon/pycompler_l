# @encoding: utf-8
# @author: anishan
# @date: 2025/04/09
# @description: DFA简单实现，也许以后用线段树实现
from common.range_map import RangeMap
from common.replace_util import ReplaceUtil
from common.common_type import StateType, NodeInfoMap, SymbolType, NodeInfo, NFAEdgeType, EPSILON



class NFA:
    """
    Simple NFA(Non-determined Finity Automatic) implementation
    """


    def __init__(self, range_map: RangeMap = None):
        self.range_map: RangeMap = range_map
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

    def add_nodes(self, *nodes: StateType):
        for node in nodes:
            self.add_node(node)


    def add_edge(self, origin: StateType, dest: StateType | set[StateType] | list[StateType], edge: SymbolType = EPSILON) -> None:
        """
        add transition(edge)
        :param origin: 初始节点（状态）
        :param dest: 目标节点（状态）
        :param edge: 边字符（转移）,默认空转移
        """
        if origin not in self.nodes:
            node = dest if origin not in self.nodes else origin
            raise RuntimeError("Unknown node: " + str(node))

        k = (origin, edge)
        if k not in self.edges:
            self.edges[k] = set()

        # I know this place looks terrible, but it works
        # if python had overload, everything would be better
        if isinstance(dest, StateType):
            if dest not in self.nodes:
                raise RuntimeError("Unknown node: " + str(dest))

            self.edges[k].add(dest)

        elif isinstance(dest, set) or isinstance(dest, list):
            if len(dest - self.nodes.keys()) != 0:
                raise RuntimeError("Unknown node: " + str(dest))

            self.edges[k].update(dest)
        else :
            raise RuntimeError("Unknown dest type: " + str(dest))

    def add_edges(self, *edges: tuple[StateType, StateType, SymbolType]):
        for edge in edges:
            origin = edge[0]
            dest = edge[1]
            edge = edge[2]
            self.add_edge(origin, dest, edge)

    def translate_to(self, node: StateType, edge: SymbolType) -> set[StateType] | None:
        k = (node, edge)
        if k not in self.edges:
            return None
        return self.edges[k]

    def closure(self, nodes: frozenset[StateType] | set[StateType]) -> set[StateType]:
        """
        epsilon闭包运算(ε-closure)
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


    def dfa_edge(self, nodes: frozenset[StateType] | set[StateType], edge: SymbolType) -> set[StateType]:
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

    def kleene_closure(self, nodes: frozenset[StateType] | set[StateType], edge: SymbolType) -> set[StateType]:
        """
        kleene closure, I_a = ε-closure(J)
        :param nodes: 'I' set
        :param edge: 'a' transition
        :return: 'I_a' set
        """
        j = self.dfa_edge(nodes, edge)
        return self.closure(j)

    def concat(self, new_nfa: 'NFA'):
        """
        拼接两个DFA，包括边和节点
        :param new_nfa:
        :return:
        """
        self.nodes.update(new_nfa.nodes)
        self.edges.update(new_nfa.edges)

    def print_edge(self):
        print(f"{'Origin':<10}{'Symbol':<10}{'Dest'}")
        for edge in self.edges:
            symbol = ReplaceUtil()\
                .add_replace('ε', "'ε'")\
                .add_replace(EPSILON, 'ε')\
                .add_replace(' ', "' '")\
                .replace(edge[1])

            # print(ord(symbol))
            print(f"{edge[0]:<10}{symbol:<10}{','.join(map(lambda x: str(x), self.edges[edge]))}")
