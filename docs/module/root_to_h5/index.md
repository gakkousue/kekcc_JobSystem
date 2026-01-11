# Module: root_to_h5

[Home](../../index.md) > [Modules](../index.md) > `root_to_h5`

ROOTファイル (`TTree`) を HDF5 形式に変換するモジュールです。
Awkward Arrayを利用して、Jagged Array（可変長配列）構造を維持したまま保存するか、フラット化して保存するかを選択できます。

## Components

### Core Logic
*   [**RootToH5BatchJob**](./root_to_h5_BatchJob.md)
    *   変換処理のロジック本体。単一ファイルに対する処理を担当します。
    *   変換オプション (`--no-flat`, `--compression-level`) の定義もここに含まれます。

### Execution Wrappers
*   [**RootToH5LSFJob**](./root_to_h5_LSFJob.md)
    *   LSF (bsub) 環境で分散処理を行うためのランチャー。
*   [**RootToH5LocalJob**](./root_to_h5_LocalJob.md)
    *   ローカル環境で実行するためのランチャー。