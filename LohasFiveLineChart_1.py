import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ==============================================================================
# 1. 系統環境配置
# ==============================================================================

st.set_page_config(page_title="股價五線譜", layout="wide")

# ==============================================================================
# 2. 側邊欄：使用者參數輸入區
# ==============================================================================

st.sidebar.header("查詢設定")

# 股票代號輸入：預設為 2330.TW (台積電)
stock_id = st.sidebar.text_input("股票代號(如2330.TW或AAPL)", "2330.TW")
# 日期範圍選擇：設定資料擷取的起始與結束時間
start_date = st.sidebar.date_input("起始日期(YYYY/MM/DD)", datetime(2022, 10, 3))
end_date = st.sidebar.date_input("結束日期(YYYY/MM/DD)", datetime.now())
# 視覺主題切換：根據網頁環境調整背景顏色
theme_choice = st.sidebar.radio("圖表主題(對應網頁背景)", ["亮色(白色背景)", "深色(深色背景)"])
# 開始計算觸發按鈕
calculate_btn = st.sidebar.button("開始計算")

# ==============================================================================
# 3. 視覺樣式優化 (CSS 強制覆蓋背景色切換邏輯)
# ==============================================================================

# 根據主題選擇，動態調整 Streamlit 元件與圖表的顏色配比
if theme_choice == "深色(深色背景)":
    chart_template = "plotly_dark"
    font_color = "white"
    bg_color = "#0E1117"
    st.markdown("""
        <style>
        /* ==========================================
             1. 核心區塊背景與全域文字顏色 (深色模式)
           ========================================== */
                
        /* 強制將側邊欄 [data-testid="stSidebar"]、主程式容器 .stApp 以及頂部標頭 header 設定為深黑色 (#0E1117)，並將基礎文字顏色設為白色 */
        [data-testid="stSidebar"], .stApp, header { background-color: #0E1117 !important; color: white !important; }
                
        /* 確保所有 Markdown 內容、段落文字 (p)、各級標題 (h1-h3) 以及通用標籤 (span) 皆呈現純白色，以確保在深色背景下的易讀性 */
        .stMarkdown, p, h1, h2, h3, span { color: white !important; }

        /* ==========================================
             2. 輸入組件 (Input) 樣式自定義
           ========================================== */
                  
        /*調整輸入框 (如股票代號輸入框) 的視覺呈現：
            - color: white 使輸入的文字變為白色
            - background-color: #262730 設定一個比主背景稍淺的深灰色，增加層次感 */
        input { color: white !important; background-color: #262730 !important; }
                
        /* --- [新增] 深色模式下的按鈕顏色 --- */
        div.stButton > button {
            background-color: #31333F !important; /* 改為深灰色 */
            border: 1px solid #4A4A4A !important;
            color: white !important;
        }

        /* --- [新增] 深色模式下的選項文字顏色 --- */
        div[data-testid="stRadio"] label p {
            color: #A0A0A0 !important; /* 讓選項文字呈現淺灰色，與背景區分 */
        }     

        </style>
        """, unsafe_allow_html=True)
