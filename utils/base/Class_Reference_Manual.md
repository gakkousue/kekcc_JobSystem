# Class Reference Manual

## 1. `utils.argument_parser.InteractiveArgumentParser`

標準ライブラリ `argparse.ArgumentParser` を拡張したクラスです。
引数が不足している場合やバリデーションエラー時に、**対話的にユーザーに入力を求める機能**と、**厳密な検証ロジック**を追加しています。

### 基本的な使い方
```python
from utils.argument_parser import InteractiveArgumentParser
parser = InteractiveArgumentParser(description="説明")
```

---

### メソッド詳細

#### `add_argument(*args, **kwargs)`
引数を定義します。標準の `argparse` の機能に加え、`prompt` と `validate` という独自のキーワード引数を受け取ります。

**引数:**
*   **`*args`**: (位置引数)
    *   引数の名前。例: `"filename"`, `"-c"`, `"--count"`。
*   **`**kwargs`**: (キーワード引数)
    *   **標準 `argparse` の引数**:
        *   `help`: ヘルプメッセージ（推奨）。
        *   `default`: デフォルト値。
        *   `type`: 型変換関数（`int`, `float` など）。
        *   `nargs`: 引数の数（`"?"`: 0or1個, `"+"`: 1個以上 など）。
        *   `dest`: 内部的な変数名。
    *   **`prompt`** (str, optional): **[独自機能]**
        *   対話モード時に表示する入力要求メッセージ。
        *   これが設定されている引数が未指定（`None`）の場合、ユーザーに入力を求めます。
        *   **注意**: バッチモード（非対話）では、この項目が設定されている引数は「必須」とみなされます。
    *   **`validate`** (str | callable | list, optional): **[独自機能]**
        *   入力値に対する検証ルール。
        *   **文字列**: 組み込みルール（後述）を指定。
        *   **関数**: 値を受け取り `True/False` を返す関数。
        *   **リスト**: 複数のルールを適用する場合（例: `["file_exists", check_ext] `）。

**使用例:**
```python
parser.add_argument("input", prompt="入力ファイル: ", validate="file_exists")
```

---

#### `parse_args(args=None, namespace=None, interactive=True)`
引数の解析と検証を実行します。このクラスの心臓部です。

**引数:**
*   **`args`** (list, optional):
    *   解析する引数のリスト。デフォルトは `sys.argv[1:]` (コマンドライン引数)。
    *   バッチ処理時はここに設定ファイルから生成したリストを渡します。
*   **`namespace`** (argparse.Namespace, optional):
    *   結果を格納するオブジェクト。通常は `None`。
*   **`interactive`** (bool, default=`True`): **[重要]**
    *   **`True` (対話モード)**:
        *   必須引数が足りない、またはバリデーションエラーの場合、**ユーザーに入力を求めます**。
    *   **`False` (非対話/バッチモード)**:
        *   対話を行わず、検証を行います。
        *   エラーが見つかった場合、その場では停止せず全ての引数をチェックし、最終的に **`argparse.ArgumentError` 例外** を発生させます。

**戻り値:**
*   `argparse.Namespace`: 解析・検証済みの引数オブジェクト。

---

#### `confirm_options(args)`
現在の引数設定を一覧表示し、実行前にユーザーに変更の機会を与えます。

**引数:**
*   **`args`** (`argparse.Namespace`): `parse_args` で解析されたオブジェクト。

**挙動:**
1.  現在のオプション値を表示します。
2.  ユーザーに変更するか尋ねます。
3.  ユーザーが `"-s 100"` のように入力すると、その内容で `args` を更新し、再度バリデーションを実行します。

---

### 組み込みバリデーションルール (文字列指定)
`add_argument` の `validate` 引数に文字列で指定できるルール一覧です。

| ルール名 | 説明 |
| :--- | :--- |
| **`"file_exists"`** | `os.path.isfile(value)` が真であること。 |

---

## 2. `utils.batch_job.BatchJob`

すべてのジョブスクリプトの親となる抽象基底クラスです。
定型的な処理（引数解析、エラーハンドリング、メイン実行フロー）を隠蔽します。

### 基本的な使い方
```python
from utils.batch_job import BatchJob

class MyJob(BatchJob):
    def get_parser(self): ...
    def execute(self, args): ...

if __name__ == "__main__":
    MyJob().main()
```

---

### メソッド詳細

#### `get_parser(self)` **[抽象メソッド/必須実装]**
このジョブで使用する `InteractiveArgumentParser` を構築して返します。

