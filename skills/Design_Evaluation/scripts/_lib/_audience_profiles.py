"""
_audience_profiles.py — Audience-aware report configuration.

4 profiles cho 4 audiences khác nhau:
- Designer: chi tiết kỹ thuật, đầy đủ calculation logs, citation, η
- Engineer: tập trung tính toán, kiểm tra chéo, ít narrative
- Contractor: bản vẽ thi công, BOQ, sequence, NCR/Submittal
- Owner: executive summary, chi phí, tiến độ, call-to-action

Updated: 2026-08-31 — Phase A of Reporting Upgrade v4.0
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
from typing import Dict, List


# ════════════════════════════════════════════════════════════════════════════
# PROFILES
# ════════════════════════════════════════════════════════════════════════════

PROFILES = {
    'designer': {
        'name': 'Tư vấn Thiết kế (Designer)',
        'description': 'Chi tiết kỹ thuật đầy đủ, calculation logs, citation, η analysis',
        'sections': {
            'cover_page': True,
            'toc': True,
            'executive_dashboard': True,
            'project_info': True,
            'design_basis': True,
            'calculation_logs': True,        # Full
            'technical_analysis': True,
            'comparison_table': True,
            'charts': True,
            'citations_appendix': True,
            'approval_matrix': True,
            'disclaimer': True,
        },
        'detail_level': 'FULL',
        'citation_style': 'FULL_4_TUPLE',     # Mã - Năm - Điều - Trích yếu
        'eta_threshold_warning': 0.85,
        'eta_threshold_critical': 1.00,
        'include_images': True,
        'include_appendix': True,
        'language_tone': 'FORMAL_TECHNICAL',
        'charts': ['comparison', 'eta_heatmap', 'cost_breakdown'],
    },

    'engineer': {
        'name': 'Kỹ sư Tính toán (Calculation Engineer)',
        'description': 'Tập trung tính toán, verification, cross-check',
        'sections': {
            'cover_page': True,
            'toc': True,
            'executive_dashboard': False,   # Engineer không cần
            'project_info': True,
            'design_basis': True,
            'calculation_logs': True,         # Full + raw
            'technical_analysis': True,
            'comparison_table': False,
            'charts': True,
            'citations_appendix': True,
            'approval_matrix': False,
            'disclaimer': True,
        },
        'detail_level': 'TECHNICAL_DEEP',
        'citation_style': 'FULL_4_TUPLE',
        'eta_threshold_warning': 0.85,
        'eta_threshold_critical': 1.00,
        'include_images': False,             # Chỉ charts
        'include_appendix': True,
        'language_tone': 'TECHNICAL_PRECISE',
        'charts': ['eta_heatmap', 'comparison'],
    },

    'contractor': {
        'name': 'Nhà thầu Thi công (Contractor)',
        'description': 'Bản vẽ thi công, BOQ, sequence, NCR/RFI workflow',
        'sections': {
            'cover_page': True,
            'toc': True,
            'executive_dashboard': False,
            'project_info': True,
            'design_basis': False,            # Không cần
            'calculation_logs': False,         # Chỉ summary
            'technical_analysis': False,
            'comparison_table': False,
            'charts': True,
            'citations_appendix': False,
            'approval_matrix': True,
            'disclaimer': True,
        },
        'detail_level': 'PRACTICAL',
        'citation_style': 'BRIEF',
        'eta_threshold_warning': 1.00,        # Ngưỡng cao
        'eta_threshold_critical': 1.10,
        'include_images': True,
        'include_appendix': False,
        'language_tone': 'PRACTICAL_CLEAR',
        'charts': ['progress', 'cost_breakdown'],
    },

    'owner': {
        'name': 'Chủ đầu tư (Owner)',
        'description': 'Executive summary, chi phí, tiến độ, call-to-action',
        'sections': {
            'cover_page': True,
            'toc': False,
            'executive_dashboard': True,       # Critical
            'project_info': True,
            'design_basis': False,
            'calculation_logs': False,         # Chỉ high-level
            'technical_analysis': False,
            'comparison_table': True,           # So sánh PA
            'charts': True,                     # Visual
            'citations_appendix': False,
            'approval_matrix': True,
            'disclaimer': True,
        },
        'detail_level': 'EXECUTIVE_SUMMARY',
        'citation_style': 'HIDDEN',           # Không hiển thị citation
        'eta_threshold_warning': 0.95,
        'eta_threshold_critical': 1.10,
        'include_images': True,
        'include_appendix': False,
        'language_tone': 'BUSINESS_FRIENDLY',
        'charts': ['comparison', 'cost_breakdown', 'progress'],
    },

    'authority': {
        'name': 'Cơ quan Thẩm tra (Authority)',
        'description': 'Tuân thủ quy chuẩn, đầy đủ citation, audit trail',
        'sections': {
            'cover_page': True,
            'toc': True,
            'executive_dashboard': False,
            'project_info': True,
            'design_basis': True,
            'calculation_logs': True,           # Full + raw
            'technical_analysis': True,
            'comparison_table': True,
            'charts': True,
            'citations_appendix': True,
            'approval_matrix': True,
            'disclaimer': True,
        },
        'detail_level': 'AUDIT_COMPLIANCE',
        'citation_style': 'FULL_4_TUPLE',
        'eta_threshold_warning': 0.85,
        'eta_threshold_critical': 1.00,
        'include_images': True,
        'include_appendix': True,             # Required
        'language_tone': 'OFFICIAL_FORMAL',
        'charts': ['comparison', 'eta_heatmap'],
    },
}


# ════════════════════════════════════════════════════════════════════════════
# PROFILE LOOKUP
# ════════════════════════════════════════════════════════════════════════════

def get_profile(audience: str = 'designer') -> dict:
    """Get profile config by audience name."""
    return PROFILES.get(audience.lower(), PROFILES['designer'])


def list_audiences() -> List[str]:
    """List available audience profiles."""
    return list(PROFILES.keys())


def should_include_section(audience: str, section: str) -> bool:
    """Check if section should be included for given audience."""
    profile = get_profile(audience)
    return profile.get('sections', {}).get(section, False)


# ════════════════════════════════════════════════════════════════════════════
# DEFAULT CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

DEFAULT_AUDIENCE = 'designer'
DEFAULT_OUTPUT_FORMAT = 'docx'
DEFAULT_OUTPUT_DIR = ''