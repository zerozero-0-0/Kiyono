# decisions.md

## 目的
このドキュメントは、実装上の重要な意思決定を記録し、**面接で設計意図を説明できる状態**を作るためのログです。  
「何を作ったか」だけでなく、「なぜその選択をしたか」「他案と比較して何を捨てたか」を残します。

---

## 記録ルール
- 重要な設計・実装判断ごとに1エントリを追加する
- **Context / Options / Decision / Consequences** を必ず埋める
- 可能であれば、関連する実験結果（`docs/experiments.md`）を紐づける
- 不採用案も削除しない（判断の根拠として価値があるため）
- 1エントリは短く・具体的に（目安 5〜15行）

---

## エントリテンプレート

## [DEC-XXX] タイトル（短く）
- Date: YYYY-MM-DD
- Status: Proposed / Accepted / Rejected / Superseded
- Owners: @your-name
- Tags: architecture, backend, frontend, prompt, validation, testing, devex など

### Context
- 背景・課題:
- 制約（期間/工数/品質/依存）:
- 成功条件:

### Options Considered
1. Option A:
   - Pros:
   - Cons:
2. Option B:
   - Pros:
   - Cons:
3. Option C:（必要に応じて）
   - Pros:
   - Cons:

### Decision
- 採用案:
- 採用理由:
- 不採用案を見送った理由:

### Consequences
- 良い影響:
- 悪い影響 / リスク:
- 緩和策:

### Implementation Notes
- 影響範囲（ファイル/モジュール）:
- 互換性・移行対応:
- TODO:

### Evidence
- 関連実験: `docs/experiments.md` の該当ID
- 参考資料: `docs/references.md` の該当項目
- PR/Commit: （任意）

---

## 決定ログ

## [DEC-001] 生成フローを1段階ではなく2段階（タイトル→本文）に分離する
- Date: 2026-03-14
- Status: Accepted
- Owners: @project-owner
- Tags: architecture, prompt, backend

### Context
- 背景・課題:
  - 一括生成（タイトル+本文）では、タイトルの意図が曖昧になり、本文構造が崩れやすい。
- 制約（期間/工数/品質/依存）:
  - 2週間の課題期間内で、面接デモ可能な安定フローが必要。
- 成功条件:
  - タイトル候補の選択性と、本文の形式準拠率を両立すること。

### Options Considered
1. Option A: 1段階生成（タイトル+本文を単一プロンプトで生成）
   - Pros:
     - 実装が最短
     - API設計が単純
   - Cons:
     - 出力安定性が低く、意図調整しづらい
2. Option B: 2段階生成（タイトル生成→ユーザー選択→本文生成）
   - Pros:
     - ユーザー意図を明示化しやすい
     - 本文プロンプトを最適化しやすい
   - Cons:
     - UI/APIの遷移が1ステップ増える

### Decision
- 採用案:
  - Option B（2段階生成）
- 採用理由:
  - 生成品質の安定性と、面接での説明可能性が高い。
- 不採用案を見送った理由:
  - Option Aは最短だが、構造崩れ時の原因分析が難しい。

### Consequences
- 良い影響:
  - タイトル品質と本文品質を個別に改善可能
  - A/B実験設計がしやすい
- 悪い影響 / リスク:
  - フロント実装がやや複雑化
- 緩和策:
  - MVPでは最小UI（生成→選択→本文表示）に限定する

### Implementation Notes
- 影響範囲（ファイル/モジュール）:
  - `app/services/title_generator.py`
  - `app/services/article_generator.py`
  - `frontend/app.py`
- 互換性・移行対応:
  - 将来1段階モードをオプション化可能
- TODO:
  - 実験で1段階との比較結果を記録する

### Evidence
- 関連実験:
  - `docs/experiments.md` の Experiment 001
- 参考資料:
  - `docs/references.md` の FastAPI/Streamlit/Gemini 関連項目
- PR/Commit:
  - TBD

---

## [DEC-002] LLMO要件を「プロンプト依存」ではなくバリデータで機械検査する
- Date: 2026-03-14
- Status: Accepted
- Owners: @project-owner
- Tags: validation, backend, quality