else:
    chart_template = "plotly_white"
    font_color = "black"
    bg_color = "#FFFFFF"
    st.markdown("""
        <style>
        /* ==========================================
            1. 全域背景與文字基礎設定 (亮色模式)
           ========================================== */
                
        /* 強制側邊欄、主畫面與頂部標頭背景設為純白 (#FFFFFF)，文字設為純黑 */
        /* [data-testid="stSidebar"] 代表側邊欄；.stApp 代表主頁面容器 */
        [data-testid="stSidebar"], .stApp, header { 
            background-color: #FFFFFF !important; 
            color: black !important; 
        }
                
        /* 確保所有 Markdown 文字、段落 (p) 與各級標題 (h1-h3) 皆呈現純黑色，以達最高對比度 */
        .stMarkdown, p, h1, h2, h3, span { color: black !important; }
        
        /* ==========================================
            2. 輸入框 (Input) 與 日期選取器 樣式優化
           ========================================== */     

        /* 針對 Streamlit 內部的 BaseWeb 輸入框組件進行視覺重構 */
        div[data-baseweb="input"], 
        div[data-baseweb="input"] > div,
        div[data-baseweb="input"] input {
            background-color: white !important;
            border-color: #dcdcdc !important; /* 使用淺灰色邊框取代預設色，風格較為簡約 */
            box-shadow: none !important;      /* 徹底移除點擊輸入框時預設產生的藍色陰影 */
        }
        
        /* 專門修正日期選擇器 (Date Picker) 或下拉選單內部的容器背景顏色 */
        /* role="combobox" 是這些複雜元件的標準 ARIA 標籤 */
        div[role="combobox"] {
            background-color: white !important;
            border: none !important;
        }
                
        /* ==========================================
            3. 「開始計算」按鈕自定義視覺 (改為深灰色)
           ========================================== */

        /* 設定按鈕主體為純黑色背景、取消圓角邊框感，並將文字設為粗體 */
        div.stButton > button {
            background-color: #31333F !important;
            border: 1px solid #31333F !important;
            font-weight: bold !important;
        }
        
        /* 強制將按鈕內部所有的文字元素 (包含 Span) 設定為白色，避免被全域黑色覆蓋 */
        div.stButton > button * {
            color: #FFFFFF !important;
        }
        
        /* 定義滑鼠懸停 (Hover) 效果：將背景色由純黑調淺為深灰色 (#333333)，提供使用者操作回饋 */
        div.stButton > button:hover {
            background-color: #4F4F4F !important;
        }
        
        /* --- [新增] 亮色模式下的選項文字顏色 --- */
        div[data-testid="stRadio"] label p {
            color: #31333F !important; /* 將選項文字從純黑改為深灰色 */

        /* ==========================================
             4. 介面層次調整 (側邊欄邊框與文字強化)
           ========================================== */

        /* 在側邊欄右側加上一條極淡的灰色格線，幫助使用者區分操作區與圖表顯示區 */
        [data-testid="stSidebar"] { border-right: 1px solid #f0f2f6; }
                
        /* 確保所有 Input 文字內容在白色背景下依然維持黑色顯示，避免因主題切換產生的文字「消失」現象 */
        input { 
            color: black !important; 
            background-color: white !important; 
        }
        </style>
        """, unsafe_allow_html=True)

# ==============================================================================
# 4. 主程式執行邏輯
# ==============================================================================

st.title("📈 股價五線譜")

# 預先處理搜尋代號邏輯：補全台股後綴
search_id = f"{stock_id}.TW" if stock_id.isdigit() else stock_id


# --- 3. 判斷邏輯：如果按鈕「還沒被按下」 ---
if not calculate_btn:
    st.info("💡 請點開左上角選單 [ > ] 在左側面板設定參數後按「開始計算」即可產出圖表")
