import json
import os

# --- 設定 ---
# JSONマッピングファイルのパス
JSON_FILE_PATH = '0-ranking/name_mapping.json'

# 処理を開始するキー (この値を変更することで開始位置を調整できます)
# Noneに設定すると、ファイル内のすべてのエントリを処理します。
# 今回の依頼内容：「ロードモバイル.md」から開始
START_KEY = 'ロードモバイル.md'
# --- 設定ここまで ---

def create_folders_from_mapping(json_path, start_key=None):
    """
    JSONマッピングファイルを読み込み、その値に基づいてディレクトリを作成します。
    
    Python 3.7以降では辞書の順序が保持されることを前提としています。

    引数:
        json_path (str): JSONマッピングファイルのパス。
        start_key (str, optional): 処理を開始するキー。Noneの場合は全件処理。
    """
    print(f"スクリプトを開始します。")
    print(f"読み込みファイル: {json_path}")
    if start_key:
        print(f"開始キー: '{start_key}'")
    else:
        print("すべてのエントリを処理します。")
    print("-" * 30)

    # 1. JSONファイルの読み込みと解析
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: '{json_path}'")
        return
    except json.JSONDecodeError as e:
        print(f"エラー: JSONの解析に失敗しました: '{json_path}'. 詳細: {e}")
        return

    # 2. 開始点の決定
    all_items = list(data.items())
    start_index = 0

    if start_key:
        found = False
        for i, (key, _) in enumerate(all_items):
            if key == start_key:
                start_index = i
                found = True
                break
        if not found:
            print(f"エラー: 指定された開始キー '{start_key}' が見つかりませんでした。")
            return
    
    items_to_process = all_items[start_index:]

    if not items_to_process:
        print("処理対象のアイテムがありません。")
        return

    # 3. ディレクトリの作成
    num_to_process = len(items_to_process)
    print(f"'{items_to_process[0][0]}' から始まる {num_to_process} 件の処理を開始します...")
    
    created_count = 0
    skipped_count = 0
    error_count = 0

    for key, dir_name in items_to_process:
        if not isinstance(dir_name, str) or not dir_name.strip():
            print(f"  [警告]  キー '{key}' のディレクトリ名が無効なためスキップします: '{dir_name}'")
            error_count += 1
            continue
        
        target_dir = dir_name.strip()
        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                print(f"  [作成]  ./{target_dir}")
                created_count += 1
            else:
                skipped_count += 1
        except OSError as e:
            print(f"  [エラー]  ./{target_dir} の作成に失敗しました: {e}")
            error_count += 1
    
    if skipped_count > 0:
        print(f"\n{skipped_count}件の既存ディレクトリはスキップしました。")
    
    # 4. 結果の要約
    print("-" * 30)
    print("処理が完了しました。")
    print(f"  - 新規作成されたディレクトリ数: {created_count}")
    print(f"  - スキップされた既存ディレクトリ数: {skipped_count}")
    if error_count > 0:
        print(f"  - エラー/警告の数: {error_count}")
    print("-" * 30)


if __name__ == '__main__':
    # スクリプトのメイン処理を実行
    create_folders_from_mapping(JSON_FILE_PATH, START_KEY) 
