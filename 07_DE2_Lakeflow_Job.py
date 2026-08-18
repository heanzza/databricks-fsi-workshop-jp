# Databricks notebook source
# MAGIC %md
# MAGIC # 07. Data Engineering Part2 — ジョブで自動化（パイプライン → ダッシュボード更新）
# MAGIC
# MAGIC ## 📋 このパートで学ぶこと（すべて画面操作・コード不要）
# MAGIC
# MAGIC 1. **Lakeflow Job** — `02` の **パイプライン** と `05` の **ダッシュボード更新** を、1つのジョブにまとめる
# MAGIC 2. **タスクの依存関係** — 「パイプラインで最新化 → そのあとダッシュボードを更新」を自動で
# MAGIC 3. **スケジュール実行・実行状況・利用状況の確認**（すべて画面から）
# MAGIC
# MAGIC ## 🎯 このモジュールのゴール
# MAGIC
# MAGIC 毎朝、**データの最新化（Silver再生成）→ ダッシュボードの更新** までを **全自動** で回す仕組みを、画面だけで作ります。
# MAGIC
# MAGIC ## 前提条件
# MAGIC - `02` の **Lakeflow Designer で公開したパイプライン**（`customers_silver` などを生成）が存在
# MAGIC - `05` の **AI/BI ダッシュボード** が存在
# MAGIC
# MAGIC > 🖱️ このモジュールは **コードを書きません**。すべて **ジョブ画面** の操作です。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧩 作るジョブの全体像
# MAGIC
# MAGIC ```
# MAGIC  [タスクA] ビジュアルデータ準備        [タスクB] ダッシュボード更新
# MAGIC  02のDesignerフロー        ──依存──▶  05のAI/BIダッシュボード
# MAGIC  （Silverを最新化）                   （最新データで更新）
# MAGIC ```
# MAGIC
# MAGIC → **A（ビジュアルデータ準備）が成功したら B（ダッシュボード更新）が走る**、という依存でつなぎます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ1:【UI】ジョブを新規作成し、タスクA（ビジュアルデータ準備）を追加
# MAGIC
# MAGIC 1. 左サイドバー **「ジョブとパイプライン」** → **「ジョブを作成」**
# MAGIC 2. ジョブ名を **`預かり資産クロスセル_日次更新`** に変更
# MAGIC 3. 最初のタスクを設定:
# MAGIC
# MAGIC | 項目 | 値 |
# MAGIC |------|-----|
# MAGIC | **タスク名** | `run_prep` |
# MAGIC | **種類（Type）** | **ビジュアルデータ準備（Visual data prep）** |
# MAGIC | **対象** | `02` の Lakeflow Designer で作成した **ビジュアルデータ準備（フロー）** を選択 |
# MAGIC
# MAGIC 4. **「タスクを作成」** で保存
# MAGIC
# MAGIC > 💡 `02` の Lakeflow Designer で作ったものは **「ビジュアルデータ準備」** なので、タスク種別もこれを選びます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ2:【UI】タスクB（ダッシュボード更新）を追加して依存でつなぐ
# MAGIC
# MAGIC 1. キャンバスで **「＋ タスクを追加」** をクリック
# MAGIC 2. 設定:
# MAGIC
# MAGIC | 項目 | 値 |
# MAGIC |------|-----|
# MAGIC | **タスク名** | `refresh_dashboard` |
# MAGIC | **種類（Type）** | **ダッシュボード（AI/BI ダッシュボード）** |
# MAGIC | **ダッシュボード** | `05` で作った「預かり資産クロスセル 提案対象ダッシュボード」を選択 |
# MAGIC | **依存先（Depends on）** | **`run_prep`** |
# MAGIC | **（任意）購読者** | メールで更新後のダッシュボードを送りたい宛先 |
# MAGIC
# MAGIC 3. **「タスクを作成」** → キャンバスに **A →（矢印）→ B** の依存が表示されればOK

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ3:【UI】まずは手動で実行（動作確認）
# MAGIC
# MAGIC 1. 右上の **「今すぐ実行」（Run now）** をクリック
# MAGIC 2. **実行が始まり、A（ビジュアルデータ準備）→ B（ダッシュボード更新）** の順に流れます
# MAGIC
# MAGIC > 💡 まずは **手動実行** で「パイプライン → ダッシュボード更新」が1本で動くことを確認できればOKです。
# MAGIC
# MAGIC ### （任意）スケジュールで自動化する
# MAGIC 定期実行にしたい場合は、**ジョブを保存したあと** ジョブ詳細画面の右側で設定します。
# MAGIC 1. 右側パネルの **「スケジュールとトリガー」** → **「トリガーを追加」**
# MAGIC 2. **種類=スケジュール（Scheduled）**、例: **毎朝 7:00**（cron でも指定可）→ 保存
# MAGIC
# MAGIC > ⚠️ 「スケジュールとトリガー」が出ない・設定できない場合:
# MAGIC > - **ジョブがまだ保存されていない** → タスクを作成して一度ジョブを保存すると、右側に表示されます
# MAGIC > - **タスクAが未完成**（`02` のビジュアルデータ準備が **未公開**）→ 先に Designer フローを **公開/実行** してから、
# MAGIC >   ジョブのタスクで選び直してください
# MAGIC > - ワークショップでは **スケジュールは任意** です。**「今すぐ実行」だけでも学習内容は完了** します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ4:【UI】実行状況の確認
# MAGIC
# MAGIC 1. ジョブ画面の **「実行」（Runs）** タブを開く
# MAGIC 2. 各実行の **ステータス（成功/失敗）・所要時間・開始終了時刻** を確認
# MAGIC 3. 実行をクリックすると、**タスクごと（A/B）のログ・出力** と DAG が見られます
# MAGIC 4. 失敗時は、赤くなったタスクをクリックすると **エラー内容** が特定できます
# MAGIC
# MAGIC > 💡 通知（メール等）や、失敗時の自動リトライも画面から設定できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ5: 利用状況（コスト）の確認 — System Tables
# MAGIC
# MAGIC DBU 消費・コストは **システムテーブル `system.billing.usage`** に記録されます（ジョブ / SQL / パイプライン別）。
# MAGIC 単価は `system.billing.list_prices` にあり、掛け合わせるとコスト（$）を集計できます。
# MAGIC
# MAGIC > 💡 利用量は、この System Tables を **SQLで集計**するか、System Tables ベースの
# MAGIC > **使用量ダッシュボード**（用意されているテンプレート）で可視化します。