else:
    # --- A. 數據下載與清理 ---
    # 使用 auto_adjust=True 取得還原股價，反映真實報酬率
    data = yf.download(search_id, start=start_date, end=end_date, auto_adjust=True)
    
    if not data.empty:
        # 重設索引（reset_index）_將yfinance 下載後的原始資料，日期轉為可以被讀取的一般欄位後，建立數字序列（回歸必備），防止計算錯誤
        df = data.copy().reset_index()
        # 處理 yfinance 可能產生的多層欄位索引 (MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # 排除無交易資料的日期 (NaN)，確保計算精確度
        df = df.dropna(subset=['Close'])
        df['Close_1D'] = df['Close'].values.flatten()
        # 建立時間索引 (0, 1, 2...) 作為線性回歸的自變數 X
        df['Time_Idx'] = np.arange(len(df)) 
        
        # --- B. 核心原理：線性回歸與標準差軌道計算 ---
        if len(df) > 1:
            # 1. 線性回歸：找出股價的中長線趨勢中心
            # 公式為：$y = ax + b$ (a=斜率, b=截距)
            z = np.polyfit(df['Time_Idx'], df['Close_1D'], 1)
            p = np.poly1d(z)
            df['Trend_Line'] = p(df['Time_Idx']) # 產出回歸趨勢線數據
            
            # 2. 計算離差標準差 (Standard Deviation)：衡量股價對趨勢線的波動幅度
            # 標準差愈大，代表股價波動愈劇烈，軌道間距也會隨之拉大
            std_dev = (df['Close_1D'] - df['Trend_Line']).std()

            # 3. 建立五線譜軌道
            # 高點軌道：趨勢中線 + 1倍或2倍標準差
            # 低點軌道：趨勢中線 - 1倍或2倍標準差
            df['Upper_2'] = df['Trend_Line'] + 2 * std_dev # 極端樂觀線
            df['Upper_1'] = df['Trend_Line'] + 1 * std_dev # 樂觀線
            df['Lower_1'] = df['Trend_Line'] - 1 * std_dev # 悲觀線
            df['Lower_2'] = df['Trend_Line'] - 2 * std_dev # 極端悲觀線

            # --- C. 視覺化繪圖 (Plotly 互動式圖表) ---
            fig = go.Figure()
            
            # 設定收盤價曲線顏色，使其在不同背景下清晰可見
            line_color = "white" if theme_choice == "深色(深色背景)" else "black"
            fig.add_trace(go.Scatter(x=df['Date'], y=df['Close_1D'], name='收盤價', 
                                     line=dict(color=line_color, width=1.5)))
            
            # 定義各軌道線的顏色與名稱
            colors = ['#FF4136', '#FF851B', '#0074D9', '#2ECC40', '#3D9970']
            names = ['極端樂觀', '樂觀', '趨勢中線', '悲觀', '極端悲觀']
            bands = ['Upper_2', 'Upper_1', 'Trend_Line', 'Lower_1', 'Lower_2']
            
            for idx, band in enumerate(bands):
                # 趨勢中線使用實線，其餘 SD 軌道使用虛線以利區分
                fig.add_trace(go.Scatter(x=df['Date'], y=df[band], name=names[idx], 
                                         line=dict(dash='dash' if 'Trend' not in band else 'solid', 
                                                   color=colors[idx], width=1)))
            # 圖表版面優化
            fig.update_layout(
                height=600, 
                template=chart_template, 
                hovermode='x unified', # 統一滑鼠懸停資訊
                paper_bgcolor=bg_color,
                plot_bgcolor=bg_color,
                font=dict(color=font_color),
                xaxis=dict(color=font_color, tickfont=dict(color=font_color)),
                yaxis=dict(color=font_color, tickfont=dict(color=font_color)),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color=font_color))
            )
            st.plotly_chart(fig, use_container_width=True)

            # --- D. 數據摘要與投資評語 ---
            st.header("📊 數據摘要")
            last_price = df['Close_1D'].iloc[-1] # 最後一筆交易價格
            trend_val = df['Trend_Line'].iloc[-1] # 對應日期的趨勢線值
            # 計算目前股價落在幾倍標準差位置 ($\sigma$ 值)
            sigma = (last_price - trend_val) / std_dev
            
            # 儀表板數值呈現
            col1, col2, col3 = st.columns(3)
            col1.metric("最後收盤價", f"{last_price:.2f}")
            col2.metric("回歸中線", f"{trend_val:.2f}")
            col3.metric("目前區間", f"{sigma:.2f} σ")
            
            # 根據 $\sigma$ (Sigma) 值給予自動化投資評註
            if sigma > 2:
                st.error(f"⚠️ 目前價格極度高估（高於中線 {sigma:.2f} 個標準差）")
            elif sigma < -2:
                st.success(f"✅ 目前價格極度低估（低於中線 {abs(sigma):.2f} 個標準差）")
            else:
                st.info(f"💡 目前價格處於合理回歸區間內")
        else:
            st.warning("資料量不足以計算回歸線。")
    else:
        st.error("找不到資料，請檢查代號是否正確。")