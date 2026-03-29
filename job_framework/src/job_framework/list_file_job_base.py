# utils/base/list_file_job_base.py
import os
from job_framework.structured_job_base import StructuredJobBase

# ==========================================
# 共通バリデーション関数 (ListFile用)
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


# ==========================================
# リストファイルジョブ基底クラス
# ==========================================
class ListFileJobBase(StructuredJobBase):
  """
  StructuredJobBaseを拡張し、.listファイルを入力として各ファイルをループ処理するクラス。
  """

  def _add_positional_args(self, parser):
    """
    引数の順序を制御するため、位置引数を定義します。
    """
    parser.add_argument("listfile", nargs="?", 
                        help="入力ファイルリスト (.list)",
                        prompt="入力ファイルリスト (.list): ",
                        validate=[check_list_extension])

    # StructuredJobBase の outputdir をリストファイルの後に追加
    super()._add_positional_args(parser)

    parser.add_argument("count", nargs="?",
                        help="処理するファイル数 (-1=全て)",
                        prompt="処理するファイル数 (-1=全て): ",
                        validate=[is_valid_count])

  def _add_optional_args(self, parser):
    """
    オプション引数を定義します。
    """
    super()._add_optional_args(parser)

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

    parser.add_argument("-b", "--list-base-dir", dest="list_base_dir", default=os.getcwd(),
                        help="リストファイルの基準ディレクトリ")

    parser.add_argument("-s", "--nstart", type=int, default=1,
                        help="開始行番号",
                        validate=[is_positive_integer])

  def process_file(self, inputfile_path, output_basename, args, output_dirs):
    """
    サブクラスでオーバーライドして、1ファイルごとの処理（コマンド生成、ジョブ投入など）を行ってください。
    
    戻り値: { 'category_key': 'list_entry_string' }
    ※ リストファイルに出力する文字列（ファイル名など）を返してください。
    """
    raise NotImplementedError("process_file must be implemented in subclass")

  def run_structured_job(self, args, custom_output_dirs):
    """
    StructuredJobBaseから委譲されるメインの実行ロジック。
    .listファイルの読み込みと各ファイルの処理を行います。
    """
    # パス結合処理
    if args.base_listfile_dir and not os.path.isabs(args.listfile):
        args.listfile = os.path.join(args.base_listfile_dir, args.listfile)
    
    # listfileのあるディレクトリを基準にする場合
    if args.use_listfile_dir:
        args.list_base_dir = os.path.dirname(os.path.abspath(args.listfile))
    elif args.base_list_base_dir_dir and not os.path.isabs(args.list_base_dir):
        args.list_base_dir = os.path.join(args.base_list_base_dir_dir, args.list_base_dir)

    listfile = args.listfile
    list_base_dir = args.list_base_dir
    count = int(args.count)
    nstart = int(args.nstart)

    if not os.path.isfile(listfile):
      raise FileNotFoundError(f"エラー: リストファイル '{listfile}' が見つかりません。")

    if not os.path.isdir(list_base_dir):
      raise FileNotFoundError(f"エラー: 基準ディレクトリ '{list_base_dir}' が見つかりません。")

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