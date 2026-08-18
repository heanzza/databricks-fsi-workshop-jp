# Databricks notebook source
# MAGIC %md
# MAGIC # 06. Unity Catalog Part2 — 権限管理・機微情報マスキング
# MAGIC
# MAGIC ## 📋 このパートで学ぶこと
# MAGIC
# MAGIC 1. **権限管理（GRANT / REVOKE）** — 画面（カタログエクスプローラー）から付与・剥奪
# MAGIC 2. **列マスキング（ABAC）** — 電話番号など機微情報（PII）を、**タグ＋ポリシー** で保護
# MAGIC
# MAGIC ## 前提条件
# MAGIC - `02` で `customers_silver` が存在すること
# MAGIC
# MAGIC > 🖱️ **ほぼ画面操作で行います**。SQLを書くのは **マスキング関数の登録（1回だけ）** です。
# MAGIC > 権限付与・タグ付け・ポリシー適用は **すべてカタログエクスプローラーの画面** から行います。

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🏦 業務シナリオ
# MAGIC
# MAGIC | ロール | 電話番号（`phone`） |
# MAGIC |--------|---------------------|
# MAGIC | **本部（企画・与信）** | 平文で閲覧可 |
# MAGIC | **それ以外（営業担当など）** | **マスク表示**（上3桁 + `-****-****`） |
# MAGIC
# MAGIC これを **列マスキング（ABAC：タグに基づくポリシー）** で実現します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ1:【UI】権限管理（GRANT / REVOKE）
# MAGIC
# MAGIC 権限の付与・剥奪は、**カタログエクスプローラーの画面** から行えます（SQLもPythonも不要）。
# MAGIC
# MAGIC ### 付与（GRANT）
# MAGIC 1. 左サイドバー **「カタログ」** → `workspace` → ご自身のスキーマ → **`customers_silver`** を開く
# MAGIC 2. **「権限」（Permissions）** タブをクリック
# MAGIC 3. **「付与」（Grant）** ボタンをクリック
# MAGIC 4. **プリンシパル**（ユーザー / グループ）を選び、付与する権限（例: `SELECT`）にチェック → **「付与」**
# MAGIC
# MAGIC ### 剥奪（REVOKE）
# MAGIC 1. 同じ **「権限」** タブで、対象プリンシパルの行の権限を外す（または **「取り消し」/ゴミ箱**）→ 保存
# MAGIC
# MAGIC > 💡 上位の **カタログ／スキーマ** に対して付与すれば、配下のテーブルにまとめて効かせられます
# MAGIC > （カタログ → スキーマ → テーブルの各「権限」タブから同様に操作）。
# MAGIC >
# MAGIC > ℹ️ 権限は本来 **グループ単位**で付けるのが定石です（本部グループに `SELECT` など）。
# MAGIC > グループが作れない環境では、まずは自分のユーザーで画面操作の流れだけ確認すればOKです。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ2: 列マスキング（ABAC）— 電話番号の保護
# MAGIC
# MAGIC **ABAC（属性ベースのアクセス制御）** では、「**タグの付いた列** に **マスキング関数** を自動適用する」という
# MAGIC **ポリシー** を作ります。列が増えても、タグを付けるだけで同じ保護が効くのが利点です。
# MAGIC
# MAGIC 流れは3つ:
# MAGIC 1. **マスキング関数を登録**（← ここだけSQL）
# MAGIC 2. **列にタグを付ける**（UI）
# MAGIC 3. **ポリシーを作成**して、タグ付き列にマスクを適用（UI）

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2-1. マスキング関数を登録（このノートブックで唯一のSQL）
# MAGIC
# MAGIC 電話番号を **上3桁 + `-****-****`** に変換する関数を作ります。
# MAGIC 「誰に適用するか（本部は除外）」は関数ではなく **ステップ2-3のポリシー** 側で指定します。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- マスキング関数（変換ロジックだけを定義。適用対象はポリシーで制御）
# MAGIC CREATE OR REPLACE FUNCTION mask_phone(phone STRING)
# MAGIC RETURNS STRING
# MAGIC RETURN CONCAT(SUBSTRING(phone, 1, 3), '-****-****');

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2-2.【UI】保護したい列にタグを付ける
# MAGIC
# MAGIC 1. カタログエクスプローラーで **`customers_silver`** → **「概要」** タブを開く（カラム一覧が表示されます）
# MAGIC 2. **`phone`** 列の行で **「タグを追加」** をクリック
# MAGIC 3. タグ **`class.phone_number`** を付与 → 保存
# MAGIC
# MAGIC > 💡 同じタグ **`class.phone_number`** を他の電話番号系の列にも付けておけば、あとで **1つのポリシー** でまとめて保護できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2-3.【UI】ABACポリシーを作成してマスクを適用
# MAGIC
# MAGIC #### ① ポリシー作成画面を開く
# MAGIC 1. カタログエクスプローラーで、ポリシーを効かせたい **スコープ** を開きます
# MAGIC    - 今回は **`customers_silver`**（テーブル）でOK。※スキーマ／カタログに付けると配下の全テーブルに自動適用されます
# MAGIC 2. **「ポリシー」（Policies）** タブ → **「ポリシーを作成」（New policy）** をクリック
# MAGIC
# MAGIC #### ② 各項目を以下のとおり入力・選択
# MAGIC
# MAGIC | 項目 | 入力・選択する値 | 補足 |
# MAGIC |------|------------------|------|
# MAGIC | **名前（Name / ポリシーID）** | `mask_phone_policy` | スコープ内で一意の名前 |
# MAGIC | **説明（Description）** | `電話番号(PIIタグ)を本部以外にマスク` | 任意。監査ログに残る |
# MAGIC | **ポリシータイプ（Policy type）** | **列マスク（Column mask）** | 行フィルタではなく列マスクを選択 |
# MAGIC | **適用先（Applied to / TO）** | `All account users`（全ユーザー） | このマスクを効かせる対象 |
# MAGIC | **除外（Except for / EXCEPT）** | **本部グループ**（例: `honbu_team`） | ここに入れた人だけ **平文** で見える |
# MAGIC | **列の条件（Match columns）** | タグ **`class.phone_number`** が付いた列 | 内部式: `has_tag('class.phone_number')`。エイリアス例 `phone_col` |
# MAGIC | **対象列（On column）** | 上の一致列（`phone_col`） | マスク関数の第1引数に自動で渡されます |
# MAGIC | **マスキング関数（Masking function）** | `mask_phone`（2-1で作成） | 関数の第1引数＝対象列に自動バインド |
# MAGIC | **関数の追加引数（Using columns）** | **なし（空）** | `mask_phone` は列1つだけなので追加不要 |
# MAGIC
# MAGIC 3. **「作成」（Create）** をクリック → 権限と参照が検証され、ポリシーが有効になります
# MAGIC
# MAGIC > ✅ これで「**`class.phone_number` タグの付いた列は、本部グループ以外にはマスク表示**」というルールが、
# MAGIC > **列名を書かなくても**（タグ基準で）自動適用されます。同じタグを付けた列はすべて同じポリシーで保護されます。
# MAGIC
# MAGIC > 🔑 **必要な権限**: ポリシー作成には対象securableへの **MANAGE** と 関数への **EXECUTE**、
# MAGIC > タグ付けには **ASSIGN（タグ）** と **APPLY TAG（テーブル）** が必要です。
# MAGIC
# MAGIC > 🧩 **（参考）SQLでの同等表現**（UIの各項目がこう対応します。実行はUIでOK）:
# MAGIC > ```sql
# MAGIC > CREATE POLICY mask_phone_policy
# MAGIC >   ON TABLE customers_silver
# MAGIC >   COLUMN MASK mask_phone
# MAGIC >   TO `account users` EXCEPT `honbu_team`
# MAGIC >   FOR TABLES
# MAGIC >   MATCH COLUMNS has_tag('class.phone_number') AS phone_col
# MAGIC >   ON COLUMN phone_col;
# MAGIC > ```
# MAGIC
# MAGIC > ⚠️ **環境について**: ABAC（ガバナンスタグ＋ポリシー）は新しめのガバナンス機能です。
# MAGIC > 「ポリシー」タブやガバナンスタグのメニューが出ない／Free Edition 等で使えない場合は、
# MAGIC > 講師環境（Premium 以上）でのデモをご検討ください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ3:【UI】適用結果の確認
# MAGIC
# MAGIC 1. カタログエクスプローラーで `customers_silver` → **「サンプルデータ」** を開く
# MAGIC 2. `phone` 列が **マスク表示**（上3桁 + `-****-****`）になっていることを確認
# MAGIC    - 除外グループ（本部）のユーザーで見ると **平文** で見えます
# MAGIC 3. **「概要」** タブのカラム一覧で `phone` に **マスク／タグ** が付いていることを確認
# MAGIC
# MAGIC > 💡 **重要**: このマスキングは **ダッシュボード（05）や Genie（04）にもそのまま効きます**。
# MAGIC > BIツール側で別途権限設計する必要がありません（Tableau との大きな違い）。

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ 完了チェック
# MAGIC - [ ] 画面（権限タブ）から GRANT / REVOKE の操作を確認した
# MAGIC - [ ] マスキング関数 `mask_phone` を登録した（唯一のSQL）
# MAGIC - [ ] `phone` 列にタグを付け、ABACポリシーでマスクを適用した
# MAGIC - [ ] マスク結果が BI/Genie にも波及することを理解した
# MAGIC
# MAGIC ### 🚀 次のモジュール
# MAGIC **07_DE2_Lakeflow_Job** → ジョブ定義・実行状況・監査ログ・利用コスト
