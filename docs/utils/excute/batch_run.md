# BatchRunnerJob

[Index](./index.md) > `utils.excute.batch_run`

```python
class utils.excute.batch_run.BatchRunnerJob
```

Bases: [`utils.base.batch_job.BatchJob`](../base/batch_job.md)

JSON設定ファイルに基づいて、指定された Python スクリプト（`BatchJob` サブクラス）を一括で連続実行するメタジョブクラスです。
実行前に全てのジョブ設定に対してバリデーションを行い、不備がある場合は実行を開始しません。

**PARAMETERS:**

*   なし

**ATTRIBUTES:**

なし

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`get_parser`](#get-parser) | 設定ファイルパスを受け取るパーサーを構築する。 |
| [`execute`](#execute) | 設定ファイルを読み込み、検証を行った後、各ジョブを順次実行する。 |
| [`_convert_params_to_arg_list`](#convert-params-to-arg-list) | **[Internal]** JSON内のパラメータ辞書をコマンドライン引数リストに変換する。 |

---

## Methods

### `get_parser()`

以下の引数を定義した `InteractiveArgumentParser` を返す。

*   `config_file` (positional): 実行ジョブ設定が記述されたJSONファイル。[必須]

**RETURN TYPE:**

`utils.base.argument_parser.InteractiveArgumentParser`

---

### `execute(args)`

1. **設定ロード**: JSONファイルを読み込む。
2. **クラスロード**: `target_script` と `target_class` で指定された `BatchJob` クラスを動的にインポートする。
3. **事前検証 (Phase 1)**:
    *   `common_settings` と個別の `jobs` 設定をマージ。
    *   ターゲットクラスのパーサーを使用して、全ジョブのパラメータ検証を実行 (`interactive=False`)。
    *   エラーがある場合は実行を中止し、エラー内容を表示する。
4. **逐次実行 (Phase 2)**:
    *   検証済みのジョブを順次実行する。
    *   各ジョブの標準出力・標準エラー出力は、指定された出力ディレクトリ内の `.log` ファイルにリダイレクトされる。
    *   実行時エラーが発生しても、次のジョブの実行は継続される（ログにスタックトレースを記録）。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- `config_file` パスを含む引数オブジェクト。

**RETURN TYPE:**

`None`

---

### `_convert_params_to_arg_list(parser, params_dict)`

**[Internal]** パラメータ辞書を `argparse` が解釈可能なリスト形式（`['val1', '--opt', 'val2']`）に変換する。
ブール値（フラグ）やリスト形式の引数にも対応。

**PARAMETERS:**

*   **parser** (*argparse.ArgumentParser*) -- ターゲットジョブのパーサー。
*   **params_dict** (*dict*) -- マージ済みのパラメータ辞書。

**RETURN TYPE:**

`list` -- コマンドライン引数リスト。