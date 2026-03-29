# Job Modules 実行フローと使用方法マニュアル

本ドキュメントでは、`job_modules` パッケージ内に実装されている個別のジョブ実行モジュールについて、それぞれの役割、実行フロー、および使い方を説明します。

---

## 1. `merge_h5` (HDF5ファイル結合ジョブ)
- **ファイル**: `merge_h5/merge_h5.py`
- **クラス**: `MergeH5Job` (← `BatchJob`)

### 役割
複数のHDF5ファイルパスが記載されたリストファイル（`.list`）を読み込み、それらを一つの大きなHDF5ファイルに結合（マージ）します。指定した上限イベント数 (`max_events`) に到達するまで抽出・結合を行います。

### 実行フロー
1. `BatchJob.execute()` から呼ばれ、出力先・入力リストのパスを解決します。
2. 入力ファイルリストからファイルを一つずつ読み込み `h5py` で開きます。
3. 指定された TTree名 (グループ名) の要素が存在するか、データ構造（VLENかどうか等）をチェックします。
4. 目標の `max_events` に到達するか、すべての入力ファイルを処理し終えるまで、新しく作成した出力先HDF5ファイルに対してデータセットを拡張(`resize`) しながらデータを追記していきます。

### 使い方
単体でバッチジョブとして実行可能です。

**このモジュールで定義された引数**:
- **必須引数**: `input_list` (入力リスト), `output_file` (出力先HDF5), `max_events` (取り出したい最大イベント数)
- **オプション**: `--tree-name` (要素取得グループ名, デフォルト: `ntp`)
- **パス解決用オプション**: `--base-output-dir`, `--base-listfile-dir`, `--base-list-base-dir-dir`, `-b` / `--list-base-dir`

---

## 2. `root_to_h5` (ROOT → HDF5変換ジョブ)
ROOTデータをHDF5（ネスト構造またはフラット配列）に変換するモジュールです。実行環境（単一プロセス、ローカルループ、LSF分散バッチ）に合わせて3つのクラスに分かれています。

### 2-1. `RootToH5BatchJob`
- **ファイル**: `root_to_h5/root_to_h5_BatchJob.py`

#### 役割と実行フロー
単一のROOTファイルを入力として受け取り、Awkward Array (`uproot`) を用いてファイルをパースしてHDF5に変換します。
1. ROOT内のTTreeを取得し、それぞれをHDF5のグループとして作成します。
2. 各ブランチを読み込み、フラット化（`--no-flat`がない場合）か、元のデータ構造（可変長配列 VLEN や多次元配列等のネスト構造）を維持してHDF5のデータセットとして作成します。
3. 指定された圧縮レベルでHDF5ファイルに書き込みます。

#### 使い方
1ファイルだけのテスト変換や、他のスクリプトから呼び出されるバックエンドとして使用します。

**このモジュールで追加された固有の引数**:
- **必須引数**: `input_file` (入力ROOT), `output_file` (出力HDF5)
- **オプション**: `--no-flat` (ネスト構造を保持), `--compression-level` (HDF5圧縮レベル 0〜9)

### 2-2. `RootToH5LocalJob` / `RootToH5LSFJob`
- **ファイル**: `root_to_h5_LocalJob.py`, `root_to_h5_LSFJob.py`

#### 役割と実行フロー
複数のROOTファイルが一列に記載されたリストファイル (`.list`) を受け取り、それぞれのファイルを順次変換するジョブです。
- `RootToH5LocalJob`: `LocalJob` を継承し、ローカル環境でシーケンシャルに `root-to-h5-batch` をサブプロセスとして実行します。
- `RootToH5LSFJob`: `LSFJob` を継承し、クラスタ環境で `bsub` を用いて複数の `root-to-h5-batch` 変換ジョブをキューに投入します。

#### 使い方
複数のファイルを一括変換する際に使用します（通常は `batch_run.py` 経由で実行します）。

**`ListFileJobBase` から継承される引数**:
- **必須引数**: `listfile` (入力リスト), `outputdir` (出力先ディレクトリ), `count` (処理ファイル数)
- **オプション**: `-b` (リスト基準ディレクトリ), `-s` (開始行) などのリスト制御引数

**`LSFJob` から継承される引数** (`RootToH5LSFJob` のみ):
- **オプション**: `-q` / `--queue` (投入先キュー名)

**このモジュールで追加された固有の引数**:
- **オプション**: `--no-flat` (ネスト構造を保持), `--compression-level` (HDF5圧縮レベル 0〜9)

---

## 3. `run_marlin` (Marlin実行ジョブ)
- **ファイル**: `run_marlin/run_marlin.py`
- **クラス**: `MarlinJob` (← `LSFJob`)

### 役割
ILC等の物理シミュレーション/再構成フレームワークである「Marlin」を、LSFクラスタ上で並列実行するためのジョブです。

### 実行フロー
1. 入力されたリストファイルからSLCIO等の入力ファイル名を1つずつ取り出します。
2. `generate_command()` にて、指定された Steering XML ファイルと入力ファイルを用いたMarlinの実行コマンド（`Marlin --global.LCIOInputFiles=... steer.xml`）を構築します。
3. コマンドライン引数（`--marlin-output-param-name` や `--root_processors`）に基づいて、出力されるSLCIOやROOTファイルの出力先パスをXMLのパラメータ上書き機能（`--[パラメータ名]=[パス]`）の形式でコマンドに追加します。
4. 生成された実行コマンドをシェルスクリプト化し、`bsub` で投入します。

### 使い方
複数ファイルに対するMarlinの分散処理を自動化・管理するために使用します。

**`ListFileJobBase` および `LSFJob` から継承される共通引数**:
- **必須引数**: `listfile` (入力リスト), `outputdir` (出力先ディレクトリ), `count` (処理ファイル数)
- **オプション**: `-q` / `--queue` (LSF投入先キュー名), `-b` (リスト基準ディレクトリ), `-s` (開始行) など

**このモジュールで追加された固有の引数**:
- **必須引数**: `xml` (Steering XMLファイルのパス)
- **オプション**:
  - `-m` / `--marlin-output-param-name`: LCIO出力プロセッサのパラメータ名（デフォルト: `MyLCIOOutputProcessor.LCIOOutputFile`）
  - `--no-slcio`: SLCIOの出力を `dev/null` に破棄する
  - `-r` / `--root_processors`: ROOT出力を行うプロセッサパラメタをリストで指定する（複数指定可）
  - `-E` / `--env-vars-file`: 実行前にロードしたい環境変数がまとめられたファイル
