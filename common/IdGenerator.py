def id_generator(init: int = 0):
    while True:
        yield init
        init += 1

