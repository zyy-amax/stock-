import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 页面配置
# -----------------------------------------------------------------------------
st.set_page_config(page_title="A股PE胜率热力图-深度版", page_icon="🔥", layout="wide")

# -----------------------------------------------------------------------------
# 2. 数据获取与深度计算
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_enhanced_data():
    try:
        # 获取 A 股 TTM PE 数据
        df = ak.stock_a_ttm_lyr()
        
        # 兼容不同接口的列名
        rename_map = {'averagePETTM': 'pe', 'averagePeTtm': 'pe', '平均市盈率': 'pe'}
        df.rename(columns=rename_map, inplace=True)
        
        if 'pe' not in df.columns:
            st.error("❌ 数据解析失败，找不到市盈率列。")
            return None, None, None

        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 计算百分位与胜率
        df['percentile'] = df['pe'].rank(pct=True) * 100
        df['win_rate'] = 100 - df['percentile']
        
        # --- 核心逻辑：计算 90% 胜率线下的天数 ---
        pe_threshold_90 = df['pe'].quantile(0.10) # 胜率90%对应PE百分位10%
        
        # 标记是否在 90% 胜率线下 (PE <= threshold)
        df['is_below_90'] = df['pe'] <= pe_threshold_90
        
        # 使用累加分组法计算连续天数
        df['group'] = (df['is_below_90'] != df['is_below_90'].shift()).cumsum()
        
        # 只保留在下方的组，并计算每组的累计天数
        df['consecutive_days'] = df.groupby('group')['is_below_90'].transform(lambda x: x.cumsum() if x.iloc[0] else 0)
        
        # 提取历史最长记录 (处理可能没有满足条件的情况)
        below_90_df = df[df['is_below_90']]
        max_duration = below_90_df['consecutive_days'].max() if not below_90_df.empty else 0
        
        return df, pe_threshold_90, max_duration
        
    except Exception as e:
        st.error(f"❌ 数据处理异常: {e}")
        return None, None, None

# -----------------------------------------------------------------------------
# 3. 辅助函数：信号与图表
# -----------------------------------------------------------------------------
def calculate_signal(cur_pe, threshold_90, current_duration, max_hist_days):
    """抄底信号触发逻辑"""
    if cur_pe > threshold_90:
        return "等待中", "🔍 市场估值尚在中位，耐心等待黄金坑。", "info"
    
    # 当前持续天数占历史最长的百分比
    time_ratio = current_duration / max_hist_days if max_hist_days > 0 else 0
    
    if time_ratio >= 0.8:
        return "🔥 史诗级抄底", f"警告：当前筑底时长({int(current_duration)}天)极度接近历史极值！胜率极高。", "error"
    elif time_ratio >= 0.5:
        return "💎 强力定投", f"信号：筑底时长已超过历史中值，当前 PE 为 {cur_pe:.2f}，建议加大定投仓位。", "warning"
    else:
        return "✅ 初级信号", "提示：PE 已进入 90% 胜率区，左侧交易机会开启。", "success"

