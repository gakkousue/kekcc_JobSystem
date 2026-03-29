# Class Reference Manual

本マニュアルは、`job_framework` パッケージ内に定義されている主要なクラス群の仕様と、開発者が新しいジョブを実装する際のリファレンスを提供します。

---

## クラス階層構造
ジョブフレームワークは用途に合わせた継承ツリーを提供しています。実装したいジョブの性質に合わせて、適切なクラスを継承してください。

- **`BatchJob`**: 最もプレーンなジョブ（引数解析と実行手順のみ）
  └── **`StructuredJobBase`**: 出力ディレクトリの構築を自動化
      ├── **`BatchRunnerJob`**: 外部モジュールを動的にロードし、順次実行とシステム全体のロギングを統括する特殊ランナー
      └── **`ListFileJobBase`**: リストファイルを入力とし、複数ファイルへのループ処理を自動化
          ├── **`LSFJob`**: 各ループ処理をLSF (`bsub`) クラスターにジョブとして投入する
          └── **`LocalJob`**: 各ループ処理をローカルマシン上で直接・逐次実行する

---

## 1. `job_framework.argument_parser.InteractiveArgumentParser`

標準ライブラリ `argparse.ArgumentParser` を拡張したクラスです。引数が不足している場合やバリデーションエラー時に、**対話的にユーザーに入力を求める機能**と、**厳密な検証ロジック**を追加しています。

### 主な拡張メソッド・引数

- **`add_argument(*args, **kwargs)`**
  標準の引数に加え、以下の独自引数を取ります。
  - **`prompt` (str)**: 対話モード時にプロンプトとして表示する文字列。指定された引数が入力されなかった場合にユーザーに入力を求めます。（バッチモード時は必須項目扱いとなります）
  - **`validate` (str | callable | list)**: 入力値のバリデーションルール。`"file_exists"` などの組み込み文字や、真偽値を返す独自関数を渡せます。

- **`parse_args(args=None, interactive=True)`**
  引数の解析と検証を実行します。
  - `interactive=True` の場合は対話モードとなり、エラー時に再入力を促します。
  - `interactive=False` （`batch_run.py` 経由など）の場合は厳密にチェックし、エラー時は即座に例外を送出します。

- **`confirm_options(args)`**
  解析完了後の引数を一覧表示し、実行前にユーザーに変更の機会を与えます。

### 組み込みバリデーションルール
| ルール名 (str) | 説明 |
| :--- | :--- |
| `"file_exists"` | 指定されたファイルパスが物理的に存在することを確認 (`os.path.isfile`) |

---

## 2. `job_framework.batch_job.BatchJob`

すべてのジョブスクリプトの親となる抽象基底クラスです。定型的な処理（引数解析と実行フロー）の面倒を見ます。

### 実装すべきメソッド
- **`get_parser(self)`** 【必須】: このジョブで使用する `InteractiveArgumentParser` オブジェクトを構築して返します。
- **`execute(self, args)`** 【必須】: パース後の引数（`args`）を受け取り、ジョブのメイン処理を実行します。

### 基本的な使い方
```python
from job_framework.batch_job import BatchJob
from job_framework.argument_parser import InteractiveArgumentParser

class MyJob(BatchJob):
    def get_parser(self):
        parser = InteractiveArgumentParser(description="My Simple Job")
        parser.add_argument("input", help="入力ファイル", prompt="入力ファイル: ")
        return parser

    def execute(self, args):
        print(f"Processing {args.input}...")

if __name__ == "__main__":
    MyJob().main()
```

---

## 3. `job_framework.structured_job_base.StructuredJobBase`

`BatchJob` を継承し、**出力先ディレクトリの自動生成と管理**を行う機能を追加した基底クラスです。「特定のディレクトリ群を準備してから処理を行うジョブ」を作る際に使います。

### 自動的に定義される引数
- `outputdir` (位置引数), `--base-output-dir`

### 実装・オーバーライドすべきメソッド
- **`run_structured_job(self, args, custom_output_dirs)`** 【必須】
  - `execute()` の代わりに、ディレクトリ作成などの準備がすべて完了した後に呼ばれるメイン処理です。`custom_output_dirs` に作成されたディレクトリ群のパスが辞書形式で渡されます。
- **`setup_output_dirs(self, args, outputdir)`** 【任意】
  - ジョブに必要なサブディレクトリを定義します。`{ "カテゴリ名": "フルパス" }` の辞書を返すと、システムが実行前にこれらを自動で作成します。
