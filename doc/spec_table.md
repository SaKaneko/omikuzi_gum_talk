# SQLite スキーマ設計（概要テーブル）

## 概要
- 目的: 既存のファイルベースの話題保存をSQLiteに移行するためのテーブル定義・DDL・主要クエリ・移行手順をまとめる。

## テーブル一覧（要約）
- `topics`: 話題（Markdown本文）を保存するメインテーブル
- `topics_fts`: FTS5 を使った全文検索用仮想テーブル（オプションだが推奨）
- （任意）`topic_history`: 変更履歴・監査用

---

## `topics` テーブル（詳細）

| カラム | 型 | 制約 | 説明 |
|---|---:|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | 一意のID |
| slug | TEXT | NOT NULL, UNIQUE | ファイル名代替の安全な識別子（URLフレンドリー）|
| title | TEXT | NOT NULL | 1行目の題名 |
| body | TEXT | NOT NULL | Markdown本文（UTF-8） |
| created_at | DATETIME | NOT NULL DEFAULT (datetime('now')) | 作成日時 |
| updated_at | DATETIME | NULLABLE | 更新日時 |

Indexes / Constraints:
- UNIQUE(`slug`)
- INDEX on `created_at`（クエリ高速化のため）

理由: CRUD操作・ソフト削除・移行トレーサビリティを満たす最小構成。

---

## `topics_fts`（FTS5）

- 目的: タイトル・本文の全文検索を高速に行う。
- 推奨定義（SQLite FTS5）:

```
CREATE VIRTUAL TABLE topics_fts USING fts5(title, body, content='topics', content_rowid='id');
```

- `topics` の INSERT/UPDATE/DELETE を同期するためにトリガーを作成する（下記参照）。

---

## トリガー例（topics <-> topics_fts 同期）

```
CREATE TRIGGER topics_ai AFTER INSERT ON topics BEGIN
  INSERT INTO topics_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;

CREATE TRIGGER topics_ad AFTER DELETE ON topics BEGIN
  DELETE FROM topics_fts WHERE rowid = old.id;
END;

CREATE TRIGGER topics_au AFTER UPDATE ON topics BEGIN
  UPDATE topics_fts SET title = new.title, body = new.body WHERE rowid = new.id;
END;
```

---

## DDL（まとめ）

```
-- topics テーブル
CREATE TABLE topics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT (datetime('now')),
  updated_at DATETIME
);

-- FTS5 テーブル（オプション）
CREATE VIRTUAL TABLE topics_fts USING fts5(title, body, content='topics', content_rowid='id');
```

（必要に応じて `schema_version` テーブルを作り、マイグレーション管理を行ってください。）

---

## 主要なクエリ（API向け）

- おみくじ（ランダム取得）:

```
SELECT id FROM topics ORDER BY RANDOM() LIMIT 1;
```

- 一覧（題名のみ）:

```
SELECT id, slug, title, created_at FROM topics ORDER BY created_at DESC;
```

- 詳細取得:

```
SELECT id, slug, title, body, created_at, updated_at FROM topics WHERE id = ?;
```


- FTS 検索:

```
SELECT topics.id, topics.title FROM topics JOIN topics_fts ON topics_fts.rowid = topics.id
 WHERE topics_fts MATCH ?;
```

---

## 実装上の注意点

- Markdown は生のテキストとして `body` に保存し、レンダリング（HTML変換）とサニタイズはサービス層で行う。
- スキーマ変更はマイグレーション管理（簡易は `schema_version` テーブル）で扱う。
- テストを追加する（読み書き、ランダム取得、FTS 検索、移行スクリプト）。

---

このドキュメントは設計の要点をまとめたものです。実装用のDDLやマイグレーションスクリプト雛形が必要であれば次に生成します。