def draw_gauge(current, maximum):
    """绘制底部热度计仪表盘"""
    # 防止 maximum 为 0 导致报错
    max_val = maximum if maximum > 0 else 100 
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current,
        title = {'text': "底部时长消耗 (天)"},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [0, max_val]},
            'bar': {'color': "darkred"},
            'steps': [
                {'range': [0, max_val * 0.5], 'color': "lightgray"},
                {'range': [max_val * 0.5, max_val * 0.8], 'color': "orange"},
                {'range': [max_val * 0.8, max_val], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': current
            }
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# -----------------------------------------------------------------------------
# 4. 主程序
# -----------------------------------------------------------------------------
def main():
    st.title("🔥 A股全市场 PE 胜率热力图与决策引擎")
    
    with st.spinner('正在回溯历史数据与计算模型...'):
        df, threshold_90, max_hist_days = get_enhanced_data()

    if df is not None:
        latest = df.iloc[-1]
        cur_pe = latest['pe']
        cur_win = latest['win_rate']
        cur_date = latest['date'].strftime('%Y-%m-%d')
        current_duration = latest['consecutive_days'] if latest['is_below_90'] else 0
        
        # --- 1. 择时决策引擎 (顶部提示) ---
        signal_title, signal_desc, signal_level = calculate_signal(
            cur_pe, threshold_90, current_duration, max_hist_days
        )
        
        st.markdown("### 🛡️ 核心决策引擎")
        if signal_level == "error":
            st.error(f"**【{signal_title}】** {signal_desc}")
        elif signal_level == "warning":
            st.warning(f"**【{signal_title}】** {signal_desc}")
        elif signal_level == "success":
            st.success(f"**【{signal_title}】** {signal_desc}")
        else:
            st.info(f"**【{signal_title}】** {signal_desc}")

        # --- 2. 核心指标面板 ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("数据更新日期", cur_date)
        m2.metric("当前理论胜率", f"{cur_win:.2f}%", delta=f"{cur_win-50:.1f}% (基准50%)")
        m3.metric("当前PE / 90%胜率线", f"{cur_pe:.2f}", f"阈值线: {threshold_90:.2f}", delta_color="inverse")
        m4.metric("90%胜率线下持续 / 历史极值", f"{int(current_duration)} 天", f"极值: {int(max_hist_days)} 天", delta_color="off")

        # --- 3. 侧边栏仪表盘 ---
        with st.sidebar:
            st.markdown("### 📊 筑底进度监控")
            if latest['is_below_90']:
                st.plotly_chart(draw_gauge(current_duration, max_hist_days), use_container_width=True)
                progress = min(current_duration / max_hist_days, 1.0) if max_hist_days > 0 else 0
                st.progress(progress, text=f"当前筑底时长已达历史极值的 {progress*100:.1f}%")
            else:
                st.info("💡 当前 PE 高于 90% 胜率线，未进入底部区间。")

        # --- 4. 增强版全景图表 ---
        threshold_80 = df['pe'].quantile(0.20)
        
        fig = px.scatter(df, x='date', y='pe', 
                         color='win_rate',
                         color_continuous_scale='RdYlBu_r', 
                         title="A股历史 PE 走势与胜率热力分布 (点击拖动可缩放)",
                         hover_data={'pe':':.2f', 'win_rate':':.2f', 'consecutive_days':True})
        
        # 添加辅助线
        fig.add_hline(y=threshold_90, line_dash="dash", line_color="red", 
                      annotation_text=f"90%胜率(PE={threshold_90:.2f})", annotation_position="bottom right")
        fig.add_hline(y=threshold_80, line_dash="dot", line_color="orange", 
                      annotation_text=f"80%胜率(PE={threshold_80:.2f})", annotation_position="bottom right")
        
        # 填充 90% 胜率以下的区域 (视觉强化黄金坑)
        fig.add_hrect(y0=df['pe'].min() * 0.9, y1=threshold_90, fillcolor="red", opacity=0.1, line_width=0, layer="below")
        
        # 标记当前位置
        fig.add_annotation(x=latest['date'], y=cur_pe, text="当前位置", showarrow=True, arrowhead=1, yshift=15)

        st.plotly_chart(fig, use_container_width=True)

        # --- 5. 历史区间复盘 ---
        st.markdown("---")
        with st.expander("📂 查看历史「90%胜率线」下的持续区间记录"):
            summary = df[df['is_below_90']].groupby('group').agg({
                'date': ['min', 'max'],
                'consecutive_days': 'max',
                'pe': 'mean'
            }).reset_index()
            summary.columns = ['组ID', '进入日期', '离开日期', '持续天数', '区间平均PE']
            summary = summary.sort_values('持续天数', ascending=False)
            
            st.dataframe(
                summary, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "进入日期": st.column_config.DateColumn(format="YYYY-MM-DD"),
                    "离开日期": st.column_config.DateColumn(format="YYYY-MM-DD"),
                    "区间平均PE": st.column_config.NumberColumn(format="%.2f")
                }
            )

if __name__ == "__main__":
    main()