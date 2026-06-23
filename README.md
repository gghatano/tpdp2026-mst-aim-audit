# tpdp2026-mst-aim-audit

**MST / AIM の差分プライバシー保証を Gaussian DP (GDP) で tight に監査する**——
論文 *Tight Auditing of Differential Privacy in MST and AIM* (Ganev, Annamalai, Kulynych, [arXiv:2604.18352](https://arxiv.org/abs/2604.18352), TPDP 2026) の調査・再現実験リポジトリ。

> ⚠️ **ステータス: 進行中（自律実験セッション）**。測定済みの数値のみ記載し、未実施は「未測定」と明記する。
> 本リポジトリは上流監査コード [`sassoftware/dpmm` (`audit-dpmm` ブランチ)](https://github.com/sassoftware/dpmm/tree/audit-dpmm) を移植・縮小再現したもの。数値完全一致でなく**傾向の再現**を目標とする（実装差・縮小試行のため）。
> 📊 **暫定結果（N_ALL=1,125/side, Default 構成）**: μ_emp=0.393 vs 理論 implied μ=0.455（gap≈0.06、原論文 μ_emp≈0.43）。μ_emp は試行数とともに implied μ へ接近（N=250→0.19, N=1,000→0.44）。不安定な閾値選択で μ_emp が 0 に潰れる現象も再現（RQ3）。詳細は [content/REPORT.md](content/REPORT.md) §3。

## 何をするか

DP 合成データ生成器（MST/AIM）が主張通りのプライバシー（μ-GDP / (ε,δ)-DP）を満たすかを、
メンバーシップ推論攻撃の **FPR–FNR トレードオフ**から経験的に監査する。
論文の主結果「`(ε,δ)=(1,10⁻²)` で経験的 μ_emp≈0.43 vs 理論 μ=0.45（小さな theory-practice gap）」を縮小規模で追試する。

## 構成

```
.
├── content/REPORT.md      … 本体レポート（モードB: 論文型）
├── methods/               … 技術解説ページ（GDP / MIA監査 / MST）
├── docs/                  … 文献(PDF/抽出テキスト)・調査メモ・実験計画
│   ├── research/issue-18-survey.md
│   └── plans/issue-18-plan.md
├── scripts/               … 再現スクリプト（setup→attack→audit→plot→build）
│   └── auditlib/          … 上流監査コードの移植（MST / adp2gdp / audit_utils）
├── figures/ outputs/      … 図 / メトリクス（metrics.json）
├── htmls/                 … 自己完結 HTML（GitHub Pages 公開元）
└── requirements.txt       … 依存のバージョン固定
```

## 再現手順（clone → setup → run）

```bash
# 1. 環境構築（uv, Python 3.11）
bash scripts/setup_env.sh

# 2. 一括実行（スモーク → 攻撃特徴生成 → 監査 → 図表）
bash scripts/run_all.sh

# 3. HTML ビルド（htmls/ に生成）
uv run python scripts/build_html.py
```

詳細・動作環境・落とし穴は [content/REPORT.md](content/REPORT.md) の付録および本 README の更新を参照。

## ライセンス / 出典

- 上流コード: [sassoftware/dpmm](https://github.com/sassoftware/dpmm) (Apache-2.0)。
- 論文: arXiv:2604.18352 (TPDP 2026)。
