# module/run_marlin/run_marlin.py
import os
from utils.base.lsf_job import LSFJob, is_non_empty_string

# ==========================================
# ジョブクラス定義
# ==========================================
class MarlinJob(LSFJob):
  
  def add_args(self, parser):
    """Marlin固有の引数を追加"""
    
    parser.add_argument("xml", nargs="?", 
                        help="MarlinのSteering XMLファイル",
                        prompt="Marlin Steering XMLファイル: ",
                        validate="file_exists")

    parser.add_argument("-m", "--marlin-output-param-name", dest="marlin_output_param_name", default="MyLCIOOutputProcessor.LCIOOutputFile",
                        help="SLCIO出力パラメータ名",
                        validate=[is_non_empty_string])

    parser.add_argument("-r", "--root_processors", nargs='+', default=[],
                        help="ROOT出力プロセッサ (例: MyProc.RootFile)")

    parser.add_argument("-E", "--env-vars-file", dest="env_vars_file", default=None,
                        help="環境変数定義ファイル",
                        validate=["file_exists"])

    parser.add_argument("--no-slcio", dest="no_slcio", action="store_true",
                        help="SLCIOファイルの出力を無効にする")

  def setup_output_dirs(self, args, outputdir):
    """Marlin固有の出力ディレクトリ定義"""
    dirs = {}
    
    # SLCIO
    if not args.no_slcio:
        dirs['slcio'] = os.path.join(outputdir, "slcio")
    
    # ROOT (プロセッサごと)
    if args.root_processors:
      root_base_dir = os.path.join(outputdir, "root")
      for param in args.root_processors:
        # '.' で分割して階層にする
        dir_parts = param.split('.')[:-1]
        proc_dir = os.path.join(root_base_dir, *dir_parts)
        dirs[param] = proc_dir
    
    return dirs

  def generate_command(self, inputfile_path, output_basename, args, output_dirs):
    """Marlinコマンドの生成"""

    input_basename = os.path.basename(inputfile_path)
    
    # 1. 環境変数の設定 (あれば)
    cmd_lines = []
    if args.env_vars_file:
        env_vars_file_path = os.path.abspath(args.env_vars_file)
        cmd_lines.append(f"export $(cat {env_vars_file_path})")
        
    # 2. Marlinコマンド本体の構築
    marlin_cmd_parts = [
        "Marlin",
        f"--global.LCIOInputFiles={inputfile_path}",
    ]

    list_entries = {}

    if args.no_slcio:
        # XMLのデフォルト設定で出力されるのを防ぐため、明示的に /dev/null に捨てる
        marlin_cmd_parts.append(f"--{args.marlin_output_param_name}=/dev/null")
    else:
        slcio_file = os.path.join(output_dirs['slcio'], input_basename)
        marlin_cmd_parts.append(f"--{args.marlin_output_param_name}={slcio_file}")
        list_entries['slcio'] = input_basename # リストにはファイル名のみ

    if args.root_processors:
        for param in args.root_processors:
            proc_root_dir = output_dirs[param]
            root_filename = f"{output_basename}.root"
            root_output_path = os.path.join(proc_root_dir, root_filename)
            
            marlin_cmd_parts.append(f"--{param}={root_output_path}")
            list_entries[param] = root_filename

    marlin_cmd_parts.append(args.xml)
    
    cmd_lines.append(" ".join(marlin_cmd_parts))

    # コマンド全体を結合して返す
    return "\n".join(cmd_lines), list_entries

if __name__ == "__main__":
  MarlinJob().main()