import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import time 
import json
from datetime import datetime


# Hardcoded usernames and passwords
USER_DATA_FILE = "user_data.json"
st.set_page_config(layout="wide")

def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is empty or invalid JSON, return an empty dictionary
        return {}
def login(username, password):
    user_data = load_user_data()
    if username in user_data and user_data[username] == password:
        st.sidebar.success("Logged in as {}".format(username))
        return True
    else:
        return False

# Initialize session state
if "login_attempted" not in st.session_state:
    st.session_state.login_attempted = False

# Sidebar widgets
st.sidebar.title("Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_button = st.sidebar.button("Login")

# Check if the login button is clicked
if login_button:
    # Mark login attempt as made
    st.session_state.login_attempted = True
    
    # Call login function with username and password
    login_successful = login(username, password)
    
    # If login attempt failed, show error message
    if not login_successful:
        st.sidebar.error("Invalid username or password")

# Function to fetch intraday data for multiple stocks
def fetch_intraday_data(symbols):
    data = {}
    for symbol in symbols:
        try:
            data[symbol] = yf.download(symbol, period="1d", interval="5m")
        except Exception as e:
            st.error(f"Failed to fetch data for {symbol}: {e}")
    return data

# Function to find candles where open price equals low, close price equals high, and open is at least 50% of the candle size
def find_equal_open_low_close_high_candles(data):
    equal_candles = {}
    for symbol, stock_data in data.items():
        candle_size = stock_data['High'] - stock_data['Low']
        equal_candles[symbol] = stock_data[(stock_data['Open'] == stock_data['Low']) & 
                                           (stock_data['Close'] == stock_data['High']) &
                                           (stock_data['Open'] >= stock_data['Low'] + 0.5 * candle_size)]
    return equal_candles


def main():

    st.title('Intraday Stock Analysis')
     # Notepad feature
    st.sidebar.title("Notepad")
    user_text = st.sidebar.text_area("Notepad to Write:")
    save_button = st.sidebar.button("Save Notes")

    if save_button:
        # Prompt user to download the notes as a text file
        user_notes_filename = f"user_notes_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        st.sidebar.markdown(f'<a href="data:text/plain;charset=utf-8,{user_text}" download="{user_notes_filename}">Click here to download your notes</a>', unsafe_allow_html=True)
        st.sidebar.success("Notes saved successfully!") 
 # Define the custom lists of stocks with their names
    groups = {
        
        'SENSEX30':["HDFCBANK.NS", "RELIANCE.NS", "ICICIBANK.NS", "INFY.NS", "LT.NS", "TCS.NS", "ITC.NS",
            "BHARTIARTL.NS", "AXISBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "HDFC.NS", "M&M.NS", 
            "BAJFINANCE.NS", "TATAMOTORS.NS", "NTPC.NS", "MARUTI.NS", "SUNPHARMA.NS", 
            "TITAN.NS", "HCLTECH.NS", "POWERGRID.NS", "TATASTEEL.NS", "ASIANPAINT.NS", 
            "ULTRACEMCO.NS", "INDUSINDBK.NS", "NESTLEIND.NS", "JSWSTEEL.NS", "TECHM.NS", 
            "BAJAJFINSV.NS", "WIPRO.NS"],
        'INDICES' : ["^NSEI", "^NSEBANK", "^NSEFINNIFTY", "^CNXAUTO", "^NSEMETAL", "^NSEIT", "^NSEPHARMA", "^NSEFMCG"],
        # Add more groups as needed
    }

    selected_groups = st.multiselect('*CANDLE UPDATE AT EVERY 5 MINS & ONLY INTRADAY CANDLE SO AS TO COMPARE STRENGTH & WEAKNESS WITH EACH OTHER*', list(groups.keys()))

    selected_symbols = []
    for group_name in selected_groups:
        selected_symbols += groups[group_name]

    while True:
        data = fetch_intraday_data(selected_symbols)
        equal_candles = find_equal_open_low_close_high_candles(data)


        st.write("Last Updated:", time.strftime('%Y-%m-%d %H:%M:%S'))

        num_columns = 3
        symbol_chunks = [selected_symbols[i:i + num_columns] for i in range(0, len(selected_symbols), num_columns)]
        
        for symbol_chunk in symbol_chunks:
            col1, col2, col3 = st.columns(num_columns)
            for symbol in symbol_chunk:
                stock_data = data[symbol]
                equal_candle_data = equal_candles[symbol]
          
                # Create candlestick trace
                candlestick = go.Candlestick(x=stock_data.index,
                                             open=stock_data['Open'],
                                             high=stock_data['High'],
                                             low=stock_data['Low'],
                                             close=stock_data['Close'],
                                             name="Candlestick")
                
                # Create highlighted candles trace
                highlight_candles = go.Scatter(x=equal_candle_data.index,
                                               y=equal_candle_data['High'],
                                               mode='markers',
                                               marker=dict(color='red', size=8),
                                               name="Highlighted Candles")
                
                # Create layout
                 # Create layout
                layout = go.Layout(title=f'Candlestick Chart with Highlights for {symbol}',
                                   xaxis=dict(title='Date', rangeslider=dict(visible=False)),
                                   yaxis=dict(title='Price'))
                
                
                # Create figure
                fig = go.Figure(data=[candlestick, highlight_candles], layout=layout)

                # Display the plot in the appropriate column
                if symbol == symbol_chunk[0]:
                    with col1:
                        st.plotly_chart(fig, use_container_width=True)
                elif symbol == symbol_chunk[1]:
                    with col2:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    with col3:
                        st.plotly_chart(fig, use_container_width=True)
        
        time.sleep(300)  # Wait for 5 minutes before refreshing the data



        # JavaScript to trigger auto-refresh
st.markdown("""
        <script>
            setTimeout(function() {
                document.querySelector(".stButton>button").click();
            }, 300000); // 5 minutes
        </script>
        """, unsafe_allow_html=True)

# Check if the user is logged in or not
def is_user_logged_in():
    return 'logged_in' in st.session_state

    # Initialize session state if not already initialized
if not is_user_logged_in():
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    if login(username, password):
        st.session_state.logged_in = True

if st.session_state.logged_in:
        main()
