# module/root_to_h5/root_to_h5_LocalJob.py

import os
import uproot
import h5py
import numpy as np
import awkward as ak
import argparse

from job_framework.local_job import LocalJob
from job_modules.root_to_h5.root_to_h5_BatchJob import RootToH5BatchJob


class RootToH5LocalJob(LocalJob):

    # ----------------------------
    # CLI 引数
    # ----------------------------
    def add_args(self, parser):
        # BatchJobと共通の引数を定義
        RootToH5BatchJob.add_conversion_args(parser)

    # ----------------------------
    # 出力ディレクトリ定義
    # ----------------------------
    def setup_output_dirs(self, args, outputdir):
        # BatchJobのロジックを再利用
        return RootToH5BatchJob.setup_output_dirs(args, outputdir)

    # ----------------------------
    # Local 実行本体
    # ----------------------------
    def run_local(self, inputfile_path, output_basename, args, output_dirs):
        h5_dir = output_dirs["h5"]
        os.makedirs(h5_dir, exist_ok=True)
        h5_file_path = os.path.join(h5_dir, f"{output_basename}.h5")

        # BatchJob用の引数を構築
        # (LocalJobのargsをベースに、入力・出力ファイルパスを追加)
        batch_args = argparse.Namespace(**vars(args))
        batch_args.input_file = inputfile_path
        batch_args.output_file = h5_file_path

        # 変換処理をBatchJobに委譲
        job = RootToH5BatchJob()
        job.execute(batch_args)

        return {"h5": h5_file_path}

if __name__ == "__main__":
    RootToH5LocaJob().main()