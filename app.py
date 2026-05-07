import streamlit as st
import pandas as pd
import json
import os
import glob
import subprocess
import shutil
import plotly.express as px
from datetime import datetime
import re
import sys
import io

st.set_page_config(page_title="Course Evaluation Dashboard", layout="wide", page_icon="⚙️")

# --- UvA House Style ---
_UVA_RED   = "#bc0031"
_UVA_BLACK = "#1B1918"
_UVA_GREY1 = "#D7D6D4"
_UVA_GREY2 = "#F5F5F3"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap');

/* === Global font — target text, NOT icon elements === */
html, body, p, li, label, div, span, h1, h2, h3, h4, h5, h6,
input[type="text"], input[type="password"], textarea, select,
.stApp, .stMarkdown, [data-testid] {
    font-family: 'Source Sans 3', 'Source Sans Pro', Arial, sans-serif !important;
}
/* Preserve Material icon fonts */
[class*="material"], .material-icons,
.material-symbols-rounded, .material-symbols-outlined,
[data-testid="stSidebarCollapseButton"] * {
    font-family: inherit;
}

/* === Targeted border-radius removal (not wildcard) === */
[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div,
[data-baseweb="input"],
[data-baseweb="base-input"],
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
[data-baseweb="notification"],
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button,
input[type="text"],
input[type="password"],
input[type="email"],
input[type="search"],
textarea { border-radius: 0 !important; }
/* Keep radio circles and checkboxes intact */
input[type="radio"]    { border-radius: 50% !important; }
input[type="checkbox"] { border-radius: 2px !important; }

/* === Sidebar === */
section[data-testid="stSidebar"] {
    background-color: #1B1918 !important;
    border-right: 4px solid #bc0031 !important;
}
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span:not(.stSelectbox span),
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] .stMarkdown * {
    color: #ffffff !important;
}
/* Sidebar select box — dark input bg so text stays visible */
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #2c2827 !important;
    border-color: #A8A29F !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #ffffff !important;
    background-color: transparent !important;
}
/* Active radio = red highlight */
section[data-testid="stSidebar"] .stRadio label { padding: 3px 0; }
section[data-testid="stSidebar"] hr {
    border-color: #bc0031 !important;
    opacity: 0.6 !important;
}
/* Sidebar form submit */
section[data-testid="stSidebar"] .stFormSubmitButton > button {
    background-color: #bc0031 !important;
    color: white !important;
    border: none !important;
}
/* Sidebar file uploader browse button */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background-color: #2c2827 !important;
    border-color: #A8A29F !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button {
    background-color: #bc0031 !important;
    color: white !important;
    border: none !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] p {
    color: #D7D6D4 !important;
}

