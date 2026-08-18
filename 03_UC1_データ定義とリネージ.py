# Databricks notebook source
# MAGIC %md
# MAGIC # 03. Unity Catalog Part1 — データ定義・日本語検索・リネージ可視化
# MAGIC
# MAGIC ## 📋 このパートで学ぶこと（すべて画面操作・コード不要）
# MAGIC
# MAGIC 1. **データ定義（メタデータ）** — テーブル・カラムへの日本語コメントを **AIで自動生成** して付与
# MAGIC 2. **定義内容の確認・自然言語でのデータ探索** — カタログエクスプローラー / Genie One
# MAGIC 3. **リネージの可視化** — 「この数字はどのデータ由来か」を追跡
# MAGIC
# MAGIC ## 前提条件
# MAGIC - `02_DE1_Lakeflow_Designer` が完了していること（`customers_silver` / `customer_voice_silver` が存在）
# MAGIC
# MAGIC > 💡 **ポイント**: カラム名は英語ですが、ここで **日本語コメント** を付けることで、
# MAGIC > 現場の誰もが **日本語でデータを検索・理解** でき、**Genie も日本語で正しく回答** できるようになります。
# MAGIC >
# MAGIC > 🖱️ **このモジュールは SQL を書きません**。すべて **カタログエクスプローラーの画面操作** で行います。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ1: テーブル・カラムのコメントを **AIで自動生成**（コード不要）
# MAGIC
# MAGIC Databricks は、テーブルの中身から **説明文（コメント）を AI が自動生成** してくれます。ボタンを押すだけです。
# MAGIC
# MAGIC ### 1-1. テーブルを開く
# MAGIC 1. 左サイドバー **「カタログ」** をクリック
# MAGIC 2. `workspace` → ご自身のスキーマ（例: `workshop_xx`）→ **`customers_silver`** を開く
# MAGIC
# MAGIC ### 1-2. テーブルの説明を AI 生成
# MAGIC 1. **「概要」（Overview）** タブを開く
# MAGIC 2. 説明欄の **✨「AI で生成」/「AI提案」** ボタンをクリック
# MAGIC 3. AI が説明文を自動生成 → 内容を確認して **「承認」/「保存」**
# MAGIC
# MAGIC ### 1-3. 各カラムのコメントを AI 生成（まとめて承認）
# MAGIC 1. **「概要」** タブのカラム一覧を確認します（各カラムがコメント欄付きで並んでいます）
# MAGIC 2. 各カラムのコメント欄に **✨ AI提案** が表示されます
# MAGIC 3. **「すべて承認」（Accept all）** をクリック（または列ごとに ✔ で承認）
# MAGIC
# MAGIC > 📝 生成された説明は **その場で編集**できます。欄をクリックして書き換えるだけ（SQLは不要）。
# MAGIC >
# MAGIC > 🔑 **ポイント**: あとで **日本語で検索**したい業務用語は、コメントに **その語をそのまま含めて**おきます。
# MAGIC > AI生成だと別の言い回しになることがあるため（例: 「預かり資産」→「管理している資産」）、検索したい語で上書きしておくと確実です。例:
# MAGIC > - `deposit_balance_manyen` → 「**預金残高**（万円）。1000以上を『潤沢』とみなす」
# MAGIC > - `managed_asset_manyen` → 「**預かり資産**残高（万円）。0 の顧客が提案対象の候補」
# MAGIC > - `phone` / `my_number` → 「個人情報（PII）。06でマスキング対象」

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ2:【UI】付与した定義を確認
# MAGIC
# MAGIC 1. カタログエクスプローラーで **`customers_silver`** を開く
# MAGIC 2. タブを確認:
# MAGIC
# MAGIC | タブ | 確認できる内容 |
# MAGIC |------|---------------|
# MAGIC | **概要** | テーブルの説明（日本語コメント）＋ **各カラムのコメント一覧** |
# MAGIC | **サンプルデータ** | 先頭行のプレビュー |
# MAGIC | **依存関係（リネージ）** | 上流・下流のデータの流れ |
# MAGIC
# MAGIC > **「概要」タブ** のカラム一覧に、各カラムの **コメント** が表示されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ3:【UI】リネージの可視化
# MAGIC
# MAGIC 「この `customers_silver` は、どのデータから来ているのか？」を追跡します。
# MAGIC
# MAGIC 1. カタログエクスプローラーで **`customers_silver`** を開く
# MAGIC 2. **「依存関係」（Lineage）** タブをクリック
# MAGIC 3. リネージグラフ:
# MAGIC ```
# MAGIC customers_bronze ─┐
# MAGIC branch_bronze   ─┼→ customers_silver
# MAGIC employee_bronze ─┘
# MAGIC ```
# MAGIC 4. ノードをクリックで各テーブル詳細へ。**列レベルリネージ**も追跡可能。
# MAGIC
# MAGIC > 💡 監査・規制対応で「この数字の根拠は？」と問われたとき、リネージが証跡になります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ4:【Genie One】自然言語でデータの在り処を尋ねる
# MAGIC
# MAGIC キーワード検索ではなく、**Genie One に日本語で質問** して「その情報がどのテーブル・列にあるか」を教えてもらいます。
# MAGIC 付与した **日本語コメント** が、Genie One の回答精度を高めます。
# MAGIC
# MAGIC 1. **Genie One** を開く（Databricks の画面から Genie / アシスタントを起動）
# MAGIC 2. 入力欄に日本語で質問してみます:
# MAGIC    ```
# MAGIC    預かり資産額はどこにある？
# MAGIC    ```
# MAGIC 3. Genie One が、該当する **テーブル・列**（例: `customers_silver` の `managed_asset_manyen`）を教えてくれます
# MAGIC 4. 他の質問例:
# MAGIC    - `顧客の電話番号はどのテーブル・列？`
# MAGIC    - `預金残高はどこで見られる？`
# MAGIC    - `お客様の声（VOC）のデータはどこ？`
# MAGIC
# MAGIC > 💡 キーワードの完全一致でなくても、**意味で** 探し当てられるのが Genie One の強みです。
# MAGIC > コメント（日本語の説明）を付けておくほど、回答が正確になります。
# MAGIC >
# MAGIC > ✨ 英語カラム名でも、日本語コメントを付ければ **現場の誰もが日本語でデータにたどり着けます**（DXの民主化）。

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ 完了チェック
# MAGIC - [ ] テーブル・カラムのコメントを **AIで自動生成**して付与した（必要に応じて日本語に編集）
# MAGIC - [ ] カタログエクスプローラーで定義を確認した
# MAGIC - [ ] Genie One に日本語で質問し、データの在り処（テーブル・列）を教えてもらえた
# MAGIC - [ ] `customers_silver` のリネージを可視化した
# MAGIC
# MAGIC ### 🚀 次のモジュール
# MAGIC **04_DA_Genie_Space** → 日本語で対話的にデータ分析
