"""
日本語ネイティブ言語 v0.1 パーサー
--------------------------------------
日本語ソース -> Lark Parse Tree -> 独自AST(SourceSpan付き)
「書き方の違い」(記号形式/日本語形式の比較など)を、ここで正規化する。
"""
from pathlib import Path
from lark import Lark, Token, Tree, UnexpectedInput

import ast_nodes as ast

GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"
GRAMMAR = GRAMMAR_PATH.read_text(encoding="utf-8")

# LALR(1)では「NAME を」で始まる文が assign_stmt(NAME を 式 と する) なのか
# print_stmt(式 を 表示する、のexprが単なる変数名の場合)なのかを1トークン先読みでは
# 判別できず、reduce/reduce競合が起きる。助詞主導の日本語文は今後も
# 同じ形の曖昧さが増えていく見込みなので、v0.1からEarleyパーサーを採用する。
_parser = Lark(GRAMMAR, parser="earley", ambiguity="resolve", propagate_positions=True)


class NihongoSyntaxError(Exception):
    """文法として正しくない場合のエラー(意味チェック層のDiagnosticとは区別する)"""
    def __init__(self, message: str, line: int | None = None, column: int | None = None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column


_JP_CMP_MAP = {
    "cmp_ge": ">=",
    "cmp_le": "<=",
    "cmp_gt": ">",
    "cmp_lt": "<",
    "cmp_eq": "==",
    "cmp_ne": "!=",
}


def _span_of(node) -> ast.SourceSpan:
    if isinstance(node, Token):
        return ast.SourceSpan(node.line, node.column, node.end_line, node.end_column)
    meta = node.meta
    return ast.SourceSpan(meta.line, meta.column, meta.end_line, meta.end_column)


def _build_expr(node) -> ast.Node:
    if isinstance(node, Token):
        # NAME/NUMBER/STRINGがトークンのまま渡ってくることはない想定だが念のため
        return ast.VarRef(_span_of(node), str(node))

    span = _span_of(node)
    data = node.data

    if data == "var":
        return ast.VarRef(span, str(node.children[0]))
    if data == "number":
        raw = str(node.children[0])
        # 小数点(または指数表記)が無ければintとして保持し、精度落ちを防ぐ
        if any(c in raw for c in ".eE"):
            value = float(raw)
        else:
            value = int(raw)
        return ast.NumberLit(span, value)
    if data == "string":
        # 前後の引用符を取り除く
        raw = str(node.children[0])
        return ast.StringLit(span, raw[1:-1])
    if data in ("add", "sub", "mul", "div"):
        op = {"add": "+", "sub": "-", "mul": "*", "div": "/"}[data]
        left, right = node.children
        return ast.BinOp(span, op, _build_expr(left), _build_expr(right))
    if data == "neg":
        (operand,) = node.children
        return ast.UnaryOp(span, "-", _build_expr(operand))
    if data == "cmp_symbol":
        left, op_token, right = node.children
        return ast.Compare(span, str(op_token), _build_expr(left), _build_expr(right))
    if data in _JP_CMP_MAP:
        left, right, _jp_token = node.children
        return ast.Compare(span, _JP_CMP_MAP[data], _build_expr(left), _build_expr(right))

    raise NihongoSyntaxError(f"未対応の式です: {data}")


def _build_stmt(node: Tree) -> ast.Node:
    span = _span_of(node)

    if node.data == "assign_stmt":
        name_token, expr_node = node.children
        return ast.SetValue(span, str(name_token), _build_expr(expr_node))

    if node.data == "print_stmt":
        (expr_node,) = node.children
        return ast.Print(span, _build_expr(expr_node))

    if node.data == "declare_stmt":
        name_token, expr_node = node.children
        return ast.DeclareVariable(span, str(name_token), _build_expr(expr_node))

    if node.data == "if_stmt":
        condition = _build_expr(node.children[0])
        body = []
        orelse = []
        for child in node.children[1:]:
            if isinstance(child, Tree) and child.data == "else_block":
                orelse = [_build_stmt(s) for s in child.children]
            else:
                body.append(_build_stmt(child))
        return ast.If(span, condition, body, orelse)

    raise NihongoSyntaxError(f"未対応の文です: {node.data}")


def parse(source: str) -> ast.Program:
    if not source.endswith("\n"):
        source += "\n"
    try:
        tree = _parser.parse(source)
    except UnexpectedInput as e:
        # UnexpectedToken/UnexpectedCharacters は line/column を持つ。
        # 将来「3行目 8文字目 ↑ここを確認してください」のような表示に使えるよう、
        # 例外オブジェクト側にも位置情報を残しておく。
        line = getattr(e, "line", None)
        column = getattr(e, "column", None)
        raise NihongoSyntaxError(
            f"文法として解釈できませんでした: {e}", line=line, column=column
        ) from e

    body = [_build_stmt(stmt) for stmt in tree.children]
    span = ast.SourceSpan(1, 0, len(source.splitlines()) or 1, 0)
    return ast.Program(span, body)
