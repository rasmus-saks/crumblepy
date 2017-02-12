import ast


class Parser:
    def __init__(self, file):
        self.root = ast.parse("\n".join(open(file).readlines()))
