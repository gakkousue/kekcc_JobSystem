# job_framework/batch_run.py
import json
import argparse
import sys
import os
import importlib
import importlib.util
import inspect
from job_framework.argument_parser import InteractiveArgumentParser
from job_framework.structured_job_base import StructuredJobBase
from job_framework.batch_job import BatchJob

class TerminalIndenter:
    """指定されたストリームにインデントを付与して出力するラッパー"""
    def __init__(self, target_stream, indent_str=""):
        self.target_stream = target_stream
        self.indent_str = indent_str

    def write(self, message):
        if self.indent_str and message:
            lines = message.splitlines(True)
            indented = "".join([self.indent_str + line if line.strip("\r\n") else line for line in lines])
            self.target_stream.write(indented)
        else:
            self.target_stream.write(message)

    def flush(self):
        if hasattr(self.target_stream, 'flush'):
            self.target_stream.flush()

class JobDualStream:
    """自分のログファイルと、別ストリーム(親のターミナル等)に分けて出力する"""
    def __init__(self, log_file, terminal_stream):
        self.log_file = log_file
        self.terminal_stream = terminal_stream

    def write(self, message):
        if self.log_file:
            self.log_file.write(message)
        if self.terminal_stream:
            self.terminal_stream.write(message)
        self.flush()

    def flush(self):
        if self.log_file:
            self.log_file.flush()
        if hasattr(self.terminal_stream, 'flush'):
            self.terminal_stream.flush()

    @property
    def terminal(self):
        """子供が親のログファイルをバイパスしてターミナルに直行できるようにする"""
        return self.terminal_stream

def load_batch_job_class(target, class_name, is_module=False):
    """
    指定されたモジュール名、またはファイルパス(.py)から、
    指定されたクラス名のBatchJobサブクラスをロードして返す。
    """
    module = None
    try:
        if is_module:
            # パッケージ化されたモジュールからのロード (例: "job_modules.run_marlin.run_marlin")
            module = importlib.import_module(target)
            module_name = target
        else:
            # 外部ファイル(.py)からのロード
            path = target
            if not path.endswith('.py'):
                path += '.py'

            if not os.path.exists(path):
                raise FileNotFoundError(f"スクリプトファイル '{path}' が見つかりません。")

            module_name = os.path.splitext(os.path.basename(path))[0]
            file_path = os.path.abspath(path)
            file_dir = os.path.dirname(file_path)

            if file_dir not in sys.path:
                sys.path.insert(0, file_dir)

            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            else:
                raise ImportError(f"モジュールスペックの作成に失敗しました: {path}")

        # ロードしたモジュールからクラスを取得
        if hasattr(module, class_name):
            obj = getattr(module, class_name)
            if inspect.isclass(obj) and issubclass(obj, BatchJob) and obj is not BatchJob:
                return obj
            else:
                raise ImportError(f"クラス '{class_name}' は BatchJob のサブクラスではありません。")
        else:
            raise ImportError(f"モジュール '{module_name}' にクラス '{class_name}' が見つかりません。")

    except Exception as e:
        target_type = "モジュール" if is_module else "スクリプト"
        raise ImportError(f"{target_type} '{target}' のロード中にエラーが発生しました: {e}")


