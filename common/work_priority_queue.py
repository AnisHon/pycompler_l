import heapq
from collections.abc import Hashable

class WorkPriorityQueue:

    EntryType = tuple[int, Hashable]

    def __init__(self, priority=lambda x: x):
        self.__working_queue = []
        self.__track = {}
        self.__priority = priority

    def push(self, *items: Hashable):
        for item in items:
            if item in self.__track:
                continue

            entry: WorkPriorityQueue.EntryType = (self.__priority(item), item)
            heapq.heappush(self.__working_queue, entry)
            self.__track[item] = True

    def remove(self, item: Hashable):
        if item in self.__track:
            self.__track[item] = False

        else:
            raise KeyError(item)

    def pop(self):
        while self.__working_queue :
            entry: WorkPriorityQueue.EntryType = heapq.heappop(self.__working_queue)


            item = entry[1]

            if not self.__track[item]:
                continue

            if item in self.__track:
                del self.__track[item]

            return item

        return None

    def __repr__(self):
        queue = list(filter(lambda x: self.__track[x[1]], self.__working_queue))
        queue.sort(key=lambda x: x[0])

        return list(map(lambda x: x[1], queue)).__repr__()


    def __bool__(self):
        return bool(self.__working_queue)

    def __contains__(self, item):
        if item in self.__track:
            return self.__track[item]
        else:
            return False
