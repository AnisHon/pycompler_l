import re

from lex.lexer import Lexer


class Token:
    def __init__(self, kind, value, line_num):
        self.kind = kind
        self.value = value
        self.line_num = line_num

    def __str__(self):
        return f"[{self.line_num}]{self.kind}( {self.value.__repr__()} )"

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
    ('STRING', r'"[^"]*"'),
    ('CHAR', r"'[^']'"),
    # 注释（直接忽略）
    # ('COMMENT', r'//.*|/\*[\s\S]*?\*/'),
    # 空白（忽略）
    ('WHITESPACE', r' +'),
    # 预处理指令
    # ('PREPROCESSOR', r'#.*'),
    # 错误处理
    # ('ERROR', r'.')
]

lex = Lexer(token_spec)

# print(len(lex.dfa.nodes))
# print(lex.dfa.edges.__len__())

# state = lex.origin
# for c in '"asdf"    ':
#     s = lex.dfa.range_map.search(c).meta
#     state = lex.dfa.translate_to(state, s)
#     print( lex.dfa.nodes[state])


def match(text: str):
    line_num = 0
    idx = 0

    state = lex.origin
    last_pos = None
    last_state = None
    start_pos = None

    result: list[Token] = []
    total_size = 0

    for line_num, line in enumerate(text.splitlines(keepends=True)):
        total_size += len(line)
        # print(total_size)
        while idx < total_size:
            c = text[idx]
            if c == '\n':
                c = ' '

            s = lex.dfa.range_map.search(c).meta
            state = lex.dfa.translate_to(state, s)



            if state is None:
                if last_state is None:
                    raise RuntimeError(f"Unexpected character {c} at line {line_num}:\n {line}\n" + "-" * (idx - total_size + len(line) + 1) + "|")

                label = lex.dfa.nodes[last_state].label
                result.append(Token(label, text[start_pos:last_pos+1], line_num))
                start_pos = last_pos + 1
                state = lex.origin
                idx = last_pos
                last_state = None


            if lex.dfa.nodes[state].accept:
                # print( lex.dfa.nodes[state])
                last_state = state
                last_pos = idx

            idx += 1


    if state is not None and lex.dfa.nodes[state].accept:
        label = lex.dfa.nodes[state].label
        result.append(Token(label, text[start_pos:last_pos+1], line_num))
        state = lex.origin

    if state is not None and state != lex.origin:
        raise RuntimeError(f"Unknown: {text[last_pos:]}")

    return result



with open("main.c", mode="r+", encoding="utf-8") as f:
    # print(f.readlines())
    text = "".join(f.readlines())
    tokens = match(text)

    tokens = filter(lambda t: t.kind != 'WHITESPACE', tokens)

    for token in tokens:
        print(token)