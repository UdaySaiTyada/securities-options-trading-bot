import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# Trading Parameters
TRADING_SYMBOLS = ['BTC/USDT', 'ETH/USDT']  # Add more trading pairs as needed
TIMEFRAME = '1h'  # Trading timeframe
POSITION_SIZE = 0.1  # Position size in percentage of portfolio

# Risk Management
MAX_POSITION_SIZE = 0.2  # Maximum position size per trade
STOP_LOSS_PERCENTAGE = 0.02  # 2% stop loss
TAKE_PROFIT_PERCENTAGE = 0.04  # 4% take profit

# Performance Optimization
CACHE_TIMEOUT = 300  # Cache timeout in seconds
MAX_CONCURRENT_TRADES = 5
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Technical Analysis Parameters
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
EMA_SHORT = 9
EMA_LONG = 21
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
