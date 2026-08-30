# 日本語ネイティブ・プログラミング言語 v0.1 Release Candidate

## 1. 最終確認結果(依頼のあった5項目)

### ① 仕様と実装の一致
以下すべて実装・動作確認済み。

| 項目 | 状態 |
|---|---|
| SetValue(`年齢 を 55 と する`) | ✅ |
| DeclareVariable(`変数 年齢 = 55`) | ✅ |
| SOV表示(`式 を 表示する`) | ✅ |
| 四則演算(`+ - * /`) | ✅ |
| 日本語比較(`が〜以上/以下/より大きい/未満/と等しい/と等しくない`) | ✅ |
| 記号比較(`>= <= > < == !=`) | ✅ |
| if / else | ✅ |
| 「終わり」必須 | ✅ |
| インデント非依存 | ✅ (example6_no_indent.njで確認) |
| `#`コメント | ✅ |
| 動的型 | ✅ |
| 二重宣言 → コンパイル時error | ✅ |
| 未定義名 → コンパイル時error | ✅ |
| SourceSpan | ✅ (AST・構文エラー両方に付与) |
| Diagnosticと表示層の分離 | ✅ (semantics.py / display.py) |

### ② 名前変換層
`v_`プレフィックスを1回だけ付ける単射な変換なので、異なる元の名前が衝突することは構造上ありません(`年齢→v_年齢`、`v_年齢→v_v_年齢`のように別名になる)。Python予約語(`if`, `class`等)を使っても衝突しないことをテストで確認済みです。将来Python以外のバックエンドに差し替える場合も、`codegen.py`の`_mangle()`関数だけを差し替えれば済む設計です。

### ③ Earley曖昧性
`check_ambiguity.py`で全10正常系サンプルを`ambiguity="explicit"`で解析し、`_ambig`ノードが1つも出ないことを確認しました。構文エラーを含むファイルはチェック対象外(構文エラー自体が先に出るため)。今後、新しい文法(繰り返し・関数など)を追加するたびに、このチェックを通す運用にします。

### ④ 構文エラーの位置情報
`NihongoSyntaxError`は`line`/`column`を保持するようになりました。例:

```
構文エラー
1行目 7列目付近
文法として解釈できませんでした: ...
```

矢印表示等は今回見送り、v0.2以降で検討します。

### ⑤ テスト
`test_v01.py`に自動テストを整備し、以下すべてパスしました。

- 正常系: Hello / SetValue / DeclareVariable / SetValue更新 / 四則演算 / 日本語比較 / 記号比較 / if / else / 入れ子 / インデント崩し / 大整数 / Python予約語変数名
- エラー系: 二重宣言 / 未定義名 / 構文エラー

```
全テスト成功
```

---

## 2. v0.1でできること

- 数値(int/float)・文字列を扱える
- `年齢 を 55 と する`(SetValue)と`変数 年齢 = 55`(DeclareVariable)の2つの代入構文を、意味を分けて使い分けられる
- 四則演算・比較(記号形式/日本語形式どちらも)ができる
- if / そうでなければ / 終わり による条件分岐(入れ子可能)ができる
- インデントを崩しても、「終わり」さえ正しければ動く
- 二重宣言・未定義名を、コンパイル時に教育的な文章で教えてくれる
- 大きな整数でも精度が落ちない
- Python予約語を変数名に使っても安全に動く
- 生成されたPythonコードを見ることができる(`--show-python`)

## 3. v0.1でできないこと(意図的にv0.2以降へ)

- 繰り返し(ループ)
- 関数
- 日本語学習モード(思想としては採用済みだが未実装)
- LearningAnnotationの本格実装(仕組みの箱だけ用意、中身は空)
- Web版 / LSP / エディタ連携
- 他言語バックエンド(Python以外への変換)
- 新しい助詞構文(動詞ごとの助詞マップの本格運用)
- 外側スコープの明示的書き換え(`外の 年齢 を 60 とする`等)
- 型変更警告(型は変わってもエラーにも警告にもならない、まだ)

## 4. ファイル一覧

```
nihongo_v01/
├── grammar.lark          文法定義(Earleyパーサー用)
├── ast_nodes.py           独自ASTノード定義
├── parser.py               Lark Tree → AST変換
├── semantics.py            意味チェック層(Diagnostic生成)
├── display.py               教育・表示レイヤー(文章化)
├── codegen.py                AST → Pythonコード生成
├── main.py                    CLI
├── check_ambiguity.py          曖昧性監視スクリプト
├── test_v01.py                  自動テストスイート
└── examples/
    ├── hello.nj
    ├── example1.nj              (SetValue+日本語比較+else)
    ├── example2.nj              (DeclareVariable+記号比較+四則演算+コメント)
    ├── example3_error.nj        (二重宣言)
    ├── example4_error.nj        (未定義名)
    ├── example5.nj               (ifの入れ子)
    ├── example6_no_indent.nj     (インデント非依存)
    ├── setvalue_update.nj        (SetValue更新)
    ├── big_integer.nj             (大整数)
    ├── python_keyword_name.nj      (Python予約語変数名)
    └── syntax_error.nj             (構文エラー)
```
