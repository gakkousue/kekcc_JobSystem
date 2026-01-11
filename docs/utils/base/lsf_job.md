# LSFJob

[Index](./index.md) > `utils.base.lsf_job`

```python
class utils.base.lsf_job.LSFJob
```

Bases: [`utils.base.structured_job_base.StructuredJobBase`](./structured_job_base.md)

StructuredJobBaseを拡張し、LSF (bsub) へのジョブ投入機能を追加したクラス。

**PARAMETERS:**

*   なし

**ATTRIBUTES:**

| 名前 | 説明 |
| :--- | :--- |
| `args.queue` | LSFキュー名 (デフォルト: "s")。 |

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`_add_args`](#add-args-internal) | LSF固有の引数 (`-q`) を追加する。 |
| [`_setup_output_dirs`](#setup-output-dirs-internal) | ログ用ディレクトリ (`log`, `bsublog`, `sh`) を追加する。 |
| [`generate_command`](#generate-command) | **[Abstract]** 実行するコマンド文字列を生成する。 |
| [`process_file`](#process-file) | シェルスクリプトを生成し、`bsub` でジョブを投入する。 |

---

## Methods

### `_add_args(parser)`

親クラスの処理に加え、LSF固有の引数 (`-q`, `--queue`) を追加する。

**PARAMETERS:**

*   **parser** (*InteractiveArgumentParser*) -- パーサーオブジェクト。

**RETURN TYPE:**

`None`

---

### `_setup_output_dirs(args, outputdir)`

ユーザー定義ディレクトリに加え、LSFJob必須ディレクトリを追加する。
*   `log`: 実行ログ (`logs/log`)
*   `bsublog`: BSUB投入ログ (`logs/bsublog`)
*   `sh`: 生成されたシェルスクリプト (`logs/sh`)

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **outputdir** (*str*) -- ルート出力ディレクトリ。

**RETURN TYPE:**

`dict`

---

### `generate_command(inputfile_path, output_basename, args, output_dirs)`

**[Abstract]** サブクラスで実装必須。実行するコマンド文字列と、リストエントリを生成する。

**PARAMETERS:**

*   **inputfile_path** (*str*) -- 入力ファイルのフルパス。
*   **output_basename** (*str*) -- 拡張子なしファイル名。
*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **output_dirs** (*dict*) -- ディレクトリパス辞書。

**RETURN TYPE:**

`tuple` -- `(cmd_string: str, list_entries: dict)`

---

### `process_file(inputfile_path, output_basename, args, output_dirs)`

1. `generate_command` でコマンドを取得。
2. `.sh` ファイルを作成。
3. `bsub` コマンドを実行してジョブを投入。

**PARAMETERS:**

*   **inputfile_path** (*str*) -- 入力ファイルのフルパス。
*   **output_basename** (*str*) -- 拡張子なしファイル名。
*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **output_dirs** (*dict*) -- ディレクトリパス辞書。

**RETURN TYPE:**

`dict` -- リストエントリ辞書。