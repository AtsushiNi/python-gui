# API Table Viewer

複数のAPIを実行し、結果をテーブル表示するPython製GUIアプリケーションです。

## 特徴

- **6つのAPI設定**: 最大6つのAPIを同時に設定・実行可能
- **直感的なGUI**: PySide6を使用したモダンなインターフェース
- **リアルタイム実行**: 複数のAPIを並列で実行し、結果をリアルタイム表示
- **詳細な結果表示**: ステータスコード、応答時間、エラー情報などをテーブル表示
- **ソート・フィルター機能**: 結果のソートやキーワードフィルター
- **エクスポート機能**: 実行結果のエクスポート（CSV予定）
- **クロスプラットフォーム**: Windows, macOS, Linuxで動作

## インストール方法

### 前提条件

- Python 3.11以上
- uv

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd api-table-viewer
```

### 2. 依存関係のインストール（uvを使用）


```bash
uv sync
```


### 3. アプリケーションの起動

```bash
uv run python src/main.py
```

## 使用方法

### 1. APIの設定

1. API設定ダイアログで、最大6つのAPIを設定します
2. 各APIについて以下の項目を設定:
   - **有効/無効**: チェックボックスで切り替え
   - **名前**: APIの表示名
   - **URL**: APIエンドポイントのURL
   - **メソッド**: HTTPメソッド（GET, POST, PUT, DELETE, PATCH, HEAD）
   - **タイムアウト**: リクエストのタイムアウト時間（秒）
3. 「テスト」ボタンで個別のAPI設定を検証

### 2. APIの実行

1. 「APIを実行」ボタンをクリック
2. 実行確認ダイアログが表示されるので「はい」を選択
3. プログレスバーで実行進捗を確認
4. 結果が右側のテーブルに表示される

### 3. 結果の確認と操作

- **テーブル表示**: API名、ステータス、ステータスコード、応答時間、メソッド、URL、実行時刻、エラー情報
- **ソート**: 列ヘッダーをクリックしてソート
- **フィルター**: 上部の検索ボックスでキーワード検索
- **詳細表示**: 行を選択して「詳細表示」ボタンで詳細情報を確認
- **結果クリア**: 「結果をクリア」ボタンでテーブルをリセット

## プロジェクト構造

```
api-table-viewer/
├── src/
│   ├── main.py                 # アプリケーションエントリーポイント
│   ├── logger.py               # ロギング設定
│   ├── models/
│   │   ├── api_config.py       # API設定データモデル
│   │   ├── applications_table_model.py # アプリケーションテーブルモデル
│   │   └── table_model.py      # テーブルデータモデル
│   ├── api/
│   │   ├── client.py           # APIクライアント実装
│   │   └── flexible_types.py   # 柔軟なAPIタイプシステム
│   ├── gui/
│   │   ├── main_window.py      # メインウィンドウ
│   │   ├── api_dialog.py       # API設定ダイアログ
│   │   ├── result_panel.py     # 結果表示パネル
│   │   └── api_result_dialog.py # API実行結果ダイアログ
│   └── mock_server/
│       ├── __init__.py         # モックサーバーパッケージ
│       └── main.py             # モックサーバー実装
├── .gitignore                  # Git除外ファイル設定
├── pyproject.toml             # プロジェクト設定と依存関係
├── uv.lock                    # uvロックファイル
├── run_mock_server.py         # モックサーバー起動スクリプト
├── api_table_viewer.spec      # PyInstaller設定
└── README.md                  # このファイル
```

## 開発者向け情報

### 依存関係の追加

```bash
# uvを使用して依存関係を追加
uv add <package-name>
```

### テスト実行

```bash
python src/main.py
```

### 実行ファイルのビルド

#### PyInstallerを使用:

```bash
uv run pyinstaller --onefile --windowed --name api_table_viewer src/main.py
```

#### ビルド成果物:
- `dist/api_table_viewer` (macOS/Linux)
- `dist/api_table_viewer.exe` (Windows)

### コードフォーマット

```bash
# blackを使用（推奨）
black src/

# isortを使用
isort src/
```

## モックサーバーの使用

外部APIサービス（Beeceptor）の代わりにローカルモックサーバーを使用できます。

### モックサーバーの起動

```bash
uv run python run_mock_server.py
```

### モックサーバーのエンドポイント

モックサーバーは以下のエンドポイントを提供します：

- `GET /` - サーバー情報と利用可能なエンドポイント
- `GET /health` - ヘルスチェック
- `GET /applications/type-a` - タイプA（経費申請）のサンプルデータ
- `GET /applications/type-b` - タイプB（休暇申請）のサンプルデータ
- `GET /applications/type-c` - タイプC（権限申請）のサンプルデータ
- `GET /applications/all` - すべてのタイプのサンプルデータ
- `GET /docs` - インタラクティブなAPIドキュメント（Swagger UI）

### API設定の変更

GUIアプリケーションでAPI設定を変更してローカルサーバーを指すようにします：

1. API設定ダイアログを開く
2. 各APIのURLを以下のように変更：
   - Type A: `http://localhost:8001/applications/type-a`
   - Type B: `http://localhost:8001/applications/type-b`
   - Type C: `http://localhost:8001/applications/type-c`
3. 「設定を保存」をクリック

### モックサーバーの特徴

- **ランダムデータ生成**: 毎回異なるサンプルデータを生成
- **リアルタイム応答**: 外部APIへの依存なし
- **エラーシミュレーション**: タイムアウトやサーバーエラーをテスト可能
- **CORS対応**: フロントエンドからのアクセスを許可

## 技術スタック

- **GUIフレームワーク**: PySide6 (Qt for Python)
- **HTTPクライアント**: requests
- **モックサーバー**: FastAPI + uvicorn
- **ロギング**: Python標準loggingモジュール
- **データモデル**: Python dataclasses
- **ビルドツール**: PyInstaller
- **パッケージ管理**: uv

## トラブルシューティング

### アプリケーションが起動しない場合

1. 依存関係が正しくインストールされているか確認:
   ```bash
   uv sync --frozen
   ```

2. Pythonバージョンを確認:
   ```bash
   python --version
   ```

3. ログファイルを確認（コンソール出力にエラーが表示されます）

### PyInstallerビルドが失敗する場合

1. PyInstallerのバージョンを確認:
   ```bash
   pyinstaller --version
   ```

2. 必要な隠しインポートをspecファイルに追加
3. UPXがインストールされているか確認（圧縮を使用する場合）
