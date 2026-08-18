# Databricks notebook source
# MAGIC %md
# MAGIC # 99. （任意）環境リセット
# MAGIC
# MAGIC このNotebookは、ワークショップ用に作成した **スキーマごと** 削除して、ゼロから再スタートするためのものです。
# MAGIC
# MAGIC > ⚠️ **注意**: 実行すると、作成したテーブル・Volume・関数がすべて削除されます。
# MAGIC > 通常のワークショップ進行では実行不要です。やり直したいときだけ使ってください。

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ## 現在の状態を確認
# MAGIC 削除前に、対象スキーマの中身を確認します。

# COMMAND ----------

print(f"削除対象スキーマ: {CATALOG_NAME}.{SCHEMA_NAME}\n")
print("テーブル一覧:")
display(spark.sql(f"SHOW TABLES IN {CATALOG_NAME}.{SCHEMA_NAME}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ1: 行フィルタ・マスクの解除（先に外す）
# MAGIC 関数を消す前に、テーブルへの適用を解除します（エラーは無視してOK）。

# COMMAND ----------

for stmt in [
    "ALTER TABLE customers_silver DROP ROW FILTER",
    "ALTER TABLE customers_silver ALTER COLUMN 電話番号 DROP MASK",
]:
    try:
        spark.sql(stmt); print(f"  ✅ {stmt}")
    except Exception as e:
        print(f"  ⏭️ スキップ: {stmt}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ2: スキーマごと削除
# MAGIC
# MAGIC 下のセルの **コメントを外して** 実行してください（誤操作防止のため既定ではコメントアウト）。

# COMMAND ----------

# ⚠️ 実行するにはこの行のコメント(#)を外してください
# spark.sql(f"DROP SCHEMA IF EXISTS {CATALOG_NAME}.{SCHEMA_NAME} CASCADE")
# print(f"🗑️ スキーマ {CATALOG_NAME}.{SCHEMA_NAME} を削除しました（CASCADE）")

print("💡 削除を実行するには、上の spark.sql(...) 行のコメント(#)を外して再実行してください。")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 再スタート方法
# MAGIC リセット後は、`01_基盤_環境セットアップ` からもう一度実行してください。
