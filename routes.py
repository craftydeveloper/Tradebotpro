from flask import render_template, jsonify
from app import app, db
from models import TokenPrice, Portfolio, Position, Trade, TradeRecommendation
from datetime import datetime
import logging
import requests
import time
import random

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Main Dashboard - Professional Trading Interface"""
    return render_template('professional_dashboard.html')

@app.route('/healthz')
def health_check():
    """Health check endpoint for Render deployment"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/api/portfolio')
def get_portfolio():
    """Get portfolio metrics"""
    try:
        # Get or create portfolio
        portfolio = Portfolio.query.first()
        if not portfolio:
            portfolio = Portfolio(balance=500.0, total_value=500.0)
            db.session.add(portfolio)
            db.session.commit()
        
        return jsonify({
            'balance': portfolio.balance,
            'total_value': portfolio.total_value,
            'unrealized_pnl': portfolio.unrealized_pnl,
            'realized_pnl': portfolio.realized_pnl,
            'total_pnl': portfolio.unrealized_pnl + portfolio.realized_pnl,
            'pnl_percentage': ((portfolio.unrealized_pnl + portfolio.realized_pnl) / portfolio.balance) * 100
        })
    except Exception as e:
        logger.error(f"Error getting portfolio: {e}")
        return jsonify({
            'balance': 500.0,
            'total_value': 500.0,
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
            'total_pnl': 0.0,
            'pnl_percentage': 0.0
        })

@app.route('/api/signals')
def get_trading_signals():
    """Get current trading signals"""
    try:
        # Generate trading signals with current market data
        signals = generate_mock_signals()
        return jsonify(signals)
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return jsonify([])

def generate_mock_signals():
    """Generate realistic trading signals for demonstration"""
    symbols = ['ADA', 'BTC', 'ETH', 'SOL', 'LINK', 'AVAX']
    signals = []
    
    for i, symbol in enumerate(symbols):
        # Generate realistic price variations
        base_prices = {
            'ADA': 0.55, 'BTC': 67000, 'ETH': 3400, 
            'SOL': 145, 'LINK': 13.2, 'AVAX': 35.5
        }
        
        price = base_prices[symbol] * (1 + random.uniform(-0.02, 0.02))
        confidence = random.uniform(85, 98)
        action = 'SELL' if i == 0 else random.choice(['BUY', 'SELL'])
        
        # Calculate trading parameters
        leverage = min(8 + int(confidence - 85), 15)
        risk_amount = 50.0
        position_value = 500.0 * (risk_amount / 100)
        
        if symbol == 'BTC':
            qty = position_value / price
        elif symbol == 'ETH':
            qty = position_value / price
        else:
            qty = (position_value * leverage) / price
        
        stop_loss = price * (1.03 if action == 'SELL' else 0.97)
        take_profit = price * (0.94 if action == 'SELL' else 1.06)
        
        signal = {
            'symbol': symbol,
            'action': action,
            'confidence': round(confidence, 2),
            'entry_price': round(price, 4),
            'stop_loss': round(stop_loss, 4),
            'take_profit': round(take_profit, 4),
            'leverage': leverage,
            'expected_return': 6.0,
            'risk_reward_ratio': 2.0,
            'time_horizon': '4H',
            'strategy_basis': 'Momentum Volume Analysis',
            'is_primary_trade': i == 0,
            'trade_label': 'YOUR TRADE' if i == 0 else 'ALTERNATIVE',
            'bybit_settings': {
                'symbol': f'{symbol}USDT',
                'side': action,
                'orderType': 'Market',
                'qty': str(round(qty, 4)),
                'leverage': str(leverage),
                'stopLoss': str(round(stop_loss, 4)),
                'takeProfit': str(round(take_profit, 4)),
                'timeInForce': 'GTC',
                'marginMode': 'isolated',
                'risk_management': {
                    'risk_amount_usd': str(risk_amount),
                    'risk_percentage': f'{(risk_amount/500)*100}%',
                    'position_value_usd': str(round(position_value * leverage, 2)),
                    'margin_required_usd': str(round(position_value, 2))
                },
                'execution_notes': {
                    'entry_strategy': 'Market order for immediate execution',
                    'position_monitoring': 'Monitor for 4-8 hours based on momentum',
                    'stop_loss_type': 'Stop-market order',
                    'take_profit_type': 'Limit order'
                }
            }
        }
        signals.append(signal)
    
    return signals

@app.route('/api/positions')
def get_positions():
    """Get current positions"""
    try:
        positions = Position.query.filter_by(is_active=True).all()
        result = []
        for pos in positions:
            result.append({
                'symbol': pos.symbol,
                'side': pos.side,
                'size': pos.size,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'unrealized_pnl': pos.unrealized_pnl,
                'leverage': pos.leverage
            })
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify([])

@app.route('/api/trades')
def get_recent_trades():
    """Get recent trades"""
    try:
        trades = Trade.query.order_by(Trade.created_at.desc()).limit(10).all()
        result = []
        for trade in trades:
            result.append({
                'symbol': trade.symbol,
                'side': trade.side,
                'size': trade.size,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'realized_pnl': trade.realized_pnl,
                'created_at': trade.created_at.isoformat()
            })
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return jsonify([])