# StructuredJobBase

[Index](./index.md) > `utils.base.structured_job_base`

```python
class utils.base.structured_job_base.StructuredJobBase()
```

Bases: [`utils.base.batch_job.BatchJob`](./batch_job.md)

リストファイルを入力とし、ディレクトリ構造を維持して処理を行うジョブの基底クラス。
ジョブの投入方法(bsub等)は関知せず、ファイルループとリスト生成の構造のみを提供する。

**PARAMETERS:**

*   なし

**ATTRIBUTES:**

なし (解析された `args` に以下の自動定義引数が含まれる)

| 自動定義引数 | 説明 |
| :--- | :--- |
| `listfile` | 入力ファイルリスト (.list)。[必須] |
| `outputdir` | 出力ディレクトリ。[必須] |
| `count` | 処理するファイル数 (-1=全て)。 |
| `base_output_dir` | 相対パスの場合の基準出力ディレクトリ。 |
| `base_listfile_dir` | 相対パスの場合の基準リストファイルディレクトリ。 |
| `list_base_dir` | リスト内のファイルパスの基準ディレクトリ。 |
| `nstart` | 開始行番号。 |

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`get_parser`](#get-parser) | 共通引数を設定したパーサーを返す。 |
| [`add_args`](#add-args) | **[Virtual]** サブクラスで独自の引数を追加する。 |
| [`_add_args`](#add-args-internal) | **[Internal]** ライブラリ内部で引数を追加する。 |
| [`setup_output_dirs`](#setup-output-dirs) | **[Virtual]** 出力ディレクトリ構成を定義する。 |
| [`_setup_output_dirs`](#setup-output-dirs-internal) | **[Internal]** システム必須ディレクトリを含めた構成を作成する。 |
| [`process_file`](#process-file) | **[Abstract]** 1ファイルごとの処理を実行する。 |
| [`execute`](#execute) | 全体の実行フロー（パス解決、ループ、リスト生成）を制御する。 |

---

## Methods

### `get_parser()`

共通の構造に関する必須引数（listfile, outputdir等）を追加した `InteractiveArgumentParser` を返す。
内部で `add_args` および `_add_args` を呼び出す。

**RETURN TYPE:**

`utils.base.argument_parser.InteractiveArgumentParser`

---

### `add_args(parser)`

サブクラスでオーバーライドして、独自の引数（queue, env, xmlなど）を追加するためのフックメソッド。

**PARAMETERS:**

*   **parser** (*InteractiveArgumentParser*) -- 引数を追加する対象のパーサー。

**RETURN TYPE:**

`None`

---

### `_add_args(parser)`

[Internal] ライブラリ拡張用（例: LSFJob）の引数追加フック。

**PARAMETERS:**

*   **parser** (*InteractiveArgumentParser*) -- 引数を追加する対象のパーサー。

**RETURN TYPE:**

`None`

---

### `setup_output_dirs(args, outputdir)`

サブクラスでオーバーライドして、必要な出力ディレクトリを定義する。
ここで返された辞書のキーは、`process_file` の戻り値で使用する。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **outputdir** (*str*) -- ルート出力ディレクトリ（絶対パス）。

**RETURN TYPE:**

`dict` -- `{ 'category_key': 'full_dir_path' }`

---

### `_setup_output_dirs(args, outputdir)`

[Internal] 最終的なディレクトリ辞書を構築する。
`setup_output_dirs` の結果に、システム必須ディレクトリ（log等）をマージする。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **outputdir** (*str*) -- ルート出力ディレクトリ。

**RETURN TYPE:**

`dict`

---

### `process_file(inputfile_path, output_basename, args, output_dirs)`

**[Abstract]** 1ファイルごとの処理（コマンド生成、ジョブ投入など）を行う。
リストファイルに出力したい文字列を辞書形式で返す。

**PARAMETERS:**

*   **inputfile_path** (*str*) -- 入力ファイルのフルパス。
*   **output_basename** (*str*) -- 拡張子を除いた入力ファイル名。
*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **output_dirs** (*dict*) -- `setup_output_dirs` で生成されたディレクトリパス。

**RETURN TYPE:**

`dict` -- `{ 'category_key': 'list_entry_string' }`

---

### `execute(args)`

ジョブの実行フローを制御する。
1. パス結合とバリデーション。
2. ディレクトリ作成。
3. リストファイルの読み込みと対象範囲の抽出。
4. ファイルループ (`process_file` 呼び出し)。
5. 結果リスト (`.list`) の生成。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- 解析済み引数。

**RETURN TYPE:**

`None`