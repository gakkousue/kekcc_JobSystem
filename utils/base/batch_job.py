# utils/base/batch_job.py
from abc import ABC, abstractmethod
import sys
from utils.base.argument_parser import InteractiveArgumentParser

class BatchJob(ABC):
  """
  バッチ処理可能なジョブスクリプトの基底クラス。
  全てのジョブスクリプトはこのクラスを継承し、get_parserとexecuteを実装する。
  """

  @abstractmethod
  def get_parser(self):
    """
    ArgumentParser (またはそのサブクラス) を構築して返す。
    """
    pass

  @abstractmethod
  def execute(self, args):
    """
    解析された引数(args)を受け取り、ジョブのメイン処理を実行する。
    """
    pass

  def get_default_values(self):
    """
    パーサーに設定されている全引数のデフォルト値を辞書として返す。
    バッチランナーがデフォルト設定を取得するために使用する。
    """
    parser = self.get_parser()
    defaults = {}
    for action in parser._actions:
      if action.dest and action.dest != argparse.SUPPRESS:
        if action.default != argparse.SUPPRESS:
          defaults[action.dest] = action.default
    return defaults

  def main(self):
    """
    単体スクリプトとして実行された場合のエントリーポイント。
    """
    parser = self.get_parser()
    args = parser.parse_args()

    # 対話型パーサーの場合、かつターミナルからの実行時のみオプション確認を実行
    if hasattr(parser, 'confirm_options') and sys.stdin.isatty():
      parser.confirm_options(args)
    
    try:
      self.execute(args)
    except Exception as e:
      print(f"\nエラーが発生したため処理を中断しました: {e}", file=sys.stderr)
      sys.exit(1)