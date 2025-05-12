from enum import Enum, auto


class QuadrupleOp(Enum):
    ASSIGN = auto()     # v4 = v1

    ADD = auto()        # v4 = v1 + v2




class Quadruple:
    def __init__(self, v1, v2, v3, v4):
        self.v1 = v1
        self.v2 = v2