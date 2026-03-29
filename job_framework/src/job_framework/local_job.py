# utils/base/local_job.py
import os
import subprocess
from job_framework.list_file_job_base import ListFileJobBase

class LocalJob(ListFileJobBase):
  """
  ListFileJobBaseを拡張し、ローカル環境で直接実行するクラス。
  ジョブスケジューラは使用しません。
  """

  def _add_args(self, parser):
    super()._add_args(parser)
    pass

  def _setup_output_dirs(self, args, outputdir):
    """ユーザー定義ディレクトリにLocalJob必須ディレクトリをマージする"""
    dirs = self.setup_output_dirs(args, outputdir)
    
    # LocalJob必須ディレクトリ(ログ用)を追加
    logs_dir = os.path.join(outputdir, "logs")
    dirs['log'] = os.path.join(logs_dir, "log")
    
    return dirs

  def run_local(self, inputfile_path, output_basename, args, output_dirs):
      """
      generate_command と同じ引数。
      戻り値も同じく list_entries。
      """
      raise NotImplementedError

  def process_file(self, inputfile_path, output_basename, args, output_dirs):
      logfile = os.path.join(output_dirs['log'], f"{output_basename}.log")
      print(f"Running (local): {output_basename}")

      with open(logfile, 'w') as log_f:
          old_stdout, old_stderr = os.sys.stdout, os.sys.stderr
          os.sys.stdout = os.sys.stderr = log_f
          try:
              list_entries = self.run_local(
                  inputfile_path,
                  output_basename,
                  args,
                  output_dirs
              )
          finally:
              os.sys.stdout, os.sys.stderr = old_stdout, old_stderr

      return list_entries