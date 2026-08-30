"""
日本語ネイティブ言語 v0.1 意味チェック層
--------------------------------------
「何が起きたか」という客観的な事実だけを Diagnostic として返す。
人間向けの文章化は display.py（教育・表示レイヤー）の責務。
"""
from dataclasses import dataclass, field
from enum import Enum

import ast_nodes as ast


class Severity(str, Enum):
    ERROR = "error"      # 実行しない
    WARNING = "warning"  # 実行はするが注意
    INFO = "info"        # 補足情報


@dataclass
class Diagnostic:
    kind: str                    # "duplicate_declaration" など
    severity: Severity
    target: str                  # 対象の名前
    span: ast.SourceSpan
    related_spans: list = field(default_factory=list)
    data: dict = field(default_factory=dict)


@dataclass
class LearningAnnotation:
    """将来の学習支援用。v0.1では空でもよい、仕組みだけ用意する。"""
    node_kind: str
    span: ast.SourceSpan
    concept: str


@dataclass
class AnalysisResult:
    diagnostics: list
    annotations: list = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(d.severity == Severity.ERROR for d in self.diagnostics)


class _Scope:
    """v0.1では関数がまだ無いため単一スコープだが、将来の入れ子に備えて
    「親スコープ」を持てる形にしておく。"""

    def __init__(self, parent: "_Scope | None" = None):
        self.parent = parent
        self.declared: dict[str, ast.SourceSpan] = {}   # 変数宣言(DeclareVariable)の名前
        self.known: set[str] = set()                     # 参照可能な名前(SetValueで作られたものも含む)

    def is_known(self, name: str) -> bool:
        if name in self.known:
            return True
        return self.parent.is_known(name) if self.parent else False


def analyze(program: ast.Program) -> AnalysisResult:
    diagnostics: list[Diagnostic] = []
    annotations: list[LearningAnnotation] = []
    scope = _Scope()

    def check_expr(node: ast.Node):
        if isinstance(node, ast.VarRef):
            if not scope.is_known(node.name):
                diagnostics.append(Diagnostic(
                    kind="undefined_name",
                    severity=Severity.ERROR,
                    target=node.name,
                    span=node.span,
                ))
        elif isinstance(node, (ast.BinOp, ast.Compare)):
            check_expr(node.left)
            check_expr(node.right)
        elif isinstance(node, ast.UnaryOp):
            check_expr(node.operand)
        # NumberLit / StringLit はチェック不要

    def check_stmt(node: ast.Node):
        if isinstance(node, ast.DeclareVariable):
            check_expr(node.value)
            if node.name in scope.declared:
                first_span = scope.declared[node.name]
                diagnostics.append(Diagnostic(
                    kind="duplicate_declaration",
                    severity=Severity.ERROR,
                    target=node.name,
                    span=node.span,
                    related_spans=[first_span],
                ))
            else:
                scope.declared[node.name] = node.span
                scope.known.add(node.name)

        elif isinstance(node, ast.SetValue):
            check_expr(node.value)
            scope.known.add(node.name)  # 無ければ作る、あれば更新

        elif isinstance(node, ast.Print):
            check_expr(node.value)

        elif isinstance(node, ast.If):
            check_expr(node.condition)
            for s in node.body:
                check_stmt(s)
            for s in node.orelse:
                check_stmt(s)

    for stmt in program.body:
        check_stmt(stmt)

    return AnalysisResult(diagnostics=diagnostics, annotations=annotations)
