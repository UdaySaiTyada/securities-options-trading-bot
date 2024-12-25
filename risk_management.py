from typing import Dict, List
import pandas as pd
import numpy as np
from config import MAX_POSITION_SIZE, STOP_LOSS_PERCENTAGE, TAKE_PROFIT_PERCENTAGE

class RiskManager:
    def __init__(self):
        self.positions = {}
        self.total_risk = 0
        self.max_risk_per_trade = 0.02  # 2% max risk per trade
        self.max_total_risk = 0.06  # 6% max total portfolio risk
        
    def calculate_position_size(self, 
                              capital: float,
                              entry_price: float,
                              stop_loss: float,
                              volatility: float) -> float:
        """Calculate appropriate position size based on risk parameters"""
        risk_amount = capital * self.max_risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        position_size = risk_amount / price_risk
        
        # Adjust for volatility
        if volatility > 0.3:  # High volatility
            position_size *= 0.7
        
        # Ensure position size doesn't exceed maximum
        max_position = capital * MAX_POSITION_SIZE
        return min(position_size, max_position)
        
    def validate_trade(self, 
                      trade: Dict,
                      portfolio_value: float,
                      current_positions: Dict) -> bool:
        """Validate if a trade meets risk management criteria"""
        # Check if total risk is within limits
        if self.total_risk + self.calculate_trade_risk(trade) > self.max_total_risk:
            return False
            
        # Check position correlation
        if not self.check_position_correlation(trade, current_positions):
            return False
            
        # Check maximum exposure per asset
        if not self.check_max_exposure(trade, portfolio_value):
            return False
            
        return True
        
    def calculate_trade_risk(self, trade: Dict) -> float:
        """Calculate risk for a specific trade"""
        entry = trade['entry_price']
        stop_loss = trade['stop_loss']
        position_size = trade['position_size']
        
        return abs((entry - stop_loss) / entry) * position_size
        
    def check_position_correlation(self, 
                                 new_trade: Dict,
                                 current_positions: Dict) -> bool:
        """Check if new trade is not too correlated with existing positions"""
        # Implement correlation check logic
        correlated_exposure = 0
        
        for position in current_positions.values():
            if self.are_correlated(new_trade['symbol'], position['symbol']):
                correlated_exposure += position['position_size']
                
        return correlated_exposure < 0.15  # Max 15% exposure to correlated assets
        
    def are_correlated(self, symbol1: str, symbol2: str) -> bool:
        """Check if two symbols are correlated"""
        # Implement correlation calculation logic
        # This would typically involve checking historical price correlation
        # For now, return a simple check
        return symbol1.split('/')[0] == symbol2.split('/')[0]
        
    def check_max_exposure(self, 
                          trade: Dict,
                          portfolio_value: float) -> bool:
        """Check if trade exceeds maximum exposure limits"""
        total_exposure = trade['position_size']
        
        # Add exposure from existing positions in the same asset
        for position in self.positions.values():
            if position['symbol'] == trade['symbol']:
                total_exposure += position['position_size']
                
        return total_exposure <= MAX_POSITION_SIZE
        
    def calculate_stop_loss(self,
                          entry_price: float,
                          direction: str,
                          volatility: float) -> float:
        """Calculate adaptive stop loss based on volatility"""
        base_stop = STOP_LOSS_PERCENTAGE
        
        # Adjust stop loss based on volatility
        if volatility > 0.3:  # High volatility
            base_stop *= 1.5
        elif volatility < 0.1:  # Low volatility
            base_stop *= 0.8
            
        if direction == 'long':
            return entry_price * (1 - base_stop)
        else:
            return entry_price * (1 + base_stop)
            
    def calculate_take_profit(self,
                            entry_price: float,
                            direction: str,
                            volatility: float) -> float:
        """Calculate adaptive take profit based on volatility"""
        base_tp = TAKE_PROFIT_PERCENTAGE
        
        # Adjust take profit based on volatility
        if volatility > 0.3:  # High volatility
            base_tp *= 1.3
        elif volatility < 0.1:  # Low volatility
            base_tp *= 0.9
            
        if direction == 'long':
            return entry_price * (1 + base_tp)
        else:
            return entry_price * (1 - base_tp)
            
    def update_position(self, trade_result: Dict):
        """Update position tracking after trade execution"""
        symbol = trade_result['symbol']
        
        if trade_result['action'] == 'open':
            self.positions[symbol] = trade_result
            self.total_risk += self.calculate_trade_risk(trade_result)
        elif trade_result['action'] == 'close':
            if symbol in self.positions:
                self.total_risk -= self.calculate_trade_risk(self.positions[symbol])
                del self.positions[symbol]
                
    def get_portfolio_stats(self) -> Dict:
        """Get current portfolio risk statistics"""
        return {
            'total_positions': len(self.positions),
            'total_risk': self.total_risk,
            'risk_capacity': self.max_total_risk - self.total_risk,
            'positions': self.positions
        }
