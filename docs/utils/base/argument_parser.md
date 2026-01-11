# InteractiveArgumentParser

[Index](./index.md) > `utils.base.argument_parser`

```python
class utils.base.argument_parser.InteractiveArgumentParser(*args, **kwargs)
```

Bases: `argparse.ArgumentParser`

`argparse.ArgumentParser` を拡張し、引数が指定されなかった場合、または指定された値が不正な場合に対話的に入力を求めるクラス。

**PARAMETERS:**

*   **args** -- `argparse.ArgumentParser` に渡される位置引数。
*   **kwargs** -- `argparse.ArgumentParser` に渡されるキーワード引数（例: `description`, `formatter_class`）。

**ATTRIBUTES:**

| 名前 | 説明 |
| :--- | :--- |
| `interactive_configs` | 引数ごとの対話設定（prompt, validate）を保持する辞書。 |

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`add_argument`](#add-argument) | 引数を定義し、対話設定（prompt, validate）を登録する。 |
| [`parse_args`](#parse-args) | 引数を解析し、不足やエラーがある場合は対話的に解決を図る。 |
| [`confirm_options`](#confirm-options) | 現在のオプション設定一覧を表示し、変更を確認する。 |
| [`get_default_values`](#get-default-values) | 全引数のデフォルト値を辞書として取得する。 |
| [`_get_action_by_dest`](#get-action-by-dest) | 内部変数名からActionオブジェクトを検索する。 |
| [`_run_validation`](#run-validation) | 値に対して検証ルールを適用する。 |
| [`_validate_single_rule`](#validate-single-rule) | 単一の検証ルールを実行する。 |
| [`_interactive_input`](#interactive-input) | ユーザーに入力を求め、検証を行う。 |

---

## Methods

### `add_argument(*args, **kwargs)`

`add_argument` をオーバーライドして、`prompt` (対話時のメッセージ) と `validate` (検証ルール) を受け取れるようにする。

**PARAMETERS:**

*   **args** (*str*) -- 引数のフラグや名前（例: `"-f"`, `"--file"`）。
*   **kwargs** -- `argparse` 標準のキーワード引数に加え、以下が使用可能。
    *   **prompt** (*str | None*) -- 引数が未指定の場合に対話入力時に表示するメッセージ。
    *   **validate** (*str | callable | list | None*) -- 入力値の検証ルール。
        *   `'file_exists'`: ファイルの実在確認。
        *   `'dir_create'`, `'any'`: 検証をパス（警告のみ）。
        *   *callable*: 値を受け取り `bool` を返す関数。
        *   *list*: 複数のルールを適用する場合。

**RETURN TYPE:**

`argparse.Action`

---

### `parse_args(args=None, namespace=None, interactive=True)`

`parse_args` をオーバーライドして、不足している引数や不正な引数について対話的に入力を求める。
`interactive=False` に設定すると、対話を試みずに例外を発生させる。

**PARAMETERS:**

*   **args** (*list | None*) -- 解析対象の引数リスト。Noneの場合は `sys.argv[1:]`。
*   **namespace** (*argparse.Namespace | None*) -- 結果を格納するオブジェクト。
*   **interactive** (*bool*) -- 対話モードの有効化フラグ (デフォルト: `True`)。
    *   `True`: エラー時にユーザーに入力を求めます。
    *   `False`: エラー時は対話を行わず、検証エラーをまとめて `argparse.ArgumentError` として送出します。

**RETURN TYPE:**

`argparse.Namespace`

---

### `confirm_options(args)`

オプション引数の確認と変更を対話的に行うメソッド。
`-h` で現在の設定値一覧とヘルプを表示する。変更された値に対しても `validate` を実行する。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- `parse_args` で解析されたオブジェクト。

**RETURN TYPE:**

`None`

---

### `get_default_values()`

パーサーに設定されている全引数のデフォルト値を辞書として返す。
バッチ処理などでデフォルト設定を取得するために使用する。

**RETURN TYPE:**

`dict`

---

### `_get_action_by_dest(dest)`

dest名からactionオブジェクトを探す。

**PARAMETERS:**

*   **dest** (*str*) -- 検索する引数の内部変数名。

**RETURN TYPE:**

`argparse.Action` | `None`

---

### `_run_validation(value, rules)`

値に対してルール（単一またはリスト）を適用する。
すべてのルールをパスしたら `True`、そうでなければ `False` を返す。

**PARAMETERS:**

*   **value** (*Any*) -- 検証対象の値。
*   **rules** (*str | callable | list*) -- 適用する検証ルール。

**RETURN TYPE:**

`bool`

---

### `_validate_single_rule(value, rule)`

単一のルールによる検証を行う。

**PARAMETERS:**

*   **value** (*Any*) -- 検証対象の値。
*   **rule** (*str | callable*) -- 適用するルール。

**RETURN TYPE:**

`bool`

---

### `_interactive_input(prompt, validate_rules)`

ユーザーに入力を求め、検証ルールに従ってチェックを行う内部メソッド。
検証が通るまでループする。

**PARAMETERS:**

*   **prompt** (*str*) -- 入力待ち時に表示するメッセージ。
*   **validate_rules** (*list | str | callable*) -- 入力値に対して適用する検証ルール。

**RETURN TYPE:**

`str`