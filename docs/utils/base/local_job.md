# LocalJob

[Index](./index.md) > `utils.base.local_job`

```python
class utils.base.local_job.LocalJob()
```

Bases: [`utils.base.structured_job_base.StructuredJobBase`](./structured_job_base.md)

StructuredJobBaseを拡張し、ローカル環境で直接実行するクラス。
ジョブスケジューラは使用しない。

**PARAMETERS:**

*   なし

**ATTRIBUTES:**

なし

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`_setup_output_dirs`](#setup-output-dirs-internal) | ログ用ディレクトリ (`log`) を追加する。 |
| [`run_local`](#run-local) | **[Abstract]** ローカルで実行する処理を記述する。 |
| [`process_file`](#process-file) | ログ出力をリダイレクトして `run_local` を実行する。 |

---

## Methods

### `_setup_output_dirs(args, outputdir)`

ユーザー定義ディレクトリに加え、LocalJob必須ディレクトリを追加する。
*   `log`: 実行ログ (`logs/log`)

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **outputdir** (*str*) -- ルート出力ディレクトリ。

**RETURN TYPE:**

`dict`

---

### `run_local(inputfile_path, output_basename, args, output_dirs)`

**[Abstract]** ローカル環境で実行する具体的な処理を記述する。
サブクラスで実装必須。

**PARAMETERS:**

*   **inputfile_path** (*str*) -- 入力ファイルのフルパス。
*   **output_basename** (*str*) -- 拡張子なしファイル名。
*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **output_dirs** (*dict*) -- ディレクトリパス辞書。

**RETURN TYPE:**

`dict` -- リストエントリ辞書。

---

### `process_file(inputfile_path, output_basename, args, output_dirs)`

標準出力・標準エラー出力を `logs/log` 内のログファイルに向け先変更した状態で、`run_local` を実行する。

**PARAMETERS:**

*   **inputfile_path** (*str*) -- 入力ファイルのフルパス。
*   **output_basename** (*str*) -- 拡張子なしファイル名。
*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **output_dirs** (*dict*) -- ディレクトリパス辞書。

**RETURN TYPE:**

`dict` -- リストエントリ辞書。