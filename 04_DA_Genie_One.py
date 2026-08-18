# Databricks notebook source
# MAGIC %md
# MAGIC # 04. Genie One — 日本語でのデータ分析（セットアップ不要）
# MAGIC
# MAGIC ## 📋 このパートで学ぶこと（すべて画面操作・コード不要）
# MAGIC
# MAGIC 1. **Genie One** — スペースを作らず、**日本語で質問するだけ** でデータ分析
# MAGIC 2. **自然言語での集計・可視化** — 「店舗別の平均預金は？」を聞くだけ
# MAGIC 3. **フォローアップ質問** で深掘り
# MAGIC
# MAGIC ## 🎯 このモジュールのゴール
# MAGIC
# MAGIC **預金残高は多いが預かり資産取引が少なく、一定期間接触していない顧客** を抽出し、**店舗別に可視化** します
# MAGIC （＝預かり資産クロスセルの提案対象顧客の抽出）。
# MAGIC 顧客属性・預金残高・預かり資産残高・交渉履歴（接触履歴）の架空データを使い、
# MAGIC **Genie One への日本語の質問だけ** で、この一連の流れを体験・確認します。
# MAGIC
# MAGIC ## 前提条件
# MAGIC - `02` の Silver テーブル（`customers_silver` / `customer_voice_silver`）が存在
# MAGIC - `01` の交渉履歴（`contacts_bronze`）が存在（「一定期間未接触」の判定に使用）
# MAGIC - `03` で日本語コメントを付与済み（Genie One の回答精度が上がります）

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🧞 Genie One とは
# MAGIC
# MAGIC **Genie One** は、**スペースの準備なしで** 日本語の質問に答えてくれる Databricks の AI アシスタントです。
# MAGIC アクセス権のあるデータの中から、Genie が **自動で対象テーブル・列を見つけ、SQLを生成して** 回答します。
# MAGIC
# MAGIC | | Genie One | Genie スペース |
# MAGIC |------|-----------|---------------|
# MAGIC | 準備 | **不要**（すぐ質問できる） | テーブル選択・指示の作り込みが必要 |
# MAGIC | 向いている場面 | まず手軽に聞きたい・探索 | 特定業務の精度を作り込む |
# MAGIC
# MAGIC > 💡 今回は **Genie One** で手軽に分析します。`03` で付けた日本語コメントのおかげで、
# MAGIC > 「預金」「預かり資産」などの用語が正しく解釈されます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ1: Genie One を開く
# MAGIC
# MAGIC 1. Databricks の画面から **Genie（Genie One）** を起動します
# MAGIC 2. 日本語の入力欄が表示されればOK。ここに質問を打ち込むだけです（コードは書きません）

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ2: 日本語で質問してみる（ウォームアップ）
# MAGIC
# MAGIC 入力欄に、以下を **日本語でそのまま** 入力して試してください。
# MAGIC
# MAGIC 1. `顧客は全部で何人いますか？`
# MAGIC 2. `顧客セグメント別の人数を教えて`
# MAGIC 3. `店舗別の平均預金残高を、多い順の棒グラフにして`
# MAGIC
# MAGIC > 💡 回答には **Genie が生成した SQL** が表示され、「＋」から **グラフ化** もできます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ3: 提案対象顧客を段階的に抽出する（このモジュールの本題）
# MAGIC
# MAGIC 「**預金は多いが預かり資産取引が少なく、一定期間接触していない顧客**」を、会話しながら少しずつ絞り込みます。
# MAGIC 前の回答を受けて質問を重ねられるのが Genie の強みです。
# MAGIC
# MAGIC 4. `預金残高が1000万以上の顧客は何人いますか？`
# MAGIC 5. `そのうち、預かり資産残高が0の顧客に絞ると何人？`
# MAGIC 6. `さらに、直近6か月（2026年2月18日以降）に交渉履歴がない顧客だけにすると？`
# MAGIC 7. `その顧客（＝提案対象顧客）を店舗別に集計して、多い順の棒グラフにして`
# MAGIC 8. `都道府県（茨城県・栃木県）別ではどうなる？`
# MAGIC 9. `提案対象顧客の一覧を、預金残高が多い順で見せて`
# MAGIC
# MAGIC > 💡 質問4〜6 で「預金が多い×預かり資産0×未接触」の3条件が揃い、**提案対象顧客**が定まります。
# MAGIC > Genie One は **顧客データ（`customers_silver`）と交渉履歴（`contacts_bronze`）を組み合わせて** 回答します。
# MAGIC > 質問7〜8 で **店舗別・地域別に可視化** でき、「どの店舗にアプローチ余地が多いか」が見えます。
# MAGIC >
# MAGIC > 🧭 もし未接触の判定がうまくいかない場合は、`最終接触日は交渉履歴（contacts）の contact_date の最大値です` と補足すると精度が上がります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## ステップ4: 「お客様の声」の感情を分析（AI関数の結果を活用）
# MAGIC
# MAGIC `02` で作った `customer_voice_silver`（感情分析済みの声）にも質問できます。
# MAGIC
# MAGIC 9. `お客様の声を、感情（positive/negative/neutral/mixed）別に件数で教えて`
# MAGIC 10. `チャネル別に、ネガティブな声の件数を多い順で`
# MAGIC 11. `ネガティブな声の本文をいくつか見せて`
# MAGIC
# MAGIC > 💡 「どのチャネルに不満が集まっているか」を、コードなしで把握できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ### ✅ 完了チェック
# MAGIC - [ ] Genie One を開いて、日本語で質問できた
# MAGIC - [ ] 集計結果をグラフ化できた
# MAGIC - [ ] フォローアップ質問で深掘りできた
# MAGIC - [ ] 「お客様の声」の感情分析結果を Genie One で確認できた
# MAGIC
# MAGIC ### 🚀 次のモジュール
# MAGIC **05_DA_AIBI_Dashboard** → 分析結果をダッシュボード・顧客リストに可視化（Tableau との比較も）
