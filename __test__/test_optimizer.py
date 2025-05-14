import unittest

from graphviz import Digraph

from optimization.optimizer import LocalOptimizer, DAGNode
from optimization.type import QuadrupleOp
from optimization.utils import load_quadruple

sign_table = {
    QuadrupleOp.ASSIGN: "=",

    QuadrupleOp.B_NOT: "~",
    QuadrupleOp.MINUS: "-",

    QuadrupleOp.ADD: "+",
    QuadrupleOp.SUB: "-",
    QuadrupleOp.MUL: "*",
    QuadrupleOp.DIV: "/",
    QuadrupleOp.MOD: "%",
    QuadrupleOp.B_AND: "&",
    QuadrupleOp.B_OR: "|",
    QuadrupleOp.B_XOR: "^",
    QuadrupleOp.SHL: "<<",
    QuadrupleOp.SHR: ">>",
}

class TestOptimizer(unittest.TestCase):
    def test_util(self):
        x = """T0 = 3.14
        T1 = 2 * T0
        T2 = R + r
        A = T1 * T2
        B = A
        T3 = 2 * T0
        T4 = R + r
        T5 = T3 * T4
        T6 = R - r
        B = T5 * T6
        """

        quadruples = load_quadruple(x.splitlines())

        opt = LocalOptimizer()
        dags = opt.to_dag(quadruples)
        code = opt.optimize(quadruples, {"A", "B"})

        fa_graph = Digraph(
            filename="dag", format='png',
            graph_attr={'fontname': 'SimHei'},
            node_attr={'fontname': 'SimHei'},
            edge_attr={'fontname': 'SimHei'}
        )

        def recursive(dag_node: DAGNode):
            if dag_node is None:
                return
            if dag_node.op:
                label = f"{dag_node.var_refs}\n\n\n{sign_table[dag_node.op]}"
            else:
                label = f"{dag_node.var_refs}\n\n\n{dag_node.value}"

            fa_graph.node(str(id(dag_node)), label=label)
            recursive(dag_node.right)
            recursive(dag_node.left)

        def recursive_edge(dag_node: DAGNode):
            if dag_node is None:
                return

            if dag_node.right:
                fa_graph.edge(str(id(dag_node)), str(id(dag_node.right)))

            if dag_node.left:
                fa_graph.edge(str(id(dag_node)), str(id(dag_node.left)))

            recursive_edge(dag_node.right)
            recursive_edge(dag_node.left)

        for dag in dags:
            recursive(dag)
            recursive_edge(dag)

        fa_graph.render(view=True, cleanup=True)
        for e in code:
            print(e)

