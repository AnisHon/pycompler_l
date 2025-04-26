import abc
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from lex.lexer import Lexer


class LexerBuilder(ABC):
    """
    分层DFA
    """
    def __init__(self):
        self.lexer = self.__parse()

    def _pattern(self):
        text = tuple(map(lambda x: (x[0].upper(), x[1]), self.text.items()))
        # literal = tuple(map(lambda x: (x[0].upper(), x[1]), self.literal.items()))
        pattern_group = [
            ("COMMENT", "|".join(map(lambda x: f"({x})", self.comment))),
            ("SPACE", "|".join(map(lambda x: f"({x})", self.space))),
            *text,
            (f"KEYWORD", "|".join(self.keywords)),
            # *literal,
            (f"OP", "|".join(self.operators.values())),
            ("BRACKET", "|".join(map(lambda x: f"\\{x}", self.brackets.values())))
        ]
        for k, v in self.other.items():
            pattern_group.append((f"{k.upper()}", v))

        pattern_group.append(("SEPARATOR", "|".join(map(lambda x: f"({x})", self.sep))))
        print(pattern_group)
        return pattern_group


    def __parse(self):
        pattern_group = self._pattern()
        return Lexer(pattern_group=pattern_group, minimization=False)



    def tokens(self) -> tuple[str, ...]:

        text = tuple("|".join(map(lambda x: f"({x})", self.text)))
        keyword = tuple(map(lambda x: f"KEYWORD_{x.upper()}", self.keywords))
        literal = tuple(map(lambda x: x.upper(), self.literal))
        operator = tuple(map(lambda x: f"OPERATOR_{x.upper()}", self.operators))
        brackets = tuple(map(lambda x: x.upper(), self.brackets))
        other = tuple(map(lambda x: x.upper(), self.other))

        return "COMMENT", "SPACE", *text, *literal, *keyword, *operator, *brackets, *other, "SEPARATOR"

    @property
    @abstractmethod
    def comment(self) -> tuple[str, ...]:
        pass

    @property
    @abstractmethod
    def space(self) -> tuple[str, ...]:
        pass

    @property
    @abstractmethod
    def text(self) -> dict[str, str]:
        pass

    @property
    @abstractmethod
    def literal(self) -> dict[str, str]:
       pass

    @property
    def sep(self) -> tuple[str, ...]:
        return ";",

    @property
    @abstractmethod
    def keywords(self) -> tuple[str, ...]:
        pass

    @property
    @abstractmethod
    def operators(self) -> dict[str, str]:
        pass

    @property
    @abstractmethod
    def brackets(self) -> dict[str, str]:
        pass

    @property
    @abstractmethod
    def other(self):
        pass


