import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# 1. 页面配置
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="A股全维度估值决策系统",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# 2. 全局 CSS — 暗色金融终端主题
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── 基础层 ── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

:root {
    --bg-base:    #0d0f14;
    --bg-card:    #151820;
    --bg-card-2:  #1c2030;
    --border:     rgba(255,255,255,0.07);
    --border-hi:  rgba(255,255,255,0.14);
    --gold:       #e8c97a;
    --gold-dim:   #a08040;
    --green:      #3ddc97;
    --red:        #f06470;
    --blue:       #5b9cf6;
    --text-pri:   #e8eaf0;
    --text-sec:   #8a8fa8;
    --text-dim:   #4e5268;
    --font-body:  'Noto Sans SC', sans-serif;
    --font-mono:  'IBM Plex Mono', monospace;
}

/* 全局背景 & 字体 */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], [data-testid="stMainBlockContainer"] {
    background-color: var(--bg-base) !important;
    color: var(--text-pri) !important;
    font-family: var(--font-body) !important;
}

/* 侧边栏 */
[data-testid="stSidebar"] { background-color: var(--bg-card) !important; border-right: 1px solid var(--border) !important; }

/* 隐藏 Streamlit 顶部装饰 */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── 标题区 ── */
.app-header {
    display: flex; align-items: baseline; gap: 14px;
    padding: 28px 0 8px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
}
.app-title {
    font-size: 22px; font-weight: 700; letter-spacing: -0.3px;
    color: var(--text-pri);
}
.app-badge {
    font-family: var(--font-mono); font-size: 11px;
    color: var(--gold); background: rgba(232,201,122,0.1);
    border: 1px solid rgba(232,201,122,0.25);
    padding: 2px 8px; border-radius: 4px; letter-spacing: 0.5px;
}
.app-time {
    margin-left: auto; font-family: var(--font-mono);
    font-size: 12px; color: var(--text-dim);
}

/* ── 核心指标卡 ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }

.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px;
    position: relative; overflow: hidden;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: var(--border-hi); }
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0;
    width: 3px; height: 100%; border-radius: 10px 0 0 10px;
}
.kpi-card.gold::before  { background: var(--gold); }
.kpi-card.green::before { background: var(--green); }
.kpi-card.red::before   { background: var(--red); }
.kpi-card.blue::before  { background: var(--blue); }

.kpi-label { font-size: 11px; color: var(--text-sec); letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 8px; }
.kpi-value { font-family: var(--font-mono); font-size: 28px; font-weight: 500; line-height: 1; }
.kpi-value.gold  { color: var(--gold); }
.kpi-value.green { color: var(--green); }
.kpi-value.red   { color: var(--red); }
.kpi-value.blue  { color: var(--blue); }
.kpi-sub { font-size: 11px; color: var(--text-dim); margin-top: 6px; }

/* ── 信号横幅 ── */
.signal-banner {
    border-radius: 10px;
    padding: 16px 22px;
    margin-bottom: 24px;
    display: flex; align-items: flex-start; gap: 14px;
    border: 1px solid;
}
.signal-banner.opportunity {
    background: rgba(61,220,151,0.07);
    border-color: rgba(61,220,151,0.25);
}
.signal-banner.danger {
    background: rgba(240,100,112,0.07);
    border-color: rgba(240,100,112,0.25);
}
.signal-banner.neutral {
    background: rgba(91,156,246,0.07);
    border-color: rgba(91,156,246,0.25);
}
.signal-banner.extreme {
    background: rgba(232,201,122,0.07);
    border-color: rgba(232,201,122,0.4);
}
.signal-icon { font-size: 22px; flex-shrink: 0; line-height: 1.4; }
.signal-body { flex: 1; }
.signal-title { font-size: 13px; font-weight: 700; margin-bottom: 4px; }
.signal-title.green { color: var(--green); }
.signal-title.red   { color: var(--red); }
.signal-title.blue  { color: var(--blue); }
.signal-title.gold  { color: var(--gold); }
.signal-desc { font-size: 13px; color: var(--text-sec); line-height: 1.7; }
.signal-desc strong { color: var(--text-pri); font-weight: 500; }

/* ── 分析卡 ── */
.analysis-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 22px;
    height: 100%;
}
.analysis-card h4 {
    font-size: 12px; color: var(--text-sec);
    letter-spacing: 0.8px; text-transform: uppercase;
    margin: 0 0 16px; padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}
.analysis-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
.analysis-row-label { font-size: 13px; color: var(--text-sec); }
.analysis-row-value { font-family: var(--font-mono); font-size: 14px; color: var(--text-pri); }
.analysis-row-value.accent { color: var(--gold); }
.analysis-row-value.positive { color: var(--green); }
.analysis-row-value.negative { color: var(--red); }

