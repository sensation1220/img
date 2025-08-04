# 🎮 ゲームランキング統合ツール

このツールは、個別のゲーム紹介記事を統合し、LLM を使用して魅力的なランキング記事として再構成する Python スクリプトです。

## ✨ 機能

- 📊 ranking.txt に基づいたゲームランキング統合
- 🤖 AI（OpenAI GPT-4 / Google Gemini）による文章リライト
- 🛡️ autohtml タグなどの保護機能
- 📝 複数の文体スタイル対応（friendly/professional/casual）
- 🔄 API プロバイダーの簡単切り替え

## 🚀 セットアップ

### 1. 必要なパッケージのインストール

```bash
# 基本パッケージ
pip install python-dotenv

# OpenAI API使用の場合
pip install openai

# Google Gemini API使用の場合
pip install google-generativeai
```

### 2. 環境変数の設定

`.env`ファイルを作成し、使用する API キーを設定してください：

```env
# OpenAI API（どちらか一方でOK）
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini API（どちらか一方でOK）
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. API キーの取得方法

#### OpenAI API

1. [OpenAI Platform](https://platform.openai.com/)にアクセス
2. アカウント作成/ログイン
3. API Keys > Create new secret key

#### Google Gemini API

1. [Google AI Studio](https://aistudio.google.com/)にアクセス
2. Google アカウントでログイン
3. Get API key をクリック

## ⚙️ 設定

`0-ranking/enhanced_merge_ranking_md.py`の設定セクションを編集：

```python
# LLM設定
LLM_PROVIDER = "openai"  # "gemini" or "openai"
ENABLE_LLM_REWRITE = True  # False にするとLLM書き換えをスキップ
REWRITE_STYLE = "friendly"  # friendly, professional, casual

# OpenAI モデル設定
OPENAI_MODEL = "gpt-4"  # gpt-4, gpt-4-turbo, gpt-3.5-turbo など

# Gemini モデル設定  
GEMINI_MODEL = "gemini-1.5-flash"  # gemini-1.5-flash, gemini-1.5-pro など
```

### 設定項目の説明

| 設定項目             | 選択肢                                       | 説明                       |
| -------------------- | -------------------------------------------- | -------------------------- |
| `LLM_PROVIDER`       | `"openai"` / `"gemini"`                      | 使用する AI プロバイダー   |
| `ENABLE_LLM_REWRITE` | `True` / `False`                             | AI 書き換え機能の有効/無効 |
| `REWRITE_STYLE`      | `"friendly"` / `"professional"` / `"casual"` | 文章のスタイル             |
| `OPENAI_MODEL`       | `"gpt-4"` / `"gpt-4-turbo"` / `"gpt-3.5-turbo"` | OpenAI使用時のモデル   |
| `GEMINI_MODEL`       | `"gemini-1.5-flash"` / `"gemini-1.5-pro"`   | Gemini使用時のモデル       |

### 使用可能モデル

#### OpenAI
- **gpt-4**: 最高品質（高コスト）
- **gpt-4-turbo**: 高品質・高速（中コスト）  
- **gpt-3.5-turbo**: 高速・経済的（低コスト）

#### Google Gemini
- **gemini-1.5-flash**: 高速・経済的
- **gemini-1.5-pro**: 高品質（やや高コスト）

### 文体スタイルの違い

- **friendly**: 明るく親しみやすいブロガー口調
- **professional**: 専門的で信頼性の高い評価口調
- **casual**: カジュアルで親近感のある口調

## 📁 ファイル構成

```
blog/
├── 0-ranking/
│   ├── ranking.txt          # ランキング順序
│   ├── ゲーム名.md          # 各ゲームの紹介記事
│   └── enhanced_merged_ranking.md  # 統合された最終出力
└── enhanced_merge_ranking_md.py
```

## 🎯 使用方法

1. `0-ranking/ranking.txt`にゲーム名を順位順で記載
2. 各ゲームの紹介記事を`0-ranking/ゲーム名.md`として保存
3. スクリプトを実行：

```bash
python 0-ranking/enhanced_merge_ranking_md.py
```

## 📋 ranking.txt の書式

```
1. ゲーム名1
2. ゲーム名2
3. ゲーム名3
...
```

## 🛡️ 保護機能

以下のタグは書き換え時に自動的に保護されます：

- `[autohtml]...[/autohtml]`
- `[autoimg]...[/autoimg]`
- `[mark]...[/mark]`
- フロントマター（`---`で囲まれた部分）

## ⚠️ 注意事項

- OpenAI API 使用時は GPT-4 モデルを使用します（料金にご注意ください）
- API キーは適切に管理し、公開リポジトリにコミットしないでください
- 大量のファイル処理時は API レート制限にご注意ください

## 🔧 トラブルシューティング

### よくあるエラー

1. **API キーエラー**: `.env`ファイルの API キーが正しく設定されているか確認
2. **インポートエラー**: 必要なパッケージがインストールされているか確認
3. **ファイルが見つからない**: ファイルパスとファイル名が正しいか確認

### ログの見方

- ✅ 成功
- ⚠️ 警告
- ❌ エラー
- 🤖 AI 処理中

## 📊 使用コスト目安

| プロバイダー | モデル           | 概算コスト（1 ゲーム） | 品質 |
| ------------ | ---------------- | ---------------------- | ---- |
| OpenAI       | GPT-4            | $0.03-0.08             | 最高 |
| OpenAI       | GPT-4-Turbo      | $0.015-0.04            | 高   |
| OpenAI       | GPT-3.5-Turbo    | $0.002-0.008           | 中   |
| Google       | Gemini 1.5 Pro   | $0.002-0.01            | 高   |
| Google       | Gemini 1.5 Flash | $0.0005-0.003          | 中〜高 |

\*実際のコストは文章量と API 料金により変動します。予算に応じて最適なモデルを選択してください。
