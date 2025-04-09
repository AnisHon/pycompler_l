from common.type import StateType, NodeInfoMap, SymbolType, DFAEdgeType, NodeInfo

class DFA:
    def __init__(self):
        self.__nodes: NodeInfoMap = {}
        self.__edges: DFAEdgeType = {}

    @property
    def nodes(self) -> NodeInfoMap:
        return self.__nodes

    @property
    def edges(self) -> DFAEdgeType:
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

    def add_edge(self, origin: StateType, dest: StateType, edge: SymbolType) -> None:
        """
        添加边（转移）
        :param origin: 初始节点（状态）
        :param dest: 目标节点（状态）
        :param edge: 边字符（转移）
        """
        if origin not in self.nodes or dest not in self.nodes:
            node = dest if origin not in self.nodes else origin
            raise RuntimeError("Unknown node: " + str(node))

        self.edges[(origin, edge)] = dest

    def translate_to(self, origin: StateType, edge: SymbolType) -> StateType | None:
        """
        进行一次转移，从origin --edge--> ???
        :param origin: 不多bb
        :param edge: 不多bb
        :return: 转移失败后返回None
        """

        k = (origin, edge)
        if k not in self.edges:
            return None
        return self.edges[k]


if __name__ == "__main__":
    # todo 测试代码
    dfa = DFA()
    dfa.add_node(0)
    dfa.add_node(2)
    dfa.add_node(1, accept=True)
    dfa.add_edge(0,  2, 'a')
    dfa.add_edge(0,  2, 'b')
    dfa.add_edge(2,  2, 'a')
    dfa.add_edge(2,  2, 'b')
    dfa.add_edge(2,  1, 'c')


    s = "aaabcaaaaaaaaaaaaabc"

    # print(dfa.edges)


    state: int = 0
    last_state = 0
    last_state_pos = 0
    beg = 0
    i = 0