**引数:** なし
**戻り値:** `InteractiveArgumentParser` オブジェクト

**実装例:**
```python
def get_parser(self):
    parser = InteractiveArgumentParser(description="My Job")
    parser.add_argument("input", help="Input file")
    return parser
```

---

#### `execute(self, args)` **[抽象メソッド/必須実装]**
ジョブのメイン処理を記述します。`parse_args` を通過した（検証済みの）引数が渡されます。

**引数:**
*   **`args`** (`argparse.Namespace`): 引数が格納されたオブジェクト。`args.変数名` でアクセスします。

**戻り値:** なし（エラー時は例外を送出）

**実装例:**
```python
def execute(self, args):
    print(f"Processing {args.input}...")
    # 処理ロジック
```

---

#### `main(self)`
スクリプトのエントリーポイントです。通常、`if __name__ == "__main__":` ブロックから呼び出します。

**引数:** なし
**戻り値:** なし

**内部フロー:**
1.  `get_parser()` を呼び出しパーサーを取得。
2.  `parser.parse_args()` を実行（対話モードON）。
3.  `parser.confirm_options(args)` を実行し、ユーザーに最終確認。
4.  `execute(args)` を呼び出して処理実行。
5.  例外が発生した場合はキャッチしてエラーメッセージを表示し、終了コード1で終了。

---

#### `get_default_values(self)`
パーサーに定義されているデフォルト値を抽出します。
主に `batch_run.py` が「デフォルト設定」を取得するために使用します。開発者が直接呼ぶことは稀です。

**引数:** なし
**戻り値:** `dict`: `{ "引数名": デフォルト値, ... }`

---

## 3. 実装上の注意点とTips

### `validate` にカスタム関数を使う場合
バリデーション関数は、失敗時に `False` を返すだけでなく、**なぜ失敗したかを `print()` する** ように実装してください。

```python
def my_check(value):
    if value == "bad":
        print("Error: 'bad' は許可されていません。") # エラー理由を表示
        return False
    return True
```

### 対話モードとバッチモードの挙動の違い
| 項目 | 対話モード (`main()`経由) | バッチモード (`batch_run.py`経由) |
| :--- | :--- | :--- |
| **引数不足 (`prompt`あり)** | プロンプトを表示して入力を待つ | **エラー** (ArgumentError) |
| **引数不足 (`prompt`なし)** | エラー (ArgumentError) | **エラー** (ArgumentError) |
| **バリデーション失敗** | 再入力を促すループ | **エラー** (ArgumentError) |
| **実行確認** | `confirm_options` で確認する | 確認なしで即実行 |

### `nargs="?"` の扱い
*   `add_argument("file", nargs="?", prompt="File: ")` と定義した場合:
    *   **対話モード**: 引数がなくてもエラーにならず、プロンプトで入力を求めます。
    *   **バッチモード**: 引数（JSON内の指定）がないと、「必須項目欠落」としてエラーになります。
    *   これにより、「手動実行時は気軽に入力、バッチ時は厳密に指定」という挙動を実現しています。

## 4. `utils.structured_job_base.StructuredJobBase`

`BatchJob` を継承し、**「リストファイルを入力として、各ファイルに対して処理を行い、結果を特定のディレクトリ構造に出力する」** タイプのジョブを作成するための基底クラスです。

パスの結合、入力ファイルの存在確認、出力ディレクトリの作成、ループ処理、そして最終的な `.list` ファイルの生成といった定型作業を自動化します。開発者は「1ファイルに対する具体的な処理内容」を記述するだけで済みます。

### 基本的な使い方
```python
from utils.structured_job_base import StructuredJobBase

class MyProcessorJob(StructuredJobBase):
    
    def add_job_specific_args(self, parser):
        # 独自の引数を追加
        parser.add_argument("--option", default="default")

    def setup_output_dirs(self, args, outputdir):
        # 出力ディレクトリ構成を定義
        return {
            "data": os.path.join(outputdir, "data"),
            "log": os.path.join(outputdir, "log")
        }

    def process_file(self, inputfile_path, output_basename, args, output_dirs):
        # 1ファイルごとの処理を記述
        print(f"Processing {inputfile_path}...")
        
        # 出力ファイル名を作成
        outfile = os.path.join(output_dirs["data"], f"{output_basename}.dat")
        
        # ... ここで実際の処理やジョブ投入を行う ...
        
        # リストファイルに記録したいファイル名を返す
        return { "data": f"{output_basename}.dat" }

if __name__ == "__main__":
    MyProcessorJob().main()
```

---

