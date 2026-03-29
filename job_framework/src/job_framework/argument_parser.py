# utils/base/argument_parser.py
import argparse
import os
import sys

class InteractiveArgumentParser(argparse.ArgumentParser):
  """
  argparse.ArgumentParserを拡張し、引数が指定されなかった場合、
  または指定された値が不正な場合に対話的に入力を求めるクラス。
  """

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # 引数ごとの対話設定を保持する辞書
    self.interactive_configs = {}

  def add_argument(self, *args, **kwargs):
    """
    add_argumentをオーバーライドして、prompt(対話時のメッセージ)とvalidate(検証ルール)を受け取れるようにする。
    """
    # カスタム引数をkwargsから取り出す（argparseに渡すとエラーになるため）
    prompt = kwargs.pop('prompt', None)
    validate = kwargs.pop('validate', None)

    # 本来のadd_argumentを呼び出してActionオブジェクトを取得
    action = super().add_argument(*args, **kwargs)

    # validateかpromptが設定されている場合、設定を保存しておく
    if prompt or validate:
      self.interactive_configs[action.dest] = {
        'prompt': prompt,
        'validate': validate
      }
    return action

  def parse_args(self, args=None, namespace=None, interactive=True):
    """
    parse_argsをオーバーライドして、不足している引数や不正な引数について対話的に入力を求める。
    interactive=False に設定すると、対話を試みずに例外を発生させる。
    """
    # まずは通常の引数解析を行う
    namespace, _ = self.parse_known_args(args, namespace)

    validation_errors = [] # エラー収集用リスト

    # 対話設定がある引数についてチェック
    for dest, config in self.interactive_configs.items():
      current_value = getattr(namespace, dest, None)
      validate_rules = config.get('validate')
      prompt = config.get('prompt')
      
      # 入力が必要かどうかのフラグ
      is_missing = current_value is None
      is_invalid = False
      if not is_missing and validate_rules:
        if not self._run_validation(current_value, validate_rules):
          is_invalid = True
      
      # 入力が必要なケース
      if is_missing or is_invalid:
        # 対話モードが有効な場合のみ入力を求める
        if interactive and prompt:
          if is_invalid:
            print(f">> 引数 '{dest}' の値 '{current_value}' は無効です。再入力してください。")
          new_value = self._interactive_input(prompt, validate_rules)
          setattr(namespace, dest, new_value)
        # 非対話モードではエラーを収集する (即時停止しない)
        else:
          action = self._get_action_by_dest(dest)
          if is_missing:
            # プロンプトが設定されている場合、非対話モードでは必須項目として扱う
            # (値がなく、かつデフォルト値もない状態)
            if prompt:
                validation_errors.append(f"必須引数 '{dest}' が指定されていません。")
            
            # プロンプトがない場合でも、必須の位置引数であればエラー
            elif action and not action.option_strings and action.nargs != '?':
                validation_errors.append(f"必須引数 '{dest}' が指定されていません。")
          
          if is_invalid:
            # バリデーション失敗時のエラーメッセージは _run_validation 内で表示されるが、
            # 最終的なエラーサマリのためにリストにも追加しておく
            validation_errors.append(f"引数 '{dest}' の値 '{current_value}' がバリデーションに失敗しました。")

    # 全ての引数のチェック終了後にエラーがあればまとめて例外を投げる
    if validation_errors and not interactive:
       error_msg = "\n".join(validation_errors)
       raise argparse.ArgumentError(None, f"パラメータ検証エラー:\n{error_msg}")

    return namespace

  def _get_action_by_dest(self, dest):
    """dest名からactionオブジェクトを探す"""
    for action in self._actions:
        if action.dest == dest:
            return action
    return None

  def _run_validation(self, value, rules):
    """
    値に対してルール（単一またはリスト）を適用する。
    すべてのルールをパスしたらTrue、そうでなければFalseを返す。
    エラーメッセージは各検証処理内で表示する。
    1つ失敗しても残りのルールも検証し、すべてのエラーを表示する。
    """
    if not isinstance(rules, list):
      rules = [rules]
    
    is_valid = True
    for rule in rules:
      if not rule: continue
      if not self._validate_single_rule(value, rule):
        is_valid = False
        # return False をしないことで全てのルールを回す
    
    return is_valid

  def _validate_single_rule(self, value, rule):
    """
    単一のルールによる検証を行う。
    """
    # 関数（callable）の場合 -> 実行してTrue/Falseを受け取る
    if callable(rule):
      return rule(value)
    
    # 文字列ルールの場合
    if isinstance(rule, str):
      if rule == 'file_exists':
        if os.path.isfile(str(value)):
          return True
        else:
          print(f"Error: ファイル '{value}' が見つかりません。")
          return False
      
      elif rule == 'dir_create' or rule == 'any':
        return True
      
      else:
        # 未定義のルールは警告のみ出して通過させる
        print(f"Warning: 未定義の検証ルール '{rule}' が指定されました。検証をスキップします。")
        return True
    
    return True

  def _interactive_input(self, prompt, validate_rules):
    """
    ユーザーに入力を求め、検証ルールに従ってチェックを行う内部メソッド。
    """
    while True:
      try:
        user_input = input(prompt).strip()
      except KeyboardInterrupt:
        print("\nキャンセルされました。")
        sys.exit(1)

      # 空入力のチェック
      if not user_input:
        print("入力が必要です。")
        continue

      # 検証ルールに基づくチェック
      if self._run_validation(user_input, validate_rules):
        return user_input

  def confirm_options(self, args):
    """
    オプション引数の確認と変更を対話的に行うメソッド。
    -h で現在の設定値一覧とヘルプを表示する。
    変更された値に対してもvalidateを実行する。
    """
    while True:
      print("\nオプション変数を変更しますか？")
      user_input = input("  (-h: 設定確認・ヘルプ / 入力例: '-s 100' / Enter: 実行): ").strip()

      if not user_input:
        break

      if user_input == '-h' or user_input == '--help':
        # 現在の設定値を表示
        print("\n--- Current Options ---")
        for key, value in vars(args).items():
          # 位置引数も含めて表示されるが、確認用として有用
          print(f"  {key} = {value}")
        print("\n--- Help ---")
        self.print_help()
        continue

      # 一時的なNamespaceを作成して検証用にする
      # argsの現在の状態をコピー
      temp_args = argparse.Namespace(**vars(args))
      
      # 位置引数を保護するために退避
      saved_positionals = {}
      for action in self._actions:
        if not action.option_strings:
          saved_positionals[action.dest] = getattr(args, action.dest, None)

      try:
        # temp_args に対してパースを実行（args自体はまだ書き換えない）
        self.parse_known_args(user_input.split(), namespace=temp_args)
        
        # 位置引数を復元（オプション指定の影響を受けないように）
        for dest, val in saved_positionals.items():
          setattr(temp_args, dest, val)

        # ---------------------------------------------------------
        # 変更された値に対してバリデーションを実行
        # ---------------------------------------------------------
        validation_passed = True
        
        for dest, config in self.interactive_configs.items():
          # 新しい値を取得
          new_value = getattr(temp_args, dest, None)
          validate_rules = config.get('validate')
          
          # ルールがあり、かつ値が存在する場合にチェック
          if validate_rules and new_value is not None:
            if not self._run_validation(new_value, validate_rules):
              print(f">> 設定変更エラー: 引数 '{dest}' への入力が無効でした。")
              validation_passed = False
              break
        
        if validation_passed:
          # 検証OKなら本番のargsに反映
          vars(args).update(vars(temp_args))
          print(">> 設定を更新しました。")
        else:
          print(">> 設定は更新されませんでした。再入力してください。")

      except SystemExit:
        print(">> エラー: 無効なオプション形式です。")
      except Exception as e:
        print(f">> エラー: {e}")

  def get_default_values(self):
    """
    パーサーに設定されている全引数のデフォルト値を辞書として返す。
    バッチ処理などでデフォルト設定を取得するために使用する。
    """
    defaults = {}
    for action in self._actions:
      # destが設定されており、かつヘルプ表示などの特殊なActionでないものを対象とする
      if action.dest and action.dest != argparse.SUPPRESS:
        # デフォルト値が設定されている場合のみ追加
        if action.default != argparse.SUPPRESS:
          defaults[action.dest] = action.default
    return defaults