
class ReplaceUtil:
    def __init__(self):
        self.__replacement = []

    def add_replace(self, origin, replace):
        self.__replacement.append((origin, replace))
        return self

    def replace(self, content):
        for (origin, replace) in self.__replacement:
            if content == origin:
                return replace
        return content