class BatchRunnerJob(StructuredJobBase):
  """
  バッチランナー自身も StructuredJobBase として実装する。
  これによりログの出力先管理などを統合し、入れ子実行時にも対応可能になる。
  """

  def _add_positional_args(self, parser):
    """
    引数の順序を制御し、config_file と outputdir を定義する。
    """
    # 1. 設定ファイル
    parser.add_argument(
      "config_file",
      nargs="?", 
      help="実行したいジョブの設定が記述されたJSONファイル。",
      prompt="ジョブ設定JSONファイル: ",
      validate="file_exists"
    )
    
    # 2. ランナー自身の出力（ログなど）用ディレクトリ
    parser.add_argument(
      "outputdir", nargs="?", 
      default=os.getcwd(),
      help="ランナー自体のログ出力ディレクトリ（省略時はカレントディレクトリ）"
    )

  def execute(self, args):
    """
    トップレベルで実行される場合(__main__から呼ばれる場合や、明示的な深さ0の場合)は、
    ランナー自身のログファイル(batch_run.log)を作成してからジョブを実行する。
    """
    depth_env = os.environ.get("BATCH_RUN_DEPTH", "0")
    depth = int(depth_env)
    
    top_log_file = None
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    if depth == 0:
        # JSON設定からbase_output_dirの取得を試みる
        config_base_dir = ""
        if hasattr(args, 'config_file') and args.config_file and os.path.exists(args.config_file):
            try:
                import json
                with open(args.config_file, 'r') as f:
                    config_data = json.load(f)
                    config_base_dir = config_data.get("common_settings", {}).get("base_output_dir", "")
            except Exception:
                pass
                
        base_dir = getattr(args, 'base_output_dir', "") or config_base_dir

        if base_dir:
            log_dir = base_dir
        else:
            log_dir = args.outputdir

        os.makedirs(log_dir, exist_ok=True)
        top_log_path = os.path.join(log_dir, "batch_run.log")
        top_log_file = open(top_log_path, 'a' if os.path.exists(top_log_path) else 'w')
        
        # トップレベルの出力はインデントなし
        sys.stdout = JobDualStream(top_log_file, original_stdout)
        sys.stderr = JobDualStream(top_log_file, original_stderr)

    try:
        super().execute(args)
    finally:
        if top_log_file:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            top_log_file.close()

  def run_structured_job(self, args, custom_output_dirs):
    depth_env = os.environ.get("BATCH_RUN_DEPTH", "0")
    depth = int(depth_env)
    os.environ["BATCH_RUN_DEPTH"] = str(depth + 1)

    try:
      config_path = args.config_file
      
      # --- 1. 設定ファイルの読み込み ---
      try:
        with open(config_path, 'r') as f:
          config_data = json.load(f)
      except json.JSONDecodeError as e:
        print(f"エラー: 設定ファイル '{config_path}' のフォーマットが不正です: {e}")
        raise e

      # --- 2. ターゲットの決定 (モジュール or スクリプト) ---
      common = config_data.get("common_settings", {})
      
      target_module = config_data.get("target_module") or common.get("target_module")
      target_script = config_data.get("target_script") or common.get("target_script")
      
      is_module = False
      target = None

      if target_module:
          target = target_module
          is_module = True
      elif target_script:
          target = target_script
          is_module = False
      else:
          print("実行対象のモジュール(target_module) または スクリプト(target_script) が指定されていません。")
          while not target:
              val = input("実行するPythonモジュール名 または スクリプトのパス: ").strip()
              if val:
                  # パスっぽい入力(.py終わり、またはスラッシュ/バックスラッシュを含む)ならスクリプトとみなす
                  if val.endswith('.py') or '/' in val or '\\' in val:
                      target = val
                      is_module = False
                  else:
                      target = val
                      is_module = True

      # --- 3. モジュールの動的ロードとクラス取得 ---
      target_class_name = config_data.get("target_class")

      if not target_class_name:
        print("エラー: 実行するクラス名が指定されていません。")
        while not target_class_name:
          val = input("実行するBatchJobクラス名: ").strip()
          if val:
            target_class_name = val

      try:
        JobClass = load_batch_job_class(target, target_class_name, is_module)
        # インスタンス化
        job_instance = JobClass()
        target_parser = job_instance.get_parser()
      except Exception as e:
        print(f"エラー: {e}")
        raise e


      # --- 4. 設定の読み込みとジョブ実行 ---
      common_settings = config_data.get("common_settings", {})
      jobs = config_data.get("jobs", [])

      if not jobs:
        print("エラー: 設定ファイルに実行すべき 'jobs' が見つかりません。")
        return

      # --- 5. 事前検証 (Phase 1) ---
      print(f"\n合計 {len(jobs)} 件のジョブの設定を検証しています...")
      target_type_str = "Module" if is_module else "Script"
      print(f"Target {target_type_str}: {target} ({JobClass.__name__})")

      execution_queue = []
      has_validation_errors = False

      for i, job_config in enumerate(jobs):
        job_number = i + 1
        
        final_params = common_settings.copy()
        final_params.update(job_config)
        comment = final_params.get("comment", f"ジョブ {job_number}")

        try:
          # パラメータ辞書をコマンドライン引数リストに変換
          arg_list = self._convert_params_to_arg_list(target_parser, final_params)
          # 非対話モードでパース＆バリデーション実行
          # ここで失敗すると例外が飛び、実行キューには追加されない
          args_namespace = target_parser.parse_args(arg_list, interactive=False)
          
          # 成功したら実行キューに追加 (パラメータとメタデータを保存)
          execution_queue.append({
            "job_number": job_number,
            "args": args_namespace,
            "params": final_params, # ログパス計算用
            "comment": comment
          })

        except (argparse.ArgumentError, SystemExit) as e:
          has_validation_errors = True
          print(f"\n[Validation Error] Job {job_number}: パラメータが不正です。")
          print(f"  Reason: {e}")
          # エラーがあっても全ジョブ検証するためにループは続ける
        
      if has_validation_errors:
        print("\n" + "!"*60)
        print("エラー: ジョブ設定に不備が見つかったため、実行を中止します。")
        print("上記のエラー内容を修正してから再実行してください。")
        print("!"*60)
        return

      # --- 6. ジョブの逐次実行 (Phase 2) ---
      print(f"\n検証完了。全てのジョブ設定は有効です。実行を開始します...")

      for task in execution_queue:
        job_number = task["job_number"]
        args_namespace = task["args"]
        final_params = task["params"]
        comment = task["comment"]

        print("\n" + "="*50)
        print(f"ジョブ {job_number}/{len(jobs)} を開始します: {comment}")
        print("="*50)

        # ログファイルの場所決定
        # ジョブごとのログは、各ジョブの outputdir に出力する（JSON内で定義されていれば）
        # 定義されていなければ、ランナー自身の outputdir を使用する
        log_dir = args.outputdir 
        if "outputdir" in final_params:
          out_dir_val = final_params["outputdir"]
          base_dir_val = final_params.get("base_output_dir", "")
          if base_dir_val and not os.path.isabs(out_dir_val):
            log_dir = os.path.join(base_dir_val, out_dir_val)
          else:
            log_dir = out_dir_val

        os.makedirs(log_dir, exist_ok=True)
        if is_module:
            # モジュール名の場合は最後の要素をベース名とする (例: "run_marlin.run_marlin" -> "run_marlin")
            script_basename = target.split('.')[-1]
        else:
            script_basename = os.path.splitext(os.path.basename(target))[0]
            
        log_file_path = os.path.join(log_dir, f"{script_basename}.log")
        print(f"ログファイル: {log_file_path}")
        
        # 実行
        original_stdout_job = sys.stdout
        original_stderr_job = sys.stderr
        parent_terminal_out = original_stdout_job.terminal if hasattr(original_stdout_job, 'terminal') else original_stdout_job
        parent_terminal_err = original_stderr_job.terminal if hasattr(original_stderr_job, 'terminal') else original_stderr_job
        
        indent_out = TerminalIndenter(parent_terminal_out, "    ")
        indent_err = TerminalIndenter(parent_terminal_err, "    ")

        with open(log_file_path, 'w') as log_f:
          sys.stdout = JobDualStream(log_f, indent_out)
          sys.stderr = JobDualStream(log_f, indent_err)
          try:
            job_instance.execute(args_namespace)
            
            sys.stdout = original_stdout_job
            print(f"\n>> ジョブ {job_number} は正常に終了しました。")

          except Exception as e:
            sys.stdout = original_stdout_job
            sys.stderr = original_stderr_job
            print(f"\n>> エラー: ジョブ {job_number} の実行中にエラーが発生しました。")
            print(f"   エラー内容: {e}")
            print(f"   エラータイプ: {type(e).__name__}")
            
            print("\n--- BATCH EXECUTION ERROR ---", file=log_f)
            print(f"Error Type: {type(e).__name__}", file=log_f)
            print(f"Error Message: {e}", file=log_f)
            import traceback
            traceback.print_exc(file=log_f)  # スタックトレースも追加
            continue
          finally:
            sys.stdout = original_stdout_job
            sys.stderr = original_stderr_job

      print("\n" + "="*50)
      print("全てのジョブ処理が完了しました。")
      print("="*50)

    finally:
      os.environ["BATCH_RUN_DEPTH"] = str(depth)

  def _convert_params_to_arg_list(self, parser, params_dict):
    """
    パラメータ辞書をコマンドライン引数のリストに変換する。
    """
    arg_list = []
    # パーサーに定義された引数のみを対象にする
    known_dests = {action.dest for action in parser._actions}
    
    # 位置引数を先に追加
    positional_actions = [action for action in parser._actions if not action.option_strings]
    for action in positional_actions:
      if action.dest in params_dict:
        value = params_dict[action.dest]
        arg_list.append(str(value))

    # オプション引数を追加
    option_actions = [action for action in parser._actions if action.option_strings]
    for action in option_actions:
      if action.dest in params_dict:
        key = action.option_strings[0] # e.g., '--queue'
        value = params_dict[action.dest]

        # store_true/store_falseのようなフラグ
        if action.nargs == 0:
          # const属性がある場合（store_true/store_falseアクション）
          if hasattr(action, 'const'):
            # valueがconstと一致する場合のみ引数を追加
            if value == action.const:
              arg_list.append(key)

        # 複数引数を取る場合 (e.g., nargs='+')
        elif isinstance(value, list):
          arg_list.append(key)
          arg_list.extend(map(str, value))
        # 通常の引数
        else:
          arg_list.append(key)
          arg_list.append(str(value))
          
    return arg_list

def main():
    BatchRunnerJob().main()

if __name__ == "__main__":
  main()