# RootToH5LSFJob

[Index](./index.md) > `module.root_to_h5.root_to_h5_LSFJob`

```python
class module.root_to_h5.root_to_h5_LSFJob.RootToH5LSFJob()
```

Bases: [`utils.base.lsf_job.LSFJob`](../../utils/base/lsf_job.md)

LSF環境で `RootToH5BatchJob` を実行するためのラッパークラス。
`root_to_h5_BatchJob.py` をサブプロセスとして呼び出すコマンドを生成し、`bsub` で投入する。

**PARAMETERS:**

*   なし

**ATTRIBUTES:**

なし

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`add_args`](#add-args) | `RootToH5BatchJob` と共通の引数を追加する。 |
| [`setup_output_dirs`](#setup-output-dirs) | `RootToH5BatchJob` のディレクトリ定義を再利用する。 |
| [`generate_command`](#generate-command) | `python root_to_h5_BatchJob.py ...` コマンド文字列を生成する。 |

---

## Methods

### `add_args(parser)`

`RootToH5BatchJob.add_conversion_args` を呼び出し、変換オプション引数を追加する。

**PARAMETERS:**

*   **parser** (*InteractiveArgumentParser*) -- パーサーオブジェクト。

**RETURN TYPE:**

`None`

---

### `setup_output_dirs(args, outputdir)`

`RootToH5BatchJob.setup_output_dirs` を呼び出し、共通のディレクトリ構成を使用する。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **outputdir** (*str*) -- ルート出力ディレクトリ。

**RETURN TYPE:**

`dict`

---

### `generate_command(inputfile_path, output_basename, args, output_dirs)`

入力ファイルに対応する `root_to_h5_BatchJob.py` の実行コマンドを構築する。
`args.force_flat` などのオプション引数もコマンドライン引数として渡す。

**PARAMETERS:**

*   **inputfile_path** (*str*) -- 入力ファイルパス。
*   **output_basename** (*str*) -- ファイル名（拡張子なし）。
*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **output_dirs** (*dict*) -- ディレクトリ情報。

**RETURN TYPE:**

`tuple` -- `(cmd_string, {'h5': output_path})`