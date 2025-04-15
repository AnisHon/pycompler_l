import heapq
from collections.abc import Hashable

class WorkPriorityQueue:

    EntryType = tuple[int, Hashable, bool]

    def __init__(self, priority=lambda x: x):
        self.__working_queue = []
        self.__track = {}
        self.__priority = priority

    def push(self, *items: Hashable):
        for item in items:
            if item in self.__track:
                continue

            entry: WorkPriorityQueue.EntryType = (self.__priority(item), item, True)
            heapq.heappush(self.__working_queue, entry)
            self.__track[item] = entry

    def remove(self, item: Hashable):
        if item in self.__track:
            self.__track[item][-1] = False
            del self.__track[item]

        else:
            raise KeyError(item)

    def pop(self):
        while self.__working_queue :
            entry: WorkPriorityQueue.EntryType = heapq.heappop(self.__working_queue)
            if not entry[-1]:
                continue

            item = entry[1]

            if item in self.__track:
                del self.__track[item]

            return item

        return None

    def __bool__(self):
        return bool(self.__working_queue)

    def __contains__(self, item):
        return item in self.__track
