from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from models.market_data import MarketDataService

class BaseStrategy(ABC):
    def __init__(self, market_data_service: MarketDataService):
        self.market_data = market_data_service
        self.positions = {}
        
    @abstractmethod
    async def analyze(self, symbol: str, timeframe: str) -> Dict:
        """Analyze market data and generate trading signals"""
        pass
        
    @abstractmethod
    async def generate_signals(self, data: pd.DataFrame) -> Dict:
        """Generate trading signals based on strategy logic"""
        pass
        
    def calculate_position_size(self, capital: float, risk_per_trade: float) -> float:
        """Calculate position size based on risk management rules"""
        return capital * risk_per_trade
        
    def validate_trade(self, signal: Dict, current_positions: Dict) -> bool:
        """Validate if a trade should be executed based on current positions and risk"""
        # Implement trade validation logic
        pass
        
    def calculate_risk_reward(self, entry: float, stop_loss: float, take_profit: float) -> float:
        """Calculate risk-reward ratio for a potential trade"""
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        return reward / risk if risk != 0 else 0
        
    @abstractmethod
    def set_stop_loss(self, entry_price: float, direction: str) -> float:
        """Calculate stop loss level"""
        pass
        
    @abstractmethod
    def set_take_profit(self, entry_price: float, direction: str) -> float:
        """Calculate take profit level"""
        pass
        
    def update_positions(self, trade_result: Dict):
        """Update current positions after trade execution"""
        symbol = trade_result['symbol']
        if trade_result['action'] == 'buy':
            self.positions[symbol] = trade_result
        elif trade_result['action'] == 'sell':
            self.positions.pop(symbol, None)
            
    def get_position_status(self, symbol: str) -> Optional[Dict]:
        """Get current position status for a symbol"""
        return self.positions.get(symbol)
