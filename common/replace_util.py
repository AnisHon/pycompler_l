
class ReplaceUtil:
    def __init__(self):
        self.__replacement = {}

    def add_replace(self, origin, replace):
        self.__replacement[origin] = replace
        return self

    def replace(self, content):
        if content in self.__replacement:
            return self.__replacement[content]
        return content
