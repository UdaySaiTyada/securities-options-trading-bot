import pandas as pd
import numpy as np
from typing import Dict, List
from .base_strategy import BaseStrategy
from models.market_data import MarketDataService
import talib

class TechnicalStrategy(BaseStrategy):
    def __init__(self, market_data_service: MarketDataService):
        super().__init__(market_data_service)
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.ema_short = 9
        self.ema_long = 21
        
    async def analyze(self, symbol: str, timeframe: str) -> Dict:
        """Analyze market data using technical indicators"""
        data = await self.market_data.get_historical_data(symbol, timeframe)
        signals = await self.generate_signals(data)
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'signals': signals,
            'timestamp': pd.Timestamp.now()
        }
        
    async def generate_signals(self, data: pd.DataFrame) -> Dict:
        """Generate trading signals based on technical analysis"""
        signals = {}
        
        # Calculate technical indicators
        data['rsi'] = talib.RSI(data['close'], timeperiod=self.rsi_period)
        data['ema_short'] = talib.EMA(data['close'], timeperiod=self.ema_short)
        data['ema_long'] = talib.EMA(data['close'], timeperiod=self.ema_long)
        data['macd'], data['macd_signal'], data['macd_hist'] = talib.MACD(
            data['close'],
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )
        data['atr'] = talib.ATR(
            data['high'],
            data['low'],
            data['close'],
            timeperiod=14
        )
        
        # Generate signals
        signals['trend'] = self.analyze_trend(data)
        signals['momentum'] = self.analyze_momentum(data)
        signals['volatility'] = self.analyze_volatility(data)
        signals['support_resistance'] = self.find_support_resistance(data)
        signals['entry_points'] = self.find_entry_points(data)
        
        return signals
        
    def analyze_trend(self, data: pd.DataFrame) -> Dict:
        """Analyze price trend using multiple indicators"""
        last_row = data.iloc[-1]
        trend = {
            'ema_trend': 'bullish' if last_row['ema_short'] > last_row['ema_long'] else 'bearish',
            'macd_trend': 'bullish' if last_row['macd'] > last_row['macd_signal'] else 'bearish',
            'strength': abs(last_row['macd'] - last_row['macd_signal'])
        }
        
        # Determine overall trend
        bullish_signals = sum(1 for v in trend.values() if v == 'bullish')
        trend['overall'] = 'bullish' if bullish_signals > len(trend) / 2 else 'bearish'
        
        return trend
        
    def analyze_momentum(self, data: pd.DataFrame) -> Dict:
        """Analyze momentum indicators"""
        last_row = data.iloc[-1]
        return {
            'rsi': last_row['rsi'],
            'rsi_signal': 'oversold' if last_row['rsi'] < self.rsi_oversold else
                         'overbought' if last_row['rsi'] > self.rsi_overbought else 'neutral',
            'macd_histogram': last_row['macd_hist']
        }
        
    def analyze_volatility(self, data: pd.DataFrame) -> Dict:
        """Analyze market volatility"""
        recent_atr = data['atr'].iloc[-5:]
        return {
            'current_atr': data['atr'].iloc[-1],
            'atr_trend': 'increasing' if recent_atr.is_monotonic_increasing else
                        'decreasing' if recent_atr.is_monotonic_decreasing else 'neutral',
            'volatility_level': self.categorize_volatility(data['atr'].iloc[-1])
        }
        
    def find_support_resistance(self, data: pd.DataFrame) -> Dict:
        """Find support and resistance levels"""
        # Calculate pivot points
        pivot = (data['high'].iloc[-1] + data['low'].iloc[-1] + data['close'].iloc[-1]) / 3
        r1 = 2 * pivot - data['low'].iloc[-1]
        s1 = 2 * pivot - data['high'].iloc[-1]
        
        return {
            'pivot': pivot,
            'resistance1': r1,
            'support1': s1
        }
        
    def find_entry_points(self, data: pd.DataFrame) -> Dict:
        """Identify potential entry points"""
        last_row = data.iloc[-1]
        signals = {}
        
        # Check for trend confirmation
        trend_confirmed = (
            last_row['ema_short'] > last_row['ema_long'] and
            last_row['macd'] > last_row['macd_signal']
        )
        
        # Check for momentum confirmation
        momentum_confirmed = (
            last_row['rsi'] < self.rsi_oversold or
            last_row['rsi'] > self.rsi_overbought
        )
        
        if trend_confirmed and momentum_confirmed:
            signals['entry'] = 'long' if last_row['ema_short'] > last_row['ema_long'] else 'short'
            signals['strength'] = 'strong'
        else:
            signals['entry'] = 'none'
            signals['strength'] = 'weak'
            
        return signals
        
    def categorize_volatility(self, atr: float) -> str:
        """Categorize volatility level"""
        if atr < 0.5:
            return 'low'
        elif atr < 1.5:
            return 'medium'
        else:
            return 'high'
            
    def set_stop_loss(self, entry_price: float, direction: str) -> float:
        """Calculate stop loss level based on ATR"""
        atr = self.data['atr'].iloc[-1]
        if direction == 'long':
            return entry_price - (2 * atr)
        else:
            return entry_price + (2 * atr)
            
    def set_take_profit(self, entry_price: float, direction: str) -> float:
        """Calculate take profit level based on risk-reward ratio"""
        atr = self.data['atr'].iloc[-1]
        if direction == 'long':
            return entry_price + (3 * atr)  # 1:1.5 risk-reward ratio
        else:
            return entry_price - (3 * atr)
