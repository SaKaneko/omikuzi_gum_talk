# 詳細設計

## 概要
この設計書は `doc/request.md` の要求と `doc/spec.md` の仕様を受け、実装に落とし込むための詳細設計を記載する。主に以下を含む:
- アーキテクチャ構成
- ディレクトリ・ファイル構成
- クラス設計（責務と主要メソッド）
- API 契約（リクエスト/レスポンス例）
- UI フロー（おみくじ、投稿、一覧、削除）
- 永続化・ファイルI/Oの取り扱い
- セキュリティとバリデーション
- テスト方針

## アーキテクチャ
- **ランタイム**: Python 3.10+ を想定
- **Web フレームワーク**: Flask（軽量）を想定。ただし FastAPI でも置き換え可能
- **WSGI**: Gunicorn（本番）
- **リバースプロキシ**: 必要に応じて Nginx
- **コンテナ**: `docker-compose` による開発/起動
- **静的ファイル**: フロントエンドの JS/CSS は Flask の静的配下に置く、もしくは別コンテナで配信

## ディレクトリ構成（案）
```
omikuzi_gum_talk/
├── app/
│   ├── __init__.py
│   ├── main.py           # Flask app のエントリ
│   ├── controllers/
│   │   └── topics.py     # ルーティング（/, /omikuji, /topics...）
│   ├── services/
│   │   └── omikuji.py    # OmikujiService
│   ├── repositories/
│   │   └── topic_repo.py # TopicRepository
│   ├── utils/
│   │   └── markdown.py   # MarkdownRenderer
│   └── i18n/
│       └── translations/  # .po/.mo を配置
├── topics/                # ホストマウント推奨: 実際の話題ファイル群
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## クラス設計
以下は主要なクラスと責務、主要メソッドを示す。実装は OOP を意識して分離する。

- **TopicRepository**
	- 責務: `topics/` ディレクトリの読み書き・削除・一覧取得、ID<->ファイル名の解決
	- 主要メソッド:
		- `list_topics() -> List[TopicMeta]` : ファイル一覧と先頭行（タイトル）を取得
		- `get_topic(id: str) -> Topic` : 指定IDのファイルを読み取り、題名・本文を返す
		- `create_topic(title: str, body: str) -> str` : 一時ファイル作成 -> 原子的リネーム -> 新しいID返却
		- `delete_topic(id: str) -> bool` : ファイル削除（成功/失敗）
	- 実装注意点: ファイル名はタイムスタンプ/UUID から生成し、パス正規化してパス走査を防止する

- **OmikujiService**
	- 責務: ランダム選択ロジック、将来的には重み付き選択などの拡張
	- 主要メソッド:
		- `pick_random_topic() -> str` : `TopicRepository.list_topics()` を参照してIDを返す
	- 実装注意点: 空リスト時の例外処理やリトライは呼び出し側で行う

- **MarkdownRenderer**
	- 責務: Markdown から HTML への変換、および HTML のサニタイズ
	- 主要メソッド:
		- `render(markdown_text: str) -> str` : HTML を返す（サニタイズ済）
	- 使用ライブラリ: `markdown`（Python Markdown） + `bleach`（XSS サニタイズ）

- **I18nManager**
	- 責務: `.po/.mo` を読み込み、テンプレートで翻訳を提供
	- 実装: `Flask-Babel` + gettext を利用し、`app` 初期化時にロードする

- **Controllers (Flask routes)**
	- `GET /` : メイン画面テンプレートを返す
	- `GET /omikuji` : `OmikujiService.pick_random_topic()` を呼び出し JSON で ID を返す
	- `GET /topics` : `TopicRepository.list_topics()` を JSON で返す
	- `GET /topics/<id>` : `TopicRepository.get_topic()` で取り出して MarkdownRenderer で HTML 変換して返す
	- `POST /topics` : フォーム/JSON で受け取り `create_topic()` を呼ぶ
	- `POST /topics/preview` : 受け取りをレンダリングして返す（CSRF トークンはフロントで管理）
	- `DELETE /topics/<id>` : `delete_topic()` を呼ぶ

## API 契約（例）
- `GET /topics`
	- レスポンス 200
	- Body (JSON):
		```json
		[{"id":"20260109_121503_how-to-talk","title":"はじめての話題"}, ...]
		```

- `GET /topics/<id>`
	- レスポンス 200
	- Body (HTML): Markdown -> HTML（サニタイズ済）

- `POST /topics` (Content-Type: application/json)
	- リクエスト:
		```json
		{"title":"題名","body":"本文（Markdown）"}
		```
	- レスポンス 201
	- Body (JSON): `{ "id": "生成されたID" }`

- `POST /topics/preview`
	- リクエスト: 上と同じ
	- レスポンス 200: HTML 文字列

- `DELETE /topics/<id>`
	- レスポンス 204 (成功, body 空)
	- エラー: 404 (NotFound) / 400 (BadRequest)

## UI フロー
- **おみくじ**
	1. ユーザーが `おみくじ` ボタンを押す。
	2. フロントは `GET /omikuji` を呼び出す。
	3. バックエンドは `OmikujiService.pick_random_topic()` で ID を返す。
	4. フロントはアニメーションを表示しつつ `GET /topics/<id>` を取得して結果画面へ遷移し表示する。
	5. 結果画面で `削除してメインへ戻る` を押すと `DELETE /topics/<id>` を実行し、成功したら `GET /` に遷移する。

- **話題投稿**
	1. ユーザーが題名/本文を入力する。
	2. `Preview` は `POST /topics/preview` へ送信し HTML を受け取る。
	3. `投稿` を押すと `POST /topics` へ送信し、成功時はメイン画面にリダイレクトする（または作成IDを表示）。

- **話題一覧 / 削除**
	1. 一覧画面は `GET /topics` を取得して題名一覧を描画する。
	2. 削除時は確認ダイアログ表示の上で `DELETE /topics/<id>` を呼ぶ。

## ファイルI/O と同時性（実装ルール）
- **書き込み**: `create_topic()` は以下手順で行う
	- (1) 入力から安全なスラッグを生成
	- (2) 一時ファイル（例: `<tmpdir>/<uuid>.tmp`）に UTF-8 で書き込む
	- (3) `os.replace()` / `Path.replace()` で原子的リネームして `topics/<timestamp>_<slug>.md` にする
	- (4) 成功なら新IDを返す
- **読み取り**: ファイルを開く際は `encoding='utf-8'` を指定し、例外時は 500 を返す
- **削除**: `os.remove()` を使用。削除前に存在確認を行い、必要ならバックアップ/ゴミ箱移動に切り替え可能
- **ロック**: 非常に高トラフィックな環境でなければファイルロックは省略可。ただし必要なら `fcntl` ベースのロックや簡易ロックファイルを導入

## セキュリティ設計
- **XSS 対策**: Markdown から生成した HTML は `bleach` などでホワイトリストベースにサニタイズする。許可タグは `p, a, strong, em, ul, ol, li, code, pre` 等に制限。
- **パス走査防止**: 外部入力（ID/ファイル名）から直接パス結合しない。ID を検証して正規表現 `^[A-Za-z0-9_\-]+$` のみ許可する。
- **CSRF**: フォーム投稿を行う場合は `Flask-WTF` の CSRF トークンを導入。API を純粋な JSON API にして JWT 等にすると別設計。
- **入力制限**: 題名長は例えば 200 文字、本文は 10000 文字以内等で制限をかける。
- **認証**: 現行要件では不要だが、管理機能を追加する際は `Flask-Login` + パスワード/セッションを検討

## ロギングと監視
- **アクセスログ**: Flask / Gunicorn の通常ログを利用
- **操作ログ**: 話題の追加・削除は INFO レベルでログに残し、ID と題名を記録する
- **ヘルスチェック**: `GET /health` を用意して 200 を返す

## テスト方針
- **単体テスト** (pytest)
	- `TopicRepository` の読み書き（テンポラリディレクトリを使う）
	- `OmikujiService` が空でない場合に ID を返すこと
	- `MarkdownRenderer.render()` が HTML を返し、XSS 用の悪意あるスクリプトを除去する
- **統合テスト**
	- Flask の `app.test_client()` を使って POST/GET/DELETE の E2E を実施
	- ファイル I/O はテスト用 `topics_test/` をマウント
- **CI**: GitHub Actions 等で pytest を走らせる想定

## Docker / デプロイの注意点
- `Dockerfile` は軽量 Python イメージ（slim）を使い、`requirements.txt` をインストールする
- `docker-compose.yml` で `./topics` をボリュームマウントしてデータを永続化
- 環境変数: `FLASK_ENV`, `SECRET_KEY`, `TOPICS_DIR` 等を使用

## エラーハンドリング
- API は一貫した JSON エラー形式を返す（例: `{ "error": "Not found", "code": 404 }`）
- 予期しない例外はサーバー側でキャッチして 500 を返し、ログにトレースを残す

## 拡張ポイント（設計上の余地）
- トピックにタグ/カテゴリを追加するためのメタデータストア（YAML ヘッダや別ファイル）
- 重み付き選択やユーザーごとの履歴を用いた推薦アルゴリズム
- 認証/権限管理を追加して複数ユーザー運用を可能にする

## 次の実装ステップ（優先順）
1. `Flask` プロジェクトのスキャフォールディングを作成（`app/` ディレクトリ、`main.py`、テンプレート、静的）
2. `TopicRepository` と `MarkdownRenderer` の実装、ユニットテスト作成
3. 基本 API と簡易 UI（メイン/おみくじ/結果/投稿/一覧）を実装
4. `docker-compose` と `Dockerfile` を作成して起動確認
5. i18n（`Flask-Babel`）を導入

