"""
日本語ネイティブ言語 v0.1 教育・表示レイヤー
--------------------------------------
意味チェック層が返した客観的な Diagnostic を、対象読者向けの文章に変換する。
「事実を見つける」(semantics.py)と「言葉にする」(このファイル)を分離することで、
将来モードを増やすときにこのファイルだけを触れば済むようにする。
"""
from semantics import Diagnostic

_TEMPLATES = {
    "duplicate_declaration": {
        "学習モード": (
            '二重宣言エラー(行{line})\n'
            '「{target}」はすでに作られています。\n'
            '値を変更したい場合は\n'
            '    {target} を ... と する\n'
            'と書けます。\n'
            '学習メモ: 新しく変数を作ることを「宣言」、既存の値を変更することを「代入」と呼びます。'
        ),
        "経験者向け": "Duplicate declaration: {target} (line {line})",
    },
    "undefined_name": {
        "学習モード": (
            '未定義の名前エラー(行{line})\n'
            '「{target}」という名前はまだ作られていません。\n'
            '先に\n'
            '    {target} を ... と する\n'
            'または\n'
            '    変数 {target} = ...\n'
            'と書いて値を作ってから使ってください。'
        ),
        "経験者向け": "Undefined name: {target} (line {line})",
    },
}


def format_diagnostic(diag: Diagnostic, mode: str = "学習モード") -> str:
    templates = _TEMPLATES.get(diag.kind)
    if templates is None:
        return f"[{diag.kind}] {diag.target} (行{diag.span.line})"
    template = templates.get(mode, templates.get("学習モード"))
    return template.format(target=diag.target, line=diag.span.line)
