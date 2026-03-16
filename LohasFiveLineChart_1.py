import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# 網頁配置
st.set_page_config(page_title="樂活五線譜自動生成", layout="wide")

# 側邊欄：查詢設定
st.sidebar.header("查詢設定")

# 6. 股票代號標示修改
stock_id = st.sidebar.text_input("股票代號(如2330.TW或AAPL)", "2330.TW")

# 2 & 3. 起始日期標示與預設值 (2022/10/03)
start_date = st.sidebar.date_input("起始日期(YYYY/MM/DD)", datetime(2022, 10, 3))

# 4 & 5. 結束日期標示與預設值 (當天)
end_date = st.sidebar.date_input("結束日期(YYYY/MM/DD)", datetime.now())

# 1. 趨勢線顏色手動切換 (解決深色背景看不見的問題)
theme_choice = st.sidebar.radio("圖表主題 (對應網頁背景)", ["亮色 (白色背景)", "深色 (深色背景)"])

if theme_choice == "深色 (深色背景)":
    main_line_color = "white"
    chart_template = "plotly_dark"
else:
    main_line_color = "black"
    chart_template = "plotly_white"

calculate_btn = st.sidebar.button("開始計算")

# 處理台股代號格式 (.TW 或 .TWO)
search_id = stock_id
if stock_id.isdigit():
    # 簡單判斷：4碼通常是上市(.TW)，但若要精確需使用者輸入完整代號
    search_id = f"{stock_id}.TW"

st.title("📈 樂活五線譜自動生成")
st.subheader(f"📊 目前分析標的: {search_id}")

if calculate_btn or stock_id:
    # 抓取資料
    data = yf.download(search_id, start=start_date, end=end_date, auto_adjust=True)
    
    if not data.empty:
        # 確保資料為一維
        close_prices = data['Close'].values.flatten()
        df = pd.DataFrame({'Date': data.index, 'Close': close_prices})
        df['Time_Idx'] = np.arange(len(df)) 
        
        # 計算線性回歸 (趨勢中線)
        z = np.polyfit(df['Time_Idx'], df['Close'], 1)
        p = np.poly1d(z)
        df['Trend_Line'] = p(df['Time_Idx'])
        
        # 計算標準差 (五線譜範圍)
        std_dev = (df['Close'] - df['Trend_Line']).std()
        df['Upper_2'] = df['Trend_Line'] + 2 * std_dev
        df['Upper_1'] = df['Trend_Line'] + 1 * std_dev
        df['Lower_1'] = df['Trend_Line'] - 1 * std_dev
        df['Lower_2'] = df['Trend_Line'] - 2 * std_dev

        # 繪製圖表
        fig = go.Figure()
        
        # 收盤價線 (動態顏色)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='收盤價', 
                                 line=dict(color=main_line_color, width=1.5)))
        
        colors = ['#FF4136', '#FF851B', '#0074D9', '#2ECC40', '#3D9970'] # 稍微鮮豔一點的顏色，在深淺色效果都好
        names = ['極端樂觀', '樂觀', '趨勢中線', '悲觀', '極端悲觀']
        lines = ['Upper_2', 'Upper_1', 'Trend_Line', 'Lower_1', 'Lower_2']
        
        for idx, line in enumerate(lines):
            fig.add_trace(go.Scatter(x=df['Date'], y=df[line], name=names[idx], 
                                     line=dict(dash='dash' if 'Trend' not in line else 'solid', 
                                               color=colors[idx], width=1)))

        fig.update_layout(height=600, hovermode='x unified', template=chart_template,
                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        
        # 顯示圖表
        st.plotly_chart(fig, use_container_width=True)

        # 數據摘要
        st.header("📊 數據摘要")
        last_price = df['Close'].iloc[-1]
        mid_price = df['Trend_Line'].iloc[-1]
        current_sd = (last_price - mid_price) / std_dev
        
        col1, col2, col3 = st.columns(3)
        col1.metric("最後收盤價", f"{last_price:.2f}")
        col2.metric("回歸中線", f"{mid_price:.2f}")
        col3.metric("目前區間", f"{current_sd:.2f} σ")
        
        if current_sd > 0:
            st.success(f"↑ 目前價格高於中線 {current_sd:.2f} 個標準差")
        else:
            st.warning(f"↓ 目前價格低於中線 {abs(current_sd):.2f} 個標準差")
    else:
        st.error("找不到該股票代號的資料，請檢查代號是否正確（台股請加 .TW 或 .TWO）。")