import unittest

from graphviz import Digraph

from parser.lr_parse import LR1Parser, ParserType
from parser.production_builder import ProductionBuilder
import pandas as pd


class TestParser(unittest.TestCase):
    def test_parser(self):
        production = ProductionBuilder([
            ("S", ("L=R", "R")),
            ("L", ("*R", "i")),
            ("R", ("L", )),
        ])


        print(production.parse())

        lr1_parser = LR1Parser(production.parse(), "S")


        df = pd.DataFrame(
            [{"src": src, "edge": edge, "dest": dest} for (src, edge), dest in lr1_parser.action_goto_table.items()]
        )
        adj_matrix = df.pivot(index="src", columns="edge", values="dest").fillna("")
        print(adj_matrix)


        fa_graph = Digraph(
            filename="lr1_table", format='png',
            graph_attr={'fontname': 'SimHei'},
            node_attr={'fontname': 'SimHei'},
            edge_attr={'fontname': 'SimHei'}
        )

        fa_graph.attr(rankdir='LR', nodesep='0.5', ranksep='1.0')
        # fa_graph.attr('node', shape='circle', width='0.5')

        state_table = {}
        for k, v in lr1_parser.state_table.items():
            state_table[v] = k

        node_table = {}
        for (src, edge), dest in lr1_parser.action_goto_table.items():
            if not (dest.cell_type != ParserType.SHIFT or dest.cell_type == ParserType.GOTO):
                continue
            src_set = state_table[src]
            dest_set = state_table[dest.value]

            src_node = "\n".join(map(lambda x: str(x), src_set))
            dest_node = "\n".join(map(lambda x: str(x), dest_set))

            node_table[src] = src_node
            node_table[dest.value] = dest_node


        for k, v in node_table.items():
            fa_graph.node(str(k), v, shape="box")

        for (src, edge), dest in lr1_parser.action_goto_table.items():
            if dest.cell_type == ParserType.REDUCE or dest.cell_type == ParserType.ACCEPT:
                continue

            fa_graph.edge(str(src), str(dest.value), edge)

        fa_graph.render(view=True, cleanup=True)