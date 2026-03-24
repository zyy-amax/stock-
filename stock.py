import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 页面基础配置
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="A股估值决策系统 2.0",
    page_icon="📈",
    layout="wide"
)

# 自定义 CSS 提升 UI 质感
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    [data-testid="stMetricDelta"] svg { display: none; } /* 隐藏默认箭头 */
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 核心数据引擎
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_processed_data():
    try:
        # 获取 A 股 TTM PE 数据
        df = ak.stock_a_ttm_lyr()
        rename_map = {'averagePETTM': 'pe', 'averagePeTtm': 'pe', '平均市盈率': 'pe'}
        df.rename(columns=rename_map, inplace=True)
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 计算百分位与胜率
        df['percentile'] = df['pe'].rank(pct=True) * 100
        df['win_rate'] = 100 - df['percentile']
        
        # 统计学边界定义
        threshold_90 = df['pe'].quantile(0.10)
        threshold_80 = df['pe'].quantile(0.20)
        
        # 筑底逻辑计算
        df['is_below_90'] = df['pe'] <= threshold_90
        df['group'] = (df['is_below_90'] != df['is_below_90'].shift()).cumsum()
        df['consecutive_days'] = df.groupby('group')['is_below_90'].transform(lambda x: x.cumsum() if x.iloc[0] else 0)
        
        max_duration = df[df['is_below_90']]['consecutive_days'].max() if any(df['is_below_90']) else 100
        
        return df, threshold_90, threshold_80, max_duration
    except Exception as e:
        st.error(f"数据处理异常: {e}")
        return None, 0, 0, 0

# -----------------------------------------------------------------------------
# 3. 绘图组件
# -----------------------------------------------------------------------------
def plot_main_chart(df, t90, t80):
    # 使用 Plotly 创建混合图表
    fig = px.line(df, x='date', y='pe', title="A股全市场估值历史全景 (PE-TTM)",
                  color_discrete_sequence=['#555555'])
    
    # 添加胜率热力散点层
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['pe'],
        mode='markers',
        marker=dict(
            size=3.5,
            color=df['win_rate'],
            colorscale='RdYlBu_r',
            showscale=True,
            colorbar=dict(title="理论胜率 %", thickness=15, x=1.02)
        ),
        name="胜率分布",
        hovertemplate="日期: %{x}<br>PE: %{y:.2f}"
    ))

    # 视觉强化：红色底部区域
    fig.add_hrect(y0=df['pe'].min()*0.9, y1=t90, fillcolor="#FF4B4B", opacity=0.1, line_width=0, layer="below")
    
    # 辅助线
    fig.add_hline(y=t90, line_dash="dash", line_color="#FF4B4B", 
                  annotation_text="90%胜率线", annotation_position="bottom right")
    fig.add_hline(y=t80, line_dash="dot", line_color="#FFA500", 
                  annotation_text="80%胜率线", annotation_position="top right")

    fig.update_layout(
        hovermode="x unified",
        plot_bgcolor='white',
        xaxis=dict(showgrid=False, title="年份", rangeselector=dict(
            buttons=list([
                dict(count=1, label="1年", step="year", stepmode="backward"),
                dict(count=5, label="5年", step="year", stepmode="backward"),
                dict(step="all", label="全部数据")
            ])
        )),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', title="市盈率 (PE)"),
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig

# -----------------------------------------------------------------------------
# 4. 界面展示逻辑
# -----------------------------------------------------------------------------
def main():
    st.title("🔥 A股估值决策系统 2.0")
    st.caption("基于全市场中位数 PE 及历史筑底时长模型 | 数据来源: AkShare")

    df, t90, t80, max_dur = get_processed_data()
    
    if df is not None:
        latest = df.iloc[-1]
        cur_pe = latest['pe']
        cur_win = latest['win_rate']
        cur_dur = latest['consecutive_days'] if latest['is_below_90'] else 0
        
        # 第一行：核心指标看板
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("当前市场 PE", f"{cur_pe:.2f}")
        m2.metric("当前理论胜率", f"{cur_win:.1f}%", f"{cur_win-50:.1f}% vs 基准", delta_color="normal")
        
        status = "🔴 极度低估 (抄底)" if latest['is_below_90'] else "⚪ 估值合理"
        if t90 < cur_pe <= t80: status = "🟠 建议配置 (定投)"
        m3.metric("市场当前状态", status)
        m4.metric("最近更新日期", latest['date'].strftime('%Y-%m-%d'))

        # 分页展示
        tab1, tab2 = st.tabs(["📊 估值热力分布", "📂 历史筑底记录"])
        
        with tab1:
            # 实时决策建议窗
            if cur_pe <= t90:
                st.error(f"发现「黄金坑」：当前 PE 已低于 90% 胜率线，底部已持续 {int(cur_dur)} 天。")
            elif cur_pe <= t80:
                st.warning("进入低估区：当前胜率已超 80%，适合分批建立长线仓位。")
            else:
                st.info("处于均衡区：市场估值回归中位，建议保持原有定投节奏。")
            
            st.plotly_chart(plot_main_chart(df, t90, t80), use_container_width=True)

        with tab2:
            st.subheader("历史「90% 胜率线」下方区间统计")
            # 整理历史数据
            summary = df[df['is_below_90']].groupby('group').agg({
                'date': ['min', 'max'],
                'consecutive_days': 'max',
                'pe': 'mean'
            }).reset_index()
            summary.columns = ['ID', '进入日期', '离开日期', '筑底持续天数', '期间平均PE']
            summary = summary.sort_values('筑底持续天数', ascending=False)
            
            # 使用原生 dataframe 渲染（避免样式组件冲突）
            st.dataframe(
                summary,
                column_config={
                    "进入日期": st.column_config.DateColumn("进入日期"),
                    "离开日期": st.column_config.DateColumn("离开日期"),
                    "期间平均PE": st.column_config.NumberColumn("期间平均PE", format="%.2f"),
                    "筑底持续天数": st.column_config.NumberColumn("天数", help="在90%胜率线下持续的天数")
                },
                use_container_width=True,
                hide_index=True
            )

        # 侧边栏说明
        with st.sidebar:
            st.header("⚙️ 系统说明")
            st.write(f"当前 90% 胜率 PE 阈值: **{t90:.2f}**")
            st.write(f"当前 80% 胜率 PE 阈值: **{t80:.2f}**")
            st.divider()
            st.info("模型逻辑：当市场整体 PE 处于历史极低水平（即胜率极高）时，是左侧布局的绝佳时机。本系统实时监控底部持续天数，帮助您识别历史级别的底部机会。")

if __name__ == "__main__":
    main()
