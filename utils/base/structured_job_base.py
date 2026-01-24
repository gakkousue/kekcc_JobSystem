# utils/base/structured_job_base.py
import os
from utils.base.batch_job import BatchJob
from utils.base.argument_parser import InteractiveArgumentParser

# ==========================================
# 共通バリデーション関数
# ==========================================
def check_list_extension(filepath):
  if not filepath.endswith(".list"):
    print(f"Error: リストファイル '{filepath}' の拡張子は .list である必要があります。")
    return False
  return True

def check_is_directory(path):
  if not os.path.isdir(path):
    print(f"エラー: ディレクトリ '{path}' が見つかりません。")
    return False
  return True

def is_valid_count(value):
  try:
    val = int(value)
    if val < -1:
      print(f"Error: '{value}' は-1以上の整数である必要があります。")
      return False
    return True
  except ValueError:
    print(f"Error: '{value}' は整数ではありません。")
    return False

def is_positive_integer(value):
  try:
    val = int(value)
    if val < 1:
      print(f"Error: '{value}' は1以上の整数である必要があります。")
      return False
    return True
  except ValueError:
    print(f"Error: '{value}' は整数ではありません。")
    return False

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
  リストファイルを入力とし、ディレクトリ構造を維持して処理を行うジョブの基底クラス。
  ジョブの投入方法(bsub等)は関知せず、ファイルループとリスト生成の構造のみを提供します。
  """

  def get_parser(self):
    parser = InteractiveArgumentParser(
      description="Structured Job Generator"
    )

    # --- 共通の構造に関する必須引数 ---
    parser.add_argument("listfile", nargs="?", 
                        help="入力ファイルリスト (.list)",
                        prompt="入力ファイルリスト (.list): ",
                        validate=[check_list_extension])

    parser.add_argument("outputdir", nargs="?", 
                        help="出力ディレクトリ",
                        prompt="出力ディレクトリ: ",
                        validate=[is_non_empty_string])
    
    # パス解決用ベースディレクトリ引数
    parser.add_argument("--base-output-dir", dest="base_output_dir", default="",
                        help="outputdirが相対パスの場合、このディレクトリを基準にします。")

    parser.add_argument("--base-listfile-dir", dest="base_listfile_dir", default="",
                        help="listfileが相対パスの場合、このディレクトリを基準にします。")

    parser.add_argument("--base-list-base-dir-dir", dest="base_list_base_dir_dir", default="",
                        help="list-base-dirが相対パスの場合、このディレクトリを基準にします。")

    parser.add_argument(
        "--use-listfile-dir", 
        dest="use_listfile_dir",
        action="store_true",
        help="listfileがあるディレクトリを基準にファイルを処理します。"
    )

    # ループ制御引数
    parser.add_argument("count", nargs="?",
                        help="処理するファイル数 (-1=全て)",
                        prompt="処理するファイル数 (-1=全て): ",
                        validate=[is_valid_count])

    parser.add_argument("-b", "--list-base-dir", dest="list_base_dir", default=os.getcwd(),
                        help="リストファイルの基準ディレクトリ")

    parser.add_argument("-s", "--nstart", type=int, default=1,
                        help="開始行番号",
                        validate=[is_positive_integer])

    # サブクラス用フック
    self._add_args(parser)
    self.add_args(parser)
    
    return parser

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

  def process_file(self, inputfile_path, output_basename, args, output_dirs):
    """
    サブクラスでオーバーライドして、1ファイルごとの処理（コマンド生成、ジョブ投入など）を行ってください。
    
    戻り値: { 'category_key': 'list_entry_string' }
    ※ リストファイルに出力する文字列（ファイル名など）を返してください。
    """
    raise NotImplementedError("process_file must be implemented in subclass")

  def execute(self, args):
    # パス結合処理
    if args.base_output_dir and not os.path.isabs(args.outputdir):
        args.outputdir = os.path.join(args.base_output_dir, args.outputdir)

    if args.base_listfile_dir and not os.path.isabs(args.listfile):
        args.listfile = os.path.join(args.base_listfile_dir, args.listfile)
    
    # listfileのあるディレクトリを基準にする場合
    if args.use_listfile_dir:
        args.list_base_dir = os.path.dirname(os.path.abspath(args.listfile))
    elif args.base_list_base_dir_dir and not os.path.isabs(args.list_base_dir):
        args.list_base_dir = os.path.join(args.base_list_base_dir_dir, args.list_base_dir)

    listfile = args.listfile
    outputdir = args.outputdir
    list_base_dir = args.list_base_dir
    count = int(args.count)
    nstart = int(args.nstart)

    if not os.path.isfile(listfile):
      raise FileNotFoundError(f"エラー: リストファイル '{listfile}' が見つかりません。")

    if not os.path.isdir(list_base_dir):
      raise FileNotFoundError(f"エラー: 基準ディレクトリ '{list_base_dir}' が見つかりません。")

    print("Setting up output directories...")
    # ジョブ固有のディレクトリ作成 (サブクラスへのフック + システム必須ディレクトリ)
    custom_output_dirs = self._setup_output_dirs(args, outputdir)
    
    # 少なくともoutputdir自体は作成
    os.makedirs(outputdir, exist_ok=True)
    for d in custom_output_dirs.values():
        os.makedirs(d, exist_ok=True)

    print("リストファイルを読み込んでいます...")
    with open(listfile, 'r') as f:
      all_files = [line.strip() for line in f if line.strip()]

    total_files = len(all_files)
    start_idx = nstart - 1

    if start_idx >= total_files:
      raise ValueError(f"エラー: 開始行 ({nstart}) がファイルの総数 ({total_files}) を超えています。")

    if count == -1:
      target_files = all_files[start_idx:]
      print(f"{nstart}行目から全てのファイル (計 {len(target_files)} ファイル) を処理します。")
    else:
      end_idx = start_idx + count
      target_files = all_files[start_idx:end_idx]
      print(f"{nstart}行目から {nstart + len(target_files) - 1}行目までの {len(target_files)} 個のファイルを処理します。")

    valid_files = []
    missing_files = []

    print("ファイルの存在を確認しています...")
    for filename in target_files:
      if os.path.isabs(filename):
        filepath = filename
      else:
        filepath = os.path.join(list_base_dir, filename)
      
      if os.path.isfile(filepath):
        valid_files.append(filepath)
      else:
        missing_files.append(filepath)

    if missing_files:
      print("-" * 50)
      print(f"警告: 以下の {len(missing_files)} 個のファイルが見つかりません:")
      for f in missing_files:
        print(f"  {f}")
      print("-" * 50)
      raise FileNotFoundError(f"{len(missing_files)} 個のファイルが見つかりません。リストを確認してください。")

    print(f"指定された {len(target_files)} 個のファイルは全て存在します。処理を開始します...")

    # 結果リスト収集用: { 'category': ['entry1', 'entry2'] }
    list_entries = {key: [] for key in custom_output_dirs.keys()}

    for inputfile_path in valid_files:
      input_basename = os.path.basename(inputfile_path)
      output_basename, _ = os.path.splitext(input_basename)

      # 個別ファイル処理 (サブクラスへのフック)
      output_entries = self.process_file(inputfile_path, output_basename, args, custom_output_dirs)
      
      # リスト用エントリを保存
      if output_entries:
        for cat, entry in output_entries.items():
            if cat in list_entries:
                list_entries[cat].append(entry)

    print(f"\n処理が完了しました。")

    # .list ファイル生成
    for category, entries in list_entries.items():
        if entries and category in custom_output_dirs:
            target_dir = custom_output_dirs[category]
            list_path = os.path.join(target_dir, ".list")
            print(f"出力リストを生成しています ({category}): {list_path}")
            with open(list_path, 'w') as f:
                f.write("\n".join(entries) + "\n")
      
    print("完了しました。")