- **`add_args(self, parser)`** 【任意】
  - ジョブ固有の独自引数を追加設定するためのフック関数です。

---

## 4. `job_framework.list_file_job_base.ListFileJobBase`

`StructuredJobBase` を継承し、**「リストファイル (`.list`) を入力として読み込み、そこに記載されたファイルパス1つひとつに対してループ処理を行う」** タイプのジョブを作成するための基底クラスです。

### 自動的に定義される引数
- 位置引数: `listfile` (リストファイル), `count` (処理する件数, -1で全件)
- パス制御: `--use-listfile-dir`, `-b` / `--list-base-dir`, `-s` / `--nstart` など

### 実装・オーバーライドすべきメソッド
- **`process_file(self, inputfile_path, output_basename, args, output_dirs)`** 【必須】
  - リスト内の各ファイルに対して呼ばれる、個別の処理を記述します。
  - 戻り値として `{ "カテゴリキー": "出力リストに書き込みたい文字列" }` を返すと、すべてのファイルの処理完了後、指定された出力ディレクトリに結果をまとめた `.list` ファイルが自動生成されます。

---

## 5. `job_framework.lsf_job.LSFJob`

`ListFileJobBase` を継承し、各ファイルへの処理をLFS分散環境 (`bsub` コマンド) に投入する機能を持ったクラスです。ログ出力用ディレクトリ (`logs/sh`, `logs/log`, `logs/bsublog`) が内部で自動的に追加生成されます。

### 自動的に定義される引数
- `-q` / `--queue`: 投入キュー名（デフォルト: `s`）

### 実装・オーバーライドすべきメソッド
- **`generate_command(self, inputfile_path, output_basename, args, output_dirs)`** 【必須】
  - `process_file` の代わりに実装し、対象ファイルに対して**実行したいコマンドの文字列**を生成して返します。
  - 指定されたコマンドは自動的にシェルスクリプト化され、標準出力をログに退避する処理などを付与された上で `bsub` によってクラスタに投入されます。
  - 戻り値は `(実行コマンド文字列全体, 返したいリストエントリの辞書)` のタプル形式で返してください。

---

## 6. `job_framework.local_job.LocalJob`

`ListFileJobBase` を継承し、LSFを使わずに**ローカル環境で直接ループ処理を実行する**クラスです。
このクラスを使用すると、対象ごとの標準出力 (`stdout`) および標準エラー出力 (`stderr`) が、各ファイル専用のログファイル (`logs/log/[ファイル名].log`) に自動的にリダイレクトされます。

### 実装・オーバーライドすべきメソッド
- **`run_local(self, inputfile_path, output_basename, args, output_dirs)`** 【必須】
  - `generate_command` や `process_file` と同様の引数を取り、ローカルで実行したい処理（Python関数の呼び出しやサブプロセスの起動など）を直接ここに記述します。
  - 戻り値として `{ "カテゴリ名": "出力文字列" }` を返す仕様は他と同じです。

---

## 7. `job_framework.batch_run.BatchRunnerJob`

システム全体を統括し、1つの設定用JSONファイルから環境設定を読み取り、指定されたジョブモジュールを連続実行するためのランナークラスです。
これ自身も `StructuredJobBase` を継承しており、システムログ（`batch_run.log`）の配置先となるディレクトリ (`outputdir`) の管理機能を持っています。

### 内部で使われる特徴的なクラス
- **`JobDualStream` / `TerminalIndenter`**
  親となる `batch_run.log`、そして各ジョブによって個別に生成されるファイルログ (`[モジュール名].log`)、さらにターミナル標準出力へのインデント付き表示。これら複数のストリームに対し、出力をフォーク（分岐）して同時に書き込むための内部ラッパークラスです。

### 実行の基本フロー
1. JSONから `target_module` または `target_script` で指定されたPythonファイルの場所を検索し、`importlib` を使って**動的にターゲットクラスをロード**します。
2. そのクラスの `InteractiveArgumentParser` (パーサー) を用いて、`common_settings` と事前定義された `jobs` 全てを一気に構文解析し、**リハーサルバリデーション (Phase 1)** を行います。
3. すべてのエラーチェックを通過した場合にのみ、初めて実際のジョブの実行ループ **(Phase 2)** を開始します。
4. ジョブ実行中、子ジョブプロセスが出力する `stdout` は動的に `JobDualStream` 等にすり替えられ、親ターミナルではインデント付きで階層が分かりやすく表示されます。