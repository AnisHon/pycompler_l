import unittest

from graphviz import Digraph

from parser.ll_parse import LL1Parser
from parser.lr_parse import LR1Parser, ParserType, LAlR1Parser
from parser.production_builder import ProductionBuilder
import pandas as pd

from parser.util import compute_first_set, compute_alter_first_set, nullable, compute_follow_set


def draw(state2collection_table, action_goto_table, filename: str):
    df = pd.DataFrame(
        [{"src": src, "edge": edge, "dest": dest} for (src, edge), dest in action_goto_table.items()]
    )
    adj_matrix = df.pivot(index="src", columns="edge", values="dest").fillna("")
    print(adj_matrix)


    fa_graph = Digraph(
        filename=filename, format='png',
        graph_attr={'fontname': 'SimHei'},
        node_attr={'fontname': 'SimHei'},
        edge_attr={'fontname': 'SimHei'}
    )

    fa_graph.attr(rankdir='LR', nodesep='0.5', ranksep='1.0')
    fa_graph.attr('node', shape='box', width='0.5')
    # fa_graph.attr('node', shape='circle', width='0.5')

    state_table = state2collection_table

    node_table = {}
    for (src, edge), dest in action_goto_table.items():
        if not (dest.cell_type != ParserType.SHIFT or dest.cell_type == ParserType.GOTO):
            continue
        src_set = state_table[src]
        dest_set = state_table[dest.value]

        src_set = sorted(src_set, key=lambda s: s.production, reverse=True)
        dest_set = sorted(dest_set, key=lambda s: s.production, reverse=True)

        src_node = "\n".join(map(lambda x: str(x), src_set))
        dest_node = "\n".join(map(lambda x: str(x), dest_set))

        node_table[src] = src_node
        node_table[dest.value] = dest_node


    for k, v in node_table.items():
        fa_graph.node(str(k), v, shape="box")

    for (src, edge), dest in action_goto_table.items():
        if dest.cell_type == ParserType.REDUCE or dest.cell_type == ParserType.ACCEPT:
            continue
        fa_graph.edge(str(src), str(dest.value), str(edge))

    fa_graph.render(view=True, cleanup=True)


class TestParser(unittest.TestCase):
    def test_util(self):
        # production = ProductionBuilder([
        #     ("S", ("AB", "bC"), ("", "")),
        #     ("A", ("b", ""), ("", "")),
        #     ("B", ("b", ''), ("", "")),
        #     ("C", ("AD", 'b'), ("", "")),
        #     ("D", ("aS", 'c'), ("", "")),
        # ], ['b', 'c', ])
        production = ProductionBuilder([
            ("E", ("TE'", ), ("", )),
            ("E'", ("ATE'", ""), ("", "")),
            ("T", ("FT'", ), ("", )),
            ("T'", ("MFT'", ""), ("", "")),
            ("F", ("(E)", "i"), ("", "")),
            ("A", ("+", "-"), ("", "")),
            ("M", ("*", "/"), ("", "")),

        ], ['b', 'c', "(", ")", "+", "-", "*", "/", 'i'])

        productions = production.parse()
        first_set, first_productions = compute_alter_first_set(production.parse())
        print(first_productions)
        # print(compute_follow_set(first_productions, "E"))
        # print(nullable(productions))
        # print(first_set)
        table = LL1Parser(productions, "E").result_table
        df = pd.DataFrame(
            [{"name": src, "char": edge, "expr": str(expr)} for (src, edge), expr in table.items()]
        )
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_colwidth', None)
        pd.set_option('display.width', None)


        # print(table)
        adj_matrix = df.pivot(index="name", columns="char", values="expr").fillna("")

        print(adj_matrix)



    def test_lr1_parser(self):
        # production = ProductionBuilder([
        #     ("S'", ("L=R", "R")),
        #     ("L", ("*R", "i")),
        #     ("R", ("L", )),
        # ])
        production = ProductionBuilder([
            ("S'", ("S", ), ("", )),
            ("S", ("BB", ), ("", )),
            ("B", ("aB", 'b'), ("", "")),
        ], ['a', 'b'])

        print(compute_first_set(production.parse()))


        print(production.parse())

        lr1_parser = LR1Parser(production.parse(), "S'")

        draw(lr1_parser.state2collection_table, lr1_parser.action_goto_table, "lr1_table")

    def test_lalr1_parser(self):
        # production = ProductionBuilder([
        #     ("S'", ("L=R", "R")),
        #     ("L", ("*R", "i")),
        #     ("R", ("L", )),
        # ])
        production = ProductionBuilder([
            ("S'", ("S", ), ("", )),
            ("S", ("BB", ), ("", )),
            ("B", ("aB", 'b'), ("", "")),
        ], ['a', 'b'])

        print(compute_first_set(production.parse()))


        print(production.parse())

        lr1_parser = LAlR1Parser(production.parse(), "S'")

        draw(lr1_parser.state2collection_table, lr1_parser.action_goto_table, "lalr1_table")

