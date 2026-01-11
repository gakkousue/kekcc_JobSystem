# RootToH5LocalJob

[Index](./index.md) > `module.root_to_h5.root_to_h5_LocalJob`

```python
class module.root_to_h5.root_to_h5_LocalJob.RootToH5LocalJob()
```

Bases: [`utils.base.local_job.LocalJob`](../../utils/base/local_job.md)

ローカル環境で `RootToH5BatchJob` を直接実行するクラス。
サブプロセス呼び出しではなく、Pythonオブジェクトとして `RootToH5BatchJob` をインスタンス化し実行する。

**PARAMETERS:**

*   なし

**ATTRIBUTES:**

なし

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`add_args`](#add-args) | `RootToH5BatchJob` と共通の引数を追加する。 |
| [`setup_output_dirs`](#setup-output-dirs) | `RootToH5BatchJob` のディレクトリ定義を再利用する。 |
| [`run_local`](#run-local) | `RootToH5BatchJob` インスタンスを作成し、変換処理を委譲実行する。 |

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

### `run_local(inputfile_path, output_basename, args, output_dirs)`

1. 出力先ディレクトリを作成。
2. `args` に `input_file` と `output_file` を追加した新しいNamespaceを作成（`RootToH5BatchJob` のI/Fに合わせるため）。
3. `RootToH5BatchJob().execute(batch_args)` を呼び出して処理を実行する。

**PARAMETERS:**

*   **inputfile_path** (*str*) -- 入力ファイルパス。
*   **output_basename** (*str*) -- ファイル名（拡張子なし）。
*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **output_dirs** (*dict*) -- ディレクトリ情報。

**RETURN TYPE:**

`dict` -- `{'h5': output_path}`