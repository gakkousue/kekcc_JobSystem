# utils/base/structured_job_base.py
import os
from job_framework.batch_job import BatchJob
from job_framework.argument_parser import InteractiveArgumentParser

# ==========================================
# 共通バリデーション関数
# ==========================================
def is_non_empty_string(value):
  if not str(value).strip():
    print("Error: 値を入力してください。")
    return False
  return True

# ==========================================
# 構造化ジョブ基底クラス
# ==========================================
class StructuredJobBase(BatchJob):
  """
  ディレクトリ構造を維持して処理を行うジョブの基底クラス。
  出力ディレクトリの作成など共通の準備を行います。
  """

  def get_parser(self):
    parser = InteractiveArgumentParser(
      description="Structured Job Generator"
    )

    # 引数追加の順序をサブクラスで制御できるようにフックメソッドを使用
    self._add_positional_args(parser)
    self._add_optional_args(parser)
    
    # サブクラス用フック
    self._add_args(parser)
    self.add_args(parser)
    
    return parser

  def _add_positional_args(self, parser):
    """
    位置引数を定義します。サブクラスでオーバーライドして順序を調整可能です。
    """
    parser.add_argument("outputdir", nargs="?", 
                        help="出力ディレクトリ",
                        prompt="出力ディレクトリ: ",
                        validate=[is_non_empty_string])

  def _add_optional_args(self, parser):
    """
    オプション引数を定義します。
    """
    parser.add_argument("--base-output-dir", dest="base_output_dir", default="",
                        help="outputdirが相対パスの場合、このディレクトリを基準にします。")

  def add_args(self, parser):
    """
    サブクラスでオーバーライドして、独自の引数（queue, env, xmlなど）を追加してください。
    """
    pass

  def _add_args(self, parser):
    """
    [内部用]サブクラスでオーバーライドして、独自の引数（queue, env, xmlなど）を追加してください。
    """
    pass

  def setup_output_dirs(self, args, outputdir):
    """
    サブクラスでオーバーライドして、必要な出力ディレクトリを定義してください。
    戻り値: { 'category_key': 'full_dir_path' }
    """
    return {}

  def _setup_output_dirs(self, args, outputdir):
    """
    [内部用] 最終的なディレクトリ辞書を構築します。
    LSFJobなどの中間クラスが、システム必須のディレクトリを追加するためにオーバーライドします。
    """
    return self.setup_output_dirs(args, outputdir)

  def run_structured_job(self, args, custom_output_dirs):
    """
    サブクラスでオーバーライドして、実際のジョブ処理フローを記述してください。
    """
    raise NotImplementedError("run_structured_job must be implemented in subclass")

  def execute(self, args):
    # パス結合処理
    if hasattr(args, 'base_output_dir') and args.base_output_dir and not os.path.isabs(args.outputdir):
        args.outputdir = os.path.join(args.base_output_dir, args.outputdir)

    outputdir = args.outputdir

    print("Setting up output directories...")
    # ジョブ固有のディレクトリ作成 (サブクラスへのフック + システム必須ディレクトリ)
    custom_output_dirs = self._setup_output_dirs(args, outputdir)
    
    # 少なくともoutputdir自体は作成
    os.makedirs(outputdir, exist_ok=True)
    for d in custom_output_dirs.values():
        os.makedirs(d, exist_ok=True)

    # 実際のジョブ実行ロジックへ委譲
    self.run_structured_job(args, custom_output_dirs)