### メソッド詳細 (サブクラス実装用)

以下のメソッドをオーバーライド（上書き）して、ジョブ固有の振る舞いを定義します。

#### `add_job_specific_args(self, parser)`
共通引数（後述）以外の、ジョブ固有の引数を追加するためのフックメソッドです。

**引数:**
*   **`parser`**: `InteractiveArgumentParser` オブジェクト。`parser.add_argument(...)` で引数を追加します。

**実装例:**
```python
def add_job_specific_args(self, parser):
    parser.add_argument("-q", "--queue", default="s", help="LSF Queue")
```

---

#### `setup_output_dirs(self, args, outputdir)`
ジョブが必要とする出力ディレクトリの構造を定義します。ここで定義したディレクトリは、実行時に自動的に `os.makedirs` で作成されます。

**引数:**
*   **`args`**: 解析済みの引数オブジェクト。
*   **`outputdir`**: ユーザーが指定したルート出力ディレクトリ（パス結合済み）。

**戻り値:**
*   `dict`: `{ "カテゴリキー": "ディレクトリのフルパス" }`
    *   ここで指定したキーは、`process_file` の戻り値でリスト生成先を指定する際に使用します。

**実装例:**
```python
def setup_output_dirs(self, args, outputdir):
    return {
        "slcio": os.path.join(outputdir, "slcio"),
        "root":  os.path.join(outputdir, "root")
    }
```

---

#### `process_file(self, inputfile_path, output_basename, args, output_dirs)` **[必須実装]**
入力リストに含まれるファイル1つひとつに対して実行される処理内容を記述します。コマンドの実行や、BSUBへのジョブ投入などはここで行います。

**引数:**
*   **`inputfile_path`**: 入力ファイルのフルパス。
*   **`output_basename`**: 入力ファイル名から拡張子を除いたもの（例: `input.slcio` -> `input`）。出力ファイル名の生成に便利です。
*   **`args`**: 解析済みの引数オブジェクト。
*   **`output_dirs`**: `setup_output_dirs` で生成されたディレクトリパスの辞書。

**戻り値:**
*   `dict`: `{ "カテゴリキー": "リストファイルに書き込む文字列" }`
    *   リストファイル (`.list`) を生成したいカテゴリに対して、そのファイルに対応するエントリ（通常はファイル名）を返します。
    *   リスト生成が不要な場合は空の辞書 `{}` または `None` を返しても構いません。

**実装例:**
```python
def process_file(self, inputfile_path, output_basename, args, output_dirs):
    # 出力パス決定
    out_path = os.path.join(output_dirs["slcio"], f"{output_basename}.slcio")
    
    # コマンド実行 (擬似コード)
    run_command(f"processor {inputfile_path} {out_path}")
    
    # リストにはファイル名だけ記録する
    return { "slcio": f"{output_basename}.slcio" }
```

---

### 自動的に定義される共通引数

`StructuredJobBase` は以下の引数を自動的に定義し、処理します。`add_job_specific_args` でこれらを再定義する必要はありません。

| 引数名 | 説明 |
| :--- | :--- |
| **`listfile`** | 入力ファイルリスト (`.list`)。 |
| **`outputdir`** | 出力のルートディレクトリ。 |
| **`--base-output-dir`** | `outputdir` が相対パスの場合の基準ディレクトリ。 |
| **`--base-listfile-dir`** | `listfile` が相対パスの場合の基準ディレクトリ。 |
| **`--base-list-base-dir-dir`** | `list_base_dir` が相対パスの場合の基準ディレクトリ。 |
| **`count`** | 処理するファイル数。`-1` で全件処理。 |
| **`-b`, `--list-base-dir`** | リスト内のファイルパスが相対パスの場合の基準ディレクトリ。 |
| **`-s`, `--nstart`** | 処理を開始する行番号（1始まり）。 |

---

### 実行フロー (executeメソッドの内部挙動)

1.  **パス結合**: `base-*` 引数が指定されている場合、`outputdir` などを絶対パスに変換します。
2.  **バリデーション**: 入力リストファイルの存在やディレクトリの存在を確認します。
3.  **ディレクトリ作成**: `setup_output_dirs` で定義されたディレクトリを作成します。
4.  **ファイルループ**:
    *   指定された範囲（`nstart` ～ `count`）の入力ファイルを抽出します。
    *   各ファイルについて `process_file` を呼び出します。
    *   `process_file` の戻り値を収集します。
5.  **リスト生成**: 収集した結果を基に、各出力ディレクトリに `.list` ファイルを生成します。