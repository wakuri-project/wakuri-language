import sys
from pathlib import Path

from parser import parse, NihongoSyntaxError
from semantics import analyze, Severity
from display import format_diagnostic
import codegen


def run_file(path: Path, show_python: bool = False):
    source = path.read_text(encoding="utf-8")

    try:
        program = parse(source)
    except NihongoSyntaxError as e:
        print("構文エラー")
        if e.line is not None:
            print(f"{e.line}行目 {e.column}文字目付近")
        print(e.message)
        sys.exit(1)

    result = analyze(program)

    if result.diagnostics:
        for diag in result.diagnostics:
            print(f"--- {diag.severity.value} ---")
            print(format_diagnostic(diag))
            print()

    if result.has_errors:
        print("意味エラーがあるため実行を中止しました。")
        sys.exit(1)

    py_code = codegen.generate(program)
    if show_python:
        print("---- 変換されたPythonコード ----")
        print(py_code)
        print("---- 実行結果 ----")

    exec(compile(py_code, str(path), "exec"), {})


def main():
    if len(sys.argv) < 2:
        print("使い方: python3 main.py <ファイル.nj> [--show-python]")
        sys.exit(1)
    run_file(Path(sys.argv[1]), show_python="--show-python" in sys.argv)


if __name__ == "__main__":
    main()
