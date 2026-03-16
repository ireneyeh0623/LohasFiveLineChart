import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# Page configuration
st.set_page_config(page_title="樂活五線譜自動生成", layout="wide")

# 1. Trend line color logic (Dynamic based on theme)
try:
    # st.get_option detects the active Streamlit theme (light/dark)
    theme_base = st.get_option("theme.base")
    main_line_color = "black" if theme_base == "light" or theme_base is None else "white"
    chart_template = "plotly_white" if theme_base == "light" or theme_base is None else "plotly_dark"
except:
    main_line_color = "black"
    chart_template = "plotly_white"

# Sidebar: Query Settings
st.sidebar.header("查詢設定")

# 6. Updated stock code label
stock_id = st.sidebar.text_input("股票代號(如2330.TW或AAPL)", "2330.TW")

# Handle Taiwan stock formatting
if stock_id.isdigit():
    search_id = f"{stock_id}.TW"
else:
    search_id = stock_id

# 2 & 3. Start date label and default (2022/10/03)
start_date = st.sidebar.date_input("起始日期(YYYY/MM/DD)", datetime(2022, 10, 3))

# 4 & 5. End date label and default (Today's date)
end_date = st.sidebar.date_input("結束日期(YYYY/MM/DD)", datetime.now())

calculate_btn = st.sidebar.button("開始計算")

st.title("📈 樂活五線譜自動生成")
st.subheader(f"📊 目前分析標的: {search_id}")

if calculate_btn or stock_id:
    # auto_adjust=True ensures prices are split-adjusted
    data = yf.download(search_id, start=start_date, end=end_date, auto_adjust=True)
    
    if not data.empty:
        # Flattening ensures a 1D array for standard linear regression
        close_prices = data['Close'].values.flatten()
        df = pd.DataFrame({'Date': data.index, 'Close': close_prices})
        df['Time_Idx'] = np.arange(len(df)) 
        
        # Calculate Linear Regression (Trend Line)
        z = np.polyfit(df['Time_Idx'], df['Close'], 1)
        p = np.poly1d(z)
        df['Trend_Line'] = p(df['Time_Idx'])
        
        # Standard Deviation calculation for bands
        std_dev = (df['Close'] - df['Trend_Line']).std()
        df['Upper_2'] = df['Trend_Line'] + 2 * std_dev
        df['Upper_1'] = df['Trend_Line'] + 1 * std_dev
        df['Lower_1'] = df['Trend_Line'] - 1 * std_dev
        df['Lower_2'] = df['Trend_Line'] - 2 * std_dev

        # Create Plotly Chart
        fig = go.Figure()
        
        # 1. Close Price line with dynamic color
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='收盤價', 
                                 line=dict(color=main_line_color, width=1.5)))
        
        # Band lines configuration
        colors = ['red', 'orange', 'blue', 'lightgreen', 'green']
        names = ['極端樂觀', '樂觀', '趨勢中線', '悲觀', '極端悲觀']
        lines = ['Upper_2', 'Upper_1', 'Trend_Line', 'Lower_1', 'Lower_2']
        
        for idx, line in enumerate(lines):
            fig.add_trace(go.Scatter(x=df['Date'], y=df[line], name=names[idx], 
                                     line=dict(dash='dash' if 'Trend' not in line else 'solid', 
                                               color=colors[idx], width=1)))

        fig.update_layout(height=600, hovermode='x unified', template=chart_template,
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

        # Data Summary Section
        st.header("📊 數據摘要")
        last_price = df['Close'].iloc[-1]
        mid_price = df['Trend_Line'].iloc[-1]
        current_sd = (last_price - mid_price) / std_dev
        
        col1, col2, col3 = st.columns(3)
        col1.metric("最後收盤價", f"{last_price:.2f}")
        col2.metric("回歸中線", f"{mid_price:.2f}")
        col3.metric("目前區間", f"{current_sd:.2f} σ")
        
        if current_sd > 0:
            st.success("↑ 高於中線")
        else:
            st.warning("↓ 低於中線")
    else:
        st.error("找不到該股票代號的資料，請檢查代號是否正確。")