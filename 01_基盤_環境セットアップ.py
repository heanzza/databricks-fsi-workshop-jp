# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # 01. 基盤 — 環境セットアップとデータ取込
# MAGIC
# MAGIC ## 📋 このパートで学ぶこと
# MAGIC
# MAGIC 1. **Unity Catalog の3層構造** — カタログ・スキーマ・テーブルの関係
# MAGIC 2. **Volume によるファイル管理** — CSV を安全に保管
# MAGIC 3. **CSV → Delta テーブルの取込** — 顧客マスタ・交渉履歴・店舗・担当者
# MAGIC
# MAGIC ## 🎯 ゴール
# MAGIC
# MAGIC - 本ワークショップ用のスキーマ・Volume を作成する
# MAGIC - 4つの CSV を **Bronze テーブル**として取り込む
# MAGIC - 以降のモジュールで使う共通データ基盤を構築する
# MAGIC
# MAGIC > ℹ️ **Free Edition のヒント**: 「大きな負荷がかかっています」と表示されたら **1分ほど待って再実行** してください。
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🏦 ビジネスシナリオ
# MAGIC
# MAGIC **預かり資産クロスセル**：預金は多いが預かり資産を持たず、一定期間未接触の顧客を抽出し、店舗別に可視化して次の提案につなげます。
# MAGIC
# MAGIC ```
# MAGIC 01 データ取込（今回） → 02 Lakeflow Designer で結合・加工 → 03 Unity Catalog 定義・リネージ
# MAGIC   → 04 Genie で対話分析 → 05 AI/BI ダッシュボード → 06 権限管理・マスキング → 07 ジョブ・監査・コスト
# MAGIC ```
# MAGIC
# MAGIC ### 取り扱うデータ（茨城・栃木の架空データ）
# MAGIC
# MAGIC | データ | 形式 | 内容 | 件数 |
# MAGIC |--------|------|------|------|
# MAGIC | `customers.csv` | CSV | 顧客マスタ（属性・預金残高・預かり資産残高・担当店舗） | 1,000 |
# MAGIC | `contacts.csv` | CSV | 交渉・接触履歴（接触日・チャネル・提案商品・結果） | 約2,300 |
# MAGIC | `branch.csv` | CSV | 店舗マスタ（茨城・栃木の16店舗） | 16 |
# MAGIC | `employee.csv` | CSV | 担当者マスタ | 81 |
# MAGIC | `customer_voice.csv` | CSV | お客様の声（VOC：窓口・電話・アプリ・営業訪問の声）※`02` のAI関数デモ用 | 12 |

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ1: スキーマ・Volume の作成
# MAGIC
# MAGIC ```
# MAGIC workspace (カタログ)
# MAGIC └── workshop_xx (スキーマ)
# MAGIC     ├── customers_bronze / contacts_bronze / branch_bronze / employee_bronze (生データ)
# MAGIC     ├── ..._silver（クレンジング済み）/ ..._gold（提案対象マート）
# MAGIC     └── source_files (Volume: CSVファイル格納)
# MAGIC ```
# MAGIC
# MAGIC 下のセルで `00_config` を呼び出し、スキーマ・Volume を自動作成します。

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# 現在のカタログ・スキーマを確認
display(spark.sql("SELECT current_catalog() AS current_catalog, current_schema() AS current_schema"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ チェックポイント1
# MAGIC - [ ] `current_catalog` に `workspace` が表示されましたか？
# MAGIC - [ ] `current_schema` にご自身のスキーマ名（例: `workshop_ys`）が表示されましたか？
# MAGIC
# MAGIC ❌ スキーマ名が `workshop_xx` のまま → `00_config` の `SCHEMA_NAME` を編集して再実行してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ2: 配布ファイルを Volume に配置
# MAGIC
# MAGIC ZIP で配布された `data/` フォルダ内の CSV を、作成した Volume にコピーします。

# COMMAND ----------

import os, shutil

source_dir = "./data"
print(f"📂 配布データのフォルダ: {source_dir}\n配布ファイル一覧:")
for f in sorted(os.listdir(source_dir)):
    print(f"  • {f} ({os.path.getsize(os.path.join(source_dir, f)):,} bytes)")

# COMMAND ----------

for filename in os.listdir(source_dir):
    if not filename.endswith(".csv"):
        continue
    shutil.copy2(os.path.join(source_dir, filename), os.path.join(VOLUME_SOURCE_FILES, filename))
    print(f"  ✅ コピー完了: {filename}")

# COMMAND ----------

# Volume内のファイルを確認
print("📁 Volume内のファイル一覧:")
display(dbutils.fs.ls(VOLUME_SOURCE_FILES))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💡（参考）UIから Volume を操作
# MAGIC 1. 左サイドバー **「カタログ」** → `workspace` → `workshop_xx` → `source_files`
# MAGIC 2. Volume を選択して **「アップロード」** からファイル追加も可能

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ3: CSV → Delta テーブルへの取込
# MAGIC
# MAGIC **Delta Lake** は Databricks 標準のテーブル形式で、ACIDトランザクション・タイムトラベル・スキーマ管理を備えます。
# MAGIC 5つの CSV を `_bronze`（生データ）テーブルとして取り込みます。

# COMMAND ----------

# DBTITLE 1,5つのCSVをまとめてBronzeテーブル化
tables = {
    "customers":      "顧客マスタ",
    "contacts":       "交渉・接触履歴",
    "branch":         "店舗マスタ",
    "employee":       "担当者マスタ",
    "customer_voice": "お客様の声（VOC）",
}

for name, jp in tables.items():
    df = (spark.read.format("csv")
          .option("header", "true")
          .option("inferSchema", "true")
          .option("encoding", "UTF-8")
          .load(f"{VOLUME_SOURCE_FILES}/{name}.csv"))
    (df.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{name}_bronze"))
    print(f"  ✅ {jp}: {name}_bronze ({df.count():,} 件)")

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 顧客マスタの中身を確認
# MAGIC SELECT * FROM customers_bronze LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC > 📝 **わざと「未整形」の状態で取り込んでいます**（`02` の Lakeflow Designer でクレンジングを体験するため）。
# MAGIC > - **`deposit_balance_manyen`** … 一部の行が **空欄（NULL）** です。→ `02` で **NULL行を除外**します。
# MAGIC >
# MAGIC > 下のセルで実際に確認してみましょう。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- deposit の欠損件数を確認（02 でクレンジングする対象）
# MAGIC SELECT
# MAGIC   COUNT(*)                                  AS `全顧客数`,
# MAGIC   COUNT(deposit_balance_manyen)             AS `預金残高あり件数`,
# MAGIC   COUNT(*) - COUNT(deposit_balance_manyen)  AS `預金残高NULL件数`
# MAGIC FROM customers_bronze;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 交渉・接触履歴の中身を確認
# MAGIC SELECT * FROM contacts_bronze LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ4: 取り込んだデータの確認

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💡 結果セルから簡易ビジュアライズ
# MAGIC SQL結果タブ右の **「+」→「可視化」** で、コードなしにグラフ化できます。下のクエリで試してみましょう。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 顧客セグメント別の人数
# MAGIC SELECT segment AS `顧客セグメント`, COUNT(*) AS `人数`
# MAGIC FROM customers_bronze
# MAGIC GROUP BY segment
# MAGIC ORDER BY `人数` DESC;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 交渉結果の分布（提案の"見送り"がどれくらいあるか）
# MAGIC SELECT result AS `結果`, COUNT(*) AS `件数`
# MAGIC FROM contacts_bronze
# MAGIC GROUP BY result
# MAGIC ORDER BY `件数` DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ 完了チェック
# MAGIC 下のセルで **5つの Bronze テーブル**が揃っていることを確認します。

# COMMAND ----------

expected = {"customers_bronze", "contacts_bronze", "branch_bronze", "employee_bronze", "customer_voice_bronze"}
actual = {r.tableName for r in spark.sql("SHOW TABLES").collect()}
missing = expected - actual
if missing:
    print(f"⚠️ 見つからないテーブル: {sorted(missing)}")
    print(f"   現在のテーブル: {sorted(actual)}")
else:
    print("✅ 5つの Bronze テーブルが揃っています")
    for t in sorted(expected):
        print(f"   • {t}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC
# MAGIC - [ ] スキーマ・Volume を作成した
# MAGIC - [ ] 4つの CSV を Volume に配置した
# MAGIC - [ ] 4つの Bronze テーブルを作成した
# MAGIC - [ ] 簡単なクエリ／可視化でデータを確認した
# MAGIC
# MAGIC ### 🚀 次のモジュール
# MAGIC **02_DE1_Lakeflow_Designer** → 自然言語ETLで **2ファイル（顧客×交渉履歴）を結合**し、提案対象顧客を抽出します。