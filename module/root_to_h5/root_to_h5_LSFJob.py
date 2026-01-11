# module/root_to_h5/root_to_h5_LSFJob.py

import os
from utils.base.lsf_job import LSFJob
from module.root_to_h5.root_to_h5_BatchJob import RootToH5BatchJob

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

        # このファイル(root_to_h5_LSFJob.py)と同じディレクトリにあるBatchJobスクリプトの絶対パスを取得
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "root_to_h5_BatchJob.py")
        
        # プロジェクトルート(../../)を算出し、PYTHONPATHに追加して実行させる
        project_root = os.path.dirname(os.path.dirname(current_dir))

        # コマンドライン引数の構築
        cmd_parts = [
            f"export PYTHONPATH={project_root}:$PYTHONPATH;",
            "python", script_path,
            inputfile_path,
            h5_file_path,
            f"--compression-level {args.compression_level}"
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