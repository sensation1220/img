import glob
import os
import json
import time
import random
import shutil
import argparse
from datetime import datetime
import re # For finding ### headings
import google.generativeai as genai
import openai
from dotenv import load_dotenv

# --- Gemini API Configuration ---
load_dotenv()

try:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("警告: GEMINI_API_KEY 環境変数が設定されていません。")
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash') # 使用するモデルを指定
    print("Gemini API configured.")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    gemini_model = None

# --- OpenAI API Configuration ---
try:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        print("警告: OPENAI_API_KEY 環境変数が設定されていません。")
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI API configured.")
except Exception as e:
    print(f"Error configuring OpenAI API: {e}")
    openai_client = None

# 設定
SOURCE_MD_DIR = "/Users/haradakouichi/Pictures/blog/0-list/"
NUM_FILES_TO_PROCESS = 30
ROOT_DIR = "/Users/haradakouichi/Pictures/blog/"
PROCESS_DIR_NAME = "3-process"

# この変数はmain関数内で動的に設定されます
CURRENT_PROCESSING_DIR = ""
PROGRESS_FILE = ""
NAME_MAPPING = {}

def load_progress():
    """進捗ファイルを読み込み、処理済みファイルと中断中のファイルを返す"""
    processed_files = set()
    interrupted_file = None
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("完了: "):
                    processed_files.add(line.replace("完了: ", ""))
                elif line.startswith("処理中: "):
                    interrupted_file = line.replace("処理中: ", "")
    return processed_files, interrupted_file

def save_progress(status, filename):
    """進捗をファイルに記録する"""
    with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{status}: {filename}\n")

def get_md_files():
    """処理対象のmdファイル一覧を取得する"""
    # .gitignoreを尊重せず、すべてのmdファイルを取得
    return sorted(glob.glob(os.path.join(CURRENT_PROCESSING_DIR, "*.md")))

def get_image_files_in_folder(folder_path):
    """指定されたフォルダ内の画像ファイル（.webp, .png, .jpg, .jpeg, .gif）をリストする"""
    images = []
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for f in os.listdir(folder_path):
            if f.lower().endswith(('.webp', '.png', '.jpg', '.jpeg', '.gif')) and f != '.DS_Store':
                images.append(f)
    return images

def reorder_h3_sections(content):
    """h3セクションを再配置する共通関数"""
    # h3セクションを抽出
    h3_sections = re.findall(r'(###\s[^\n]*\n(?:(?!###)[\s\S])*)', content)
    
    if len(h3_sections) < 6:
        print("警告: h3セクションが6つ未満です。再配置をスキップします。")
        return content
    
    # 最初の2つのh3は固定、残りの4つをランダムに並べ替え
    fixed_h3_sections = h3_sections[:2]
    random_h3_sections = h3_sections[2:6]
    random.shuffle(random_h3_sections)
    
    # 再配置されたh3セクションを結合
    reordered_h3_sections = fixed_h3_sections + random_h3_sections
    
    # 元のコンテンツからh3セクション以外の部分を抽出
    # [autohtml]タグなどの冒頭部分を保護
    content_before_h3 = ""
    first_h3_match = re.search(r'###\s[^\n]*\n', content)
    if first_h3_match:
        content_before_h3 = content[:first_h3_match.start()]
    
    # 再構成されたコンテンツを作成
    reordered_content = content_before_h3 + "\n".join(reordered_h3_sections)
    
    return reordered_content

def insert_images(processed_content, file_path):
    """処理済みコンテンツに画像URLを挿入する共通関数"""
    original_filename_with_ext = os.path.basename(file_path)
    romanized_folder_name = NAME_MAPPING.get(original_filename_with_ext)

    if not romanized_folder_name:
        print(f"警告: {original_filename_with_ext} のローマ字フォルダ名がname_mapping.jsonに見つかりません。画像を挿入しません。")
        return processed_content

    image_folder_path = os.path.join(ROOT_DIR, romanized_folder_name)
    available_images = get_image_files_in_folder(image_folder_path)
    
    if not available_images:
        print(f"警告: フォルダ {image_folder_path} に画像ファイルが見つかりません。画像を挿入しません。")
        return processed_content

    inserted_images = set()
    output_lines = []
    h3_count = 0
    
    lines = processed_content.splitlines()
    for i, line in enumerate(lines):
        output_lines.append(line)
        if line.strip().startswith("###"): # ###で始まる行を検出
            h3_count += 1
            image_to_insert = None
            
            if h3_count == 1:
                if "eye.webp" in available_images:
                    image_to_insert = "eye.webp"
                    inserted_images.add("eye.webp")
                else:
                    print(f"警告: {image_folder_path} に eye.webp が見つかりません。最初のh3の下に画像を挿入できませんでした。")
            else:
                potential_images = [img for img in available_images if img != "eye.webp" and img not in inserted_images]
                if potential_images:
                    image_to_insert = random.choice(potential_images)
                    inserted_images.add(image_to_insert)
                else:
                    print(f"警告: {image_folder_path} に利用可能なランダムな画像がありません。h3の下に画像を挿入できませんでした。")

            if image_to_insert:
                image_string = f"[autoimg]https://cdn.jsdelivr.net/gh/sensation1220/img/{romanized_folder_name}/{image_to_insert}[/autoimg]"
                output_lines.append(image_string)
                output_lines.append("")

    return "\n".join(output_lines)

