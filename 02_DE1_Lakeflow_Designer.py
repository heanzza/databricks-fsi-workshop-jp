# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # 02. Data Engineering Part1 — Lakeflow Designer で Silver を整える
# MAGIC
# MAGIC ## 📋 このパートで学ぶこと
# MAGIC
# MAGIC **コードを一切書かず**、Lakeflow Designer の **キャンバス** で、生データ（Bronze）を
# MAGIC **結合・整形して分析しやすい Silver テーブルに整えます**。
# MAGIC
# MAGIC 1. **Bronze → Silver** — 顧客マスタに店舗・担当者を結合
# MAGIC 2. **データクレンジング** — **欠損値（NULL）の除外** を Designer で体験
# MAGIC 3. **AI関数（感情分析）** — 「お客様の声」テキストを Designer で **感情分析**（`ai_analyze_sentiment`）
# MAGIC
# MAGIC > 💡 **役割分担がポイント**
# MAGIC > - **Lakeflow Designer（このノートブック）** … データを **結合・整形して整える** ところまで
# MAGIC > - **Genie（`04`）／ダッシュボード（`05`）** … 「交渉履歴との結合」「提案対象顧客の抽出」「店舗別集計」などの **分析・絞り込み**
# MAGIC >
# MAGIC > つまり Designer では **フィルタ（抽出条件）は書きません**。整えたテーブルに対して、条件は Genie に日本語で聞きます。
# MAGIC
# MAGIC ## 前提条件
# MAGIC - `01_基盤_環境セットアップ` が完了していること（Bronze テーブルが存在）
# MAGIC
# MAGIC > ℹ️ **Free Edition のヒント**: 「大きな負荷がかかっています」と表示されたら **1分ほど待って再実行** してください。
# MAGIC >
# MAGIC > 📝 **列名について**: 本ワークショップのテーブルは **英語のカラム名**（例: `deposit_balance_manyen`）を採用しています。
# MAGIC > 日本語の意味は `03` で **コメント（COMMENT）** として付与し、Genie や検索で日本語が使えるようにします。
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🎨 Lakeflow Designer とは
# MAGIC
# MAGIC **ドラッグ＆ドロップ＋自然言語** で ETL パイプラインを構築できるツールです。コードを書かずに「ソース→変換→ターゲット」をキャンバスで組み立てられます。
# MAGIC
# MAGIC > 💡 **イメージ**: 「Excelのピボットテーブルをもっと強力にしたもの」。今回はこれ **だけ** で、生データのクレンジング（結合・NULL除外・AI関数）を **すべてノーコード** で行います。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📖 カラム名の対応表（日本語 → 英語）
# MAGIC
# MAGIC | 日本語 | customers | 日本語 | customer_voice |
# MAGIC |--------|-----------|--------|----------------|
# MAGIC | 顧客ID | `customer_id` | 声ID | `voice_id` |
# MAGIC | 氏名 | `name` | 受付日 | `received_date` |
# MAGIC | 年齢 | `age` | チャネル | `channel` |
# MAGIC | 顧客セグメント | `segment` | 本文 | `voice_text` |
# MAGIC | 預金残高(万円) | `deposit_balance_manyen` | | |
# MAGIC | 預かり資産残高(万円) | `managed_asset_manyen` | | |
# MAGIC | 生年月日 | `birth_date` | | |
# MAGIC | メイン店舗ID | `branch_id` | | |
# MAGIC | 担当者ID | `employee_id` | | |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🗺️ パイプライン全体像（Designer で作るもの）
# MAGIC
# MAGIC ```
# MAGIC  [Bronze]                              [Silver：Designerで整える]
# MAGIC  customers_bronze ┐
# MAGIC  branch_bronze    ├─(結合×2＋NULL除外)──────────▶ customers_silver
# MAGIC  employee_bronze  ┘
# MAGIC
# MAGIC  customer_voice_bronze ───(AI関数：感情分析)──────▶ customer_voice_silver   （＝お客様の声＋sentiment）
# MAGIC ```
# MAGIC
# MAGIC 最終的に作る **2つの Silver テーブル**：
# MAGIC
# MAGIC | # | テーブル | 内容 | 作成 |
# MAGIC |---|---|---|---|
# MAGIC | 1 | **`customers_silver`** | 顧客マスタ＋店舗名・担当者名（＋ 預金残高NULL行を除外） | ステップ2 |
# MAGIC | 2 | **`customer_voice_silver`** | お客様の声（VOC）に **感情分析**（sentiment）を付与 | ステップ4 |
# MAGIC
# MAGIC > 🔎 「交渉履歴との結合」や「提案対象顧客の抽出（預金1000万以上・預かり資産0・未接触）」は Designer では行いません。
# MAGIC > 次の `04`（Genie）・`05`（ダッシュボード）で、`customers_silver` と交渉履歴を使って分析します。
# MAGIC
# MAGIC 作り方は2通り。**どちらか1つ**でOKです（出力は同じ）。
# MAGIC
# MAGIC | 方法 | 概要 | こんな方に |
# MAGIC |------|------|-----------|
# MAGIC | **方法A** | 自然言語（Genie Code）でAIに生成してもらう | まずはラクに試したい方 |
# MAGIC | **方法B** | 演算子を自分でドラッグ配置・設定する | 確実に同じ結果にしたい方 |

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ1: Lakeflow Designer を開いてソースを追加
# MAGIC
# MAGIC 1. 左サイドバーの **「+ 新規」** → **「ビジュアルデータ準備」（Visual data prep）** をクリック
# MAGIC 2. Lakeflow Designer のキャンバスが表示されます
# MAGIC
# MAGIC ### ソーステーブル（Bronze）を3つ追加
# MAGIC 1. 左の **「演算子」** → **「ソースと出力」** → **「ソース」** をクリック
# MAGIC 2. 配置された箱 → 右パネルの **「既存を参照」** をクリック
# MAGIC 3. 検索欄に **`customers_bronze`** と入力して選択
# MAGIC 4. 同じ手順で **`branch_bronze`**・**`employee_bronze`** も追加
# MAGIC
# MAGIC → キャンバスに **3つのソース箱** が並んだ状態がゴールです。これ以降、この **同じキャンバス** に変換と出力を足していきます。
# MAGIC
# MAGIC > 🔍 **`customers_bronze` を選ぶと、右側に列と型・プレビューが表示されます**。ここで **`deposit_balance_manyen` に欠損（NULL）の行がある** ことに気づきます。
# MAGIC > 分析の妨げになるので、次のステップで **NULL行を除外**します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ2:【Silver】`customers_silver` を作成（結合＋NULL除外）
# MAGIC
# MAGIC `customers_bronze` に **店舗（branch）** と **担当者（employee）** を結合し、さらに **預金残高NULLの除外** を行います。
# MAGIC
# MAGIC ### 方法A｜自然言語（Genie Code）
# MAGIC キャンバス下部中央の **「ワークフローを編集または拡張...」** 入力欄に、次のように指示します。
# MAGIC
# MAGIC ```
# MAGIC customers_bronze に branch_bronze と employee_bronze を左結合し、
# MAGIC branch_name, area, prefecture, employee_name の列を追加してください。
# MAGIC また、deposit_balance_manyen が NULL（欠損）の行は除外してください。
# MAGIC 結果を customers_silver という名前で出力してください。
# MAGIC ```
# MAGIC
# MAGIC > 💡 **キーの設定は不要です**。方法A（自然言語）では結合キーを手動で選ぶ必要はありません。
# MAGIC > `branch_id`・`employee_id` は両テーブルで同じ列名なので、AIが自動で結合します。
# MAGIC > （もし結合がずれたら「`branch_id` と `employee_id` で結合してください」と一言足せばOK）
# MAGIC > ※ キーを自分で設定するのは **方法B** の場合だけです。
# MAGIC
# MAGIC ### 方法B｜演算子を手動で配置
# MAGIC 1. `customers_bronze` に **「結合」** を接続
# MAGIC    - 左入力=`customers_bronze`、右入力=`branch_bronze`
# MAGIC    - **結合タイプ**: 左結合（Left Join）／**結合条件**: 左 `branch_id` ＝ 右 `branch_id`
# MAGIC 2. その出力にもう1つ **「結合」** を接続
# MAGIC    - 右入力=`employee_bronze`
# MAGIC    - **結合タイプ**: 左結合（Left Join）／**結合条件**: 左 `employee_id` ＝ 右 `employee_id`
# MAGIC 3. **【NULL除外】** 「演算子」→ **「フィルター」** を接続し、条件に **`deposit_balance_manyen` が NULL でない** を指定
# MAGIC 4. （任意）**「選択」** で列を整理：`customers_bronze` の全列 ＋ `branch_name`, `area`, `prefecture`, `employee_name`
# MAGIC 5. **「ソースと出力」→「出力」** を接続 → **カタログ**=`workspace`／**スキーマ**=ご自身のスキーマ／**テーブル名**=`customers_silver`

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ3: 公開／実行
# MAGIC
# MAGIC 1. キャンバスに **出力 `customers_silver`** が接続されていることを確認
# MAGIC 2. 右上の **「公開」/「実行」** をクリック
# MAGIC 3. 出力の右下に **「✅ 成功」** が表示されれば完了です

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ4:【AI関数】「お客様の声」を感情分析する
# MAGIC
# MAGIC Lakeflow Designer では、**AI関数**（Foundation Model を呼ぶ組み込み関数）も **ノーコード** で使えます。
# MAGIC ここでは「お客様の声」（`customer_voice_bronze`：窓口・電話・アプリ・営業訪問で寄せられた声）の
# MAGIC テキスト列 `voice_text` を **感情分析**（`ai_analyze_sentiment`）し、`positive / negative / neutral / mixed` を付与します。
# MAGIC
# MAGIC > 🤖 モデルのエンドポイント設定やAPIキーは不要。列に対して関数を当てるだけで LLM の推論が使えます。
# MAGIC
# MAGIC ### ソースを追加
# MAGIC 1. 同じキャンバス（または新しいビジュアルデータ準備）で **「ソース」→「既存を参照」** → **`customer_voice_bronze`** を追加
# MAGIC
# MAGIC ### 方法A｜自然言語（Genie Code）※おすすめ
# MAGIC 入力欄に、次のように指示します。
# MAGIC
# MAGIC ```
# MAGIC customer_voice_bronze の voice_text を感情分析して sentiment 列を追加し、customer_voice_silver として出力してください。
# MAGIC ```
# MAGIC
# MAGIC > 💡 「感情を分析して」と書くだけで、Designer は内部で **`ai_analyze_sentiment(voice_text)`** を使ったSQLを生成します。
# MAGIC
# MAGIC ### 方法B｜演算子を手動で配置
# MAGIC 1. `customer_voice_bronze` に **「計算列」/「変換」** を接続し、新しい列 `sentiment` を追加
# MAGIC    - 式: `ai_analyze_sentiment(voice_text)`
# MAGIC 2. **「出力」** を接続 → **テーブル名**=`customer_voice_silver`
# MAGIC
# MAGIC > 💡 感情分析以外にも、`ai_classify`（種別分類）・`ai_summarize`（要約）・`ai_mask`（PII マスク）などの
# MAGIC > AI関数を、同じように自然言語や計算列で使えます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ5: 結果の確認（UI）
# MAGIC
# MAGIC コードを書かずに、UI で仕上がりを確認します。
# MAGIC
# MAGIC 1. 左サイドバー **「カタログ」** → `workspace` → ご自身のスキーマ → **`customers_silver`** を開く
# MAGIC 2. **「サンプルデータ」** タブでプレビュー、**行数が減っている**（預金残高NULLの行が除外された）ことを確認
# MAGIC 3. **「概要」/「列」** タブで、店舗名・担当者名の列が結合されていることを確認
# MAGIC 4. 同様に **`customer_voice_silver`** も開き、`sentiment`（ポジティブ／ネガティブ／中立／混在）が付与されていることを確認
# MAGIC
# MAGIC > 💡 Designer のキャンバス上でも、各出力ノードをクリックすると **プレビューと件数** が確認できます。
# MAGIC > 「ネガティブが多いチャネルは？」「交渉履歴との結合」「提案対象顧客の抽出」「店舗別集計」は、次の `04`（Genie）・`05`（ダッシュボード）で行います。

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ 完了チェック
# MAGIC - [ ] Lakeflow Designer で `customers_silver` を作成した（店舗・担当者を結合）
# MAGIC - [ ] `customers_silver` で **deposit_balance_manyen が NULL の行を除外**した
# MAGIC - [ ] AI関数（`ai_analyze_sentiment`）で「お客様の声」を感情分析し `customer_voice_silver` を作成した
# MAGIC - [ ] 「交渉履歴との結合・提案対象の抽出」は Designer では行わず、`04` の Genie / `05` のダッシュボードで実施することを理解した
# MAGIC
# MAGIC ### 🚀 次のモジュール
# MAGIC **03_UC1_データ定義とリネージ** → 日本語コメント・タグ・日本語検索・リネージ可視化