class CLexerBuilder(LexerBuilder):
    def __init__(self):
        super().__init__()

    @property
    def keywords(self) -> tuple[str, ...]:
        keywords: tuple[str, ...] = (
            'auto', 'break', 'case', 'char',
            'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern',
            'float', 'for', 'goto', 'if',
            'int', 'long', 'register', 'return',
            'short', 'signed', 'sizeof', 'static',
            'struct', 'switch', 'typedef', 'union',
            'unsigned', 'void', 'volatile', 'while'
        )
        return keywords

    @property
    def operators(self) -> dict[str, str]:
        operators: dict[str, str] = {
            "add": "\\+", "sub": "-",  "mul ": "\\*", "div": "\\/", "mod": "%",  "inc": "\\+\\+", "dec": "--",
            "equ": "==", "ieq": "!=", "gt": ">", "lt": "<",  "ge": ">=", "le": "<=",
            "logical_not": "!",  "logical_and": "&&",  "logical_or": "\\|\\|",
            "bitwise_and":"&", "bitwise_or" :"\\|",  "x_or": "^", "bitwise_not": "~", "shl": "<<",  "shr": ">>",
            "assign": "=", "add_assign": "\\+=",  "sub_assign": "-=",  "mul_assign": "\\*=",  "div_assign": "/=", "mod_assgin": "%=", "and_assign": "&=", "or_assign": "\\|=", "xor_assign": "^=", "not_assign": "!=", "shl_assign": "<<=", "shr_assign": ">>=",
            "dot": "\\.", "arrow": "->", "comma": ",", "question": "\\?", "colon": ":", "sizof": "sizeof"
        }
        return operators
    #
    @property
    def brackets(self) -> dict[str, str]:
        brackets: dict[str, str] = {
            "l_paren":"(",
            "r_paren": ")",
            "l_bracket": "[",
            "r_bracket": "]",
            "l_brace": "{",
            "r_brace": "}"
        }
        return brackets

    @property
    def comment(self) -> tuple[str, ...]:
        return "(//[^\n]*)", "/\*.*?\*/"

    @property
    def space(self) -> tuple[str, ...]:
        return ("[ \t\n\r\v\f]+", )

    @property
    def text(self) -> dict[str, str]:
        return {
            "string": r'"[^"]*"',
            "char": r"'[^']*'",
        }

    @property
    def literal(self) -> dict[str, str]:
        return {
            "hex_integer": r"0[xX][0-9a-fA-F]+[uU]?",
            "oct_integer": r"0[0-7]+[uU]?",
            "integer": r"(0|[1-9][0-9]*)[uU]?",
            "float_": r"[0-9]+\.[0-9]+[eE][+-]?[0-9]+",
            "float": r"[0-9]+\.[0-9]+",
        }


    @property
    def sep(self) -> tuple[str, ...]:
        return ";",

    @property
    def other(self) -> dict[str, str]:
        other: dict[str, str] = {
            "omit": r"\.\.\.",
            "identifier": r"[a-zA-Z_][a-zA-Z0-9_]*",
        }
        return other

@dataclass(frozen=True)
class LayeringPatten:
    typ: str
    prefix: tuple[str, ...]
    detail: dict[str, str]
    comment: str
    ignore: bool = field(default=False)

class LayeringLexerBuilder(abc.ABC):
    def __init__(self):
        outer, inner_lex, ignore = self._compile()
        self.outer = outer
        self.inner_dfa = inner_lex
        self.ignore = ignore

    def _compile(self):
        pattens = self.get_pattens()
        outer = {}
        ignore = set()
        inner_dfa = {}
        for patten in pattens:
            if patten.ignore:
                ignore.add(patten.typ.upper())
            typ = f"DFA_{patten.typ.upper()}"
            outer[typ] = patten.prefix
            patten_group = [(k.upper(), v) for k, v in patten.detail.items()]
            if not patten_group:
                inner_dfa[typ] = None
            inner_dfa[typ] = Lexer(patten_group)
        return outer, inner_dfa, ignore






    @abc.abstractmethod
    def get_pattens(self) -> list[LayeringPatten]:
        pass

