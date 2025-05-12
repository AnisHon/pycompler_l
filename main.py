import re

from lex.lexer import Lexer


class Token:
    def __init__(self, kind, value, line_num):
        self.kind = kind
        self.value = value
        self.line_num = line_num

    def __str__(self):
        return f"[{self.line_num}]{self.kind}( {self.value} )"

    def __repr__(self):
        return f"\"{self.__str__()}\""

# 定义词法规则（正则表达式）
token_spec = [
    # 关键字（必须放在标识符前）
    ('KEYWORD', r'int|float|char|if|else|while|return'),
    # 数字（整数/浮点数）
    ('NUMBER', r'[0-9]+\.[0-9]+|[0-9]+'),
    # 运算符和分隔符
    ('OP', r'[+\-*/=<>!&|^%]'),
    ('SEPARATOR', r'[(),;{}]'),
    # 标识符
    ('ID', r'[a-zA-Z_][A-Za-z0-9_]*'),
    # 字符串和字符
    ('STRING', r'".*?"'),
    ('CHAR', r"'.'"),
    # 注释（直接忽略）
    # ('COMMENT', r'//.*|/\*[\s\S]*?\*/'),
    # 空白（忽略）
    # ('WHITESPACE', r'\s+'),
    # 预处理指令
    # ('PREPROCESSOR', r'#.*'),
    # 错误处理
    # ('ERROR', r'.')
]

lex = Lexer(token_spec)

print(len(lex.dfa.nodes))
print(lex.dfa.edges.__len__())


state = lex.origin




def match():
    idx = 0
    text = """
    """

    last_pos = 0
    last_state = lex.origin

    while idx < len(text):
        s = lex.dfa.range_map.search().meta
        state = lex.dfa.translate_to(state, s)
        if lex.dfa.nodes[state].accept:
            last_state = state
            last_pos = idx