/* === Main headings === */
h1 {
    color: #bc0031 !important;
    border-bottom: 3px solid #bc0031 !important;
    padding-bottom: 8px !important;
    font-weight: 700 !important;
}
h2 { color: #1B1918 !important; font-weight: 600 !important; }
h3 { color: #1B1918 !important; font-weight: 600 !important; }

/* === Metric values === */
[data-testid="stMetricValue"] { color: #bc0031 !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #1B1918 !important; font-weight: 600 !important; }
[data-testid="stMetric"]      { border-left: 3px solid #bc0031 !important; padding-left: 10px !important; }

/* === Buttons === */
.stButton > button {
    border-radius: 0 !important;
    border: 2px solid #bc0031 !important;
    color: #bc0031 !important;
    font-weight: 600 !important;
    background-color: white !important;
}
.stButton > button:hover {
    background-color: #bc0031 !important;
    color: white !important;
}
.stDownloadButton > button,
.stFormSubmitButton > button {
    border-radius: 0 !important;
    background-color: #bc0031 !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}

/* === Tabs === */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid #bc0031 !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0 !important;
    font-weight: 600 !important;
    color: #1B1918 !important;
    background-color: transparent !important;
    border-bottom: 3px solid transparent !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    color: #bc0031 !important;
    background-color: transparent !important;
    border-bottom: 3px solid #bc0031 !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 16px !important;
}

/* === Expanders === */
details { border-left: 3px solid #bc0031 !important; border-radius: 0 !important; }
summary { font-weight: 600 !important; }

/* === Dividers === */
hr { border-color: #bc0031 !important; border-width: 1px 0 0 !important; opacity: 0.35 !important; }

/* === Alerts === */
.stAlert { border-radius: 0 !important; border-left-width: 4px !important; }

/* === DataFrames === */
.stDataFrame { border: 1px solid #D7D6D4 !important; }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSES_DIR = os.path.join(BASE_DIR, "Analyses")
os.makedirs(ANALYSES_DIR, exist_ok=True)

SKIP_SECTIONS = {'counts', 'tutorial group counts', 'representative quotes'}
THEMES_KEYS = {'summary', 'integrated summary'}

# --- Utilities ---

def get_past_analyses():
    analyses = []
    for d in os.listdir(ANALYSES_DIR):
        d_path = os.path.join(ANALYSES_DIR, d)
        if os.path.isdir(d_path):
            meta_path = os.path.join(d_path, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    meta = json.load(f)
                    analyses.append(meta)
    analyses.sort(key=lambda x: x['timestamp'], reverse=True)
    return analyses

def strip_ref_ids(text):
    text = re.sub(r'\[r\d+_(?:tip|top)_[a-z_]+_\d+\]', '', text)
    text = re.sub(r'\br\d+_(?:tip|top)_[a-z_]+_\d+', '', text)
    text = re.sub(r';\s*\)', ')', text)
    text = re.sub(r'\(\s*;', '(', text)
    text = re.sub(r',\s*\)', ')', text)
    text = re.sub(r'\(e\.g\.,?\s*\)', '', text)
    text = re.sub(r'\(\s*\)', '', text)
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r' \.', '.', text)
    return text.strip()

def parse_md_sections(md_text):
    sections = {}
    current = None
    buf = []
    for line in md_text.split('\n'):
        h_match = re.match(r'^#{2,3}\s+(.+)', line)
        if h_match:
            if current is not None and current.lower() not in SKIP_SECTIONS:
                sections[current] = strip_ref_ids('\n'.join(buf).strip())
            current = h_match.group(1).strip().rstrip('\U0001f517').strip()
            buf = []
        else:
            if current is not None:
                buf.append(line)
    if current is not None and current.lower() not in SKIP_SECTIONS:
        sections[current] = strip_ref_ids('\n'.join(buf).strip())
    return {k: v for k, v in sections.items() if not k.lower().startswith('aspect:')}

def load_aspect_data(selected_analysis):
    json_path = os.path.join(selected_analysis, "JSON Outputs")
    md_path = os.path.join(selected_analysis, "Markdown Summaries")
    aspect_data = {}
    for f in glob.glob(os.path.join(json_path, "*.json")):
        with open(f) as fh:
            data = json.load(fh)
            k = data['aspect']['aspect_key']
            aspect_data[k] = data
    md_sections = {}
    for f in glob.glob(os.path.join(md_path, "*.md")):
        k = os.path.basename(f).replace("_summary.md", "")
        with open(f, encoding='utf-8') as fh:
            md_sections[k] = parse_md_sections(fh.read())
    return aspect_data, md_sections

def build_pdf(selected_analysis, aspect_data, md_sections):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Image, Table, TableStyle, PageBreak)
        from reportlab.platypus.flowables import HRFlowable
    except ImportError as e:
        raise RuntimeError(f"PDF export requires reportlab: {e}")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.cm as mcm
        import numpy as np
    except ImportError as e:
        raise RuntimeError(f"PDF export requires matplotlib: {e}")

    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.edgecolor': '#D7D6D4',
        'axes.labelcolor': '#1B1918',
        'xtick.color': '#1B1918',
        'ytick.color': '#1B1918',
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
    })

    def _esc(t):
        # Transliterate common typographic unicode → Latin-1 (reportlab built-in fonts only support Latin-1)
        _TR = {
            '—': '--',  '–': '-',   '‒': '-',  '‑': '-',
            '“': '"',   '”': '"',   '‘': "'",  '’': "'",
            '…': '...', ' ': ' ',   '•': '-',  '‐': '-',
            '―': '--',  '­': '-',   '′': "'",  '″': '"',
        }
        for src, dst in _TR.items():
            t = t.replace(src, dst)
        # Drop any remaining non-Latin-1 chars
        t = ''.join(c if ord(c) < 256 else '-' for c in t)
        return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _md_inline(t):
        t = _esc(t)
        t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
        t = re.sub(r'\*(.+?)\*', r'<i>\1</i>', t)
        return t

    buf = io.BytesIO()
    page_w, _ = A4
    margin = 2.5 * cm
    content_w = page_w - 2 * margin

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=2 * cm, bottomMargin=2.5 * cm,
        title="Course Feedback Analysis",
    )

    UVA_RED   = colors.HexColor("#bc0031")
    UVA_BLACK = colors.HexColor("#1B1918")
    UVA_GREY1 = colors.HexColor("#D7D6D4")
    UVA_GREY2 = colors.HexColor("#F5F5F3")

    ss = getSampleStyleSheet()
    S = {
        'h1':          ParagraphStyle('h1',  parent=ss['Heading1'], fontName='Helvetica-Bold',
                                      fontSize=20, spaceBefore=22, spaceAfter=10, textColor=UVA_RED),
        'h2':          ParagraphStyle('h2',  parent=ss['Heading2'], fontName='Helvetica-Bold',
                                      fontSize=13, spaceBefore=14, spaceAfter=6,  textColor=UVA_BLACK),
        'h3':          ParagraphStyle('h3',  parent=ss['Heading3'], fontName='Helvetica-Bold',
                                      fontSize=11, spaceBefore=10, spaceAfter=4,  textColor=UVA_BLACK),
        'body':        ParagraphStyle('body', parent=ss['Normal'],  fontName='Times-Roman',
                                      fontSize=10, leading=15, spaceAfter=6,      textColor=UVA_BLACK),
        'bullet':      ParagraphStyle('bul', parent=ss['Normal'],   fontName='Times-Roman',
                                      fontSize=10, leading=14, leftIndent=14, spaceAfter=3, textColor=UVA_BLACK),
        'cover_inst':  ParagraphStyle('ci',  parent=ss['Normal'],   fontName='Helvetica',
                                      fontSize=9,  alignment=0, spaceAfter=4, textColor=UVA_BLACK,
                                      letterSpacing=2),
        'cover_title': ParagraphStyle('ct',  parent=ss['Title'],    fontName='Helvetica-Bold',
                                      fontSize=28, alignment=0, spaceAfter=10, textColor=UVA_BLACK),
        'cover_sub':   ParagraphStyle('cs',  parent=ss['Normal'],   fontName='Helvetica',
                                      fontSize=13, alignment=0, spaceAfter=6,  textColor=UVA_BLACK),
        'cover_date':  ParagraphStyle('cd',  parent=ss['Normal'],   fontName='Helvetica',
                                      fontSize=9,  alignment=0, textColor=UVA_GREY1),
    }

    def _render_md(text, story):
        for line in text.split('\n'):
            s = line.strip()
            if not s:
                story.append(Spacer(1, 0.1 * cm))
                continue
            if s.startswith('- ') or s.startswith('* '):
                story.append(Paragraph('• ' + _md_inline(s[2:]), S['bullet']))
            elif s.startswith('**') and s.endswith('**') and len(s) > 4:
                story.append(Paragraph(_md_inline(s), S['h3']))
            else:
                story.append(Paragraph(_md_inline(s), S['body']))

    def _mpl_img(fig, w_cm, h_cm):
        buf2 = io.BytesIO()
        fig.savefig(buf2, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        buf2.seek(0)
        return Image(buf2, width=w_cm * cm, height=h_cm * cm)

    def _group_table(d):
        all_g = sort_groups(set(
            list(d['tips_by_tutorial_group'].keys()) +
            list(d['tops_by_tutorial_group'].keys())
        ))
        rows = [["Tutorial Group", "Tips", "Tops", "Total"]]
        for g in all_g:
            t = d['tips_by_tutorial_group'].get(g, {}).get('comment_count', 0)
            o = d['tops_by_tutorial_group'].get(g, {}).get('comment_count', 0)
            rows.append([f"Group {g}", str(t), str(o), str(t + o)])
        tbl = Table(rows, colWidths=[5 * cm, 3 * cm, 3 * cm, 3 * cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1, 0),  UVA_RED),
            ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTNAME',       (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE',       (0, 0), (-1, -1), 9),
            ('ALIGN',          (1, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, UVA_GREY2]),
            ('GRID',           (0, 0), (-1, -1), 0.5, UVA_GREY1),
            ('TOPPADDING',     (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',  (0, 0), (-1, -1), 5),
        ]))
        return tbl

    story = []

    # === Cover page ===
    # Red top bar
    red_bar = Table([["  "]], colWidths=[content_w], rowHeights=[0.6 * cm])
    red_bar.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), UVA_RED),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(red_bar)
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("UNIVERSITEIT VAN AMSTERDAM", S['cover_inst']))
    story.append(Spacer(1, 1.2 * cm))
    story.append(HRFlowable(width=content_w, thickness=2, color=UVA_RED))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Course Feedback Analysis", S['cover_title']))
    story.append(Spacer(1, 0.3 * cm))
    meta_path = os.path.join(selected_analysis, "meta.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        story.append(Paragraph(_esc(meta.get('filename', '')), S['cover_sub']))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph(meta.get('date', '')[:10], S['cover_date']))
    story.append(PageBreak())

    # === Executive Summary ===
    exe_path = os.path.join(selected_analysis, "Executive_Course_Summary.md")
    if os.path.exists(exe_path):
        with open(exe_path, encoding='utf-8') as f:
            exe_md = f.read()
        exe_md = re.sub(r'\n\|[^\n]+', '', exe_md)
        story.append(Paragraph("Executive Summary", S['h1']))
        story.append(HRFlowable(width=content_w, thickness=2, color=UVA_RED))
        story.append(Spacer(1, 0.3 * cm))
        for line in exe_md.split('\n'):
            s = line.strip()
            if not s or s.startswith('|') or s.startswith('---') or s.startswith('==='):
                continue
            if s.startswith('## '):
                story.append(Paragraph(_md_inline(s[3:]), S['h2']))
            elif s.startswith('### '):
                story.append(Paragraph(_md_inline(s[4:]), S['h3']))
            elif s.startswith('**') and s.endswith('**') and len(s) > 4:
                story.append(Paragraph(_md_inline(s), S['h2']))
            else:
                story.append(Paragraph(_md_inline(s), S['body']))
    story.append(PageBreak())

    # === Overview Charts ===
    story.append(Paragraph("Overview", S['h1']))
    story.append(HRFlowable(width=content_w, thickness=2, color=UVA_RED))
    story.append(Spacer(1, 0.4 * cm))

    aspect_rows, ga_rows = [], []
    for k, d in aspect_data.items():
        display = d['aspect']['display_name']
        tips_c = d['counts']['tip_comment_count']
        tops_c = d['counts']['top_comment_count']
        aspect_rows.append({"Aspect": display, "Type": "Tips", "Count": tips_c})
        aspect_rows.append({"Aspect": display, "Type": "Tops", "Count": tops_c})
        for g in set(list(d['tips_by_tutorial_group'].keys()) + list(d['tops_by_tutorial_group'].keys())):
            t = d['tips_by_tutorial_group'].get(g, {}).get('comment_count', 0)
            o = d['tops_by_tutorial_group'].get(g, {}).get('comment_count', 0)
            ga_rows.append({"Group": f"Group {g}", "Aspect": display, "Tips": t, "Tops": o})

    df_asp = pd.DataFrame(aspect_rows)
    df_ga  = pd.DataFrame(ga_rows)

    # --- Volume grouped bar ---
    aspects = df_asp[df_asp['Type'] == 'Tips']['Aspect'].tolist()
    tips_vals = [df_asp[(df_asp['Aspect'] == a) & (df_asp['Type'] == 'Tips')]['Count'].sum() for a in aspects]
    tops_vals = [df_asp[(df_asp['Aspect'] == a) & (df_asp['Type'] == 'Tops')]['Count'].sum() for a in aspects]
    x_pos = np.arange(len(aspects))
    w = 0.35
    fig1, ax1 = plt.subplots(figsize=(16 / 2.54, 7 / 2.54))
    ax1.bar(x_pos - w / 2, tips_vals, w, label='Tips', color='#bc0031')
    ax1.bar(x_pos + w / 2, tops_vals, w, label='Tops', color='#66bb6a')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(aspects, rotation=30, ha='right', fontsize=7)
    ax1.set_ylabel("Comments", fontsize=8)
    ax1.legend(fontsize=8)
    ax1.tick_params(axis='y', labelsize=7)
    ax1.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    story.append(Paragraph("Tips and Tops by Aspect", S['h3']))
    story.append(_mpl_img(fig1, 16, 7))
    story.append(Spacer(1, 0.5 * cm))

    # --- Positivity ranking horizontal bar ---
    df_piv = df_asp.pivot_table(index="Aspect", columns="Type", values="Count", fill_value=0).reset_index()
    for col in ("Tips", "Tops"):
        if col not in df_piv.columns:
            df_piv[col] = 0
    df_piv["Total"] = df_piv["Tips"] + df_piv["Tops"]
    df_piv["Positivity"] = df_piv["Tops"] / df_piv["Total"]
    df_piv = df_piv.sort_values("Positivity")
    cmap_rdylgn = mcm.get_cmap('RdYlGn')
    bar_colors = [cmap_rdylgn(v) for v in df_piv["Positivity"]]
    fig2, ax2 = plt.subplots(figsize=(16 / 2.54, max(5, len(df_piv) * 0.55 + 1) / 2.54))
    ax2.barh(df_piv["Aspect"], df_piv["Positivity"], color=bar_colors)
    ax2.set_xlim(0, 1)
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
    ax2.tick_params(labelsize=7)
    ax2.spines[['top', 'right']].set_visible(False)
    plt.tight_layout()
    story.append(Paragraph("Positivity Ranking — % Tops", S['h3']))
    story.append(_mpl_img(fig2, 16, max(5, len(df_piv) * 0.55 + 1)))
    story.append(Spacer(1, 0.5 * cm))

    # --- Aspect × Group heatmap ---
    df_ga_pos = df_ga.copy()
    df_ga_pos["Total"] = df_ga_pos["Tips"] + df_ga_pos["Tops"]
    df_ga_pos["Positivity"] = df_ga_pos.apply(
        lambda r: r["Tops"] / r["Total"] if r["Total"] > 0 else np.nan, axis=1)
    heat_df = df_ga_pos.pivot_table(index="Aspect", columns="Group", values="Positivity")
    n_r, n_c = heat_df.shape
    heat_h_cm = max(5.0, n_r * 1.1 + 2)
    fig3, ax3 = plt.subplots(figsize=(16 / 2.54, heat_h_cm / 2.54))
    data_np = heat_df.values.astype(float)
    im = ax3.imshow(data_np, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
    ax3.set_xticks(range(n_c))
    ax3.set_xticklabels(heat_df.columns, rotation=30, ha='right', fontsize=7)
    ax3.set_yticks(range(n_r))
    ax3.set_yticklabels(heat_df.index, fontsize=7)
    for i in range(n_r):
        for j in range(n_c):
            v = data_np[i, j]
            if not np.isnan(v):
                txt_col = 'white' if v < 0.35 or v > 0.75 else 'black'
                ax3.text(j, i, f'{v:.0%}', ha='center', va='center', fontsize=7, color=txt_col)
    plt.tight_layout()
    story.append(Paragraph("Positivity by Aspect and Tutorial Group", S['h3']))
    story.append(_mpl_img(fig3, 16, heat_h_cm))

    # === Per-aspect sections ===
    for k in sorted(aspect_data.keys()):
        d = aspect_data[k]
        display = d['aspect']['display_name']
        secs = {sk.lower(): sv for sk, sv in md_sections.get(k, {}).items()}

        story.append(PageBreak())
        story.append(Paragraph(_esc(display), S['h1']))
        story.append(HRFlowable(width=content_w, thickness=2, color=UVA_RED))
        story.append(Spacer(1, 0.3 * cm))

        themes = next((secs[sk] for sk in THEMES_KEYS if sk in secs and secs[sk]), None)
        if themes:
            story.append(Paragraph("Summary", S['h2']))
            _render_md(themes, story)

        gd = secs.get('tutorial group differences', '')
        if gd:
            story.append(Paragraph("Tutorial Group Differences", S['h2']))
            _render_md(gd, story)

        ten = secs.get('key tensions / mixed signals', '')
        if ten:
            story.append(Paragraph("Key Tensions", S['h2']))
            _render_md(ten, story)

        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("Comment Counts by Tutorial Group", S['h2']))
        story.append(Spacer(1, 0.15 * cm))
        story.append(_group_table(d))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def sort_groups(groups):
    def key(g):
        try:
            return (0, int(g))
        except ValueError:
            return (1, g)
    return sorted(groups, key=key)

def run_pipeline(api_key, csv_file_object):
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(ANALYSES_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)

    input_csv_path = os.path.join(run_dir, csv_file_object.name)
    with open(input_csv_path, "wb") as f:
        f.write(csv_file_object.getbuffer())

    json_out_dir = os.path.join(run_dir, "JSON Outputs")
    md_out_dir = os.path.join(run_dir, "Markdown Summaries")
    os.makedirs(json_out_dir, exist_ok=True)
    os.makedirs(md_out_dir, exist_ok=True)

    env = os.environ.copy()
    env["INPUT_CSV"] = input_csv_path
    env["OUTPUT_DIR"] = json_out_dir
    env["API_KEY"] = api_key

    msg = st.empty()

    # Step 1: CSV → JSON
    msg.info("Step 1/3: Converting CSV to Aspect JSONs...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "csv_to_json_converter.py")], env=env, check=True)

    temp_json = os.path.join(BASE_DIR, "JSON Outputs")
    temp_md = os.path.join(BASE_DIR, "Markdown Summaries")
    os.makedirs(temp_json, exist_ok=True)
    os.makedirs(temp_md, exist_ok=True)

    for f in glob.glob(os.path.join(temp_json, "*")): os.remove(f)
    for f in glob.glob(os.path.join(temp_md, "*")): os.remove(f)
    for f in glob.glob(os.path.join(json_out_dir, "*")): shutil.copy(f, temp_json)

    # Step 2: Aspect summaries
    msg.info("Step 2/3: Generating aspect summaries (this may take a few minutes)...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "generate_summaries.py")], env=env, check=True)
    for f in glob.glob(os.path.join(temp_md, "*")): shutil.copy(f, md_out_dir)

    # Step 3: Executive summary
    msg.info("Step 3/3: Generating executive summary...")
    subprocess.run([sys.executable, os.path.join(BASE_DIR, "generate_executive_summary.py")], env=env, check=True)
    exe_sum = os.path.join(BASE_DIR, "Executive_Course_Summary.md")
    if os.path.exists(exe_sum):
        shutil.copy(exe_sum, os.path.join(run_dir, "Executive_Course_Summary.md"))

    with open(os.path.join(run_dir, "meta.json"), "w") as f:
        json.dump({
            "id": run_id,
            "filename": csv_file_object.name,
            "timestamp": run_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, f)

    msg.success("✅ Analysis complete!")

# --- Shared UI Setup ---

_logo_path = os.path.join(BASE_DIR, "uva_logo.svg")
if os.path.exists(_logo_path):
    import base64
    _svg_b64 = base64.b64encode(open(_logo_path, "rb").read()).decode()
    st.sidebar.markdown(
        '<img src="data:image/svg+xml;base64,' + _svg_b64 + '" style="width:64px;height:64px;margin-bottom:4px;">',
        unsafe_allow_html=True
    )
st.sidebar.markdown(
    '<div style="font-size:1rem;font-weight:700;color:#fff;margin-bottom:4px;">Course Evaluator</div>',
    unsafe_allow_html=True
)
page = st.sidebar.radio("Navigate", ["Login", "Filter", "Student View", "Dashboard"], label_visibility="collapsed")

analyses = get_past_analyses()
selected_analysis = None

if analyses:
    st.sidebar.divider()
    st.sidebar.markdown("**Active Analysis**")
    res_list = [f"{a['id']} — {a['filename']}" for a in analyses]
    sel = st.sidebar.selectbox("Select", res_list, label_visibility="collapsed")
    sel_id = sel.split(" — ")[0]
    selected_analysis = os.path.join(ANALYSES_DIR, sel_id)


# -----------------
# 1) LOGIN PAGE
# -----------------
if page == "Login":
    st.title("Run & Manage Analyses")
    st.caption("Upload a Qualtrics CSV export and provide your API key to generate a new analysis. Previous runs are listed below.")

    with st.sidebar.form("run_form"):
        st.subheader("New Analysis")
        api_key_input = st.text_input("AI Proxy API Key", type="password")
        file_input = st.file_uploader("Qualtrics CSV", type=["csv"])
        submitted = st.form_submit_button("Run Pipeline", use_container_width=True)

        if submitted:
            if api_key_input and file_input:
                run_pipeline(api_key_input, file_input)
                st.rerun()
            else:
                st.error("Provide both an API key and a CSV.")

    st.subheader("Past Analyses")
    if analyses:
        df = pd.DataFrame(analyses)
        st.dataframe(df[['id', 'date', 'filename']], use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Manage Analysis")

        manage_options = [f"{a['id']} — {a['filename']}" for a in analyses]
        manage_sel = st.selectbox("Select analysis", manage_options, key="manage_sel")
        manage_id = manage_sel.split(" — ")[0]
        manage_dir = os.path.join(ANALYSES_DIR, manage_id)
        manage_meta = next((a for a in analyses if a['id'] == manage_id), None)

        if manage_meta:
            col_r, col_d = st.columns([3, 1])

            with col_r:
                new_name = st.text_input("Rename", value=manage_meta.get('filename', ''), key="rename_input",
                                         help="Change the display name shown in the analysis selector.")
                if st.button("Save Name", key="save_rename"):
                    manage_meta['filename'] = new_name.strip()
                    with open(os.path.join(manage_dir, "meta.json"), "w") as f:
                        json.dump(manage_meta, f, indent=2)
                    st.success("Name saved.")
                    st.rerun()

            with col_d:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("Delete", key="delete_btn", type="secondary", use_container_width=True):
                    st.session_state['pending_delete'] = manage_id

        # Delete confirmation dialog
        if st.session_state.get('pending_delete') == manage_id:
            st.warning(f"Permanently delete **{manage_id}**? This cannot be undone.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, delete", type="primary", use_container_width=True):
                    shutil.rmtree(manage_dir, ignore_errors=True)
                    st.session_state.pop('pending_delete', None)
                    st.success("Deleted.")
                    st.rerun()
            with c2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.pop('pending_delete', None)
                    st.rerun()
    else:
        st.info("No past analyses found. Run a new one from the sidebar.")

# -----------------
# 2) FILTER PAGE
# -----------------
elif page == "Filter":
    st.title("Feedback Explorer")
    st.caption("Filter by aspect, tutorial group, and type to drill into summaries and individual quotes.")
    if not selected_analysis:
        st.warning("No analyses found. Please run an analysis on the Login page.")
        st.stop()

    aspect_data, md_sections = load_aspect_data(selected_analysis)

    all_groups = set()
    for d in aspect_data.values():
        all_groups.update(d['tips_by_tutorial_group'].keys())
        all_groups.update(d['tops_by_tutorial_group'].keys())

    # Sidebar filters
    st.sidebar.subheader("Filters")
    aspect_options = ["All"] + sorted(aspect_data.keys())
    sel_aspect = st.sidebar.selectbox("Aspect", aspect_options)
    sel_type = st.sidebar.selectbox("Type", ["All", "Tips", "Tops"])
    group_options = ["All"] + sort_groups(all_groups)
    sel_group = st.sidebar.selectbox("Tutorial Group", group_options)

    active_aspects = [sel_aspect] if sel_aspect != "All" else sorted(aspect_data.keys())
    active_groups = [sel_group] if sel_group != "All" else list(all_groups)

    # --- Zone 1: Metrics ---
    total_tips, total_tops = 0, 0
    for k in active_aspects:
        d = aspect_data[k]
        for g in active_groups:
            total_tips += d['tips_by_tutorial_group'].get(g, {}).get('comment_count', 0)
            total_tops += d['tops_by_tutorial_group'].get(g, {}).get('comment_count', 0)

    total = total_tips + total_tops
    ratio = total_tops / total if total > 0 else 0
    balance = "More Tips" if total_tips > total_tops else "More Tops" if total_tops > total_tips else "Balanced"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tips", total_tips, help="Improvement suggestions")
    c2.metric("Tops", total_tops, help="Positive feedback")
    c3.metric("Positivity ratio", f"{ratio:.0%}", help="Share of comments that are Tops")
    c4.metric("Balance", balance)

    st.divider()

    # --- Zone 2: Summary panels with tabs ---
    st.subheader("Aspect Summaries")
    st.caption("Themes tab leads. Use Group Differences for cross-group comparison, Tensions for split signals.")

    TAB_MAP = {
        "Themes": None,
        "Group Differences": "tutorial group differences",
        "Tensions": "key tensions / mixed signals",
    }

    for asp_key in active_aspects:
        display_name = aspect_data[asp_key]['aspect']['display_name']
        with st.expander(display_name, expanded=True):
            sections = md_sections.get(asp_key, {})
            section_lookup = {k.lower(): v for k, v in sections.items()}

            available_tabs = []
            for label, lookup_key in TAB_MAP.items():
                if label == "Themes":
                    content = next((section_lookup[k] for k in THEMES_KEYS if k in section_lookup and section_lookup[k]), None)
                else:
                    content = section_lookup.get(lookup_key, "")
                if content:
                    available_tabs.append((label, content))

            if available_tabs:
                tabs = st.tabs([t[0] for t in available_tabs])
                for tab, (_, content) in zip(tabs, available_tabs):
                    with tab:
                        st.markdown(content)
            else:
                st.info("No summary available for this aspect.")

    st.divider()

    # --- Zone 3: Quote Explorer ---
    st.subheader("Quote Explorer")
    st.caption("Individual student quotes, filtered live.")

    quotes = []
    for k in active_aspects:
        d = aspect_data[k]
        display = d['aspect']['display_name']
        if sel_type in ["All", "Tips"]:
            for g, g_data in d['tips_by_tutorial_group'].items():
                if sel_group != "All" and g != sel_group:
                    continue
                for c in g_data['comments']:
                    quotes.append({"aspect": display, "type": "Tip", "group": g, "text": c['text']})
        if sel_type in ["All", "Tops"]:
            for g, g_data in d['tops_by_tutorial_group'].items():
                if sel_group != "All" and g != sel_group:
                    continue
                for c in g_data['comments']:
                    quotes.append({"aspect": display, "type": "Top", "group": g, "text": c['text']})

    if not quotes:
        st.info("No quotes match current filters.")
    else:
        st.caption(f"{len(quotes)} quotes — use sidebar filters to narrow down.")
        for i in range(0, len(quotes), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j >= len(quotes):
                    break
                q = quotes[i + j]
                is_tip = q['type'] == "Tip"
                border_color = "#bc0031" if is_tip else "#66bb6a"
                badge_bg     = "#bc0031" if is_tip else "#2e7d32"

                with col:
                    qtype = q["type"]
                    qgroup = q["group"]
                    qaspect = q["aspect"]
                    qtext = q["text"]
                    card = (
                        '<div style="border-left:3px solid ' + border_color + ';border-top:1px solid #D7D6D4;border-right:1px solid #D7D6D4;border-bottom:1px solid #D7D6D4;padding:12px 14px;margin-bottom:8px;background:#ffffff;min-height:110px;display:flex;flex-direction:column;">'
                        + '<div style="margin-bottom:8px;line-height:1.8;">'
                        + '<span style="background:' + badge_bg + ';color:#fff;padding:2px 8px;font-size:0.7rem;font-weight:700;letter-spacing:.06em;">' + qtype.upper() + '</span>'
                        + '<span style="background:#F5F5F3;color:#1B1918;padding:2px 8px;font-size:0.7rem;font-weight:600;margin-left:5px;">Group ' + qgroup + '</span>'
                        + '<span style="color:#A8A29F;font-size:0.7rem;margin-left:8px;">' + qaspect + '</span>'
                        + '</div>'
                        + '<div style="font-size:0.9rem;color:#1B1918;line-height:1.55;flex-grow:1;">&ldquo;' + qtext + '&rdquo;</div>'
                        + '</div>'
                    )
                    st.markdown(card, unsafe_allow_html=True)

# -----------------
# 3) STUDENT VIEW
# -----------------
elif page == "Student View":
    st.title("Student Profiles")
    st.caption("Overview of feedback volume per student. Select a student to see their full comment set.")
    if not selected_analysis:
        st.warning("No analyses found. Please run an analysis on the Login page.")
        st.stop()

    aspect_data, _ = load_aspect_data(selected_analysis)

    comments = []
    for k, d in aspect_data.items():
        display = d['aspect']['display_name']
        for g, g_data in d['tips_by_tutorial_group'].items():
            for c in g_data['comments']:
                student_id = c['id'].split('_')[0]
                comments.append({"Student": student_id, "Aspect": display, "Type": "Tip", "Group": g, "Text": c['text']})
        for g, g_data in d['tops_by_tutorial_group'].items():
            for c in g_data['comments']:
                student_id = c['id'].split('_')[0]
                comments.append({"Student": student_id, "Aspect": display, "Type": "Top", "Group": g, "Text": c['text']})

    df = pd.DataFrame(comments)
    if df.empty:
        st.info("No feedback entries available.")
        st.stop()

    st.sidebar.subheader("Filters")
    group_options = ["All"] + sort_groups(df['Group'].unique())
    sel_group = st.sidebar.selectbox("Tutorial Group", group_options)
    f_df = df if sel_group == "All" else df[df['Group'] == sel_group]

    st.subheader("Student Overview")
    st.caption("Sorted by tip count. Click a row to select, or use the dropdown below.")
    summary = (
        f_df.groupby('Student')
        .agg(
            Group=('Group', 'first'),
            Tips=('Type', lambda x: (x == 'Tip').sum()),
            Tops=('Type', lambda x: (x == 'Top').sum()),
            Aspects=('Aspect', 'nunique'),
        )
        .reset_index()
    )
    summary['Total'] = summary['Tips'] + summary['Tops']
    summary = summary.sort_values('Tips', ascending=False)
    st.dataframe(summary[['Student', 'Group', 'Tips', 'Tops', 'Total', 'Aspects']], use_container_width=True)

    st.divider()
    st.subheader("Individual Student Detail")
    students = sort_groups(f_df['Student'].unique())
    sel_student = st.selectbox("Select Student ID", students)

    if sel_student:
        stud_df = f_df[f_df['Student'] == sel_student]
        tips_n = (stud_df['Type'] == 'Tip').sum()
        tops_n = (stud_df['Type'] == 'Top').sum()

        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Tips", tips_n)
        sc2.metric("Tops", tops_n)
        sc3.metric("Aspects mentioned", stud_df['Aspect'].nunique())

        tip_df = stud_df[stud_df['Type'] == 'Tip']
        top_df = stud_df[stud_df['Type'] == 'Top']

        if not tip_df.empty:
            st.markdown("**Tips — improvement suggestions**")
            for _, row in tip_df.iterrows():
                st.markdown(
                    f'<div style="border-left:3px solid #bc0031;padding:8px 14px;margin:4px 0;background:#fff9f9;border-radius:0;">'
                    f'<span style="font-size:0.78rem;color:#aaa;">{row["Aspect"]} · Group {row["Group"]}</span>'
                    f'<div style="margin:4px 0 0 0;color:#212121;font-size:0.9rem;">"{row["Text"]}"</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        if not top_df.empty:
            st.markdown("**Tops — positive feedback**")
            for _, row in top_df.iterrows():
                st.markdown(
                    f'<div style="border-left:3px solid #66bb6a;padding:8px 14px;margin:4px 0;background:#f9fff9;border-radius:0;">'
                    f'<span style="font-size:0.78rem;color:#aaa;">{row["Aspect"]} · Group {row["Group"]}</span>'
                    f'<div style="margin:4px 0 0 0;color:#212121;font-size:0.9rem;">"{row["Text"]}"</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# -----------------
# 4) DASHBOARD
# -----------------
elif page == "Dashboard":
    st.title("Dashboard")
    st.caption("Executive synthesis at the top. Charts break down Tips vs Tops by aspect and group and positivity ratios.")
    if not selected_analysis:
        st.warning("No analyses found. Please run an analysis on the Login page.")
        st.stop()

    aspect_data, md_sections_dash = load_aspect_data(selected_analysis)

    # --- Executive Summary (top) ---
    st.subheader("Executive Summary")
    exe_path = os.path.join(selected_analysis, "Executive_Course_Summary.md")
    if os.path.exists(exe_path):
        with open(exe_path, encoding="utf-8") as f:
            exe_text = f.read()
        exe_text = re.sub(r'(\n\|[^\n]+)+', '', exe_text)
        st.markdown(exe_text)
    else:
        st.info("No executive summary generated for this analysis.")

    st.divider()

    # Build chart records
    aspect_rows = []
    ga_rows = []

    for k, d in aspect_data.items():
        display = d['aspect']['display_name']
        tips_c = d['counts']['tip_comment_count']
        tops_c = d['counts']['top_comment_count']
        aspect_rows.append({"Aspect": display, "Type": "Tips", "Count": tips_c})
        aspect_rows.append({"Aspect": display, "Type": "Tops", "Count": tops_c})

        all_g = set(list(d['tips_by_tutorial_group'].keys()) + list(d['tops_by_tutorial_group'].keys()))
        for g in all_g:
            t = d['tips_by_tutorial_group'].get(g, {}).get('comment_count', 0)
            o = d['tops_by_tutorial_group'].get(g, {}).get('comment_count', 0)
            ga_rows.append({"Group": f"Group {g}", "Aspect": display, "Tips": t, "Tops": o})

    df_aspect = pd.DataFrame(aspect_rows)
    df_ga = pd.DataFrame(ga_rows)

    df_group = df_ga.groupby("Group")[["Tips", "Tops"]].sum().reset_index()
    df_group["Total"] = df_group["Tips"] + df_group["Tops"]
    df_group["Positivity"] = df_group["Tops"] / df_group["Total"]
    df_group = df_group.sort_values("Group")

    df_asp_piv = df_aspect.pivot_table(index="Aspect", columns="Type", values="Count", fill_value=0).reset_index()
    df_asp_piv["Total"] = df_asp_piv["Tips"] + df_asp_piv["Tops"]
    df_asp_piv["Positivity"] = df_asp_piv["Tops"] / df_asp_piv["Total"]
    df_asp_piv = df_asp_piv.sort_values("Positivity")

    # --- Volume bars ---
    st.subheader("Volume")
    st.caption("Raw Tips and Tops counts, split by aspect and tutorial group.")
    col1, col2 = st.columns(2)

    with col1:
        fig_asp = px.bar(
            df_aspect, x="Aspect", y="Count", color="Type",
            barmode="group",
            color_discrete_map={"Tips": "#bc0031", "Tops": "#66bb6a"},
            title="By Aspect",
            labels={"Count": "Comments", "Aspect": ""},
        )
        fig_asp.update_layout(xaxis_tickangle=-30, legend_title="", margin=dict(t=40, b=100))
        st.plotly_chart(fig_asp, use_container_width=True)

    with col2:
        df_grp_long = df_group.melt(id_vars="Group", value_vars=["Tips", "Tops"], var_name="Type", value_name="Count")
        fig_grp = px.bar(
            df_grp_long, x="Group", y="Count", color="Type",
            barmode="group",
            color_discrete_map={"Tips": "#bc0031", "Tops": "#66bb6a"},
            title="By Tutorial Group",
            labels={"Count": "Comments", "Group": ""},
        )
        fig_grp.update_layout(legend_title="", margin=dict(t=40))
        st.plotly_chart(fig_grp, use_container_width=True)

    st.divider()

    # --- Positivity ratio ---
    st.subheader("Positivity")
    st.caption("Proportion of Tops relative to total comments. Aspect ranking on left; per-group breakdown on right.")
    col3, col4 = st.columns(2)

    with col3:
        fig_ratio = px.bar(
            df_asp_piv, x="Positivity", y="Aspect",
            orientation="h",
            color="Positivity",
            color_continuous_scale="RdYlGn",
            range_color=[0, 1],
            title="Aspect Ranking — % Tops",
            labels={"Positivity": "% Tops", "Aspect": ""},
        )
        fig_ratio.update_xaxes(tickformat=".0%")
        fig_ratio.update_layout(coloraxis_showscale=False, margin=dict(t=40))
        st.plotly_chart(fig_ratio, use_container_width=True)

    with col4:
        df_ga_pos = df_ga.copy()
        df_ga_pos["Total"] = df_ga_pos["Tips"] + df_ga_pos["Tops"]
        df_ga_pos["Positivity"] = df_ga_pos.apply(
            lambda r: r["Tops"] / r["Total"] if r["Total"] > 0 else None, axis=1
        )
        heat_df = df_ga_pos.pivot_table(index="Aspect", columns="Group", values="Positivity")

        n_rows = len(heat_df)
        fig_heat = px.imshow(
            heat_df,
            color_continuous_scale="RdYlGn",
            zmin=0, zmax=1,
            text_auto=".0%",
            title="Positivity % — Aspect × Group",
        )
        fig_heat.update_layout(
            height=max(320, n_rows * 55 + 80),
            margin=dict(t=50, b=20, l=10, r=10),
            coloraxis_showscale=False,
            xaxis=dict(side="bottom"),
        )
        fig_heat.update_xaxes(tickangle=-30)
        st.plotly_chart(fig_heat, use_container_width=True)

    # --- PDF Export ---
    st.divider()
    st.subheader("Export")
    if st.button("Generate PDF Report", use_container_width=True):
        with st.spinner("Building PDF — rendering charts, this may take a moment..."):
            try:
                pdf_bytes = build_pdf(selected_analysis, aspect_data, md_sections_dash)
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"course_feedback_{sel_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