### Context
- 背景・課題:
  - LLM出力は揺らぎがあり、プロンプトだけでは形式要件を保証できない。
- 制約（期間/工数/品質/依存）:
  - 完全な品質保証は難しいが、最低限の形式準拠は可視化したい。
- 成功条件:
  - Summary/定義/表/FAQ の有無を自動判定し、欠落時に明示できること。

### Options Considered
1. Option A: プロンプトのみで制約を強化
   - Pros:
     - 実装が簡単
   - Cons:
     - 失敗時の原因切り分けが難しい
2. Option B: 生成後にルールベース検査を実施
   - Pros:
     - 欠落要件を具体的に可視化できる
     - 比較実験に使える指標が得られる
   - Cons:
     - 実装が増える（validator設計が必要）

### Decision
- 採用案:
  - Option B（バリデータ導入）
- 採用理由:
  - 面接で「品質担保の仕組み」を説明しやすく、改善サイクルを回しやすい。
- 不採用案を見送った理由:
  - Option Aのみでは再現性・説明責任が弱い。

### Consequences
- 良い影響:
  - 形式準拠スコア化が可能
  - 欠落箇所に対する改善指示が出しやすい
- 悪い影響 / リスク:
  - ルールが厳しすぎると自然文を不当に低評価する
- 緩和策:
  - MVPは最低限の検査項目に限定し、運用で調整する

### Implementation Notes
- 影響範囲（ファイル/モジュール）:
  - `app/services/llmo_validator.py`
  - `app/schemas.py`
  - `app/services/article_generator.py`
- 互換性・移行対応:
  - 将来、重み付きスコアや再生成提案機能を追加可能
- TODO:
  - 検査結果をUIに分かりやすく表示する

### Evidence
- 関連実験:
  - `docs/experiments.md` の Experiment 002
- 参考資料:
  - `docs/references.md` の FastAPI/Pydantic 項目
- PR/Commit:
  - TBD

---

## [DEC-003] 初期UIはStreamlitを採用し、デモ速度を優先する
- Date: 2026-03-14
- Status: Accepted
- Owners: @project-owner
- Tags: frontend, delivery, interview

### Context
- 背景・課題:
  - 本課題はデプロイ不要で、面接デモに耐える実装速度が重要。
- 制約（期間/工数/品質/依存）:
  - 2週間で企画説明資料と動作デモを両立する必要がある。
- 成功条件:
  - 入力→生成→選択→表示フローを短期間で安定実装すること。

### Options Considered
1. Option A: Streamlit
   - Pros:
     - 実装が速い
     - デモ向けに十分
   - Cons:
     - 複雑UIや拡張性は限定的
2. Option B: React等のSPAを別途構築
   - Pros:
     - UI自由度が高い
   - Cons:
     - 工数が大きく、課題の主目的から逸れやすい

### Decision
- 採用案:
  - Option A（Streamlit）
- 採用理由:
  - 期間制約下で、価値の中心（生成ロジック・検証）に工数を集中できる。
- 不採用案を見送った理由:
  - Option Bは学習/実装コストが高く、面接準備時間を圧迫する。

### Consequences
- 良い影響:
  - 早期に縦切りデモを成立できる
- 悪い影響 / リスク:
  - UI表現に限界がある
- 緩和策:
  - MVP後に必要最小限のUI改善のみ実施する

### Implementation Notes
- 影響範囲（ファイル/モジュール）:
  - `frontend/app.py`
- 互換性・移行対応:
  - 将来的にフロントを分離してもAPIを再利用可能
- TODO:
  - セッション状態管理の設計を簡潔に保つ

### Evidence
- 関連実験:
  - N/A（選定判断）
- 参考資料:
  - `docs/references.md` の Streamlit 項目
- PR/Commit:
  - TBD

---

## Superseded / Rejected Decisions
（差し替え・取り下げした意思決定を記録）

## [DEC-XXX] タイトル
- Status: Superseded by DEC-YYY
- 理由:
  - 

---

## メモ（面接での話し方）
- 決定ログは「背景→選択肢→判断→結果」で説明する
- 失敗や不採用案も、学びとして語れるよう残しておく
- 実験結果と決定ログを1対1で結びつけると説得力が上がる