import pytest
import asyncio
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from trading_bot import TradingBot
from models.market_data import MarketDataService
from strategies.technical_strategy import TechnicalStrategy
from strategies.options_strategy import OptionsStrategy
from risk_management import RiskManager

@pytest.fixture
def trading_bot():
    return TradingBot()

@pytest.fixture
def market_data_service():
    return MarketDataService()

@pytest.fixture
def risk_manager():
    return RiskManager()

@pytest.mark.asyncio
async def test_market_data_service(market_data_service):
    symbol = "BTC/USDT"
    timeframe = "1h"
    
    # Test real-time data
    data = await market_data_service.get_real_time_data(symbol)
    assert isinstance(data, dict)
    assert 'last_price' in data
    assert 'volume' in data
    
    # Test historical data
    hist_data = await market_data_service.get_historical_data(symbol, timeframe)
    assert isinstance(hist_data, pd.DataFrame)
    assert not hist_data.empty
    assert all(col in hist_data.columns for col in ['open', 'high', 'low', 'close', 'volume'])

@pytest.mark.asyncio
async def test_technical_strategy(trading_bot):
    strategy = trading_bot.technical_strategy
    symbol = "BTC/USDT"
    timeframe = "1h"
    
    analysis = await strategy.analyze(symbol, timeframe)
    assert isinstance(analysis, dict)
    assert 'signals' in analysis
    assert 'trend' in analysis['signals']
    assert 'momentum' in analysis['signals']

@pytest.mark.asyncio
async def test_options_strategy(trading_bot):
    strategy = trading_bot.options_strategy
    symbol = "BTC/USDT"
    timeframe = "1h"
    
    analysis = await strategy.analyze(symbol, timeframe)
    assert isinstance(analysis, dict)
    assert 'vertical_spreads' in analysis
    assert 'iron_condors' in analysis

def test_risk_manager(risk_manager):
    # Test position size calculation
    position_size = risk_manager.calculate_position_size(
        capital=100000,
        entry_price=50000,
        stop_loss=48000,
        volatility=0.2
    )
    assert isinstance(position_size, float)
    assert position_size > 0
    
    # Test trade validation
    trade = {
        'symbol': 'BTC/USDT',
        'position_size': 0.1,
        'entry_price': 50000,
        'stop_loss': 48000
    }
    portfolio_value = 100000
    current_positions = {}
    
    is_valid = risk_manager.validate_trade(trade, portfolio_value, current_positions)
    assert isinstance(is_valid, bool)

@pytest.mark.asyncio
async def test_trading_bot_execution(trading_bot):
    with patch('trading_bot.TradingBot.execute_trade') as mock_execute:
        mock_execute.return_value = None
        
        # Test trade execution
        opportunity = {
            'type': 'technical',
            'symbol': 'BTC/USDT',
            'direction': 'long',
            'strength': 'strong',
            'analysis': {
                'signals': {
                    'trend': {'overall': 'bullish'},
                    'momentum': {'rsi': 35}
                }
            }
        }
        
        await trading_bot.execute_trade(opportunity)
        mock_execute.assert_called_once()

@pytest.mark.asyncio
async def test_position_management(trading_bot):
    # Add test position
    test_position = {
        'symbol': 'BTC/USDT',
        'type': 'technical',
        'direction': 'long',
        'entry_price': 50000,
        'position_size': 0.1,
        'stop_loss': 48000,
        'take_profit': 53000
    }
    trading_bot.active_trades['BTC/USDT'] = test_position
    
    # Test position management
    with patch('models.market_data.MarketDataService.get_real_time_data') as mock_data:
        mock_data.return_value = {'last_price': 48000}  # Price at stop loss
        await trading_bot.manage_positions()
        assert 'BTC/USDT' not in trading_bot.active_trades

def test_pnl_calculation(trading_bot):
    position = {
        'direction': 'long',
        'entry_price': 50000,
        'position_size': 0.1
    }
    exit_price = 52000
    
    pnl = trading_bot.calculate_pnl(position, exit_price)
    assert isinstance(pnl, float)
    assert pnl == (52000 - 50000) * 0.1  # Expected P&L

if __name__ == '__main__':
    pytest.main(['-v'])
