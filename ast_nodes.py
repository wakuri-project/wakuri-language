"""
日本語ネイティブ言語 v0.1 独自AST定義
--------------------------------------
Lark Parse Treeとは別に持つ、意味を正規化したASTノード群。
例えば `年齢 >= 50` と `年齢 が 50 以上` は表記が違っても
同じ Compare(op=">=", ...) ノードになる。
"""
from dataclasses import dataclass, field


@dataclass
class SourceSpan:
    """元のソースコード上の位置。エラー表示・エディタ連携・将来の学習注釈に使う。"""
    line: int
    column: int
    end_line: int
    end_column: int


@dataclass
class Node:
    span: SourceSpan


# ---- 式 ----

@dataclass
class NumberLit(Node):
    # 小数点が無ければ int、あれば float として保持する。
    # すべて float 化すると大きな整数(例: 9007199254740993)が
    # IEEE754の丸めで精度を失うため、リテラルの見た目で型を分ける。
    value: int | float


@dataclass
class StringLit(Node):
    value: str


@dataclass
class VarRef(Node):
    name: str


@dataclass
class BinOp(Node):
    op: str  # '+' '-' '*' '/'
    left: Node
    right: Node


@dataclass
class UnaryOp(Node):
    op: str  # '-'
    operand: Node


@dataclass
class Compare(Node):
    op: str  # '>=' '<=' '>' '<' '==' '!='
    left: Node
    right: Node


# ---- 文 ----

@dataclass
class SetValue(Node):
    """やさしい代入: 年齢 を 55 とする"""
    name: str
    value: Node


@dataclass
class DeclareVariable(Node):
    """学習構文: 変数 年齢 = 55"""
    name: str
    value: Node


@dataclass
class Print(Node):
    """式 を 表示する"""
    value: Node


@dataclass
class If(Node):
    condition: Node
    body: list
    orelse: list = field(default_factory=list)


@dataclass
class Program(Node):
    body: list
