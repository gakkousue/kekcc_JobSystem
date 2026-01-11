# BatchJob

[Index](./index.md) > `utils.base.batch_job`

```python
class utils.base.batch_job.BatchJob()
```

Bases: `ABC` (Abstract Base Class)

バッチ処理可能なジョブスクリプトの基底クラス。
全てのジョブスクリプトはこのクラスを継承し、`get_parser` と `execute` を実装する。

**PARAMETERS:**

*   なし (抽象クラスのため直接インスタンス化しない)

**ATTRIBUTES:**

なし

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`get_parser`](#get-parser) | **[Abstract]** ArgumentParserを構築して返す。 |
| [`execute`](#execute) | **[Abstract]** ジョブのメイン処理を実行する。 |
| [`main`](#main) | スクリプトのエントリーポイント。 |
| [`get_default_values`](#get-default-values) | パーサーからデフォルト設定を取得する。 |

---

## Methods

### `get_parser()`

**[Abstract]** ArgumentParser (またはそのサブクラス) を構築して返す。

**RETURN TYPE:**

`utils.base.argument_parser.InteractiveArgumentParser`

---

### `execute(args)`

**[Abstract]** 解析された引数(args)を受け取り、ジョブのメイン処理を実行する。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- `parse_args` を通過した引数オブジェクト。

**RETURN TYPE:**

`None`

---

### `main()`

単体スクリプトとして実行された場合のエントリーポイント。
引数解析、確認(`confirm_options`)、実行(`execute`)、例外処理を行う。

**RETURN TYPE:**

`None`

---

### `get_default_values()`

パーサーに設定されている全引数のデフォルト値を辞書として返す。
バッチランナーがデフォルト設定を取得するために使用する。

**RETURN TYPE:**

`dict`