# COMMAND ----------

# DBTITLE 1,直近7日のDBU消費（system.billing.usage）
# MAGIC %sql
# MAGIC SELECT usage_date, sku_name, SUM(usage_quantity) AS total_dbus
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= current_date() - INTERVAL 7 DAYS
# MAGIC GROUP BY usage_date, sku_name
# MAGIC ORDER BY usage_date DESC, total_dbus DESC;

# COMMAND ----------

# MAGIC %md
# MAGIC > ⚠️ **Free Edition の制約**: `system.billing`（課金系のSystem Tables）は **参照できない場合があります**。
# MAGIC > その場合は本ステップはスキップし、「利用量は System Tables で確認する」という考え方だけ押さえればOKです。
# MAGIC >
# MAGIC > 💡 タグ（コストセンター等）を付けておくと、`system.billing.usage` の集計で **部門別のコスト配賦** も可能です。

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ 完了チェック
# MAGIC - [ ] ジョブを作成し、タスクA（ビジュアルデータ準備）を追加した
# MAGIC - [ ] タスクB（ダッシュボード更新）を追加し、A→B の依存でつないだ
# MAGIC - [ ] スケジュールを設定し、「今すぐ実行」で動作確認した
# MAGIC - [ ] 実行状況・利用状況を画面で確認した
# MAGIC
# MAGIC # 🎉 ワークショップ完了！
# MAGIC
# MAGIC ### 全体で体験したこと
# MAGIC 1. **DE Part1（02）**：Lakeflow Designer で結合・NULL除外・感情分析（Silver を整える）
# MAGIC 2. **UC Part1（03）**：AIによる日本語コメント自動生成・Genie One でのデータ探索・リネージ
# MAGIC 3. **Genie One（04）**：日本語で対話的にデータ分析（提案対象の抽出・店舗別可視化）
# MAGIC 4. **AI/BI Dashboard（05）**：自然言語の指示だけでダッシュボードを自動生成
# MAGIC 5. **UC Part2（06）**：権限管理（画面）・列マスキング（ABAC）
# MAGIC 6. **DE Part2（07）**：ジョブでパイプライン→ダッシュボード更新を自動化
# MAGIC
# MAGIC → **取込からガバナンス・AI・可視化・運用まで、単一プラットフォームで完結**することを体験しました。
# MAGIC
# MAGIC > 環境をリセットする場合は `99_リセット` を実行してください。
