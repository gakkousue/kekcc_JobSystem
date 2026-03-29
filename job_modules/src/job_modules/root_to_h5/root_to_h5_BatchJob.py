# module/root_to_h5/root_to_h5_BatchJob.py

import os
import argparse
import uproot
import h5py
import numpy as np
import awkward as ak

from job_framework.batch_job import BatchJob
from job_framework.argument_parser import InteractiveArgumentParser

class RootToH5BatchJob(BatchJob):
    """
    単一のROOTファイルをHDF5に変換するバッチジョブ。
    """

    @staticmethod
    def add_conversion_args(parser):
        """
        LocalJobやLSFJobと共有するための引数定義
        """
        parser.add_argument(
            "--no-flat",
            dest="force_flat",
            action="store_false",
            default=True,
            help="フラット化を無効にし、ネスト構造を保持する（デフォルトはフラット化）"
        )
        
        parser.add_argument(
            "--compression-level",
            dest="compression_level",
            type=int,
            default=9,
            choices=range(0, 10),
            help="HDF5圧縮レベル (0=無効, 1=低圧縮/高速, 9=高圧縮/低速, デフォルト:9)"
        )

    @staticmethod
    def setup_output_dirs(args, outputdir):
        """
        LocalJobとLSFJobで共有する出力ディレクトリ定義
        """
        dirs = {}
        force_flat = args.force_flat
        
        if force_flat:
          dirs['h5'] = os.path.join(outputdir, "h5_flat")
        else:
          dirs['h5'] = os.path.join(outputdir, "h5")
        
        return dirs

    def get_parser(self):
        parser = InteractiveArgumentParser(description="ROOT to HDF5 Converter (Single File)")
        
        # 単体実行用の必須引数
        parser.add_argument("input_file", help="Input ROOT file path")
        parser.add_argument("output_file", help="Output HDF5 file path")
        
        # 共通オプション引数
        self.add_conversion_args(parser)
        
        return parser

    # ----------------------------
    # 配列タイプ判定関数
    # ----------------------------
    def _get_array_info(self, ak_array):
        """awkward配列の構造情報を取得"""
        type_str = str(ak_array.type)
        dim_count = type_str.count('*')
        is_variable = "var" in type_str
        
        return {
            "type_str": type_str,
            "dimensions": dim_count,
            "is_variable": is_variable,
        }

    def _get_primitive_dtype(self, ak_array):
        """
        Awkward配列の最深部のプリミティブ型(numpy.dtype)を取得する。
        データを走査せず、レイアウト情報から直接型を決定する。
        """
        try:
            # layoutを取得
            node = ak_array.layout
            
            # ListArray, RegularArrayなどのラッパーを剥がして最深部へ
            while hasattr(node, "content"):
                node = node.content
            
            # 最深部のデータノード(NumpyArray等)からdtypeを取得
            if hasattr(node, "dtype"):
                return np.dtype(node.dtype)
            
            # 万が一解決できない場合は従来のflatten方式（保険）
            print("flatten方式でdtypeを取得")
            flat = ak.flatten(ak_array, axis=None)
            return flat.to_numpy().dtype
            
        except Exception:
            # エラー時はfloat64をデフォルトとする
            return np.float64

    # ----------------------------
    # データ保存関数
    # ----------------------------
    def _save_dataset(self, h5_group, name, data, compression_level=1):
        try:
            if compression_level > 0:
                h5_group.create_dataset(
                    name,
                    data=data,
                    compression="gzip",
                    compression_opts=compression_level,
                    shuffle=True
                )
            else:
                h5_group.create_dataset(name, data=data)
            return True
        except Exception as e:
            print(f"      [error] データセット '{name}' の保存に失敗: {e}")
            return False

    def _save_vlen_dataset(self, h5_group, name, ak_array, compression_level=1):
        try:
            # 型推論ではなく、AwkwardArrayの定義から正しい型を取得
            inner_dtype = self._get_primitive_dtype(ak_array)
            
            # h5pyに渡すためにPythonリスト化（h5pyのVLEN書き込み仕様）
            data_list = ak_array.to_list()
            
            # 書き込み用の一時Object配列を作成
            # (h5pyでVLENを書くには、入力はobject dtypeのnumpy配列である必要がある)
            np_obj_arr = np.empty(len(data_list), dtype=object)
            
            for i, item in enumerate(data_list):
                # 個々の要素を正しい型(inner_dtype)のnumpy配列に変換して格納
                if hasattr(item, '__len__') and not isinstance(item, (str, bytes)):
                    np_obj_arr[i] = np.array(item, dtype=inner_dtype)
                else:
                    # スカラーやNoneが入っている場合の安全策
                    if item is None:
                         np_obj_arr[i] = np.array([], dtype=inner_dtype)
                    else:
                         np_obj_arr[i] = np.array([item], dtype=inner_dtype)
            
            # HDF5上での型定義 (ここで int や float が確定する)
            vlen_dtype = h5py.vlen_dtype(inner_dtype)
            
            if compression_level > 0:
                h5_group.create_dataset(
                    name,
                    data=np_obj_arr,
                    dtype=vlen_dtype,
                    compression="gzip",
                    compression_opts=compression_level,
                    shuffle=True
                )
            else:
                h5_group.create_dataset(name, data=np_obj_arr, dtype=vlen_dtype)
            
            return True, inner_dtype
        except Exception as e:
            print(f"      [error] VLENデータセット '{name}' の保存に失敗: {e}")
            return False, None

    # ----------------------------
    # 実行本体
    # ----------------------------
    def execute(self, args):
        inputfile_path = args.input_file
        h5_file_path = args.output_file
        force_flat = args.force_flat
        compression_level = args.compression_level
        
        # 出力ディレクトリの作成（ファイルパスからディレクトリを抽出）
        os.makedirs(os.path.dirname(os.path.abspath(h5_file_path)), exist_ok=True)

        print(f"ROOT → H5 変換開始")
        print(f"  input : {inputfile_path}")
        print(f"  output: {h5_file_path}")
        print(f"  モード: {'フラット化' if force_flat else 'ネスト構造保持'}")
        print(f"  圧縮レベル: {compression_level}")
        
        with uproot.open(inputfile_path) as file:
            tree_names = [
                k.split(";")[0]
                for k, v in file.items()
                if isinstance(v, uproot.behaviors.TTree.TTree)
            ]

            if not tree_names:
                raise RuntimeError("変換対象の TTree がありません")

            with h5py.File(h5_file_path, "w") as h5f:
                for tree_name in tree_names:
                    print(f"Tree 変換中: {tree_name}")
                    tree = file[tree_name]
                    
                    original_tree_name = tree_name
                    counter = 1
                    while tree_name in h5f:
                        tree_name = f"{original_tree_name}_{counter}"
                        counter += 1
                    
                    if tree_name != original_tree_name:
                        print(f"  重複TTree名をリネーム: {original_tree_name} → {tree_name}")
                    
                    tree_grp = h5f.create_group(tree_name)
                    
                    for branch_name in tree.keys():
                        try:
                            # awkward arrayとして読み込み
                            ak_array = tree[branch_name].array(library="ak")
                            array_info = self._get_array_info(ak_array)
                            
                            if force_flat:
                                try:
                                    # Flat化: 構造は失われるが型(int/float)は維持して保存
                                    flat_data = ak.flatten(ak_array, axis=None).to_numpy()
                                    dataset_name = f"{branch_name}"
                                    success = self._save_dataset(
                                        tree_grp, dataset_name, flat_data, compression_level
                                    )
                                    if success:
                                        print(f"      [flat] {dataset_name}: 形状={flat_data.shape}, 型={flat_data.dtype}")
                                except Exception as e:
                                    print(f"      [skip-flat] {branch_name}: {e}")
                            else:
                                if array_info['dimensions'] == 1 or not array_info['is_variable']:
                                    try:
                                        np_array = ak.to_numpy(ak_array)
                                        success = self._save_dataset(
                                            tree_grp, branch_name, np_array, compression_level
                                        )
                                        if success:
                                            print(f"      [regular] {branch_name}: 形状={np_array.shape}")
                                    except Exception as e:
                                        print(f"      [skip-regular] {branch_name}: {e}")
                                else:
                                    success, dtype = self._save_vlen_dataset(
                                        tree_grp, branch_name, ak_array, compression_level
                                    )
                                    if success:
                                        print(f"      [vlen] {branch_name}: VLEN型({dtype})として保存")

                        except Exception as e:
                            print(f"    [skip-error] branch {branch_name}: {type(e).__name__}: {e}")

        print("変換完了")


if __name__ == "__main__":
    RootToH5BatchJob().main()