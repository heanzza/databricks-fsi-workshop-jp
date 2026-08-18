# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # 共通設定 (00_config)
# MAGIC
# MAGIC このNotebookは、本ワークショップで使用する **カタログ・スキーマ・Volume** を作成・指定します。
# MAGIC `01` 以降のNotebookから `%run ./00_config` で呼び出されるため、**単独で実行する必要はありません**。
# MAGIC
# MAGIC ## 📝 参加者の方への注意
# MAGIC
# MAGIC 下のセルで **`SCHEMA_NAME`** をご自身のイニシャル付きの名前に変更してください（例: `workshop_ys`）。
# MAGIC 複数の参加者が同じ環境で作業する場合の名前衝突を避けるための慣例です。
# MAGIC
# MAGIC > 💡 Databricks Free Edition では1人1ワークスペースなので衝突は起きませんが、慣例として実施します。

# COMMAND ----------

# DBTITLE 1,参加者が変更する設定
# ============================================================
# カタログ名 — Databricks Free Edition では `workspace` カタログが既定で用意されています
# ============================================================
CATALOG_NAME = "workspace"

# ============================================================
# スキーマ名 — `xx` の部分をご自身のイニシャルに変更してください（例: workshop_ys）
# ============================================================
SCHEMA_NAME = "workshop_xx"

# COMMAND ----------

# DBTITLE 1,Volume パスの定義（変更不要）
# データファイル（CSV）を格納する Volume のフルパス
VOLUME_SOURCE_FILES = f"/Volumes/{CATALOG_NAME}/{SCHEMA_NAME}/source_files"

# COMMAND ----------

# MAGIC %md
# MAGIC ## カタログ・スキーマ・Volume の作成
# MAGIC
# MAGIC | リソース | 役割 |
# MAGIC |---------|------|
# MAGIC | カタログ `workspace` | データの最上位の入れ物（Free Edition で既存のため作成不要） |
# MAGIC | スキーマ `workshop_xx` | 本ワークショップで使う **テーブル・Volume** をまとめる場所 |
# MAGIC | Volume `source_files` | CSV ファイルを格納する場所 |

# COMMAND ----------

# 使用するカタログを指定
spark.sql(f"USE CATALOG {CATALOG_NAME}")

# スキーマを作成（既に存在する場合はスキップ）
spark.sql(f"""
    CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}
    COMMENT 'Databricks ワークショップ用スキーマ（預かり資産クロスセル想定）'
""")

# 使用するスキーマを指定
spark.sql(f"USE SCHEMA {SCHEMA_NAME}")

# Volume を作成（既に存在する場合はスキップ）
spark.sql(f"""
    CREATE VOLUME IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}.source_files
    COMMENT 'CSV などのソースファイルを格納'
""")

print("✅ セットアップ完了")
print(f"   カタログ : {CATALOG_NAME}")
print(f"   スキーマ : {SCHEMA_NAME}")
print(f"   Volume   : {VOLUME_SOURCE_FILES}")