def format_content_with_llm(content, api_type="gemini", game_title=""):
    """第2段階: リライト済みコンテンツのフォーマット調整（改行・マーク付け）"""
    print(f"--- フォーマット調整開始 ({api_type}) ---")
    
    prompt = f"""
以下のMarkdownコンテンツに、読みやすさと重要な情報の強調のためのフォーマット調整を行ってください。

## フォーマット調整ルール:
1. **適切な改行と空白行**:
   - 段落間に適切な空白行を挿入
   - 長い段落は読みやすくなるよう適度に分割
   - リスト項目の前後にも空白行を挿入

2. **重要な内容の強調**:
   - 特に重要で読者の関心を引く部分を[mark][/mark]で囲う
   - ゲームの魅力的な特徴、攻略のポイント、おすすめ要素など
   - 1つのh3セクションにつき1~2箇所必ず囲うこと
   - 例: この設定をすることで[mark]一気に敵を倒せるんです！[/mark]

3. **注意事項**:
   - h2、h3見出しは変更しない
   - [autohtml]タグは絶対に変更しない
   - 文章の内容や意味は変更しない

## 処理対象のコンテンツ:
{content}
"""

    try:
        if api_type == "openai" and openai_client:
            response = openai_client.chat.completions.create(
                model="o4-mini",
                messages=[
                    {"role": "system", "content": "あなたは文章フォーマットの専門家です。"},
                    {"role": "user", "content": prompt}
                ]
            )
            formatted_content = response.choices[0].message.content.strip()
        elif api_type == "gemini" and gemini_model:
            response = gemini_model.generate_content(prompt)
            formatted_content = response.text.strip()
        else:
            print(f"エラー: {api_type} APIが利用できません。フォーマット調整をスキップします。")
            return content
            
        print(f"--- フォーマット調整完了 ({api_type}) ---")
        return formatted_content
        
    except Exception as e:
        print(f"エラー: フォーマット調整中に問題が発生しました: {e}")
        return content

def process_file_with_openai(file_path):
    """OpenAI APIにファイル処理を依頼し、結果を取得する"""
    if not openai_client:
        print("エラー: OpenAIクライアントが設定されていません。処理をスキップします。")
        return None

    print(f"--- OpenAI処理開始: {os.path.basename(file_path)} ---")
    
    with open(file_path, 'r', encoding='utf-8') as f_in:
        content = f_in.read()

    # h3セクションの再配置をプログラムで実行
    reordered_content = reorder_h3_sections(content)
    
    game_title = os.path.basename(file_path).replace(".md", "")
    
    # 第1段階: リライト処理（プロンプトを簡潔化）
    prompt = f"""
以下のMarkdownコンテンツを、指定されたルールに従ってリライトしてください。
**注意事項**: 冒頭の[autohtml]タグに囲われた文字列はそのままにしてください。変更を禁じます。

## 変換ルール:
1.  **h2見出しのグループ化**: h3セクションを2つずつグループ化し、各グループに読者が読みたくなるようなh2見出しを作成してください（合計3つのh2見出し）。
2.  **ゲームタイトルの追加**: 各h2見出しにゲームタイトル「{game_title}」を追加してください。
3.  **ブロガー風リライト**: 全てのh3見出しを読者が読みたくなるようにリライトし、対応する本文も以下の口調でリライトしてください。
    -   口調: 偉人が語っているような感じ。「〜じゃぞ」のような親しみやすい年配の語り方。
    -   絵文字は使用しないでください。
    -   **重要**: 元の文章量を維持してください。文章を短縮しないでください。
4.  **記事まとめの生成**: 記事の最後に「## まとめ」のh2見出しを作成し、ゲームの魅力を簡潔にまとめた本文を生成してください。読者がプレイしたくなるような魅力的な内容を簡潔に作成してください。

## 処理対象のMarkdownコンテンツ（h3セクションは既に適切に再配置済み）:
{reordered_content}
"""

    try:
        response = openai_client.chat.completions.create(
            model="o4-mini",
            messages=[
                {"role": "system", "content": "あなたはプロのブロガーです。"},
                {"role": "user", "content": prompt}
            ]
        )
        rewritten_content = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"エラー: OpenAI API呼び出し中に問題が発生しました: {e}")
        return None

    # 第2段階: フォーマット調整（改行・マーク付け）
    formatted_content = format_content_with_llm(rewritten_content, "openai", game_title)
    
    # 第3段階: 画像挿入
    final_content = insert_images(formatted_content, file_path)
    print(f"--- OpenAI処理完了: {os.path.basename(file_path)} ---\n")
    return final_content


