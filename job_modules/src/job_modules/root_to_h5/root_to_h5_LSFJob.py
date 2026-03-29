# module/root_to_h5/root_to_h5_LSFJob.py

import os
from job_framework.lsf_job import LSFJob
from job_modules.root_to_h5.root_to_h5_BatchJob import RootToH5BatchJob

class RootToH5LSFJob(LSFJob):

    def add_args(self, parser):
        # BatchJobと共通の引数を定義
        RootToH5BatchJob.add_conversion_args(parser)

    def setup_output_dirs(self, args, outputdir):
        # BatchJobのロジックを再利用
        return RootToH5BatchJob.setup_output_dirs(args, outputdir)

    def generate_command(self, inputfile_path, output_basename, args, output_dirs):
        h5_dir = output_dirs["h5"]
        h5_file_path = os.path.join(h5_dir, f"{output_basename}.h5")

        # コマンドライン引数の構築
        # インストールされた `root-to-h5-batch` コマンドを使用する
        cmd_parts = [
            "root-to-h5-batch",
            inputfile_path,
            h5_file_path,
            "--compression-level", str(args.compression_level)
        ]

        # フラグ引数の処理 (store_falseなので、Falseの場合にフラグを付与)
        if not args.force_flat:
            cmd_parts.append("--no-flat")

        cmd = " ".join(cmd_parts)
        
        # リストファイル用エントリ
        list_entries = {"h5": h5_file_path}
        
        return cmd, list_entries

if __name__ == "__main__":
    RootToH5LSFJob().main()