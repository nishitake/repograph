## repograph

Git リポジトリ内のコミットから、著者ごとの変更行数・コミット数を集計し、PNG グラフとして出力するためのシンプルなスクリプトです。

### 必要環境

- Python 3.10+ 目安
- Git がインストール済みであること
- 主要ライブラリ
  - gitpython
  - matplotlib
  - numpy

（必要に応じて `pip install gitpython matplotlib numpy` を実行してください）

### 使い方（基本）

カレントディレクトリが対象リポジトリの場合:

```bash
python contributor_graph.py
```

リポジトリパスを明示する場合:

```bash
python contributor_graph.py --repo c:/path/to/repo
```

### 期間の指定方法

#### 日付で指定（両端含む）

```bash
python contributor_graph.py \
  --repo c:/path/to/repo \
  --since-date 2024-01-01 \
  --until-date 2024-03-31
```

- `--since-date`: 開始日（この日を含む）
- `--until-date`: 終了日（この日を含む）

#### コミット ID で指定

```bash
# start..end の間のコミット
python contributor_graph.py \
  --repo c:/path/to/repo \
  --since-commit 1234abcd \
  --until-commit 9f8e7654

# あるコミット以降（〜HEAD）
python contributor_graph.py --repo c:/path/to/repo --since-commit 1234abcd

# あるコミットまでの履歴
python contributor_graph.py --repo c:/path/to/repo --until-commit 9f8e7654
```

> 日付による範囲指定と、コミット ID による範囲指定は **同時には使えません**。

### 出力ファイル

- デフォルトでは、リポジトリ直下に次の形式で PNG ファイルを出力します:
  - `<repo_name>_(YYYYMMDD-YYYYMMDD).png`
- `-o` / `--output` オプションで出力先を指定できます。

```bash
# ファイル名を直接指定
python contributor_graph.py -o report.png

# 拡張子なしの場合は .png が付与される
python contributor_graph.py -o out/report

# 既存ディレクトリを指定すると、その中に自動命名で保存
python contributor_graph.py -o c:/tmp/graphs/
```

### グラフの内容

- 著者ごとに以下を可視化します:
  - 赤い棒グラフ: 追加行数（insertions）
  - 青い棒グラフ: 削除行数（deletions）
  - 緑の折れ線グラフ（右軸）: コミット数

