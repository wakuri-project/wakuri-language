"""
日本語ネイティブ言語 v0.1 Pythonコード生成
--------------------------------------
独自AST（意味チェック済み）を受け取り、Pythonソースコードへ変換する。
"""
import ast_nodes as ast


def _mangle(name: str) -> str:
    """ユーザーが書いた変数名をPython生成用の内部名に変換する。
    「if」のようなPython予約語が変数名として書かれても衝突しないよう、
    常に固定プレフィックスを付ける(予約語リストを個別に禁止するのではなく、
    構造的にすべての名前を安全な形へ変換する)。
    将来Python以外のバックエンドに変えた場合もこの層だけ差し替えればよい。
    """
    return f"v_{name}"


def _gen_expr(node: ast.Node) -> str:
    if isinstance(node, ast.VarRef):
        return _mangle(node.name)
    if isinstance(node, ast.NumberLit):
        # value は既にparser側でint/floatに正しく分類済みなので、そのままreprでよい
        return repr(node.value)
    if isinstance(node, ast.StringLit):
        return repr(node.value)
    if isinstance(node, ast.BinOp):
        return f"({_gen_expr(node.left)} {node.op} {_gen_expr(node.right)})"
    if isinstance(node, ast.UnaryOp):
        return f"({node.op}{_gen_expr(node.operand)})"
    if isinstance(node, ast.Compare):
        return f"({_gen_expr(node.left)} {node.op} {_gen_expr(node.right)})"
    raise ValueError(f"未対応の式ノードです: {node}")


def _gen_stmt(node: ast.Node, indent: int) -> list[str]:
    pad = "    " * indent

    if isinstance(node, ast.SetValue):
        return [f"{pad}{_mangle(node.name)} = {_gen_expr(node.value)}"]

    if isinstance(node, ast.DeclareVariable):
        return [f"{pad}{_mangle(node.name)} = {_gen_expr(node.value)}"]

    if isinstance(node, ast.Print):
        return [f"{pad}print({_gen_expr(node.value)})"]

    if isinstance(node, ast.If):
        lines = [f"{pad}if {_gen_expr(node.condition)}:"]
        for s in node.body:
            lines.extend(_gen_stmt(s, indent + 1))
        if node.orelse:
            lines.append(f"{pad}else:")
            for s in node.orelse:
                lines.extend(_gen_stmt(s, indent + 1))
        return lines

    raise ValueError(f"未対応の文ノードです: {node}")


def generate(program: ast.Program) -> str:
    lines: list[str] = []
    for stmt in program.body:
        lines.extend(_gen_stmt(stmt, 0))
    return "\n".join(lines) + "\n"
