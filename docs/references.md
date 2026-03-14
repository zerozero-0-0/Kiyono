# References Log

このファイルは、実装時に参照した外部情報の記録と、採用/不採用の判断理由を残すためのログです。  
面接で「どう情報を取捨選択したか」を説明できるよう、必ず更新してください。

---

## 記録ルール

- 参考にしたURLを必ず記録する
- 何を学んだかを1〜3行で要約する
- **採用した場合**は「どこに反映したか」を記録する
- **不採用の場合**は「なぜ使わなかったか」を記録する
- 文章の転載はしない（構造・観点のみ抽象化して利用）

---

## Entry Template

## [YYYY-MM-DD] タイトル
- URL: 
- 種別: 公式ドキュメント / Zenn / Qiita / Blog / その他
- 要点:
  - 
- 採用可否: 採用 / 不採用 / 保留
- 判断理由:
  - 
- 反映先（採用時）:
  - `path/to/file`（何を反映したか）
- メモ:
  - 

---

## Logs

## [2026-03-14] FastAPI - Request Body / Pydantic Models
- URL: https://fastapi.tiangolo.com/tutorial/body/
- 種別: 公式ドキュメント
- 要点:
  - PydanticモデルでAPIの入出力を厳密に定義できる
  - 型ヒントとバリデーションをAPI仕様として一貫管理できる
- 採用可否: 採用
- 判断理由:
  - 本課題は入力（keyword/brief）と出力（titles/article/validation_report）の形式保証が重要
- 反映先（採用時）:
  - `app/schemas.py` の設計方針
- メモ:
  - バリデーションエラー時のレスポンス形式も統一する

## [2026-03-14] FastAPI - Error Handling / HTTPException
- URL: https://fastapi.tiangolo.com/tutorial/handling-errors/
- 種別: 公式ドキュメント
- 要点:
  - 失敗時のエラーメッセージを構造化して返せる
  - 例外処理をAPI層で明示化できる
- 採用可否: 採用
- 判断理由:
  - LLM API失敗時に、ユーザー向け説明と内部原因を分けて扱う必要があるため
- 反映先（採用時）:
  - `app/main.py` の例外ハンドリング方針
- メモ:
  - APIキー不足、レート制限、タイムアウトを区別して返す

## [2026-03-14] Streamlit - Text Input / Selectbox / Button
- URL: https://docs.streamlit.io/
- 種別: 公式ドキュメント
- 要点:
  - 入力→生成→選択→表示のプロトタイプUIを短時間で構築できる
  - セッション状態でタイトル候補の選択フローを維持できる
- 採用可否: 採用
- 判断理由:
  - 面接デモ向けに、実装スピードと説明しやすさを優先
- 反映先（採用時）:
  - `frontend/app.py` のUI設計
- メモ:
  - 初期は最小機能に絞り、後でUX改善する

## [2026-03-14] Google AI for Developers (Gemini API)
- URL: https://ai.google.dev/
- 種別: 公式ドキュメント
- 要点:
  - 生成モデル呼び出し方法と認証方法を確認
  - システム指示とユーザー入力を分離して扱える
- 採用可否: 採用
- 判断理由:
  - 課題要件でGemini利用が自然。まずは単一プロバイダでMVPを構築する
- 反映先（採用時）:
  - `app/services/llm_client.py`
- メモ:
  - 将来的にOpenAI/Anthropicへ差し替え可能な抽象化を維持する

## [2026-03-14] Schema.org - Article
- URL: https://schema.org/Article
- 種別: 公式ドキュメント
- 要点:
  - 記事の構造化データ（JSON-LD）で使う基本プロパティを確認
  - `headline`, `description`, `author`, `datePublished` 等が中心
- 採用可否: 採用（任意機能）
- 判断理由:
  - 課題成果物として構造化データ出力を示せると説明価値が高い
- 反映先（採用時）:
  - `app/services/jsonld_generator.py`（任意）
- メモ:
  - MVP段階では必須項目のみ実装する

## [2026-03-14] Zenn / Qiita のLLM関連記事（調査まとめ）
- URL: （調査した記事URLを個別に追記）
- 種別: Zenn / Qiita
- 要点:
  - 読まれやすい記事は「冒頭要約→定義→比較表→FAQ」の構成が多い
  - 具体例と比較軸を明示すると理解しやすい
- 採用可否: 採用（構成のみ）
- 判断理由:
  - LLMOの要件（高情報密度・構造化）と整合するため
- 反映先（採用時）:
  - `prompts/article_system.txt` の出力制約
  - `app/services/llmo_validator.py` の検査項目
- メモ:
  - 文章表現の転載は行わず、構造のみ取り入れる

---

## Backlog (今後調べる候補)

- OpenAI / Anthropic APIの抽象化パターン比較
- Markdownテーブル品質を安定させるプロンプト設計
- FAQ生成の重複抑制テクニック
- 生成品質の簡易自動評価指標（形式準拠率など）

---

## Change Log

- 2026-03-14: 初版作成（テンプレート + 主要参照先のたたき台）