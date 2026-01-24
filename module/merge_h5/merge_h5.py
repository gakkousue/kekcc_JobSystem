# module/merge_h5/merge_h5.py

import os
import sys
import h5py
import numpy as np
import argparse

from utils.base.batch_job import BatchJob
from utils.base.argument_parser import InteractiveArgumentParser


class MergeH5Job(BatchJob):
  """
  複数のHDF5ファイルを結合し、指定されたイベント数だけ抽出するジョブ。
  """

  def get_parser(self):
    parser = InteractiveArgumentParser(description="Merge HDF5 files with event limit")

    # 必須引数
    parser.add_argument("input_list", help="入力HDF5ファイルパスが記述されたリストファイル (.list)",
                        prompt="入力リストファイル (.list): ")
    
    parser.add_argument("output_file", help="出力HDF5ファイルパス (.h5)",
                        prompt="出力ファイルパス (.h5): ")
    
    parser.add_argument("max_events", type=int, help="取り出したい合計要素数",
                        prompt="取り出したい合計要素数: ")

    # オプション
    parser.add_argument("--tree-name", dest="tree_name", default="ntp",
                        help="HDF5内のグループ名 (TTree名)")

    # パス解決用引数
    parser.add_argument("--base-output-dir", dest="base_output_dir", default="",
                        help="output_fileが相対パスの場合、このディレクトリを基準にします。")

    parser.add_argument("--base-listfile-dir", dest="base_listfile_dir", default="",
                        help="input_listが相対パスの場合、このディレクトリを基準にします。")

    parser.add_argument("--base-list-base-dir-dir", dest="base_list_base_dir_dir", default="",
                        help="list-base-dirが相対パスの場合、このディレクトリを基準にします。")

    parser.add_argument("-b", "--list-base-dir", dest="list_base_dir", default=os.getcwd(),
                        help="リストファイルの基準ディレクトリ")

    return parser

  def execute(self, args):
    # ---------------------------------------------------------
    # 1. パス解決 (StructuredJobBase相当のロジック)
    # ---------------------------------------------------------
    if args.base_output_dir and not os.path.isabs(args.output_file):
        args.output_file = os.path.join(args.base_output_dir, args.output_file)

    if args.base_listfile_dir and not os.path.isabs(args.input_list):
        args.input_list = os.path.join(args.base_listfile_dir, args.input_list)

    if args.base_list_base_dir_dir and not os.path.isabs(args.list_base_dir):
        args.list_base_dir = os.path.join(args.base_list_base_dir_dir, args.list_base_dir)

    input_list_path = args.input_list
    output_file_path = args.output_file
    list_base_dir = args.list_base_dir
    max_events = args.max_events
    tree_name = args.tree_name

    print(f"Merge H5 Start")
    print(f"  Input List : {input_list_path}")
    print(f"  Output File: {output_file_path}")
    print(f"  Max Events : {max_events}")
    print(f"  Tree Name  : {tree_name}")

    # ---------------------------------------------------------
    # 2. リストファイルの読み込み
    # ---------------------------------------------------------
    if not os.path.isfile(input_list_path):
        raise FileNotFoundError(f"リストファイルが見つかりません: {input_list_path}")

    with open(input_list_path, 'r') as f:
        input_files = [line.strip() for line in f if line.strip()]

    if not input_files:
        print("警告: 入力ファイルリストが空です。")
        return

    # 出力ディレクトリ作成
    os.makedirs(os.path.dirname(os.path.abspath(output_file_path)), exist_ok=True)

    # ---------------------------------------------------------
    # 3. マージ処理
    # ---------------------------------------------------------
    current_events = 0
    file_idx = 0
    
    # 書き込みモードで出力ファイルを開く
    with h5py.File(output_file_path, 'w') as h5_out:
        # グループ作成
        grp_out = h5_out.create_group(tree_name)
        
        # データセット初期化済みフラグ
        initialized = False
        
        while current_events < max_events and file_idx < len(input_files):
            # 入力ファイルパス解決
            filename = input_files[file_idx]
            if not os.path.isabs(filename):
                filepath = os.path.join(list_base_dir, filename)
            else:
                filepath = filename
            
            file_idx += 1
            
            if not os.path.exists(filepath):
                print(f"警告: ファイルが見つかりません (スキップ): {filepath}")
                continue

            print(f"Processing ({file_idx}/{len(input_files)}): {os.path.basename(filepath)}")
            
            try:
                with h5py.File(filepath, 'r') as h5_in:
                    if tree_name not in h5_in:
                        print(f"  エラー: グループ '{tree_name}' が見つかりません。スキップします。")
                        continue
                    
                    grp_in = h5_in[tree_name]
                    keys = list(grp_in.keys())
                    
                    if not keys:
                        print("  警告: データセットが空です。")
                        continue

                    # --- 要素数の一貫性チェック ---
                    lengths = {}
                    for k in keys:
                        dset = grp_in[k]
                        if hasattr(dset, 'shape') and len(dset.shape) > 0:
                            lengths[k] = dset.shape[0]
                        else:
                            lengths[k] = 0 # スカラーまたは空

                    unique_lengths = set(lengths.values())
                    if len(unique_lengths) > 1:
                        print(f"  [警告] 要素数が一致していません: {unique_lengths}")
                        # 詳細表示
                        for k, v in lengths.items():
                            if v != list(unique_lengths)[0]: # 多数決判定などはせず単純に表示
                                print(f"    - {k}: {v}")
                    else:
                        n_entries = list(unique_lengths)[0]
                        print(f"  Entries: {n_entries}")

                    # --- 読み出し範囲の計算 ---
                    # 残り必要なイベント数
                    needed = max_events - current_events
                    # このファイルから取得する数
                    # n_entries(ファイル内の数) と needed の小さい方
                    # ただし n_entries が 0 の場合は何もしない
                    if n_entries == 0:
                        continue
                        
                    n_take = min(n_entries, needed)
                    
                    # --- データ転送 ---
                    for k in keys:
                        # データの読み込み
                        ds_in = grp_in[k]
                        data = ds_in[:n_take] # スライスで取得
                        
                        # --- 初期化 (最初のファイルのとき) ---
                        if k not in grp_out:
                            # shape: 初期サイズは0とする
                            init_shape = list(ds_in.shape)
                            init_shape[0] = 0
                            
                            # maxshape: 第1次元を無制限(None)にする
                            max_shape = list(ds_in.shape)
                            max_shape[0] = None
                            
                            # VLENデータの判定
                            # h5pyでは、VLENデータ型のdtypeは object であり、metadataを持つ
                            dtype = ds_in.dtype
                            
                            # check_dtype で vlen かどうか確認
                            vlen_type = h5py.check_dtype(vlen=ds_in.dtype)
                            if vlen_type:
                                # VLENの場合、dtypeにその型を指定
                                dtype = h5py.vlen_dtype(vlen_type)
                            
                            # 圧縮設定
                            compression = ds_in.compression
                            compression_opts = ds_in.compression_opts
                            
                            # データセット作成 (maxshapeを指定してリサイズ可能に)
                            grp_out.create_dataset(
                                k,
                                shape=tuple(init_shape),
                                maxshape=tuple(max_shape),
                                dtype=dtype,
                                compression=compression,
                                compression_opts=compression_opts,
                                chunks=True # チャンク有効化
                            )

                        # --- 書き込み ---
                        ds_out = grp_out[k]
                        
                        # 現在のサイズ
                        current_size = ds_out.shape[0]
                        new_size = current_size + n_take
                        
                        # リサイズ
                        ds_out.resize(new_size, axis=0)
                        
                        # データ追記
                        ds_out[current_size:new_size] = data

                    current_events += n_take
                    print(f"  -> Added {n_take} events. (Total: {current_events}/{max_events})")

            except Exception as e:
                print(f"  エラー: ファイル処理中に例外が発生しました: {e}")
                # 処理を続行するか中断するか: ここではスキップして続行する方針
                continue

    if current_events < max_events:
        print(f"警告: 入力ファイルを全て処理しましたが、目標イベント数に達しませんでした。")
        print(f"  Target: {max_events}, Actual: {current_events}")
    else:
        print("目標イベント数に到達しました。")

    print(f"出力完了: {output_file_path}")

if __name__ == "__main__":
    MergeH5Job().main()