def process_file_with_gemini(file_path):
    """LLMエージェントにファイル処理を依頼し、結果を取得し、画像を挿入する"""
    if not gemini_model:
        print("エラー: Geminiモデルが設定されていません。処理をスキップします。")
        return None

    print(f"--- Gemini処理開始: {os.path.basename(file_path)} ---")
    
    with open(file_path, 'r', encoding='utf-8') as f_in:
        content = f_in.read()

    # h3セクションの再配置をプログラムで実行
    reordered_content = reorder_h3_sections(content)
    
    # ファイル名からゲームタイトルを特定
    game_title = os.path.basename(file_path).replace(".md", "")

    # 第1段階: リライト処理（プロンプトを簡潔化）
    prompt = f"""
以下のMarkdownコンテンツを、指定されたルールに従ってリライトしてください。
**注意事項**: 冒頭の[autohtml]タグに囲われた文字列はそのままにしてください。変更を禁じます。

## 変換ルール:
1.  **h2見出しのグループ化**: h3セクションを2つずつグループ化し、各グループに読者が読みたくなるようなh2見出しを作成してください（合計3つのh2見出し）。
2.  **ゲームタイトルの追加**: 各h2見出しにゲームタイトル「{game_title}」を追加してください。
3.  **ブロガー風リライト**: 全てのh3見出しを読者が読みたくなるようにリライトし、対応する本文も以下の口調でリライトしてください。
    -   口調: 上品だが軽やかな大人女性口調。少し辛口なレビューもあり。「〜かしら？」「これは推せるわね」をたまに使う。
    -   絵文字は使用しないでください。
    -   **重要**: 元の文章量を維持してください。文章を短縮しないでください。
4.  **記事まとめの生成**: 記事の最後に「## まとめ」のh2見出しを作成し、ゲームの魅力を簡潔にまとめた本文を生成してください。読者がプレイしたくなるような魅力的な内容を簡潔に作成してください。

## 処理対象のMarkdownコンテンツ（h3セクションは既に適切に再配置済み）:
{reordered_content}
"""

    try:
        response = gemini_model.generate_content(prompt)
        rewritten_content = response.text.strip()
    except Exception as e:
        print(f"エラー: Gemini API呼び出し中に問題が発生しました: {e}")
        return None

    # 第2段階: フォーマット調整（改行・マーク付け）
    formatted_content = format_content_with_llm(rewritten_content, "gemini", game_title)
    
    # 第3段階: 画像挿入
    final_content = insert_images(formatted_content, file_path)

    print(f"--- Gemini処理完了（画像挿入済み）: {os.path.basename(file_path)} ---\n")
    return final_content

def get_latest_processing_dir(base_dir):
    """指定されたベースディレクトリ内で最も新しい処理ディレクトリを見つける"""
    subdirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("processed_md_files_")]
    if not subdirs:
        return None
    return max(subdirs, key=os.path.getmtime)

