# Execution Utilities (utils.excute)

[Home](../../index.md) > `utils.excute`

バッチジョブの実行を制御・自動化するためのユーティリティ群です。

## Batch Execution
*   [**BatchRunnerJob**](./batch_run.md)
    *   JSON設定ファイルを読み込み、指定された `BatchJob` スクリプトを連続実行します。
    *   メタジョブとして機能し、自身も `BatchJob` のインターフェースを持ちます。