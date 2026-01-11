# Core Utilities (utils.base)

[Home](../../../docs/index.md) > `utils.base`

バッチジョブ開発のための基底クラスおよびユーティリティです。

## Argument Parsing
*   [**InteractiveArgumentParser**](./argument_parser.md)
    *   対話機能と強力なバリデーションを備えた `argparse` の拡張。

## Job Base Classes
*   [**BatchJob**](./batch_job.md)
    *   全てのジョブの抽象基底クラス。
*   [**StructuredJobBase**](./structured_job_base.md)
    *   リストファイルとディレクトリ構造に基づく処理の基底クラス。

## Execution Implementations
*   [**LSFJob**](./lsf_job.md)
    *   `bsub` コマンドを使用したLSF環境での実行。
*   [**LocalJob**](./local_job.md)
    *   ローカルマシン上での直接実行。