def main():
    global CURRENT_PROCESSING_DIR, PROGRESS_FILE, NAME_MAPPING

    parser = argparse.ArgumentParser(description="Markdownファイル処理を自動化するスクリプト")
    parser.add_argument("--resume", action="store_true", help="中断した最新の処理を再開します")
    parser.add_argument("--api", type=str, default="gemini", choices=['gemini', 'openai'], help="使用するAPIを選択します (gemini or openai)")
    args = parser.parse_args()

    print(f"--- 自動化処理を開始します (API: {args.api}) ---")

    # name_mapping.jsonを読み込む
    name_mapping_path = os.path.join(ROOT_DIR, "2-src", "name_mapping.json")
    if os.path.exists(name_mapping_path):
        with open(name_mapping_path, 'r', encoding='utf-8') as f:
            NAME_MAPPING = json.load(f)
        print("name_mapping.json を読み込みました。")
    else:
        print(f"エラー: name_mapping.json が見つかりません: {name_mapping_path}")
        print("--- 自動化処理を終了します ---")
        return

    process_base_dir = os.path.join(ROOT_DIR, PROCESS_DIR_NAME)
    os.makedirs(process_base_dir, exist_ok=True)

    if args.resume:
        print("再開モードで実行します。")
        CURRENT_PROCESSING_DIR = get_latest_processing_dir(process_base_dir)
        if not CURRENT_PROCESSING_DIR:
            print("エラー: 再開対象の処理ディレクトリが見つかりません。新規で実行してください。")
            print("--- 自動化処理を終了します ---")
            return
        print(f"最新の処理ディレクトリを再開します: {CURRENT_PROCESSING_DIR}")
        PROGRESS_FILE = os.path.join(CURRENT_PROCESSING_DIR, "progress.txt")
        if not os.path.exists(PROGRESS_FILE):
             print(f"警告: progress.txt が見つかりません: {PROGRESS_FILE}")
             print("このディレクトリで新規処理を開始します。")

    else:
        print("新規モードで実行します。")
        all_source_md_files = glob.glob(os.path.join(SOURCE_MD_DIR, "*.md"))
        if len(all_source_md_files) < NUM_FILES_TO_PROCESS:
            print(f"エラー: '{SOURCE_MD_DIR}' に十分な数の.mdファイルが見つかりません。少なくとも {NUM_FILES_TO_PROCESS} 個必要です。")
            print("--- 自動化処理を終了します ---")
            return

        selected_files = random.sample(all_source_md_files, NUM_FILES_TO_PROCESS)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        CURRENT_PROCESSING_DIR = os.path.join(process_base_dir, f"processed_md_files_{timestamp}")
        PROGRESS_FILE = os.path.join(CURRENT_PROCESSING_DIR, "progress.txt")

        os.makedirs(CURRENT_PROCESSING_DIR, exist_ok=True)
        print(f"新しい処理ディレクトリを作成しました: {CURRENT_PROCESSING_DIR}")

        print(f"{NUM_FILES_TO_PROCESS} 個のファイルをコピー中...")
        for src_path in selected_files:
            shutil.copy2(src_path, CURRENT_PROCESSING_DIR)
            print(f"  コピー済み: {os.path.basename(src_path)}")
        print("ファイルコピー完了。")

    all_md_files = get_md_files()
    if not all_md_files:
        print(f"エラー: '{CURRENT_PROCESSING_DIR}' に処理対象の.mdファイルが見つかりません。")
        print("--- 自動化処理を終了します ---")
        return

    processed_files, interrupted_file = load_progress()
    
    print(f"総ファイル数: {len(all_md_files)}")
    print(f"既に完了したファイル数: {len(processed_files)}")
    if interrupted_file:
        print(f"中断されたファイル: {interrupted_file}")

    if not os.path.exists(PROGRESS_FILE) or os.path.getsize(PROGRESS_FILE) == 0:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            f.write(f"開始時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"総ファイル数: {len(all_md_files)}\n")

    start_processing = not interrupted_file

    for file_path in all_md_files:
        filename = os.path.basename(file_path)

        if not start_processing:
            if interrupted_file and filename == interrupted_file:
                start_processing = True
                print(f"中断されたファイル '{filename}' から処理を再開します。")
            else:
                continue

        if filename in processed_files:
            print(f"スキップ: '{filename}' (既に完了済み)")
            continue

        print(f"処理中: {filename}")
        save_progress("処理中", filename)

        # APIに応じて処理を分岐
        if args.api == 'openai':
            processed_content = process_file_with_openai(file_path)
        else: # デフォルトはgemini
            processed_content = process_file_with_gemini(file_path)

        if processed_content is None:
            print(f"エラー: '{filename}' の処理中に問題が発生しました。処理を中断します。")
            break

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(processed_content)
        
        save_progress("完了", filename)
        print(f"完了: {filename}\n")

    final_processed_files, _ = load_progress()
    if len(final_processed_files) == len(all_md_files):
        with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"全処理完了: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("--- 全てのファイルの処理が完了しました ---")
    else:
        print(f"--- 処理が中断されました。完了: {len(final_processed_files)}/{len(all_md_files)} ---")

if __name__ == "__main__":
    main()
