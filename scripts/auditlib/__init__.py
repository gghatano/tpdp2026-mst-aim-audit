"""auditlib — 上流 sassoftware/dpmm (audit-dpmm ブランチ) の監査コードを移植したパッケージ。

出典: https://github.com/sassoftware/dpmm/tree/audit-dpmm/experimental/audit_dpmm
変更点: パッケージ化に伴う相対 import への修正のみ（ロジックは未改変）。
論文: Tight Auditing of Differential Privacy in MST and AIM (arXiv:2604.18352, TPDP 2026)。
"""

from .adp2gdp import mu_from_eps_delta, delta_from_eps_mu
from .mst import MST
from .audit_utils import run_audit, mu_lower_from_two_groups

__all__ = [
    "mu_from_eps_delta",
    "delta_from_eps_mu",
    "MST",
    "run_audit",
    "mu_lower_from_two_groups",
]
