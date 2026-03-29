# utils/excute/batch_run.py
import json
import argparse
import sys
import os
import importlib
import importlib.util
import inspect
from utils.base.argument_parser import InteractiveArgumentParser
from utils.base.structured_job_base import StructuredJobBase
from utils.base.batch_job import BatchJob

def load_batch_job_class(path, class_name):
    """
    指定されたファイルパス(.py)から指定されたクラス名のBatchJobサブクラスを返す。
    class_nameの指定が必須となります。
    """
    if not path.endswith('.py'):
        path += '.py'

    if not os.path.exists(path):
        raise FileNotFoundError(f"スクリプトファイル '{path}' が見つかりません。")

    try:
        module_name = os.path.splitext(os.path.basename(path))[0]
        file_path = os.path.abspath(path)
        file_dir = os.path.dirname(file_path)

        # モジュールのディレクトリをsys.pathに追加
        if file_dir not in sys.path:
            sys.path.insert(0, file_dir)

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # class_nameが指定されている場合のみそのクラスを探す
            if hasattr(module, class_name):
                obj = getattr(module, class_name)
                if inspect.isclass(obj) and issubclass(obj, BatchJob) and obj is not BatchJob:
                    return obj
                else:
                    raise ImportError(
                        f"クラス '{class_name}' は BatchJob のサブクラスではありません。"
                    )
            else:
                raise ImportError(
                    f"モジュール '{module_name}' にクラス '{class_name}' が見つかりません。"
                )
        else:
            raise ImportError(f"モジュールスペックの作成に失敗しました: {path}")

    except Exception as e:
        raise ImportError(f"スクリプト '{path}' のロード中にエラーが発生しました: {e}")


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

  def run_structured_job(self, args, custom_output_dirs):
    config_path = args.config_file
    
    # --- 1. 設定ファイルの読み込み ---
    try:
      with open(config_path, 'r') as f:
        config_data = json.load(f)
    except json.JSONDecodeError as e:
      print(f"エラー: 設定ファイル '{config_path}' のフォーマットが不正です: {e}")
      raise e

    # --- 2. ターゲットスクリプトの決定 ---
    target_script_path = config_data.get("target_script")
    
    if not target_script_path:
      common = config_data.get("common_settings", {})
      target_script_path = common.get("target_script")

    if not target_script_path:
      print("実行対象のスクリプトが指定されていません。")
      while not target_script_path:
        val = input("実行するPythonスクリプトのパス (例: run_marlin.py): ").strip()
        if val: target_script_path = val

    # --- 3. モジュールの動的ロードとクラス取得 ---
    target_class_name = config_data.get("target_class")  # 設定ファイルからクラス名取得

    if not target_class_name:
      print("エラー: 実行するクラス名が指定されていません。")
      while not target_class_name:
        val = input("実行するBatchJobクラス名: ").strip()
        if val:
          target_class_name = val

    try:
      JobClass = load_batch_job_class(target_script_path, target_class_name)
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
    print(f"Target Script: {target_script_path} ({JobClass.__name__})")

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
      script_basename = os.path.splitext(os.path.basename(target_script_path))[0]
      log_file_path = os.path.join(log_dir, f"{script_basename}.log")
      print(f"ログファイル: {log_file_path}")
      
      # 実行
      original_stdout = sys.stdout
      original_stderr = sys.stderr
      with open(log_file_path, 'w') as log_f:
        sys.stdout = log_f
        sys.stderr = log_f
        try:
          job_instance.execute(args_namespace)
          
          sys.stdout = original_stdout
          print(f"\n>> ジョブ {job_number} は正常に終了しました。")

        except Exception as e:
          sys.stdout = original_stdout
          sys.stderr = original_stderr
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
          sys.stdout = original_stdout
          sys.stderr = original_stderr

    print("\n" + "="*50)
    print("全てのジョブ処理が完了しました。")
    print("="*50)

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

if __name__ == "__main__":
  BatchRunnerJob().main()