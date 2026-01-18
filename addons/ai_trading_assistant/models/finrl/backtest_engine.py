# -*- coding: utf-8 -*-
"""
International Standard Backtest Engine for FinRL

Provides production-grade backtesting with:
- Walk-Forward Analysis (WFA)
- Monte Carlo Simulation
- Comprehensive metrics (20+)
- Benchmark comparison
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime

import numpy as np
import pandas as pd

from .constants import ENV_PARAMS

_logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

BACKTEST_CONFIG = {
    'walk_forward_windows': 5,          # Number of WFA windows
    'monte_carlo_simulations': 1000,    # Number of MC simulations
    'confidence_level': 0.95,           # For VaR/CVaR (95%)
    'risk_free_rate': 0.02,             # 2% annual (VN T-bills approximation)
    'trading_days_per_year': 252,       # Vietnamese market
    'min_samples_per_window': 30,       # Minimum samples for valid window
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class BacktestResult:
    """Complete backtest result with all metrics and data."""
    
    # Core Results
    metrics: Dict[str, float] = field(default_factory=dict)
    trades: List[Dict] = field(default_factory=list)
    portfolio_values: List[float] = field(default_factory=list)
    
    # Equity Curve
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    
    # Walk-Forward Results (optional)
    walk_forward_results: Optional[List[Dict]] = None
    
    # Monte Carlo Results (optional)
    monte_carlo_distribution: Optional[Dict] = None
    
    # Benchmark Comparison (optional)
    benchmark_metrics: Optional[Dict] = None
    
    # Metadata
    backtest_mode: str = 'simple'
    start_date: str = ''
    end_date: str = ''
    symbols: List[str] = field(default_factory=list)


@dataclass
class TradeRecord:
    """Individual trade record."""
    entry_date: str
    exit_date: str
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    pnl_pct: float
    hold_duration: int  # in trading days


# =============================================================================
# BacktestEngine
# =============================================================================

class BacktestEngine:
    """
    International-standard backtest engine.
    
    Features:
    - Simple backtest (single pass)
    - Walk-Forward Analysis (rolling windows)
    - Monte Carlo Simulation (statistical robustness)
    - Comprehensive metrics (20+)
    - Customizable benchmark comparison
    """
    
    def __init__(
        self,
        config: Optional[Dict] = None,
        risk_free_rate: Optional[float] = None,
        benchmark_symbol: Optional[str] = None,
    ):
        """
        Initialize backtest engine.
        
        Args:
            config: Custom configuration overrides
            risk_free_rate: Annual risk-free rate (default: 2%)
            benchmark_symbol: Symbol for benchmark comparison (e.g., 'VN30', 'VNINDEX')
        """
        self.config = {**BACKTEST_CONFIG, **(config or {})}
        self.risk_free_rate = risk_free_rate or self.config['risk_free_rate']
        self.benchmark_symbol = benchmark_symbol
        
        # Cache for benchmark data
        self._benchmark_cache: Optional[pd.Series] = None
    
    # =========================================================================
    # Main Backtest Methods
    # =========================================================================
    
    def run_simple_backtest(
        self,
        env: Any,
        model: Any,
        prices: Optional[np.ndarray] = None,
        dates: Optional[List] = None,
    ) -> BacktestResult:
        """
        Run simple single-pass backtest.
        
        Args:
            env: SSIStockTradingEnv instance
            model: Trained DRL model
            prices: Price array for additional analysis
            dates: Date labels for equity curve
        
        Returns:
            BacktestResult with metrics and trades
        """
        _logger.info('Running simple backtest...')
        
        # Run simulation
        obs, info = env.reset()
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        
        # Extract results
        trades = env.trades
        portfolio_values = env.portfolio_values
        
        # Compute metrics
        metrics = self.compute_advanced_metrics(
            portfolio_values=portfolio_values,
            trades=trades,
            initial_balance=env.initial_balance,
        )
        
        # Build equity curve
        equity_curve = self._build_equity_curve(portfolio_values, dates)
        
        result = BacktestResult(
            metrics=metrics,
            trades=trades,
            portfolio_values=portfolio_values,
            equity_curve=equity_curve,
            backtest_mode='simple',
            symbols=env.symbols if hasattr(env, 'symbols') else [],
        )
        
        _logger.info(
            f"Simple backtest completed. "
            f"Return: {metrics.get('total_return', 0):.2%}, "
            f"Sharpe: {metrics.get('sharpe_ratio', 0):.2f}"
        )
        
        return result
    
    def run_walk_forward(
        self,
        data: np.ndarray,
        prices: np.ndarray,
        feature_names: List[str],
        symbols: List[str],
        model_factory: Callable,
        env_factory: Callable,
        n_windows: Optional[int] = None,
        train_ratio: float = 0.7,
    ) -> BacktestResult:
        """
        Run Walk-Forward Analysis.
        
        Train on window[i], test on window[i+1] for each rolling window.
        Aggregates out-of-sample results to detect overfitting.
        
        Args:
            data: Feature array (n_samples, n_features)
            prices: Price array
            feature_names: Feature column names
            symbols: Stock symbols
            model_factory: Function to create/train model
            env_factory: Function to create environment
            n_windows: Number of windows (default from config)
            train_ratio: Ratio of training data in each window
        
        Returns:
            BacktestResult with aggregated walk-forward results
        """
        n_windows = n_windows or self.config['walk_forward_windows']
        min_samples = self.config['min_samples_per_window']
        
        n_samples = len(data)
        window_size = n_samples // n_windows
        
        if window_size < min_samples * 2:
            raise ValueError(
                f'Insufficient data for {n_windows} windows. '
                f'Need at least {min_samples * 2 * n_windows} samples.'
            )
        
        _logger.info(
            f'Running Walk-Forward Analysis with {n_windows} windows, '
            f'{window_size} samples each'
        )
        
        all_oos_values = []  # Out-of-sample portfolio values
        all_oos_trades = []
        window_results = []
        
        for i in range(n_windows - 1):
            # Define window boundaries
            train_start = i * window_size
            train_end = train_start + int(window_size * train_ratio)
            test_start = train_end
            test_end = (i + 2) * window_size if i < n_windows - 2 else n_samples
            
            _logger.info(
                f'WFA Window {i+1}/{n_windows-1}: '
                f'Train [{train_start}:{train_end}], Test [{test_start}:{test_end}]'
            )
            
            # Extract window data
            train_data = data[train_start:train_end]
            train_prices = prices[train_start:train_end]
            test_data = data[test_start:test_end]
            test_prices = prices[test_start:test_end]
            
            if len(train_data) < min_samples or len(test_data) < min_samples:
                _logger.warning(f'Skipping window {i+1} due to insufficient data')
                continue
            
            try:
                # Create training environment and train model
                train_env = env_factory(train_data, feature_names, symbols, train_prices)
                model = model_factory(train_env)
                
                # Create test environment and run backtest
                test_env = env_factory(test_data, feature_names, symbols, test_prices)
                
                obs, _ = test_env.reset()
                done = False
                while not done:
                    action, _ = model.predict(obs, deterministic=True)
                    obs, _, terminated, truncated, _ = test_env.step(action)
                    done = terminated or truncated
                
                # Collect out-of-sample results
                all_oos_values.extend(test_env.portfolio_values)
                all_oos_trades.extend(test_env.trades)
                
                # Window metrics
                window_metrics = self.compute_advanced_metrics(
                    portfolio_values=test_env.portfolio_values,
                    trades=test_env.trades,
                    initial_balance=test_env.initial_balance,
                )
                
                window_results.append({
                    'window': i + 1,
                    'train_samples': len(train_data),
                    'test_samples': len(test_data),
                    'metrics': window_metrics,
                })
                
            except Exception as e:
                _logger.error(f'WFA window {i+1} failed: {e}', exc_info=True)
                continue
        
        if not all_oos_values:
            raise ValueError('All WFA windows failed. Check data quality.')
        
        # Compute aggregated out-of-sample metrics
        initial_balance = ENV_PARAMS.get('initial_balance', 100_000_000)
        aggregated_metrics = self.compute_advanced_metrics(
            portfolio_values=all_oos_values,
            trades=all_oos_trades,
            initial_balance=initial_balance,
        )
        
        # Add WFA-specific metrics
        sharpe_values = [w['metrics'].get('sharpe_ratio', 0) for w in window_results]
        aggregated_metrics['wfa_sharpe_mean'] = np.mean(sharpe_values)
        aggregated_metrics['wfa_sharpe_std'] = np.std(sharpe_values)
        aggregated_metrics['wfa_consistency'] = sum(1 for s in sharpe_values if s > 0) / len(sharpe_values)
        
        result = BacktestResult(
            metrics=aggregated_metrics,
            trades=all_oos_trades,
            portfolio_values=all_oos_values,
            walk_forward_results=window_results,
            backtest_mode='walk_forward',
            symbols=symbols,
        )
        
        _logger.info(
            f"WFA completed. OOS Return: {aggregated_metrics.get('total_return', 0):.2%}, "
            f"Consistency: {aggregated_metrics.get('wfa_consistency', 0):.1%}"
        )
        
        return result
    
    def run_monte_carlo(
        self,
        trades: List[Dict],
        initial_balance: float,
        n_simulations: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo Simulation on trade returns.
        
        Resamples trade sequence to estimate distribution of outcomes.
        
        Args:
            trades: List of trade dictionaries with 'pnl' or return info
            initial_balance: Starting capital
            n_simulations: Number of simulations (default from config)
        
        Returns:
            Distribution of outcomes with confidence intervals
        """
        n_simulations = n_simulations or self.config['monte_carlo_simulations']
        confidence_level = self.config['confidence_level']
        
        if not trades:
            _logger.warning('No trades for Monte Carlo simulation')
            return {}
        
        # Extract trade returns
        trade_returns = []
        for trade in trades:
            if 'pnl' in trade and trade.get('action') == 'sell':
                # Calculate return from PnL
                entry_value = trade.get('price', 0) * trade.get('shares', 0)
                if entry_value > 0:
                    trade_returns.append(trade['pnl'] / entry_value)
        
        if len(trade_returns) < 5:
            _logger.warning(f'Too few trades ({len(trade_returns)}) for Monte Carlo')
            return {}
        
        _logger.info(
            f'Running Monte Carlo with {n_simulations} simulations '
            f'on {len(trade_returns)} trades'
        )
        
        trade_returns = np.array(trade_returns)
        
        # Run simulations
        final_values = []
        max_drawdowns = []
        sharpe_ratios = []
        
        for _ in range(n_simulations):
            # Resample trades with replacement
            resampled_returns = np.random.choice(
                trade_returns, 
                size=len(trade_returns), 
                replace=True
            )
            
            # Build equity curve
            equity = [initial_balance]
            for ret in resampled_returns:
                equity.append(equity[-1] * (1 + ret))
            
            equity = np.array(equity)
            final_values.append(equity[-1])
            
            # Calculate drawdown
            peak = np.maximum.accumulate(equity)
            drawdown = (peak - equity) / peak
            max_drawdowns.append(np.max(drawdown))
            
            # Calculate Sharpe (simplified)
            returns = np.diff(equity) / equity[:-1]
            if len(returns) > 1 and np.std(returns) > 1e-8:
                sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252)
                sharpe_ratios.append(sharpe)
        
        final_values = np.array(final_values)
        max_drawdowns = np.array(max_drawdowns)
        sharpe_ratios = np.array(sharpe_ratios) if sharpe_ratios else np.array([0])
        
        # Calculate statistics
        alpha = 1 - confidence_level
        
        monte_carlo_result = {
            'n_simulations': n_simulations,
            'n_trades': len(trade_returns),
            
            # Final Value Distribution
            'final_value_mean': float(np.mean(final_values)),
            'final_value_median': float(np.median(final_values)),
            'final_value_std': float(np.std(final_values)),
            'final_value_lower': float(np.percentile(final_values, alpha/2 * 100)),
            'final_value_upper': float(np.percentile(final_values, (1 - alpha/2) * 100)),
            
            # Return Distribution
            'total_return_mean': float(np.mean(final_values) / initial_balance - 1),
            'total_return_median': float(np.median(final_values) / initial_balance - 1),
            'total_return_worst': float(np.min(final_values) / initial_balance - 1),
            'total_return_best': float(np.max(final_values) / initial_balance - 1),
            
            # Drawdown Distribution (Realistic MDD)
            'max_drawdown_mean': float(np.mean(max_drawdowns)),
            'max_drawdown_median': float(np.median(max_drawdowns)),
            'max_drawdown_worst': float(np.max(max_drawdowns)),
            'max_drawdown_95': float(np.percentile(max_drawdowns, 95)),
            
            # Sharpe Distribution
            'sharpe_mean': float(np.mean(sharpe_ratios)),
            'sharpe_median': float(np.median(sharpe_ratios)),
            'sharpe_std': float(np.std(sharpe_ratios)),
            
            # Probability Metrics
            'prob_profit': float(np.mean(final_values > initial_balance)),
            'prob_double': float(np.mean(final_values > initial_balance * 2)),
            'prob_loss_50pct': float(np.mean(final_values < initial_balance * 0.5)),
        }
        
        _logger.info(
            f"Monte Carlo completed. "
            f"Prob(Profit): {monte_carlo_result['prob_profit']:.1%}, "
            f"Realistic MDD: {monte_carlo_result['max_drawdown_95']:.1%}"
        )
        
        return monte_carlo_result
    
    # =========================================================================
    # Metrics Computation
    # =========================================================================
    
    def compute_advanced_metrics(
        self,
        portfolio_values: List[float],
        trades: List[Dict],
        initial_balance: float,
        benchmark_returns: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        """
        Compute comprehensive performance metrics.
        
        Args:
            portfolio_values: List of portfolio values over time
            trades: List of trade records
            initial_balance: Starting capital
            benchmark_returns: Optional benchmark returns for Alpha/Beta
        
        Returns:
            Dictionary with 20+ metrics
        """
        if not portfolio_values or len(portfolio_values) < 2:
            return self._empty_metrics()
        
        values = np.array(portfolio_values)
        returns = np.diff(values) / values[:-1]
        
        trading_days = self.config['trading_days_per_year']
        daily_rf = self.risk_free_rate / trading_days
        
        metrics = {}
        
        # =====================================================================
        # Return Metrics
        # =====================================================================
        metrics['total_return'] = float((values[-1] - initial_balance) / initial_balance)
        metrics['final_value'] = float(values[-1])
        
        # Annualized return (CAGR)
        n_days = len(returns)
        if n_days > 0 and values[-1] > 0 and initial_balance > 0:
            metrics['annualized_return'] = float(
                (values[-1] / initial_balance) ** (trading_days / n_days) - 1
            )
            metrics['cagr'] = metrics['annualized_return']
        else:
            metrics['annualized_return'] = 0.0
            metrics['cagr'] = 0.0
        
        # =====================================================================
        # Risk Metrics
        # =====================================================================
        metrics['volatility'] = float(np.std(returns) * np.sqrt(trading_days))
        
        # Downside volatility (for Sortino)
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            metrics['downside_volatility'] = float(
                np.std(negative_returns) * np.sqrt(trading_days)
            )
        else:
            metrics['downside_volatility'] = 0.0
        
        # =====================================================================
        # Risk-Adjusted Returns
        # =====================================================================
        
        # =====================================================================
        # Risk-Adjusted Returns
        # =====================================================================
        
        # Calculate daily risk-free rate using geometric mean (more precise)
        # (1 + r_annual) = (1 + r_daily)^252  =>  r_daily = (1 + r_annual)^(1/252) - 1
        daily_rf_geo = (1 + self.risk_free_rate) ** (1 / trading_days) - 1
        
        # Sharpe Ratio
        # Standard definition: mean(excess_ret) / std(excess_ret) * sqrt(252)
        # Note: std(excess_ret) approx std(ret) since rf is constant
        excess_returns = returns - daily_rf_geo
        if np.std(excess_returns) > 1e-8:
            metrics['sharpe_ratio'] = float(
                np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(trading_days)
            )
        else:
            metrics['sharpe_ratio'] = 0.0
        
        # Sortino Ratio
        # Standard definition: mean(excess_ret) / downside_deviation * sqrt(252)
        # Downside deviation: sqrt(mean(min(0, returns - target)^2)) where target is usually 0 or Rf
        # Here we use 0 as Target Return (MAR = 0) which is common standard
        downside_returns = np.minimum(returns, 0)
        downside_deviation = np.sqrt(np.mean(downside_returns**2))
        
        if downside_deviation > 1e-8:
            metrics['sortino_ratio'] = float(
                np.mean(returns) / downside_deviation * np.sqrt(trading_days)
            )
        else:
             # If no downside volatility (only wins), Sortino is technically infinite. 
             # We cap it or return a high value, or just Sharpe if appropriate.
             # Here we return 0 to avoid Infinity issues in JSON.
            metrics['sortino_ratio'] = 0.0 if np.mean(returns) <= 0 else 10.0

        
        # =====================================================================
        # Drawdown Metrics
        # =====================================================================
        peak = np.maximum.accumulate(values)
        drawdown = (peak - values) / peak
        
        metrics['max_drawdown'] = float(np.max(drawdown))
        metrics['avg_drawdown'] = float(np.mean(drawdown[drawdown > 0])) if np.any(drawdown > 0) else 0.0
        
        # Calmar Ratio
        if metrics['max_drawdown'] > 1e-8:
            metrics['calmar_ratio'] = float(
                metrics['annualized_return'] / metrics['max_drawdown']
            )
        else:
            metrics['calmar_ratio'] = 0.0
        
        # Drawdown duration
        in_drawdown = drawdown > 0
        if np.any(in_drawdown):
            # Find longest consecutive drawdown period
            dd_changes = np.diff(in_drawdown.astype(int))
            dd_starts = np.where(dd_changes == 1)[0]
            dd_ends = np.where(dd_changes == -1)[0]
            
            if len(dd_starts) > 0 and len(dd_ends) > 0:
                if dd_ends[0] < dd_starts[0]:
                    dd_ends = dd_ends[1:]
                if len(dd_starts) > len(dd_ends):
                    dd_ends = np.append(dd_ends, len(drawdown) - 1)
                
                if len(dd_starts) > 0 and len(dd_ends) > 0:
                    durations = dd_ends[:len(dd_starts)] - dd_starts[:len(dd_ends)]
                    metrics['max_drawdown_duration'] = int(np.max(durations))
                else:
                    metrics['max_drawdown_duration'] = 0
            else:
                metrics['max_drawdown_duration'] = 0
        else:
            metrics['max_drawdown_duration'] = 0
        
        # =====================================================================
        # Value at Risk (VaR) and Conditional VaR (CVaR/Expected Shortfall)
        # =====================================================================
        alpha = 1 - self.config['confidence_level']
        
        metrics['var_95'] = float(np.percentile(returns, alpha * 100))
        metrics['cvar_95'] = float(np.mean(returns[returns <= metrics['var_95']]))
        
        # =====================================================================
        # Trade Statistics
        # =====================================================================
        sell_trades = [t for t in trades if t.get('action') == 'sell' and 'pnl' in t]
        
        if sell_trades:
            pnls = [t['pnl'] for t in sell_trades]
            winning = [p for p in pnls if p > 0]
            losing = [p for p in pnls if p < 0]
            
            metrics['total_trades'] = len(sell_trades)
            metrics['winning_trades'] = len(winning)
            metrics['losing_trades'] = len(losing)
            metrics['win_rate'] = float(len(winning) / len(sell_trades)) if sell_trades else 0.0
            
            metrics['avg_win'] = float(np.mean(winning)) if winning else 0.0
            metrics['avg_loss'] = float(np.mean(losing)) if losing else 0.0
            
            # Profit Factor
            gross_profit = sum(winning)
            gross_loss = abs(sum(losing))
            if gross_loss > 0:
                metrics['profit_factor'] = float(gross_profit / gross_loss)
            else:
                metrics['profit_factor'] = float(gross_profit) if gross_profit > 0 else 0.0
            
            # Payoff Ratio (avg win / avg loss)
            if metrics['avg_loss'] != 0:
                metrics['payoff_ratio'] = float(abs(metrics['avg_win'] / metrics['avg_loss']))
            else:
                metrics['payoff_ratio'] = 0.0
            
            # Expectancy (average profit per trade)
            metrics['expectancy'] = float(np.mean(pnls))
            
        else:
            metrics['total_trades'] = 0
            metrics['winning_trades'] = 0
            metrics['losing_trades'] = 0
            metrics['win_rate'] = 0.0
            metrics['avg_win'] = 0.0
            metrics['avg_loss'] = 0.0
            metrics['profit_factor'] = 0.0
            metrics['payoff_ratio'] = 0.0
            metrics['expectancy'] = 0.0
        
        # =====================================================================
        # Benchmark Comparison (Alpha, Beta, Information Ratio)
        # =====================================================================
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            # Beta
            covariance = np.cov(returns, benchmark_returns)[0, 1]
            benchmark_var = np.var(benchmark_returns)
            if benchmark_var > 1e-8:
                metrics['beta'] = float(covariance / benchmark_var)
            else:
                metrics['beta'] = 0.0
            
            # Alpha (Jensen's Alpha)
            benchmark_annual_return = float(
                np.mean(benchmark_returns) * trading_days
            )
            expected_return = self.risk_free_rate + metrics['beta'] * (
                benchmark_annual_return - self.risk_free_rate
            )
            metrics['alpha'] = float(metrics['annualized_return'] - expected_return)
            
            # Information Ratio
            active_returns = returns - benchmark_returns
            tracking_error = np.std(active_returns) * np.sqrt(trading_days)
            if tracking_error > 1e-8:
                metrics['information_ratio'] = float(
                    np.mean(active_returns) * trading_days / tracking_error
                )
            else:
                metrics['information_ratio'] = 0.0
        else:
            metrics['alpha'] = 0.0
            metrics['beta'] = 0.0
            metrics['information_ratio'] = 0.0
        
        return metrics
    
    def compare_to_benchmark(
        self,
        portfolio_values: List[float],
        benchmark_prices: np.ndarray,
        initial_balance: float,
    ) -> Dict[str, Any]:
        """
        Compare strategy performance to a benchmark.
        
        Args:
            portfolio_values: Strategy portfolio values
            benchmark_prices: Benchmark price series
            initial_balance: Starting capital
        
        Returns:
            Comparison metrics and data
        """
        if len(benchmark_prices) == 0:
            return {}
        
        # Align lengths
        min_len = min(len(portfolio_values), len(benchmark_prices))
        portfolio_values = portfolio_values[:min_len]
        benchmark_prices = benchmark_prices[:min_len]
        
        # Calculate benchmark portfolio (buy-and-hold)
        benchmark_initial = benchmark_prices[0]
        benchmark_values = (benchmark_prices / benchmark_initial) * initial_balance
        
        # Calculate returns
        strategy_returns = np.diff(portfolio_values) / np.array(portfolio_values[:-1])
        benchmark_returns = np.diff(benchmark_values) / benchmark_values[:-1]
        
        # Compute metrics for benchmark
        benchmark_metrics = self.compute_advanced_metrics(
            portfolio_values=list(benchmark_values),
            trades=[],  # Buy-and-hold has no trades
            initial_balance=initial_balance,
        )
        
        # Compute strategy metrics with benchmark comparison
        strategy_metrics = self.compute_advanced_metrics(
            portfolio_values=portfolio_values,
            trades=[],
            initial_balance=initial_balance,
            benchmark_returns=benchmark_returns,
        )
        
        return {
            'strategy_metrics': strategy_metrics,
            'benchmark_metrics': benchmark_metrics,
            'outperformance': strategy_metrics['total_return'] - benchmark_metrics['total_return'],
            'benchmark_values': list(benchmark_values),
        }
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _build_equity_curve(
        self,
        portfolio_values: List[float],
        dates: Optional[List] = None,
    ) -> pd.DataFrame:
        """Build equity curve DataFrame."""
        n = len(portfolio_values)
        
        if dates is None or len(dates) != n:
            dates = list(range(n))
        
        df = pd.DataFrame({
            'date': dates,
            'value': portfolio_values,
        })
        
        # Add returns
        df['return'] = df['value'].pct_change()
        
        # Add drawdown
        df['peak'] = df['value'].cummax()
        df['drawdown'] = (df['peak'] - df['value']) / df['peak']
        
        return df
    
    def _empty_metrics(self) -> Dict[str, float]:
        """Return empty metrics dictionary."""
        return {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'var_95': 0.0,
            'cvar_95': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
        }


# =============================================================================
# Factory Function
# =============================================================================

def create_backtest_engine(
    risk_free_rate: float = 0.02,
    benchmark_symbol: Optional[str] = None,
    config: Optional[Dict] = None,
) -> BacktestEngine:
    """
    Factory function to create BacktestEngine.
    
    Args:
        risk_free_rate: Annual risk-free rate
        benchmark_symbol: Symbol for benchmark comparison
        config: Custom configuration
    
    Returns:
        Configured BacktestEngine instance
    """
    return BacktestEngine(
        config=config,
        risk_free_rate=risk_free_rate,
        benchmark_symbol=benchmark_symbol,
    )
