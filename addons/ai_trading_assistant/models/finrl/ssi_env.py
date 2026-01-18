# -*- coding: utf-8 -*-
"""
SSI Stock Trading Environment for FinRL

Custom Gymnasium environment for Vietnamese stock trading
via SSI FastConnect API.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union

import numpy as np

from .constants import (
    ACTION_SPACE_TYPES,
    ENV_PARAMS,
    REWARD_SCALING,
)

_logger = logging.getLogger(__name__)

# Gymnasium import with fallback
try:
    import gymnasium as gym
    from gymnasium import spaces
    GYM_AVAILABLE = True
except ImportError:
    try:
        import gym
        from gym import spaces
        GYM_AVAILABLE = True
        _logger.warning('Using legacy gym instead of gymnasium')
    except ImportError:
        GYM_AVAILABLE = False
        gym = None
        spaces = None
        _logger.error('Neither gymnasium nor gym is installed')


class SSIStockTradingEnv(gym.Env):
    """
    Custom Gymnasium environment for SSI Vietnamese stock trading.
    
    Supports both single-stock and portfolio trading modes.
    
    Observation Space:
        - OHLCV data and technical indicators
        - Portfolio state (balance, holdings, etc.)
    
    Action Space:
        - Discrete: [0=Sell, 1=Hold, 2=Buy]
        - Continuous: Position sizing [-1, 1]
    
    Reward:
        - Portfolio return with risk-adjusted bonuses/penalties
    """
    
    def __init__(
        self,
        data: np.ndarray,
        feature_names: List[str],
        symbols: List[str],
        prices: np.ndarray,
        action_space_type: str = 'discrete',
        initial_balance: Optional[float] = None,
        buy_cost_pct: Optional[float] = None,
        sell_cost_pct: Optional[float] = None,
        tax_sell_pct: Optional[float] = None,
        lot_size: Optional[int] = None,
        max_shares_per_trade: Optional[int] = None,
        reward_scaling: Optional[float] = None,
        normalize_reward: bool = True,
        slippage_max_pct: Optional[float] = None,
    ):
        """
        Initialize the SSI trading environment.
        
        Args:
            data: Feature array of shape (n_timesteps, n_features)
            feature_names: List of feature column names
            symbols: List of stock symbols being traded
            prices: Price array of shape (n_timesteps,) or (n_timesteps, n_symbols)
            action_space_type: 'discrete' or 'continuous'
            initial_balance: Starting cash balance (VND)
            buy_cost_pct: Buy commission percentage
            sell_cost_pct: Sell commission percentage
            tax_sell_pct: Selling tax percentage
            lot_size: Vietnamese stock lot size (usually 100)
            max_shares_per_trade: Maximum shares per single trade
            reward_scaling: Scaling factor for rewards
            normalize_reward: Whether to normalize rewards
        """
        if not GYM_AVAILABLE:
            raise ImportError('gymnasium or gym is required for SSIStockTradingEnv')
        
        # Validate inputs
        if len(data) == 0:
            raise ValueError('Data array cannot be empty')
        if len(prices) != len(data):
            raise ValueError('Prices and data must have same length')
        
        # Store data
        self.data = data
        self.feature_names = feature_names
        self.symbols = symbols if isinstance(symbols, list) else [symbols]
        self.prices = prices if prices.ndim > 1 else prices.reshape(-1, 1)
        self.n_symbols = len(self.symbols)
        
        # Environment parameters (use defaults from constants if not provided)
        env_defaults = ENV_PARAMS
        self.initial_balance = initial_balance or env_defaults['initial_balance']
        self.buy_cost_pct = buy_cost_pct or env_defaults['buy_cost_pct']
        self.sell_cost_pct = sell_cost_pct or env_defaults['sell_cost_pct']
        self.tax_sell_pct = tax_sell_pct or env_defaults['tax_sell_pct']
        self.lot_size = lot_size or env_defaults['lot_size']
        self.max_shares_per_trade = max_shares_per_trade or env_defaults['max_shares_per_trade']
        self.reward_scaling = reward_scaling or env_defaults['reward_scaling']
        self.normalize_reward = normalize_reward
        self.slippage_max_pct = slippage_max_pct or env_defaults.get('slippage_max_pct', 0.001)
        
        # Action space configuration
        self.action_space_type = action_space_type
        self._setup_action_space()
        
        # Observation space
        self._setup_observation_space()
        
        # Initialize state
        self._reset_state()
    
    
    def _setup_action_space(self) -> None:
        """Setup the action space based on configuration."""
        action_config = ACTION_SPACE_TYPES.get(self.action_space_type)
        if action_config is None:
            raise ValueError(f'Unknown action space type: {self.action_space_type}')
        
        if self.action_space_type == 'discrete':
            # For multiple symbols: n_actions^n_symbols combinations
            # For simplicity, use n_actions per symbol independently
            n_actions = action_config['n_actions']
            if self.n_symbols == 1:
                self.action_space = spaces.Discrete(n_actions)
            else:
                self.action_space = spaces.MultiDiscrete([n_actions] * self.n_symbols)
            self.action_mapping = action_config['action_mapping']
        else:
            # Continuous: position sizing from -1 to 1 for each symbol
            # We use float32 to ensure compatibility with SB3
            low = np.full(self.n_symbols, action_config['low'], dtype=np.float32)
            high = np.full(self.n_symbols, action_config['high'], dtype=np.float32)
            self.action_space = spaces.Box(low=low, high=high, dtype=np.float32)

    
    def _setup_observation_space(self) -> None:
        """Setup the observation space."""
        # Features from data + portfolio state
        n_features = self.data.shape[1]
        n_portfolio = 1 + self.n_symbols  # balance + shares for each symbol
        
        total_features = n_features + n_portfolio
        
        # All features normalized to [0, 1] or similar range
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(total_features,),
            dtype=np.float32,
        )
    
    def _reset_state(self) -> None:
        """Reset the environment state."""
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares = np.zeros(self.n_symbols, dtype=np.float32)
        self.cost_basis = np.zeros(self.n_symbols, dtype=np.float32)
        
        # Tracking
        self.portfolio_values = [self.initial_balance]
        self.trades = []
        self.done = False
    
    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict] = None,
    ) -> Tuple[np.ndarray, Dict]:
        """
        Reset the environment to initial state.
        
        Args:
            seed: Random seed for reproducibility
            options: Additional options (unused)
        
        Returns:
            Tuple of (observation, info)
        """
        if seed is not None:
            np.random.seed(seed)
        
        self._reset_state()
        
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, info
    
    def step(self, action: Union[int, np.ndarray]) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one step in the environment.
        
        Args:
            action: Action to take (discrete index or continuous array)
        
        Returns:
            Tuple of (observation, reward, terminated, truncated, info)
        """
        if self.done:
            raise RuntimeError('Environment is done. Call reset() first.')
        
        # Get current prices
        current_prices = self.prices[self.current_step]
        
        # Record portfolio value before action
        prev_portfolio_value = self._get_portfolio_value(current_prices)
        
        # Execute action
        self._execute_action(action, current_prices)
        
        # Move to next step
        self.current_step += 1
        
        # Check if done
        terminated = self.current_step >= len(self.data) - 1
        truncated = False
        
        # Get new prices and portfolio value
        if not terminated:
            new_prices = self.prices[self.current_step]
            new_portfolio_value = self._get_portfolio_value(new_prices)
        else:
            new_portfolio_value = self._get_portfolio_value(current_prices)
            self.done = True
        
        # Calculate reward
        reward = self._calculate_reward(prev_portfolio_value, new_portfolio_value)
        
        # Record portfolio value
        self.portfolio_values.append(new_portfolio_value)
        
        # Get observation and info
        obs = self._get_observation()
        info = self._get_info()
        
        return obs, reward, terminated, truncated, info
    
    def _execute_action(self, action: Union[int, np.ndarray], prices: np.ndarray) -> None:
        """
        Execute the trading action.
        
        Args:
            action: Action to execute
            prices: Current prices for each symbol
        """
        if self.action_space_type == 'discrete':
            self._execute_discrete_action(action, prices)
        else:
            self._execute_continuous_action(action, prices)
    
    def _execute_discrete_action(
        self,
        action: Union[int, np.ndarray],
        prices: np.ndarray,
    ) -> None:
        """Execute discrete action (Buy/Hold/Sell)."""
        if self.n_symbols == 1:
            actions = [action]
        else:
            actions = action
        
        for i, act in enumerate(actions):
            # Ensure act is a scalar (int) for dictionary lookup
            if hasattr(act, 'item'):
                act = act.item()
            action_name = self.action_mapping.get(int(act), 'hold')
            price = prices[i] if len(prices) > i else prices[0]
            
            if action_name == 'buy':
                self._buy(i, price)
            elif action_name == 'sell':
                self._sell(i, price)
            # 'hold' does nothing
            if action_name == 'hold':
                 pass
                 # _logger.debug(f"Step {self.current_step}: Hold signal for {self.symbols[i]}")
            elif action_name == 'buy':
                self._buy(i, price)
            elif action_name == 'sell':
                self._sell(i, price)
            
            # Log non-hold actions (DEBUG only to prevent spam during training)
            if action_name != 'hold':
                 _logger.debug(f"Step {self.current_step} [{self.symbols[i]}]: Action {action_name} executed @ {price:,.0f}")
    
    def _execute_continuous_action(
        self,
        action: np.ndarray,
        prices: np.ndarray,
    ) -> None:
        """Execute continuous action (position sizing)."""
        action = np.clip(action, -1.0, 1.0)
        
        for i, act in enumerate(action.flatten()):
            price = prices[i] if len(prices) > i else prices[0]
            
            # Target position as fraction of portfolio
            portfolio_value = self._get_portfolio_value(prices)
            target_value = portfolio_value * abs(act)
            target_shares = int(target_value / price / self.lot_size) * self.lot_size
            
            current_shares = self.shares[i]
            
            if act > 0.001:  # Buy threshold
                shares_to_buy = max(0, target_shares - current_shares)
                if shares_to_buy > 0:
                    self._buy(i, price, shares_to_buy)
            elif act < -0.001:  # Sell threshold
                shares_to_sell = min(current_shares, target_shares)
                if shares_to_sell > 0:
                    self._sell(i, price, shares_to_sell)
    
    def _buy(
        self,
        symbol_idx: int,
        price: float,
        shares: Optional[int] = None,
    ) -> None:
        """
        Execute a buy order with slippage.
        
        Args:
            symbol_idx: Index of the symbol to buy
            price: Current price
            shares: Number of shares to buy (uses max affordable if None)
        """
        if price <= 0:
            return
            
        # Slippage Simulation (configurable, not hardcoded)
        # Add random slippage between 0% and max slippage to execution price
        # This simulates market depth and bid-ask spread
        slippage_pct = np.random.uniform(0.0, self.slippage_max_pct)
        execution_price = price * (1 + slippage_pct)
        
        # Calculate affordable shares using execution price
        cost_per_share = execution_price * (1 + self.buy_cost_pct)
        max_affordable = int(self.balance / cost_per_share / self.lot_size) * self.lot_size
        max_affordable = min(max_affordable, self.max_shares_per_trade)
        
        if shares is None:
            shares = max_affordable
        else:
            shares = min(shares, max_affordable)
            shares = int(shares / self.lot_size) * self.lot_size
        
        # Calculate affordable shares using execution price
        cost_per_share = execution_price * (1 + self.buy_cost_pct)
        max_affordable = int(self.balance / cost_per_share / self.lot_size) * self.lot_size
        max_affordable = min(max_affordable, self.max_shares_per_trade)
        
        if shares is None:
            shares = max_affordable
        else:
            shares = min(shares, max_affordable)
            shares = int(shares / self.lot_size) * self.lot_size
        
        if shares <= 0:
            # _logger.warning(f"Buy failed: funds {self.balance:,.0f} < min_cost {cost_per_share * self.lot_size:,.0f}")
            return
        
        # Execute buy
        total_cost = shares * cost_per_share
        self.balance -= total_cost
        self.shares[symbol_idx] += shares
        
        # Update cost basis
        old_shares = self.shares[symbol_idx] - shares
        old_cost = self.cost_basis[symbol_idx]
        self.cost_basis[symbol_idx] = (old_cost * old_shares + execution_price * shares) / self.shares[symbol_idx]
        
        # Record trade
        self.trades.append({
            'step': self.current_step,
            'symbol': self.symbols[symbol_idx],
            'action': 'buy',
            'shares': shares,
            'price': execution_price,
            'slippage': slippage_pct,
            'cost': total_cost,
        })
    
    def _sell(
        self,
        symbol_idx: int,
        price: float,
        shares: Optional[int] = None,
    ) -> None:
        """
        Execute a sell order with slippage.
        
        Args:
            symbol_idx: Index of the symbol to sell
            price: Current price
            shares: Number of shares to sell (sells all if None)
        """
        if price <= 0 or self.shares[symbol_idx] <= 0:
            return
        
        # Slippage Simulation (configurable, not hardcoded)
        # Sell at slightly lower price due to market slippage
        slippage_pct = np.random.uniform(0.0, self.slippage_max_pct)
        execution_price = price * (1 - slippage_pct)
        
        if shares is None:
            shares = int(self.shares[symbol_idx])
        else:
            shares = min(int(shares), int(self.shares[symbol_idx]))
            shares = int(shares / self.lot_size) * self.lot_size
        
        if shares <= 0:
            return
        
        # Calculate proceeds (after commission and tax)
        total_cost_rate = self.sell_cost_pct + self.tax_sell_pct
        proceeds = shares * execution_price * (1 - total_cost_rate)
        
        # Calculate realized PnL
        avg_cost = self.cost_basis[symbol_idx]
        realized_pnl = (execution_price - avg_cost) * shares
        
        # Execute sell
        self.balance += proceeds
        self.shares[symbol_idx] -= shares
        
        # Record trade
        self.trades.append({
            'step': self.current_step,
            'symbol': self.symbols[symbol_idx],
            'action': 'sell',
            'shares': shares,
            'price': execution_price,
            'slippage': slippage_pct,
            'proceeds': proceeds,
            'pnl': realized_pnl,
        })
    
    def _get_portfolio_value(self, prices: np.ndarray) -> float:
        """Calculate current portfolio value."""
        stock_value = np.sum(self.shares * prices)
        return float(self.balance + stock_value)
    
    def _calculate_reward(
        self,
        prev_value: float,
        new_value: float,
    ) -> float:
        """
        Calculate the reward for this step.
        
        Args:
            prev_value: Portfolio value before action
            new_value: Portfolio value after action
        
        Returns:
            Scaled reward value
        """
        # International Standard: Logarithmic Returns
        # Log returns are additive and symmetric, better for ML training than simple % returns
        if prev_value > 0 and new_value > 0:
            log_return = np.log(new_value / prev_value)
        else:
            log_return = 0.0
            
        reward = log_return * REWARD_SCALING.get('portfolio_return', 1.0)
        
        # Risk Adjustment: Volatility Penalty (Sortino-like)
        # Penalize if volatility is high, especially downside
        # We use a rolling window of recent returns to estimate current volatility
        if len(self.portfolio_values) > 5:
            recent_values = self.portfolio_values[-5:]
            if len(recent_values) > 1:
                recent_returns = np.diff(recent_values) / recent_values[:-1]
                volatility = np.std(recent_returns)
                # Penalize volatility to encourage stable growth
                reward -= volatility * REWARD_SCALING.get('volatility_penalty', 0.1)

        # Drawdown penalty (Max Drawdown)
        # Keeps the agent safe from catastrophic losses
        max_value = max(self.portfolio_values) if self.portfolio_values else self.initial_balance
        drawdown = (max_value - new_value) / max_value if max_value > 0 else 0
        
        # Non-linear drawdown penalty: punishes deeper drawdowns much harder
        # e.g. 10% DD -> 0.01 penalty, 50% DD -> 0.25 penalty
        reward -= (drawdown ** 2) * REWARD_SCALING.get('drawdown_penalty', 1.0)
        
        # Transaction penalty (if we just traded)
        # Reduces churn (over-trading)
        if self.trades and self.trades[-1]['step'] == self.current_step:
            reward -= REWARD_SCALING.get('transaction_penalty', 0.005)
        
        # Turbulence Penalty
        # If market is crashing (turbulence > threshold), penalize holding risky assets
        # We need to look up turbulence from data
        if self.current_step < len(self.data):
             # Assuming 'turbulence' and 'turbulence_threshold' are the last 2 features if added
             # But for safety, we rely on the fact that high turbulence usually causes negative returns
             # which are already penalized by log_returns.
             
             # However, we can add a specific "Panic Penalty" if we are BUYING during high turbulence
             # This encourages the agent to learn to sit out during crashes.
             pass
        
        # Scale reward
        reward *= self.reward_scaling
        
        return float(reward)
    
    def _get_observation(self) -> np.ndarray:
        """Get the current observation."""
        # Market features
        market_features = self.data[self.current_step]
        
        # Portfolio state (normalized)
        balance_norm = self.balance / self.initial_balance
        shares_norm = self.shares / (self.max_shares_per_trade or 1.0)
        
        portfolio_state = np.concatenate([[balance_norm], shares_norm])
        
        # Combine
        obs = np.concatenate([market_features, portfolio_state])
        
        return obs.astype(np.float32)
    
    def _get_info(self) -> Dict[str, Any]:
        """Get additional info about current state."""
        current_prices = self.prices[self.current_step]
        portfolio_value = self._get_portfolio_value(current_prices)
        
        # Calculate metrics
        returns = (portfolio_value - self.initial_balance) / self.initial_balance
        max_value = max(self.portfolio_values) if self.portfolio_values else portfolio_value
        drawdown = (max_value - portfolio_value) / max_value if max_value > 0 else 0
        
        return {
            'step': self.current_step,
            'balance': self.balance,
            'shares': self.shares.copy(),
            'portfolio_value': portfolio_value,
            'total_return': returns,
            'max_drawdown': drawdown,
            'n_trades': len(self.trades),
        }
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Calculate final performance metrics.
        
        Returns:
            Dictionary with Sharpe ratio, returns, drawdown, etc.
        """
        portfolio_returns = np.diff(self.portfolio_values) / np.array(self.portfolio_values[:-1])
        
        if len(portfolio_returns) == 0:
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'n_trades': 0,
            }
        
        # Calculate metrics
        total_return = (self.portfolio_values[-1] - self.initial_balance) / self.initial_balance
        
        # Sharpe ratio (annualized, assuming daily data)
        mean_return = np.mean(portfolio_returns)
        std_return = np.std(portfolio_returns)
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 1e-8 else 0.0
        
        # Max drawdown
        peak = np.maximum.accumulate(self.portfolio_values)
        drawdowns = (peak - self.portfolio_values) / peak
        max_drawdown = float(np.max(drawdowns))
        
        # Calculate trade statistics based on realized PnL in trades
        winning_trades = 0
        losing_trades = 0
        gross_profit = 0.0
        gross_loss = 0.0
        
        for trade in self.trades:
            if trade.get('action') == 'sell' and 'pnl' in trade:
                pnl = trade['pnl']
                if pnl > 0:
                    winning_trades += 1
                    gross_profit += pnl
                elif pnl < 0:
                    losing_trades += 1
                    gross_loss += abs(pnl)
        
        total_closed_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_closed_trades) if total_closed_trades > 0 else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)

        return {
            'total_return': float(total_return),
            'sharpe_ratio': float(sharpe),
            'max_drawdown': max_drawdown,
            'n_trades': len(self.trades),
            'avg_return': float(mean_return),
            'volatility': float(std_return),
            'final_portfolio_value': float(self.portfolio_values[-1]),
            'win_rate': float(win_rate),
            'profit_factor': float(profit_factor),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
        }


def create_ssi_env(
    data: np.ndarray,
    feature_names: List[str],
    symbols: List[str],
    prices: np.ndarray,
    **kwargs,
) -> SSIStockTradingEnv:
    """
    Factory function to create SSI trading environment.
    
    Args:
        data: Feature array
        feature_names: Feature column names
        symbols: Stock symbols
        prices: Price array
        **kwargs: Additional environment parameters
    
    Returns:
        Configured SSIStockTradingEnv instance
    """
    return SSIStockTradingEnv(
        data=data,
        feature_names=feature_names,
        symbols=symbols,
        prices=prices,
        **kwargs,
    )


# Register environment with Gymnasium if available
if GYM_AVAILABLE:
    try:
        gym.register(
            id='SSIStockTrading-v0',
            entry_point='odoo.addons.ai_trading_assistant.models.finrl.ssi_env:SSIStockTradingEnv',
        )
    except Exception:
        pass  # Already registered or registration not supported
