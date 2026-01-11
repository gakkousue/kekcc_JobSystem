# RootToH5BatchJob

[Index](./index.md) > `module.root_to_h5.root_to_h5_BatchJob`

```python
class module.root_to_h5.root_to_h5_BatchJob.RootToH5BatchJob()
```

Bases: [`utils.base.batch_job.BatchJob`](../../utils/base/batch_job.md)

単一のROOTファイルをHDF5形式に変換するバッチジョブクラス。
Awkward Arrayを使用してネストされたデータを処理し、フラット化またはVLEN（Variable Length）データセットとしてHDF5に保存します。

**PARAMETERS:**

*   なし

**ATTRIBUTES:**

なし

**METHODS:**

| メソッド名 | 説明 |
| :--- | :--- |
| [`add_conversion_args`](#add-conversion-args) | **[Static]** 変換処理に関する共通引数（`--no-flat`, `--compression-level`）を定義する。 |
| [`setup_output_dirs`](#setup-output-dirs) | **[Static]** 変換モードに応じた出力ディレクトリ構成を定義する。 |
| [`get_parser`](#get-parser) | 単体実行用のパーサー（入力・出力ファイル引数含む）を返す。 |
| [`execute`](#execute) | ROOT → H5 変換のメイン処理を実行する。 |
| [`_get_array_type`](#get-array-type) | **[Internal]** Awkward配列の次元やタイプを判定する。 |
| [`_save_dataset`](#save-dataset) | **[Internal]** 通常のNumPy配列をHDF5データセットとして保存する。 |
| [`_save_vlen_dataset`](#save-vlen-dataset) | **[Internal]** 可変長配列をVLEN型としてHDF5に保存する。 |

---

## Methods

### `add_conversion_args(parser)`

**[Static]** `LocalJob` や `LSFJob` と共有するための変換オプション引数を定義する。

**PARAMETERS:**

*   **parser** (*argparse.ArgumentParser*) -- 引数を追加するパーサーオブジェクト。

**RETURN TYPE:**

`None`

---

### `setup_output_dirs(args, outputdir)`

**[Static]** `LocalJob` と `LSFJob` で共有する出力ディレクトリ定義。
`force_flat` オプションの状態により、出力先ディレクトリ名（`h5_flat` または `h5`）を切り替える。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- 解析済み引数。
*   **outputdir** (*str*) -- ルート出力ディレクトリ。

**RETURN TYPE:**

`dict` -- `{ 'h5': '.../h5_flat' }` or `{ 'h5': '.../h5' }`

---

### `get_parser()`

単体スクリプト実行用の `InteractiveArgumentParser` を構築する。
`add_conversion_args` に加え、単体実行に必要な `input_file` と `output_file` 引数を定義する。

**RETURN TYPE:**

`utils.base.argument_parser.InteractiveArgumentParser`

---

### `execute(args)`

解析された引数に基づいて、単一ファイルの変換を実行する。
1. ROOTファイルを開き、TTreeを走査。
2. ブランチごとにAwkward Arrayとして読み込み。
3. `force_flat` フラグに従い、フラット化またはネスト保持（VLEN）でHDF5に保存。

**PARAMETERS:**

*   **args** (*argparse.Namespace*) -- `input_file`, `output_file`, `force_flat`, `compression_level` を含む引数オブジェクト。

**RETURN TYPE:**

`None`

---

### `_get_array_type(ak_array)`

**[Internal]** Awkward Arrayの型情報を解析する。

**PARAMETERS:**

*   **ak_array** (*awkward.Array*) -- 解析対象の配列。

**RETURN TYPE:**

`dict` -- `{'type_str': str, 'dimensions': int, 'is_variable': bool, 'shape': tuple}`

---

### `_save_dataset(h5_group, name, data, compression_level=1)`

**[Internal]** データをHDF5データセットとして保存する。

**PARAMETERS:**

*   **h5_group** (*h5py.Group*) -- 保存先のHDF5グループ。
*   **name** (*str*) -- データセット名。
*   **data** (*numpy.ndarray*) -- 保存するデータ。
*   **compression_level** (*int*) -- gzip圧縮レベル (0-9)。

**RETURN TYPE:**

`bool` -- 保存成功なら `True`。

---

### `_save_vlen_dataset(h5_group, name, ak_array, compression_level=1)`

**[Internal]** 可変長配列（Jagged Array）をHDF5のVLENデータタイプとして保存する。

**PARAMETERS:**

*   **h5_group** (*h5py.Group*) -- 保存先のHDF5グループ。
*   **name** (*str*) -- データセット名。
*   **ak_array** (*awkward.Array*) -- 保存する可変長配列。
*   **compression_level** (*int*) -- gzip圧縮レベル (0-9)。

**RETURN TYPE:**

`tuple` -- `(success: bool, inner_dtype: dtype)`