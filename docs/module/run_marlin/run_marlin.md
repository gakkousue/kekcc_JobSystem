# MarlinJob

[Index](./index.md) > `module.run_marlin.run_marlin`

```python
class module.run_marlin.run_marlin.MarlinJob()
```

Bases: [`utils.base.lsf_job.LSFJob`](../../utils/base/lsf_job.md)

ILCSoftの解析フレームワークである **Marlin** をLSF環境で実行するためのジョブクラス。
Steering XMLファイルを入力として受け取り、コマンドライン引数でのパラメータオーバーライド（InputFile, OutputFile等）を行います。

**PARAMETERS:**

*   なし

**ATTRIBUTES:**

なし

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`add_args`](#add-args) | Marlin XMLや出力制御に関する引数を追加する。 |
| [`setup_output_dirs`](#setup-output-dirs) | SLCIOおよびROOTファイルの出力ディレクトリを定義する。 |
| [`generate_command`](#generate-command) | `Marlin` コマンド文字列を生成する。 |

---

## Methods

### `add_args(parser)`

以下のMarlin固有引数を追加する。

*   `xml` (positional): Steering XMLファイル。[必須]
*   `-m`, `--marlin-output-param-name`: LCIO出力ファイルパスを指定するパラメータ名（デフォルト: `MyLCIOOutputProcessor.LCIOOutputFile`）。
*   `-r`, `--root_processors`: ROOT出力を指定するプロセッサパラメータ名のリスト（例: `-r MyProc.RootFile`）。
*   `-E`, `--env-vars-file`: 実行前に読み込む環境変数定義ファイル。
*   `--no-slcio`: SLCIOファイルの出力を無効化（`/dev/null`へ破棄）するフラグ。

**PARAMETERS:**

*   **parser** (*InteractiveArgumentParser*) -- パーサーオブジェクト。

**RETURN TYPE:**

`None`

---

### `setup_output_dirs(args, outputdir)`

出力ファイルの種類に応じたディレクトリ構成を定義する。
*   `slcio`: `--no-slcio` が指定されていない場合作成。
*   ROOT用ディレクトリ: `-r` で指定されたプロセッサごとに階層ディレクトリを作成（例: `root/MyProc/`）。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **outputdir** (*str*) -- ルート出力ディレクトリ。

**RETURN TYPE:**

`dict` -- `{ 'slcio': path, 'MyProc.RootFile': path, ... }`

---

### `generate_command(inputfile_path, output_basename, args, output_dirs)`

1. 必要であれば環境変数を読み込む（`source` ではなく `export $(cat ...)` 方式）。
2. `Marlin` コマンドを構築する。
    *   `--global.LCIOInputFiles` に入力ファイルを指定。
    *   `--no-slcio` なら出力先を `/dev/null` に、そうでなければ `slcio` ディレクトリ内のファイルパスを指定。
    *   ROOT出力プロセッサパラメータ (`--MyProc.RootFile=...`) を指定。
    *   最後にXMLファイルを指定。

**PARAMETERS:**

*   **inputfile_path** (*str*) -- 入力ファイルパス。
*   **output_basename** (*str*) -- ファイル名（拡張子なし）。
*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **output_dirs** (*dict*) -- ディレクトリ情報。

**RETURN TYPE:**

`tuple` -- `(cmd_string, list_entries)`