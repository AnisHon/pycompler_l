import re


class Token:
    def __init__(self, kind, value, line_num):
        self.kind = kind
        self.value = value
        self.line_num = line_num

    def __str__(self):
        return f"[{self.line_num}]{self.kind}( {self.value} )"

    def __repr__(self):
        return f"\"self.__str__()\""

# 定义词法规则（正则表达式）
token_spec = [
    # 关键字（必须放在标识符前）
    ('KEYWORD', r'\b(int|float|char|if|else|while|return)\b'),
    # 数字（整数/浮点数）
    ('NUMBER', r'\d+\.\d+|\d+'),
    # 运算符和分隔符
    ('OP', r'[+\-*/=<>!&|^%]'),
    ('SEPARATOR', r'[(),;{}]'),
    # 标识符
    ('ID', r'[a-zA-Z_]\w*'),
    # 字符串和字符
    ('STRING', r'\".*?\"'),
    ('CHAR', r'\'.\''),
    # 注释（直接忽略）
    ('COMMENT', r'//.*|/\*[\s\S]*?\*/'),
    # 空白（忽略）
    ('WHITESPACE', r'\s+'),
    # 预处理指令
    ('PREPROCESSOR', r'#.*'),
    # 错误处理
    ('ERROR', r'.')
]

# 编译正则表达式
token_re = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_spec))


def tokenize(code):
    tokens = []
    line_num = 1
    for mo in token_re.finditer(code):
        kind = mo.lastgroup
        value = mo.group()

        # 处理换行
        if '\n' in value:
            line_num += value.count('\n')
            continue

        # 跳过注释和空白
        if kind in ['COMMENT', 'WHITESPACE']:
            continue

        # 错误处理
        if kind == 'ERROR':
            raise ValueError(f'第 {line_num} 行出现非法字符: {value}')

        tokens.append(Token(kind, value, line_num))

    return tokens


# 测试示例
code = '''
int main() {
    int x = 123;
    float y = 3.14;
    char c = 'a';
    return 0;
}
'''

for token in tokenize(code):
    print(f"{token}")