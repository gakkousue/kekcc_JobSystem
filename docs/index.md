# Documentation Home

本プロジェクトのバッチ処理フレームワークおよびモジュール仕様書です。

## Categories

*   [**Core Utilities (`utils/base`)**](./utils/base/index.md)
    *   引数処理、ジョブ実行の基盤となる共通クラス群です。
    *   開発者はまずここを参照し、`BatchJob` や `StructuredJobBase` の仕様を理解してください。

*   [**Execution Utilities (`utils/excute`)**](./utils/excute/index.md)  <-- [New]
    *   バッチジョブの一括実行など、実行制御に関するツール群です。
    *   `batch_run.py` (JSONベースのバッチランナー) などが含まれます。

*   [**Modules (`module`)**](./module/index.md)
    *   実際にデータ処理を行う実装済みモジュール（ジョブスクリプト）のマニュアルです。
    *   `root_to_h5`, `run_marlin` などが含まれます。