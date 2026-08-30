"""
v0.1 Release Candidate 自動テストスイート
--------------------------------------
正常系は「期待する標準出力」と一致するか、
エラー系は「意図した種類のエラーで止まるか」を確認する。
"""
import io
import sys
import contextlib
from pathlib import Path

from parser import parse, NihongoSyntaxError
from semantics import analyze
import codegen

EXAMPLES = Path(__file__).parent / "examples"


def run_source(source: str) -> str:
    """ソースを実行し、標準出力の文字列を返す(正常系専用)"""
    program = parse(source)
    result = analyze(program)
    if result.has_errors:
        raise AssertionError(f"予期せぬ意味エラー: {result.diagnostics}")
    py_code = codegen.generate(program)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(py_code, "<test>", "exec"), {})
    return buf.getvalue()


def read(name: str) -> str:
    return (EXAMPLES / name).read_text(encoding="utf-8")


def expect_output(name: str, expected: str):
    actual = run_source(read(name))
    assert actual == expected, f"{name}: 期待={expected!r} 実際={actual!r}"
    print(f"[OK] {name}")


def expect_diagnostic_kind(name: str, expected_kind: str):
    program = parse(read(name))
    result = analyze(program)
    kinds = [d.kind for d in result.diagnostics]
    assert expected_kind in kinds, f"{name}: {expected_kind} が診断結果に無い(実際: {kinds})"
    print(f"[OK] {name} -> {expected_kind}")


def expect_syntax_error(name: str):
    try:
        parse(read(name))
    except NihongoSyntaxError as e:
        assert e.line is not None, f"{name}: 構文エラーに行番号が無い"
        print(f"[OK] {name} -> 構文エラー({e.line}行{e.column}列)")
        return
    raise AssertionError(f"{name}: 構文エラーになるはずが解析できてしまった")


def main():
    failures = []

    def safe(fn, *args):
        try:
            fn(*args)
        except Exception as e:
            failures.append((args[0] if args else fn.__name__, str(e)))
            print(f"[NG] {args[0] if args else fn.__name__}: {e}")

    print("=== 正常系 ===")
    safe(expect_output, "hello.nj", "こんにちは\n")
    safe(expect_output, "example1.nj", "まだまだいける\n")          # SetValue + 日本語比較 + else
    safe(expect_output, "setvalue_update.nj", "10\n20\n")          # SetValueの更新
    safe(expect_output, "example2.nj", "3.0\n")                     # DeclareVariable + 記号比較 + 四則演算
    safe(expect_output, "example5.nj", "50歳以上です\n高齢者です\n")  # ifの入れ子
    safe(expect_output, "example6_no_indent.nj", "OK\n")             # インデント非依存
    safe(expect_output, "big_integer.nj", "9007199254740993\n")      # 大整数の精度
    safe(expect_output, "python_keyword_name.nj", "55\n100\n")       # Python予約語を変数名に使用
    safe(expect_output, "negative_number.nj", "-1500\n7\n")           # 負の数(単項マイナス)

    print("\n=== エラー系(意味チェック) ===")
    safe(expect_diagnostic_kind, "example3_error.nj", "duplicate_declaration")
    safe(expect_diagnostic_kind, "example4_error.nj", "undefined_name")

    print("\n=== エラー系(構文) ===")
    safe(expect_syntax_error, "syntax_error.nj")

    print()
    if failures:
        print(f"失敗: {len(failures)}件")
        for name, msg in failures:
            print(f"  - {name}: {msg}")
        sys.exit(1)
    else:
        print("全テスト成功")


if __name__ == "__main__":
    main()
