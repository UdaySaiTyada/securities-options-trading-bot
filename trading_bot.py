import asyncio
import logging
from typing import Dict, List
from datetime import datetime
import pandas as pd

from models.market_data import MarketDataService
from strategies.technical_strategy import TechnicalStrategy
from strategies.options_strategy import OptionsStrategy
from risk_management import RiskManager
from config import (
    TRADING_SYMBOLS,
    TIMEFRAME,
    MAX_CONCURRENT_TRADES
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.market_data = MarketDataService()
        self.technical_strategy = TechnicalStrategy(self.market_data)
        self.options_strategy = OptionsStrategy(self.market_data)
        self.risk_manager = RiskManager()
        self.active_trades = {}
        self.portfolio_value = 0
        self.is_running = False
        
    async def start(self, initial_portfolio_value: float):
        """Start the trading bot"""
        self.is_running = True
        self.portfolio_value = initial_portfolio_value
        logger.info(f"Starting trading bot with portfolio value: {self.portfolio_value}")
        
        while self.is_running:
            try:
                await self.trading_loop()
                await asyncio.sleep(60)  # Check for opportunities every minute
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
                
    async def trading_loop(self):
        """Main trading loop"""
        for symbol in TRADING_SYMBOLS:
            if len(self.active_trades) >= MAX_CONCURRENT_TRADES:
                break
                
            # Analyze market conditions
            technical_analysis = await self.technical_strategy.analyze(symbol, TIMEFRAME)
            options_analysis = await self.options_strategy.analyze(symbol, TIMEFRAME)
            
            # Check for trading opportunities
            opportunities = self.identify_opportunities(
                technical_analysis,
                options_analysis
            )
            
            # Execute trades if opportunities found
            for opportunity in opportunities:
                if self.validate_opportunity(opportunity):
                    await self.execute_trade(opportunity)
                    
            # Monitor and manage existing positions
            await self.manage_positions()
            
    def identify_opportunities(self,
                             technical_analysis: Dict,
                             options_analysis: Dict) -> List[Dict]:
        """Identify trading opportunities based on analysis"""
        opportunities = []
        
        # Check technical signals
        if technical_analysis['signals']['entry'] != 'none':
            opportunities.append({
                'type': 'technical',
                'symbol': technical_analysis['symbol'],
                'direction': technical_analysis['signals']['entry'],
                'strength': technical_analysis['signals']['strength'],
                'analysis': technical_analysis
            })
            
        # Check options opportunities
        for strategy_type, strategy_opportunities in options_analysis.items():
            for opportunity in strategy_opportunities:
                if opportunity:  # If valid opportunity exists
                    opportunities.append({
                        'type': 'options',
                        'strategy': strategy_type,
                        'symbol': technical_analysis['symbol'],
                        'analysis': opportunity
                    })
                    
        return opportunities
        
    def validate_opportunity(self, opportunity: Dict) -> bool:
        """Validate if an opportunity meets all trading criteria"""
        # Check if we're already in a position for this symbol
        if opportunity['symbol'] in self.active_trades:
            return False
            
        # Validate based on opportunity type
        if opportunity['type'] == 'technical':
            return self.validate_technical_trade(opportunity)
        elif opportunity['type'] == 'options':
            return self.validate_options_trade(opportunity)
            
        return False
        
    def validate_technical_trade(self, opportunity: Dict) -> bool:
        """Validate technical analysis based trade"""
        analysis = opportunity['analysis']
        
        # Check signal strength
        if opportunity['strength'] != 'strong':
            return False
            
        # Check trend confirmation
        if analysis['signals']['trend']['overall'] != opportunity['direction']:
            return False
            
        # Validate through risk management
        trade_params = self.prepare_trade_parameters(opportunity)
        return self.risk_manager.validate_trade(
            trade_params,
            self.portfolio_value,
            self.active_trades
        )
        
    def validate_options_trade(self, opportunity: Dict) -> bool:
        """Validate options trade opportunity"""
        analysis = opportunity['analysis']
        
        # Implement options-specific validation logic
        # This would depend on the specific options strategy
        return True
        
    async def execute_trade(self, opportunity: Dict):
        """Execute a trade based on the opportunity"""
        try:
            # Prepare trade parameters
            trade_params = self.prepare_trade_parameters(opportunity)
            
            # Execute the trade
            if opportunity['type'] == 'technical':
                await self.execute_technical_trade(trade_params)
            elif opportunity['type'] == 'options':
                await self.execute_options_trade(trade_params)
                
            # Update portfolio and risk tracking
            self.active_trades[trade_params['symbol']] = trade_params
            self.risk_manager.update_position({
                'action': 'open',
                **trade_params
            })
            
            logger.info(f"Executed trade: {trade_params}")
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            
    def prepare_trade_parameters(self, opportunity: Dict) -> Dict:
        """Prepare parameters for trade execution"""
        symbol = opportunity['symbol']
        
        # Get current market data
        market_data = self.market_data.get_real_time_data(symbol)
        entry_price = market_data['last_price']
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            self.portfolio_value,
            entry_price,
            market_data['volatility']
        )
        
        # Calculate stop loss and take profit levels
        stop_loss = self.risk_manager.calculate_stop_loss(
            entry_price,
            opportunity['direction'],
            market_data['volatility']
        )
        
        take_profit = self.risk_manager.calculate_take_profit(
            entry_price,
            opportunity['direction'],
            market_data['volatility']
        )
        
        return {
            'symbol': symbol,
            'type': opportunity['type'],
            'direction': opportunity['direction'],
            'entry_price': entry_price,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'timestamp': datetime.now()
        }
        
    async def manage_positions(self):
        """Monitor and manage existing positions"""
        for symbol, position in list(self.active_trades.items()):
            try:
                current_price = (await self.market_data.get_real_time_data(symbol))['last_price']
                
                # Check stop loss and take profit levels
                if self.check_exit_conditions(position, current_price):
                    await self.close_position(position, current_price)
                    
            except Exception as e:
                logger.error(f"Error managing position {symbol}: {str(e)}")
                
    def check_exit_conditions(self, position: Dict, current_price: float) -> bool:
        """Check if position should be closed"""
        if position['direction'] == 'long':
            if current_price <= position['stop_loss'] or current_price >= position['take_profit']:
                return True
        else:  # Short position
            if current_price >= position['stop_loss'] or current_price <= position['take_profit']:
                return True
                
        return False
        
    async def close_position(self, position: Dict, current_price: float):
        """Close an open position"""
        try:
            # Execute closing trade
            if position['type'] == 'technical':
                await self.execute_technical_trade({
                    **position,
                    'action': 'close',
                    'exit_price': current_price
                })
            elif position['type'] == 'options':
                await self.execute_options_trade({
                    **position,
                    'action': 'close',
                    'exit_price': current_price
                })
                
            # Update tracking
            symbol = position['symbol']
            self.risk_manager.update_position({
                'action': 'close',
                'symbol': symbol
            })
            del self.active_trades[symbol]
            
            # Calculate and log P&L
            pnl = self.calculate_pnl(position, current_price)
            logger.info(f"Closed position {symbol} with P&L: {pnl}")
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            
    def calculate_pnl(self, position: Dict, exit_price: float) -> float:
        """Calculate P&L for a closed position"""
        if position['direction'] == 'long':
            return (exit_price - position['entry_price']) * position['position_size']
        else:  # Short position
            return (position['entry_price'] - exit_price) * position['position_size']
            
    async def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        logger.info("Stopping trading bot...")
        
        # Close all open positions
        for position in list(self.active_trades.values()):
            current_price = (await self.market_data.get_real_time_data(position['symbol']))['last_price']
            await self.close_position(position, current_price)
            
if __name__ == "__main__":
    # Example usage
    bot = TradingBot()
    initial_portfolio = 100000  # $100,000 initial portfolio
    
    try:
        asyncio.run(bot.start(initial_portfolio))
    except KeyboardInterrupt:
        asyncio.run(bot.stop())
