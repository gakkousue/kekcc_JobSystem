# utils/base/lsf_job.py
import os
import stat
import subprocess
from utils.base.structured_job_base import StructuredJobBase, is_non_empty_string

class LSFJob(StructuredJobBase):
  """
  StructuredJobBaseを拡張し、LSF (bsub) へのジョブ投入機能を追加したクラス。
  """

  def _add_args(self, parser):
    super()._add_args(parser)
    # LSF固有の引数を追加
    parser.add_argument("-q", "--queue", default="s",
                        help="キュー名",
                        validate=[is_non_empty_string])
    pass

  def _setup_output_dirs(self, args, outputdir):
    """ユーザー定義ディレクトリにLSF必須ディレクトリをマージする"""
    dirs = super()._setup_output_dirs(args, outputdir)
    
    # LSFJob必須ディレクトリを追加
    logs_dir = os.path.join(outputdir, "logs")
    dirs['log'] = os.path.join(logs_dir, "log")
    dirs['bsublog'] = os.path.join(logs_dir, "bsublog")
    dirs['sh'] = os.path.join(logs_dir, "sh")
    
    return dirs

  def generate_command(self, inputfile_path, output_basename, args, output_dirs):
    """
    サブクラスで実装必須。
    戻り値: (実行するコマンド文字列, リストエントリの辞書)
    """
    raise NotImplementedError

  def process_file(self, inputfile_path, output_basename, args, output_dirs):
    """StructuredJobBaseから呼ばれるメイン処理: .sh作成 -> bsub"""
    
    workdir = os.getcwd()
    input_basename = os.path.basename(inputfile_path)
    
    # 1. 実行コマンドとリストエントリの取得
    cmd_string, list_entries = self.generate_command(inputfile_path, output_basename, args, output_dirs)
    
    # ログファイルのパス (setup_output_dirsで定義されている前提)
    logfile = os.path.join(output_dirs['log'], f"{output_basename}.log")
    bsublogfile = os.path.join(output_dirs['bsublog'], f"{output_basename}.bsublog")
    shfile = os.path.join(output_dirs['sh'], f"{output_basename}.sh")

    # 2. シェルスクリプト生成
    sh_content = [
        f"cd {workdir}",
        f"{cmd_string} >& {logfile}"
    ]

    with open(shfile, 'w') as sh:
      sh.write("\n".join(sh_content) + "\n")

    os.chmod(shfile, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    # 3. BSUB投入
    cmd = ["bsub", "-o", bsublogfile, "-q", args.queue, shfile]
    
    try:
      subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
      print(f"Failed to submit job for {inputfile_path}: {e}")
      raise e

    return list_entries