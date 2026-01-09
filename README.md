# Omikuzi Gum Talk

**軽量なトークテーマおみくじ Web アプリケーション（Python / Flask）**

---

**概要**
- このリポジトリは、ランダムにトークテーマ（話題）を提示する小さな Web アプリケーションです。
- 主に Python（Flask）で実装され、`topics/` ディレクトリに Markdown ファイル（1行目をタイトル）を置くことで話題を管理します。
- ローカルや Docker（`docker-compose`）で簡単に立ち上げられるように構成されています。

**特徴**
- シンプルなメイン画面・おみくじ画面・おみくじ結果画面・投稿画面・一覧画面を備えます。
- 投稿は Markdown 形式で行い、プレビュー機能あり。
- 多言語対応（UI の翻訳は `.po` / `.mo` 想定）。
- Markdown から HTML への変換時に `bleach` でサニタイズして XSS を抑制。

---

**すばやい開始方法（ローカル）**
- 依存をインストールして直接実行:

```bash
python3 -m pip install -r requirements.txt
python3 -m src.app.main
```

- デフォルトでは `topics/` をプロジェクトルートから参照します。別の場所を使いたい場合は環境変数 `TOPICS_DIR` を設定してください。

**Docker (docker-compose)**
- Docker で簡単に起動できます（ホストの `topics/` をコンテナにマウントして永続化）:

```bash
docker compose build
docker compose up
# アクセス: http://localhost:8082/  (compose で '8082:8000' をマッピングしています)
```

---

**主要設定（環境変数）**
- `TOPICS_DIR` : 話題ファイルを保存/参照するディレクトリ（デフォルト: `./topics`）
- `PORT` : ローカル起動時のポート（デフォルト: `8000`）
- `FLASK_DEBUG` : デバッグモードを有効にする場合は `1` を設定

---

**ファイル/ディレクトリ構成（抜粋）**
- `src/app/` : Flask アプリケーションのソース
	- `__init__.py` : アプリファクトリ（`create_app`）と `/favicon.ico` のルート
	- `main.py` : 実行エントリ（`python -m src.app.main` で起動）
	- `controllers/topics.py` : ルーティングとコントローラ
	- `repositories/topic_repo.py` : ファイルベースの永続化（create/list/get/delete）
	- `services/omikuji.py` : おみくじのランダム選択ロジック
	- `utils/markdown.py` : Markdown -> HTML 変換＋サニタイズ
	- `templates/` : Jinja2 テンプレート（`index.html`, `list.html`, `post.html`, `topic.html`, `omikuji.html`, `base.html`）
	- `static/` : CSS/JS/画像（`style.css`, `omikuji.js`, `title.png`, `favicon.ico` 等）
- `topics/` : 話題の Markdown ファイルを置くディレクトリ（1行目はタイトル）
- `requirements.txt`, `Dockerfile`, `docker-compose.yml` : 実行/コンテナ用設定
- `doc/` : `request.md`, `spec.md`, `design.md`（要件・仕様・設計書）

---

**主要エンドポイント（HTTP API / 画面）**
- `GET /` : メイン画面
- `GET /omikuji` : ブラウザの場合はおみくじページ（GIF アニメ再生）を返し、JSON Accept の場合はランダムに選んだ話題の ID を返します
- `GET /topics` : ブラウザの場合は一覧ページ、Accept: application/json の場合は JSON のリストを返します
- `GET /topics/<id>` : 指定 ID の話題ページ（Markdown を HTML に変換して返す）
- `POST /topics` : 新しい話題を作成（JSON またはフォーム）
- `POST /topics/preview` : Markdown のプレビュー（HTML 断片を返す）
- `DELETE /topics/<id>` : 話題を削除

**話題ファイル仕様**
- 保存形式: UTF-8 の Markdown ファイル（拡張子 `.md`）
- 先頭行: 題名（タイトル）
- 例ファイル: `topics/20260109_153124_sample.md`

---

**開発ノート / 実装のポイント**
- `TopicRepository.create_topic` は一時ファイルを書いて `os.replace` で原子的に配置します。
- Markdown->HTML は `markdown` ライブラリを使い、`bleach` でサニタイズしています。
- UI は Jinja2 テンプレート + 小さなフロントエンド JS（`omikuji.js` など）で実現しています。

**セキュリティ注意点**
- 入力はサニタイズしていますが、本番公開する場合は認証（投稿・削除操作の保護）や CSRF 対策を追加してください。

---

**テスト & CI**
- 現時点でテストは含まれていません。`pytest` を使ったユニットテスト（`TopicRepository`, `MarkdownRenderer` 等）を追加することを推奨します。

---

**今後の改善案（提案）**
- 投稿の認証/権限管理の追加
- 話題にタグ/検索を追加
- Lottie 等を使ったより正確なアニメーション管理（GIF の代替）
- ユニット / 統合テストの追加

---

**ライセンス**
- 特に明記がない場合は個人利用の範囲でお使いください。ライセンスを明確にしたい場合は `LICENSE` ファイルを追加してください。

---

**連絡 / 変更履歴**
- このリポジトリの設計情報は `doc/` にあります（`request.md`, `spec.md`, `design.md`）。

---

質問や追加の希望があれば教えてください — README をさらに詳細化（API スキーマ、例リクエスト/レスポンス、開発者向け手順）できます。