.divider { border: none; border-top: 1px solid var(--border); margin: 14px 0; }

/* ── Tab 样式 ── */
[data-baseweb="tab-list"] { background: var(--bg-card) !important; border-radius: 8px !important; padding: 4px !important; gap: 4px !important; border: 1px solid var(--border) !important; }
[data-baseweb="tab"] { border-radius: 6px !important; color: var(--text-sec) !important; font-size: 13px !important; }
[aria-selected="true"][data-baseweb="tab"] { background: var(--bg-card-2) !important; color: var(--text-pri) !important; }
[data-baseweb="tab-highlight"] { display: none !important; }
[data-baseweb="tab-panel"] { background: transparent !important; padding-top: 16px !important; }

/* ── DataFrame ── */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 10px !important; overflow: hidden; }
[data-testid="stDataFrame"] table { background: var(--bg-card) !important; }
[data-testid="stDataFrame"] thead th { background: var(--bg-card-2) !important; color: var(--text-sec) !important; font-size: 12px !important; }
[data-testid="stDataFrame"] tbody td { color: var(--text-pri) !important; font-family: var(--font-mono); font-size: 13px !important; }

/* ── Metric ── */
[data-testid="stMetric"] { background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; }
[data-testid="stMetricLabel"] { color: var(--text-sec) !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { font-family: var(--font-mono) !important; color: var(--text-pri) !important; }

/* ── 分隔线 ── */
hr { border-color: var(--border) !important; }

/* ── 滚动条 ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--text-dim); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 3. 数据引擎（逻辑不变）
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_advanced_data():
    try:
        df = ak.stock_a_ttm_lyr()
        rename_map = {'averagePETTM': 'pe', 'averagePeTtm': 'pe', '平均市盈率': 'pe'}
        df.rename(columns=rename_map, inplace=True)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

        df['percentile'] = df['pe'].rank(pct=True) * 100
        df['win_rate'] = 100 - df['percentile']

        t90_pe = df['pe'].quantile(0.10)
        t20_pe = df['pe'].quantile(0.80)
        avg_pe = df['pe'].mean()
        min_pe = df['pe'].min()

        df['is_below_90'] = df['pe'] <= t90_pe
        df['group'] = (df['is_below_90'] != df['is_below_90'].shift()).cumsum()
        df['consecutive_days'] = df.groupby('group')['is_below_90'].transform(
            lambda x: x.cumsum() if x.iloc[0] else 0
        )

        risk_free_rate = 0.023
        df['risk_premium'] = (1 / df['pe'] - risk_free_rate) * 100

        return df, t90_pe, t20_pe, avg_pe, min_pe
    except Exception as e:
        st.error(f"数据获取异常: {e}")
        return None, 0, 0, 0, 0


# ─────────────────────────────────────────────
# 4. 仪表盘组件 — 暗色风格
# ─────────────────────────────────────────────
def draw_valuation_clock(win_rate):
    # 根据胜率决定指针颜色
    if win_rate >= 80:
        bar_color = "#3ddc97"
    elif win_rate <= 20:
        bar_color = "#f06470"
    else:
        bar_color = "#e8c97a"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=win_rate,
        number={"suffix": "%", "font": {"size": 36, "color": bar_color, "family": "IBM Plex Mono"}},
        title={"text": "当前市场胜率", "font": {"size": 13, "color": "#8a8fa8"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickvals": [0, 20, 50, 80, 100],
                "ticktext": ["0", "20", "50", "80", "100"],
                "tickcolor": "#4e5268",
                "tickfont": {"color": "#4e5268", "size": 11},
                "linecolor": "rgba(0,0,0,0)",
            },
            "bar": {"color": bar_color, "thickness": 0.22},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 20],  "color": "rgba(240,100,112,0.12)"},
                {"range": [20, 80], "color": "rgba(232,201,122,0.08)"},
                {"range": [80, 100],"color": "rgba(61,220,151,0.12)"},
            ],
            "threshold": {
                "line": {"color": "#ffffff", "width": 1.5},
                "thickness": 0.8,
                "value": win_rate,
            },
        },
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Noto Sans SC"},
    )
    return fig


def make_pe_chart(df, t90, t20):
    """PE 历史走势 — 暗色主题"""
    fig = go.Figure()

    # 区域着色
    fig.add_hrect(
        y0=df['pe'].min(), y1=t90,
        fillcolor="rgba(61,220,151,0.06)", line_width=0,
        annotation_text="捡钱区", annotation_font_size=11,
        annotation_font_color="#3ddc97",
    )
    fig.add_hrect(
        y0=t20, y1=df['pe'].max(),
        fillcolor="rgba(240,100,112,0.06)", line_width=0,
        annotation_text="博傻区", annotation_font_size=11,
        annotation_font_color="#f06470",
    )

    # 辅助线
    fig.add_hline(y=t90, line_dash="dot", line_color="rgba(61,220,151,0.4)", line_width=1)
    fig.add_hline(y=t20, line_dash="dot", line_color="rgba(240,100,112,0.4)", line_width=1)

    # PE 折线
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['pe'],
        mode='lines',
        line=dict(color="rgba(232,201,122,0.25)", width=1),
        showlegend=False, hoverinfo='skip',
    ))

    # 散点（胜率热力）
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['pe'],
        mode='markers',
        marker=dict(
            size=3.5,
            color=df['win_rate'],
            colorscale=[
                [0.0, "#f06470"],
                [0.2, "#f06470"],
                [0.5, "#e8c97a"],
                [0.8, "#3ddc97"],
                [1.0, "#3ddc97"],
            ],
            cmin=0, cmax=100,
            showscale=True,
            colorbar=dict(
                title=dict(text="胜率%", font=dict(color="#8a8fa8", size=11)),
                tickfont=dict(color="#8a8fa8", size=10),
                thickness=10,
                len=0.6,
                bgcolor="rgba(0,0,0,0)",
                outlinewidth=0,
            ),
        ),
        name="胜率热力",
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>PE: %{y:.1f}<br>胜率: %{marker.color:.0f}%<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="PE 历史走势 · 胜率热力分布", font=dict(color="#8a8fa8", size=13)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=340,
        margin=dict(l=10, r=50, t=44, b=10),
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(color="#4e5268", size=10),
            linecolor="rgba(255,255,255,0.07)",
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            tickfont=dict(color="#4e5268", size=10),
            linecolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor="#1c2030", bordercolor="#3a3f55",
            font_color="#e8eaf0", font_size=12,
        ),
    )
    return fig


# ─────────────────────────────────────────────
# 5. 主程序
# ─────────────────────────────────────────────
def main():

    # ── 顶部 Header ──
    from datetime import datetime
    st.markdown(f"""
    <div class="app-header">
        <span class="app-title">⚖ A股全维度估值决策系统</span>
        <span class="app-badge">v2.0</span>
        <span class="app-time">LAST UPDATE · {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
    </div>
    """, unsafe_allow_html=True)

    df, t90, t20, avg_pe, min_pe = get_advanced_data()

    if df is None:
        return

    latest = df.iloc[-1]
    cur_pe      = latest['pe']
    cur_win     = latest['win_rate']
    cur_premium = latest['risk_premium']
    years_diff  = cur_pe - avg_pe
    risk_bottom = (cur_pe - min_pe) / cur_pe * 100

    # ── KPI 卡片 ──
    kpi_win_color   = "green" if cur_win >= 80 else "red" if cur_win <= 20 else "gold"
    kpi_prem_color  = "green" if cur_premium > 4 else "red" if cur_premium < 0 else "blue"

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card gold">
            <div class="kpi-label">当前 PE（TTM）</div>
            <div class="kpi-value gold">{cur_pe:.2f}<span style="font-size:14px;margin-left:4px;color:var(--gold-dim)">x</span></div>
            <div class="kpi-sub">历史均值 {avg_pe:.1f}x · {'↓ 低估' if cur_pe < avg_pe else '↑ 高估'} {abs(years_diff):.1f}x</div>
        </div>
        <div class="kpi-card {kpi_win_color}">
            <div class="kpi-label">历史胜率</div>
            <div class="kpi-value {kpi_win_color}">{cur_win:.1f}<span style="font-size:14px;margin-left:2px;color:var(--text-sec)">%</span></div>
            <div class="kpi-sub">10%分位 ≤ {t90:.1f}x · 80%分位 ≥ {t20:.1f}x</div>
        </div>
        <div class="kpi-card {kpi_prem_color}">
            <div class="kpi-label">风险溢价（FED）</div>
            <div class="kpi-value {kpi_prem_color}">{cur_premium:.2f}<span style="font-size:14px;margin-left:2px;color:var(--text-sec)">%</span></div>
            <div class="kpi-sub">相对无风险利率 2.3% 超额回报</div>
        </div>
        <div class="kpi-card blue">
            <div class="kpi-label">极限回撤空间</div>
            <div class="kpi-value blue">{risk_bottom:.1f}<span style="font-size:14px;margin-left:2px;color:var(--text-sec)">%</span></div>
            <div class="kpi-sub">回到史上最低 PE {min_pe:.1f}x 的距离</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 操作信号横幅 ──
    if cur_win >= 90:
        banner_class, icon, title_color, title_text, desc = (
            "extreme", "💎",  "gold",
            "【最高指令】千载难逢的黄金坑",
            f"PE 已跌破历史 <strong>10% 分位</strong>！在过去 20 年中，仅有 <strong>{100-cur_win:.1f}%</strong> 的时间比现在更便宜。极少数人才能等到的机会——请保持极度贪婪，分批重仓。"
        )
    elif cur_pe < t90:
        banner_class, icon, title_color, title_text, desc = (
            "opportunity", "🎯", "green",
            "历史级底部区域 · 高安全边际",
            f"当前 PE <strong>{cur_pe:.1f}x</strong> 处于历史底部区间，胜率 <strong>{cur_win:.1f}%</strong>。安全边际极高，适合分批买入并长期持有。"
        )
    elif cur_win < 20:
        banner_class, icon, title_color, title_text, desc = (
            "danger", "🚫", "red",
            "市场情绪严重过热 · 高风险区间",
            f"当前 PE <strong>{cur_pe:.1f}x</strong> 位于历史高位，仅有 <strong>{cur_win:.1f}%</strong> 的胜率。收益纯靠博弈，小心成为最后的接盘侠，建议控仓观望。"
        )
    else:
        banner_class, icon, title_color, title_text, desc = (
            "neutral", "⚖️", "blue",
            "估值均衡水位 · 维持定投节奏",
            f"当前 PE <strong>{cur_pe:.1f}x</strong>，胜率 <strong>{cur_win:.1f}%</strong>，市场处于均衡区间。建议维持原有定投计划，不宜激进加减仓。"
        )

    st.markdown(f"""
    <div class="signal-banner {banner_class}">
        <span class="signal-icon">{icon}</span>
        <div class="signal-body">
            <div class="signal-title {title_color}">{title_text}</div>
            <div class="signal-desc">{desc}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 仪表盘 + 分析卡 ──
    col_gauge, col_analysis = st.columns([1, 1], gap="medium")

    with col_gauge:
        st.plotly_chart(draw_valuation_clock(cur_win), use_container_width=True)

    with col_analysis:
        is_cheaper = years_diff < 0
        prem_level = "较高，股市吸引力强" if cur_premium > 4 else "偏低，注意性价比" if cur_premium < 2 else "适中"
        st.markdown(f"""
        <div class="analysis-card">
            <h4>深度解读</h4>
            <div class="analysis-row">
                <span class="analysis-row-label">回本周期类比</span>
                <span class="analysis-row-value accent">{cur_pe:.1f} 年</span>
            </div>
            <div class="analysis-row">
                <span class="analysis-row-label">vs 历史均值</span>
                <span class="analysis-row-value {'positive' if is_cheaper else 'negative'}">{'节省' if is_cheaper else '多等'} {abs(years_diff):.1f} 年</span>
            </div>
            <hr class="divider">
            <div class="analysis-row">
                <span class="analysis-row-label">风险溢价水平</span>
                <span class="analysis-row-value">{prem_level}</span>
            </div>
            <div class="analysis-row">
                <span class="analysis-row-label">距历史最低 PE</span>
                <span class="analysis-row-value {'positive' if risk_bottom < 30 else ''}">{risk_bottom:.1f}% 空间</span>
            </div>
            <hr class="divider">
            <div style="font-size:12px;color:var(--text-dim);line-height:1.7;">
                现在的 A 股就像一门回本期 <strong style="color:var(--text-sec)">{cur_pe:.1f} 年</strong> 的生意。
                相比历史均值，你{'<strong style="color:#3ddc97">节省了</strong>' if is_cheaper else '<strong style="color:#f06470">多付了</strong>'}
                <strong style="color:var(--text-sec)">{abs(years_diff):.1f} 年</strong> 的等待成本。
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 图表 Tab ──
    tab1, tab2 = st.tabs(["  🔥 情绪热力全景  ", "  📂 历史筑底档案  "])

    with tab1:
        st.plotly_chart(make_pe_chart(df, t90, t20), use_container_width=True)

    with tab2:
        summary = df[df['is_below_90']].groupby('group').agg({
            'date': ['min', 'max'],
            'consecutive_days': 'max',
            'pe': 'mean',
        }).reset_index()
        summary.columns = ['区间ID', '起始日期', '结束日期', '持续天数', '平均PE']
        summary['起始日期'] = summary['起始日期'].dt.strftime('%Y-%m-%d')
        summary['结束日期'] = summary['结束日期'].dt.strftime('%Y-%m-%d')
        summary['平均PE']  = summary['平均PE'].round(2)
        st.dataframe(
            summary.sort_values('持续天数', ascending=False),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