class CLayeringLexerBuilder(LayeringLexerBuilder):
    """
    分层DFA极其高效，加起来不到300个点，不到500条边
    """
    def __init__(self):
        super().__init__()



    def get_pattens(self) -> list[LayeringPatten]:
        key_id = {f"keyword_{item}": item for item in self.keywords}
        key_id.update({f"keyword_{item}": item for item in self.keywords})

        op = {f"op_{k}": v for k, v in self.operators.items()}
        op.update({k: f"\\{v}" for k, v in self.brackets.items()})
        op_prefix = set()
        for v in op.values():
            op_prefix.update(v)

        op_prefix.remove("\\")

        return [
            LayeringPatten(
                typ="hex_oct_flo_int",
                prefix=("0", ),
                detail={
                    "integer": r"0",
                    "hex_integer": r"0[xX][0-9a-fA-F]*",
                    "unsigned_hex_integer": r"0[xX][0-9a-fA-F]*[uU]",
                    "oct_integer": r"0[0-7]+",
                    "unsigned_oct_integer": r"0[0-7]*[uU]",
                    "float_": r"0[0-9]*\.[0-9]+[eE][+-]?[0-9]+",
                    "float": r"0[0-9]*\.[0-9]+",
                },
                comment="hex oct float 0",
            ),
            LayeringPatten(
                typ="int_flo",
                prefix=("1-9", ),
                detail={
                    "integer": r"[1-9][0-9]*",
                    "unsigned_integer": r"[1-9][0-9]*[uU]",
                    "float_": r"[1-9][0-9]*\.[0-9]+[eE][+-]?[0-9]+",
                    "float": r"[1-9][0-9]*\.[0-9]+",
                },
                comment="int float",
            ),
            LayeringPatten(
                typ="Operator",
                prefix=tuple(op_prefix),
                detail=op,
                comment="Operator",
            ),
            LayeringPatten(
                typ="key_id",
                prefix=("a-z", "A-Z", "_"),
                detail=key_id,
                comment="keyword identifier"
            ),
            LayeringPatten(
                typ="string",
                prefix=('"', ),
                detail={
                    "end": '"',
                    "new_line": r"\\n",
                    "back": r"\\r",
                    "char": '.',
                },
                comment="string",
            ),
            LayeringPatten(
                typ="char",
                prefix=("'", ),
                detail={
                    "char": ".",
                },
                comment="char",
            ),
            LayeringPatten(
                typ="space",
                prefix=("\n", "\t", "\r", "\v", "\f"),
                detail={},
                ignore=True,
                comment="\\n\\t...",
            ),
            LayeringPatten(
                typ="comment",
                prefix=("//", "/*"),
                detail={
                    "comment": "/\\*.*\\*/",
                    "comment2": "//.*\n",
                },
                ignore=True,
                comment="comment",
            ),
            LayeringPatten(
                typ="terminate",
                prefix=(";", ),
                detail={},
                ignore=True,
                comment="sep",
            ),
            LayeringPatten(
                typ="identifier",
                prefix=("a", ),
                detail={
                    "identifier": "[a-zA-Z_][a-zA-Z0-9_]*",
                },
                comment="identifier",
            )
        ]

    @property
    def keywords(self) -> tuple[str, ...]:
        return (
            'auto', 'break', 'case', 'char',
            'const', 'continue', 'default', 'do',
            'double', 'else', 'enum', 'extern',
            'float', 'for', 'goto', 'if',
            'int', 'long', 'register', 'return',
            'short', 'signed', 'sizeof', 'static',
            'struct', 'switch', 'typedef', 'union',
            'unsigned', 'void', 'volatile', 'while'
        )

    @property
    def operators(self) -> dict[str, str]:
        return {
            "add": "\\+", "sub": "-",  "mul ": "\\*", "div": "\\/", "mod": "%",  "inc": "\\+\\+", "dec": "--",
            "equ": "==", "ieq": "!=", "gt": ">", "lt": "<",  "ge": ">=", "le": "<=",
            "logical_not": "!",  "logical_and": "&&",  "logical_or": "\\|\\|",
            "bitwise_and":"&", "bitwise_or" :"\\|",  "x_or": "^", "bitwise_not": "~", "shl": "<<",  "shr": ">>",
            "assign": "=", "add_assign": "\\+=",  "sub_assign": "-=",  "mul_assign": "\\*=",  "div_assign": "/=", "mod_assgin": "%=", "and_assign": "&=", "or_assign": "\\|=", "xor_assign": "^=", "not_assign": "!=", "shl_assign": "<<=", "shr_assign": ">>=",
            "dot": "\\.", "arrow": "->", "comma": ",", "question": "\\?", "colon": ":", "sizof": "sizeof"
        }

    @property
    def brackets(self) -> dict[str, str]:
        return {
            "l_paren":"(",
            "r_paren": ")",
            "l_bracket": "[",
            "r_bracket": "]",
            "l_brace": "{",
            "r_brace": "}"
        }

    @property
    def comment(self) -> tuple[str, ...]:
        return "(//[^\n]*)", "/\*.*?\*/"

    @property
    def literal(self):
        return {
            "string": r'"[^"]*"',
            "char": r"'[^']*'",
        }

