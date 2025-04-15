import unittest

from common.work_priority_queue import WorkPriorityQueue


class TestWorkQueue(unittest.TestCase):
    def test(self):
        work_queue = WorkPriorityQueue(lambda x: len(x))
        work_queue.push(frozenset([1, 2, 3]), frozenset([1, 2]), frozenset([1, 2, 3, 5]), frozenset([1]))
        print(work_queue.pop())
        print(work_queue.pop())
        print(work_queue.pop())
        print(work_queue.pop())
