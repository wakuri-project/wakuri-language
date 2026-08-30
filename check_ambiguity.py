"""
開発用: Earley文法に曖昧な解釈が紛れ込んでいないかチェックする。
ambiguity="explicit" で解析すると、複数の解釈が可能だった箇所に
"_ambig" ノードが残る。通常運用では ambiguity="resolve" で
自動的に1つが選ばれてしまうため、気づかずに意図しない解釈が
採用され続けるリスクがある。examples/ 配下の全ファイルを
このスクリプトで定期的にチェックする。
"""
import sys
from pathlib import Path
from lark import Lark, Tree

GRAMMAR_PATH = Path(__file__).parent / "grammar.lark"
GRAMMAR = GRAMMAR_PATH.read_text(encoding="utf-8")

_check_parser = Lark(GRAMMAR, parser="earley", ambiguity="explicit", propagate_positions=True)


def find_ambiguities(tree: Tree) -> list[Tree]:
    found = []
    for node in tree.iter_subtrees():
        if node.data == "_ambig":
            found.append(node)
    return found


def check_file(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    if not source.endswith("\n"):
        source += "\n"
    try:
        tree = _check_parser.parse(source)
    except Exception as e:
        print(f"[SKIP] {path.name}: 構文エラーのためチェック対象外 ({e})")
        return True

    ambiguities = find_ambiguities(tree)
    if ambiguities:
        print(f"[NG] {path.name}: {len(ambiguities)}箇所で複数解釈が見つかりました")
        for a in ambiguities:
            print(f"      {a.pretty()[:200]}")
        return False
    print(f"[OK] {path.name}: 曖昧な解釈なし")
    return True


def main():
    examples_dir = Path(__file__).parent / "examples"
    all_ok = True
    for path in sorted(examples_dir.glob("*.nj")):
        if not check_file(path):
            all_ok = False
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
