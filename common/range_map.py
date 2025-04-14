# @encoding: utf-8
# @author: anishan
# @date: 2025/04/09
# @description: range mapping, currently implemented by range AVL

class TreeRangeNode:
    """
    [beg, end)
    """
    __slots__ = 'beg', 'end', 'height', 'left', 'right', 'meta', 'min', 'max'

    def __init__(self, beg, end):
        self.beg: int = beg
        self.end: int = end
        self.height: int = 1
        self.left: TreeRangeNode | None = None
        self.right: TreeRangeNode | None = None
        self.meta: any = None
        self.min: int = beg
        self.max: int = end

    @property
    def mid(self):
        return (self.beg + self.end - 1) //  2

    def __repr__(self) -> str:
        return f'({self.beg}, {self.end})'

    def __str__(self) -> str:
        return self.__repr__()

    @staticmethod
    def clone(node):
        if node is None:
            return None
        obj = TreeRangeNode(node.beg, node.end)
        obj.height = node.height
        obj.meta = node.meta
        return obj


class RangeMap:
    """
    区间映射，目前不确定用什么实现，目前最简实现非平衡的树
    """
    def __init__(self):
        self.__root = None


    @staticmethod
    def __left_limit(curr: TreeRangeNode, left_root: TreeRangeNode):
        """
        check if it needs to reduce left interval
        """
        if left_root is None:
            return curr.beg

        return max(curr.beg, left_root.max)

    @staticmethod
    def __right_limit(curr: TreeRangeNode, right_root: TreeRangeNode):
        """
        check if it needs to reduce right interval
        """
        if right_root is None:
            return curr.end

        return min(curr.end, right_root.min)

    @staticmethod
    def __get_height(root: TreeRangeNode | None):
        return 0 if root is None else root.height

    @staticmethod
    def __set_height(root: TreeRangeNode):
        if root is None:
            return
        l_height = RangeMap.__get_height(root.left)
        r_height = RangeMap.__get_height(root.right)
        root.height = max(l_height, r_height) + 1

    @staticmethod
    def __left_rotate(x: TreeRangeNode) -> TreeRangeNode:
        """
                   x                                   y
                       y           ->              x       z
                     b   z                           b
        """
        assert x is not None
        assert x.right is not None
        y, z, b = x.right, x.right.right, x.right.left

        x.right = b
        y.left = x

        RangeMap.__set_height(x)
        RangeMap.__set_height(y)

        return y

    @staticmethod
    def __right_rotate(x: TreeRangeNode) -> TreeRangeNode:
        """
                   x                                   y
               y      a            ->             z         x
            z    b                                        b   a
        """
        assert x is not None
        assert x.left is not None
        y, z, b = x.left, x.left.left, x.left.right

        x.left = b
        y.right = x

        RangeMap.__set_height(x)
        RangeMap.__set_height(y)

        return y


    @staticmethod
    def __right_left_rotate(root: TreeRangeNode) -> TreeRangeNode:
        root.right = RangeMap.__right_rotate(root.right)
        return RangeMap.__left_rotate(root)



    @staticmethod
    def __left_right_rotate(root: TreeRangeNode) -> TreeRangeNode:
        root.left = RangeMap.__left_rotate(root.left)
        return RangeMap.__right_rotate(root)

    @staticmethod
    def __get_left(root: TreeRangeNode | None) -> TreeRangeNode | None:
        return None if root is None else root.left

    @staticmethod
    def __get_right(root: TreeRangeNode | None) -> TreeRangeNode | None:
        return None if root is None else root.right

    @staticmethod
    def __balance(root: TreeRangeNode) -> TreeRangeNode:
        left_height = RangeMap.__get_height(root.left)
        right_height = RangeMap.__get_height(root.right)



        if left_height > right_height:  # L
            left_left_height = RangeMap.__get_height(RangeMap.__get_left(root.left))
            left_right_height = RangeMap.__get_height(RangeMap.__get_right(root.right))

            if left_left_height > left_right_height:  # LL
                root = RangeMap.__right_rotate(root)
            else:                                     # LR
                root = RangeMap.__left_right_rotate(root)

        else:                           #R
            right_left_height = RangeMap.__get_height(root.right.left)
            right_right_height = RangeMap.__get_height(root.right.right)

            if right_right_height > right_left_height: #RR
                root = RangeMap.__left_rotate(root)
            else:
                root = RangeMap.__right_left_rotate(root)
        RangeMap.__set_height(root)
        return root

    @staticmethod
    def __maintain(root: TreeRangeNode):
        left_height = RangeMap.__get_height(root.left)
        right_height = RangeMap.__get_height(root.right)

        root.beg = RangeMap.__left_limit(root, root.left)
        root.end = RangeMap.__right_limit(root, root.right)


        root.height = max(left_height, right_height) + 1


        if abs(left_height - right_height) > 1:
            root = RangeMap.__balance(root)



        return root

    @staticmethod
    def __dlr(root, dlr_handler = None, ldr_handler = None, lrd_handler = None):
        if root is None:
            return

        if dlr_handler is not None:
            dlr_handler(root, root.left, root.right)

        RangeMap.__dlr(root.left, dlr_handler, ldr_handler, lrd_handler)

        if ldr_handler is not None:
            ldr_handler(root, root.left, root.right)

        RangeMap.__dlr(root.right, dlr_handler, ldr_handler, lrd_handler)

        if lrd_handler is not None:
            dlr_handler(root, root.left, root.right)

    def __insert(self, root: TreeRangeNode, beg, end):
        if root is None:
            return TreeRangeNode(beg, end)
        if beg >= end:
            return root

        if beg < root.beg:      # root (1, 5): (0, 5) => (0, 1) (1, 5)  or (-1, 0) => (-1, 0) (1, 5)
            root.left = self.__insert(root.left, beg, min(root.beg, end))
        elif root.beg < beg < root.end:    # root (1, 5): (2, 7) => (1, 2) (2, 5) or (6, 7) => (1, 5) (6, 7)
            root.left = self.__insert(root.left, root.beg, beg)

        if root.beg < end < root.end:
            root.right = self.__insert(root.right, end, root.end)
        elif end > root.end:
            root.right = self.__insert(root.right, max(beg, root.end), end)

        return RangeMap.__maintain(root)

    def insert(self, beg, end):
        assert beg < end
        self.__root = self.__insert(self.__root, beg, end)


    def search(self, ele):
        root: TreeRangeNode = self.__root
        while root is not None and not root.beg <= ele < root.end:
            if ele > root.mid:
                root = root.right
            elif ele < root.mid:
                root = root.left
            else:
                break

        return root

    def dfs(self, dlr_handler = None, ldr_handler = None, lrd_handler = None):
        RangeMap.__dlr(self.__root, dlr_handler, ldr_handler, lrd_handler)

