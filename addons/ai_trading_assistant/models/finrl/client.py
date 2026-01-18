# -*- coding: utf-8 -*-
"""
FinRL Client for AI Trading Assistant

High-level client that orchestrates data processing, environment creation,
agent training, backtesting, and prediction generation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Force non-interactive backend to prevent font warnings

from .constants import (
    DRL_ALGORITHMS,
    ENV_PARAMS,
    DEFAULT_TRAINING_PARAMS,
)
from .data_processor import SSIDataProcessor
from .ssi_env import SSIStockTradingEnv, create_ssi_env
from .agents import DRLAgentFactory

_logger = logging.getLogger(__name__)


class FinRLClient:
    """
    High-level client for FinRL operations.
    
    Provides a unified interface for:
    - Training DRL agents
    - Running backtests
    - Generating predictions
    - Managing models
    """
    
    def __init__(
        self,
        ssi_client: Any,
        model_dir: Optional[str] = None,
        tensorboard_log: Optional[str] = None,
        algorithm: str = 'ppo',
    ):
        """
        Initialize the FinRL client.
        
        Args:
            ssi_client: SSIClient instance for data fetching
            model_dir: Directory for saving models
            tensorboard_log: Directory for TensorBoard logs
            algorithm: Default DRL algorithm
        """
        self.ssi_client = ssi_client
        self.model_dir = Path(model_dir or '~/.finrl/models').expanduser()
        self.tensorboard_log = Path(tensorboard_log or '~/.finrl/logs').expanduser()
        self.algorithm = algorithm
        
        # Initialize components
        self.data_processor = SSIDataProcessor(ssi_client)
        self.agent_factory: Optional[DRLAgentFactory] = None
        
        # Cached data
        self._data_cache: Dict[str, pd.DataFrame] = {}
    
    def train(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        algorithm: Optional[str] = None,
        market: str = 'HOSE',
        data_type: str = 'daily',
        resolution: str = '1',
        total_timesteps: Optional[int] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        action_space_type: str = 'discrete',
        progress_callback: Optional[callable] = None,
        seed: Optional[int] = None,
        initial_balance: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Train a DRL agent on SSI market data.
        
        Args:
            symbols: List of stock symbols to trade
            start_date: Training data start date (YYYY-MM-DD)
            end_date: Training data end date (YYYY-MM-DD)
            algorithm: DRL algorithm (overrides default)
            market: Stock market (HOSE, HNX, UPCOM)
            data_type: 'daily' or 'intraday'
            total_timesteps: Training timesteps
            custom_params: Custom hyperparameters
            action_space_type: 'discrete' or 'continuous'
            progress_callback: Progress update function
            seed: Random seed
            initial_balance: Optional initial balance for the trading environment.
        
        Returns:
            Training results with metrics
        """
        algorithm = algorithm or self.algorithm
        # Note: total_timesteps = 0 or None means full-data mode (handled below after data fetch)
        
        _logger.info(
            f'Starting {algorithm.upper()} training for {symbols} '
            f'from {start_date} to {end_date}'
        )
        
        # Fetch and process data
        df = self._fetch_and_process_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            market=market,
            data_type=data_type,
            resolution=resolution,
        )
        
        if df.empty:
            raise ValueError('No training data available')
        
        if len(df) < 30:
            raise ValueError(
                f'Insufficient training data: {len(df)} samples. '
                'Need at least 30 samples.'
            )
        
        # SPLIT DATA FIRST (80/20) to avoid lookahead bias in normalization
        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx]
        eval_df = df.iloc[split_idx:]
        
        # Dynamic timesteps: train on full data if not specified or 0
        if not total_timesteps or total_timesteps <= 0:
            # Default to dynamic epochs based on data length
            data_len = len(train_df)
            
            if data_len < 2000:
                # Daily data or short intraday: 50 epochs
                epochs = 50
            elif data_len < 10000:
                # Medium intraday (e.g. 1 month): 10 epochs
                epochs = 10
            else:
                # Long intraday: 3 epochs
                epochs = 3
                
            total_timesteps = int(data_len * epochs)
            
            # Cap maximum steps to prevent excessively long training
            # 50,000 steps @ 250it/s ~= 3.5 minutes. Maximum budget for interactive training.
            if total_timesteps > 50000:
                total_timesteps = 50000
                
            # Ensure minimum steps
            if total_timesteps < 5000:
                total_timesteps = 5000
                
            _logger.info(f'Auto-calculated training timesteps: {total_timesteps} (based on {data_len} samples * {epochs} epochs, capped at 200k)')
        
        # Prepare Data (Calculate scaler on Train, apply to Eval)
        features, feature_names = self.data_processor.prepare_for_env(train_df, is_training=True)
        prices = train_df['close'].values
        
        eval_features, _ = self.data_processor.prepare_for_env(eval_df, is_training=False)
        eval_prices = eval_df['close'].values
        
        # Create Train Environment
        env_kwargs = {}
        if initial_balance:
            env_kwargs['initial_balance'] = initial_balance
            
        env = create_ssi_env(
            data=features,
            feature_names=feature_names,
            symbols=symbols,
            prices=prices,
            action_space_type=action_space_type,
            **env_kwargs
        )
        
        # Create Eval Environment
        eval_env = None
        if len(eval_features) >= 10:
            eval_env = create_ssi_env(
                data=eval_features,
                feature_names=feature_names,
                symbols=symbols,
                prices=eval_prices,
                action_space_type=action_space_type,
                **env_kwargs
            )
        
        # Standard Single Agent Training
        # Initialize agent factory
        self.agent_factory = DRLAgentFactory(
            algorithm=algorithm,
            model_dir=str(self.model_dir),
            tensorboard_log=str(self.tensorboard_log),
        )
        
        # Train
        model, training_info = self.agent_factory.train(
            env=DRLAgentFactory.wrap_env(env),
            total_timesteps=total_timesteps,
            eval_env=DRLAgentFactory.wrap_env(eval_env) if eval_env else None,
            progress_callback=progress_callback,
            custom_params=custom_params,
            seed=seed,
        )
        
        # Report Finalizing Status
        if progress_callback:
            progress_callback(99.9, total_timesteps, total_timesteps)

        # Create a FRESH environment for backtesting to get accurate metrics
        # The original env may have been modified during training
        backtest_env = create_ssi_env(
            data=features,
            feature_names=feature_names,
            symbols=symbols,
            prices=prices,
            action_space_type=action_space_type,
            **env_kwargs
        )
        
        # Run backtest on fresh environment for metrics
        backtest_metrics = self._run_backtest_on_env(backtest_env, model)
        
        # Build result
        result = {
            'algorithm': algorithm,
            'symbols': symbols,
            'market': market,
            'data_type': data_type,
            'date_range': {'start': start_date, 'end': end_date},
            'total_timesteps': total_timesteps,
            'training_samples': len(features),
            'training_duration_seconds': training_info.get('training_duration_seconds', 0),
            'metrics': backtest_metrics,
            'params': custom_params or (DRL_ALGORITHMS.get(algorithm, {}).get('default_params', {})),
        }
        
        _logger.info(
            f'Training completed. '
            f"Total return: {backtest_metrics.get('total_return', 0):.2%}, "
            f"Sharpe: {backtest_metrics.get('sharpe_ratio', 0):.2f}"
        )
        
        return result
    
    def tune(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        algorithm: str = 'ppo',
        total_timesteps: int = 20000,
        n_trials: int = 10,
        market: str = 'HOSE',
        data_type: str = 'daily',
        initial_balance: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Tune hyperparameters using Optuna.
        
        Args:
            symbols: List of symbols
            start_date: Start date
            end_date: End date
            algorithm: Algorithm to tune
            total_timesteps: Timesteps per trial
            n_trials: Number of trials
            initial_balance: Optional initial balance
        
        Returns:
            Best hyperparameters
        """
        from .tuner import HyperparameterTuner
        
        # Data Preparation (Same as train)
        df = self._fetch_and_process_data(
            symbols=symbols, 
            start_date=start_date, 
            end_date=end_date, 
            market=market, 
            data_type=data_type
        )
        if df.empty:
            raise ValueError('No data for tuning')
            
        features, feature_names = self.data_processor.prepare_for_env(df)
        prices = df['close'].values
        
        # Split Train/Eval
        split_idx = int(len(features) * 0.8)
        train_features = features[:split_idx]
        train_prices = prices[:split_idx]
        eval_features = features[split_idx:]
        eval_prices = prices[split_idx:]
        
        if len(eval_features) < 10:
             raise ValueError("Not enough data for tuning validation set")
        
        # Factories for Tuner
        env_kwargs = {}
        if initial_balance:
            env_kwargs['initial_balance'] = initial_balance

        def env_factory():
            return create_ssi_env(
                data=train_features, 
                feature_names=feature_names, 
                symbols=symbols, 
                prices=train_prices,
                **env_kwargs
            )
            
        def eval_env_factory():
            return create_ssi_env(
                data=eval_features, 
                feature_names=feature_names, 
                symbols=symbols, 
                prices=eval_prices,
                **env_kwargs
            )
            
        tuner = HyperparameterTuner(
            env_factory=env_factory,
            eval_env_factory=eval_env_factory,
            algorithm=algorithm,
            n_trials=n_trials,
            total_timesteps=total_timesteps
        )
        
        result = tuner.optimize()
        return result.get('best_params', {})

    
    def backtest(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        model_name_or_path: Optional[str] = None,
        market: str = 'HOSE',
        data_type: str = 'daily',
        action_space_type: str = 'discrete',
        mode: str = 'simple',
        benchmark_symbol: Optional[str] = None,
        n_monte_carlo: Optional[int] = None,
        n_walk_forward_windows: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run backtest with a trained model.
        
        Args:
            symbols: List of stock symbols
            start_date: Backtest start date
            end_date: Backtest end date
            model_name_or_path: Model to use (uses last trained if None)
            market: Stock market
            data_type: 'daily' or 'intraday'
            action_space_type: 'discrete' or 'continuous'
            mode: 'simple', 'walk_forward', or 'monte_carlo'
            benchmark_symbol: Symbol for benchmark comparison (e.g., 'VN30')
            n_monte_carlo: Number of Monte Carlo simulations (default: 1000)
            n_walk_forward_windows: Number of WFA windows (default: 5)
        
        Returns:
            Backtest results with comprehensive metrics
        """
        from .backtest_engine import BacktestEngine, create_backtest_engine
        
        if self.agent_factory is None or self.agent_factory.model is None:
            if model_name_or_path is None:
                raise ValueError('No model available. Train or load a model first.')
            # Initialize factory and load model
            self.agent_factory = DRLAgentFactory(
                algorithm=self.algorithm,
                model_dir=str(self.model_dir),
                tensorboard_log=str(self.tensorboard_log),
            )
            self.agent_factory.load(model_name_or_path)
        
        _logger.info(
            f'Running {mode} backtest for {symbols} from {start_date} to {end_date}'
        )
        
        # Fetch and process data
        df = self._fetch_and_process_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            market=market,
            data_type=data_type,
        )
        
        if df.empty:
            raise ValueError('No backtest data available')
        
        # Prepare for environment
        features, feature_names = self.data_processor.prepare_for_env(df)
        prices = df['close'].values
        dates = df['date'].tolist() if 'date' in df.columns else None
        
        # Create backtest engine
        engine = create_backtest_engine(benchmark_symbol=benchmark_symbol)
        
        # Create environment
        env = create_ssi_env(
            data=features,
            feature_names=feature_names,
            symbols=symbols,
            prices=prices,
            action_space_type=action_space_type,
        )
        
        # Run backtest based on mode
        if mode == 'simple':
            # Simple single-pass backtest with advanced metrics
            backtest_result = engine.run_simple_backtest(
                env=env,
                model=self.agent_factory.model,
                prices=prices,
                dates=dates,
            )
            
        elif mode == 'walk_forward':
            # Walk-Forward Analysis
            def model_factory(train_env):
                """Train new model for each window (simplified - uses current model)."""
                return self.agent_factory.model
            
            def env_factory(data, feature_names, symbols, prices):
                return create_ssi_env(
                    data=data,
                    feature_names=feature_names,
                    symbols=symbols,
                    prices=prices,
                    action_space_type=action_space_type,
                )
            
            backtest_result = engine.run_walk_forward(
                data=features,
                prices=prices,
                feature_names=feature_names,
                symbols=symbols,
                model_factory=model_factory,
                env_factory=env_factory,
                n_windows=n_walk_forward_windows,
            )
            
        elif mode == 'monte_carlo':
            # Run simple backtest first to get trades
            backtest_result = engine.run_simple_backtest(
                env=env,
                model=self.agent_factory.model,
                prices=prices,
                dates=dates,
            )
            
            # Then run Monte Carlo on the trades
            mc_result = engine.run_monte_carlo(
                trades=backtest_result.trades,
                initial_balance=env.initial_balance,
                n_simulations=n_monte_carlo,
            )
            backtest_result.monte_carlo_distribution = mc_result
            backtest_result.backtest_mode = 'monte_carlo'
            
        else:
            raise ValueError(f"Unknown backtest mode: {mode}. Use 'simple', 'walk_forward', or 'monte_carlo'")
        
        # Fetch benchmark data if specified
        if benchmark_symbol:
            try:
                benchmark_df = self.data_processor.fetch_data(
                    symbols=[benchmark_symbol],
                    start_date=start_date,
                    end_date=end_date,
                    market=market,
                    data_type=data_type,
                )
                if not benchmark_df.empty:
                    benchmark_prices = benchmark_df['close'].values
                    benchmark_comparison = engine.compare_to_benchmark(
                        portfolio_values=backtest_result.portfolio_values,
                        benchmark_prices=benchmark_prices,
                        initial_balance=env.initial_balance,
                    )
                    backtest_result.benchmark_metrics = benchmark_comparison
            except Exception as e:
                _logger.warning(f'Failed to fetch benchmark {benchmark_symbol}: {e}')
        
        # Build result dictionary
        result = {
            'symbols': symbols,
            'market': market,
            'data_type': data_type,
            'date_range': {'start': start_date, 'end': end_date},
            'n_samples': len(features),
            'mode': backtest_result.backtest_mode,
            'metrics': backtest_result.metrics,
            'trades': backtest_result.trades,
            'portfolio_values': backtest_result.portfolio_values,
        }
        
        # Add optional results
        if backtest_result.walk_forward_results:
            result['walk_forward_results'] = backtest_result.walk_forward_results
        
        if backtest_result.monte_carlo_distribution:
            result['monte_carlo'] = backtest_result.monte_carlo_distribution
        
        if backtest_result.benchmark_metrics:
            result['benchmark'] = backtest_result.benchmark_metrics
        
        _logger.info(
            f'{mode.upper()} backtest completed. '
            f"Return: {backtest_result.metrics.get('total_return', 0):.2%}, "
            f"Sharpe: {backtest_result.metrics.get('sharpe_ratio', 0):.2f}, "
            f"Trades: {backtest_result.metrics.get('total_trades', 0)}"
        )
        
        return result
    
    def predict(
        self,
        symbol: str,
        market: str = 'HOSE',
        lookback_days: int = 200,
        model_name_or_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate prediction for a symbol using the trained model.
        
        Args:
            symbol: Stock symbol
            market: Stock market
            lookback_days: Number of days for historical context
            model_name_or_path: Model to use
        
        Returns:
            Prediction with action and confidence
        """
        if self.agent_factory is None or self.agent_factory.model is None:
            if model_name_or_path is None:
                raise ValueError('No model available. Train or load a model first.')
            self.agent_factory = DRLAgentFactory(
                algorithm=self.algorithm,
                model_dir=str(self.model_dir),
                tensorboard_log=str(self.tensorboard_log),
            )
            self.agent_factory.load(model_name_or_path)
        
        # Calculate date range
        end_date = datetime.now().strftime('%Y-%m-%d')
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        # Fetch recent data
        df = self._fetch_and_process_data(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date,
            market=market,
            data_type='daily',
        )
        
        if df.empty or len(df) < 5:
            raise ValueError(f'Insufficient data for prediction: {len(df)} samples')
        
        # Prepare observation
        features, feature_names = self.data_processor.prepare_for_env(df)
        
        # Get latest observation
        latest_obs = features[-1].reshape(1, -1)
        
        # Add portfolio state (assume initial state)
        balance_norm = 1.0  # Full balance
        shares_norm = 0.0  # No holdings
        portfolio_state = np.array([[balance_norm, shares_norm]], dtype=np.float32)
        obs = np.concatenate([latest_obs, portfolio_state], axis=1).flatten()
        
        # Predict
        # Get action and confidence from agent
        try:
            # Use new probabilistic prediction if available
            action, state, proba_confidence = self.agent_factory.predict_proba(obs)
        except AttributeError:
            # Fallback for older agents
            action, state = self.agent_factory.predict(obs)
            proba_confidence = 0.0

        # Interpret action
        if isinstance(action, np.ndarray):
            action = action.item() if action.size == 1 else action[0]
        
        # Log raw action for debugging
        _logger.info(f"FinRL raw action for {symbol}: {action} (type: {type(action)})")

        # Robust Discrete vs Continuous Detection
        is_discrete = False
        # PPO MlpPolicy is usually discrete in FinRL unless configured otherwise
        if self.agent_factory.algorithm_config.get('policy') == 'MlpPolicy':
             # Check if action is integer-like
            if isinstance(action, (int, np.integer)):
                is_discrete = True
            elif isinstance(action, float) and action.is_integer() and 0 <= action <= 2:
                is_discrete = True
            
        signal = 'hold'
        confidence = 0.0
            
        if is_discrete:
            # Discrete actions: 0=Sell, 1=Hold, 2=Buy
            action_map = {0: 'sell', 1: 'hold', 2: 'buy'}
            signal = action_map.get(int(action), 'hold')
            
            # Use true probability if available
            if proba_confidence > 0:
                confidence = proba_confidence
            else:
                # Fallback: 80% baseline for unknown discrete confidence
                confidence = 0.8 
        else:
            # Continuous actions: [-1, 1]
            # Threshold for Buy/Sell
            threshold = 0.1
            
            if action > threshold:
                signal = 'buy'
                # For continuous, Magnitude IS Confidence (Conviction)
                confidence = min(1.0, abs(action))
            elif action < -threshold:
                signal = 'sell'
                confidence = min(1.0, abs(action))
            else:
                signal = 'hold'
                # Confidence in HOLD is inverse of action magnitude
                confidence = max(0.5, 1.0 - (abs(action) * 5.0))
        
        # Ensure confidence is float and bounded
        confidence = float(max(0.0, min(1.0, confidence)))
        
        # Get latest price
        latest_price = float(df['close'].iloc[-1])
        
        result = {
            'symbol': symbol,
            'market': market,
            'signal': signal,
            'action_value': float(action),
            'confidence': float(confidence),
            'current_price': latest_price,
            'prediction_date': end_date,
            'lookback_days': lookback_days,
            'data_points': len(df),
        }
        
        _logger.info(f'Prediction for {symbol}: {signal} (confidence: {confidence:.2f})')
        
        return result
    
    def save_model(
        self,
        name: str,
        include_replay_buffer: bool = False,
    ) -> str:
        """
        Save the current model.
        
        Args:
            name: Model name
            include_replay_buffer: Whether to save replay buffer
        
        Returns:
            Path to saved model
        """
        if self.agent_factory is None:
            raise ValueError('No model to save')
        
        return self.agent_factory.save(name, include_replay_buffer)
    
    def load_model(
        self,
        name_or_path: str,
        algorithm: Optional[str] = None,
    ) -> None:
        """
        Load a saved model.
        
        Args:
            name_or_path: Model name or path
            algorithm: DRL algorithm (required if factory not initialized)
        """
        algorithm = algorithm or self.algorithm
        
        # Check if it's an Ensemble
        import os
        is_ensemble = (algorithm == 'ensemble')
        
        # Resolve path
        if os.path.isabs(name_or_path):
            path = name_or_path
        else:
            path = str(self.model_dir / name_or_path)
        
        # Strip .zip extension if present for ensemble config check
        base_path = path.replace('.zip', '')
        ensemble_config_path = base_path + "_ensemble_config.json"
        
        _logger.info(f"Loading model - path: {path}, base_path: {base_path}, is_ensemble: {is_ensemble}")
        _logger.info(f"Checking ensemble config at: {ensemble_config_path}, exists: {os.path.exists(ensemble_config_path)}")
            
        if is_ensemble or os.path.exists(ensemble_config_path):
            try:
                _logger.info(f"Attempting to load as Ensemble from {base_path}")
                model = EnsembleAgent.load(base_path)
                self.agent_factory = DRLAgentFactory(
                    algorithm='ppo',  # Use ppo as base for ensemble (just for factory initialization)
                    model_dir=str(self.model_dir),
                    tensorboard_log=str(self.tensorboard_log),
                )
                self.agent_factory.model = model
                _logger.info(f"Successfully loaded Ensemble model from {base_path}")
                return
            except Exception as e:
                _logger.error(f"Failed to load as ensemble: {e}", exc_info=True)
                # If ensemble fails AND algorithm was 'ensemble', we can't fallback
                if is_ensemble:
                    raise ValueError(f"Failed to load ensemble model from {base_path}: {e}")
        
        # For single agent models (not ensemble)
        if algorithm == 'ensemble':
            # Should not reach here if ensemble loading failed above
            raise ValueError("Cannot load ensemble model as single agent")
            
        self.agent_factory = DRLAgentFactory(
            algorithm=algorithm,
            model_dir=str(self.model_dir),
            tensorboard_log=str(self.tensorboard_log),
        )
        self.agent_factory.load(name_or_path)
    
    def _fetch_and_process_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        market: str,
        data_type: str,
        resolution: str = '1',
    ) -> pd.DataFrame:
        """Fetch and process data from SSI."""
        # Create cache key
        cache_key = f"{','.join(sorted(symbols))}_{start_date}_{end_date}_{market}_{data_type}_{resolution}"
        
        if cache_key in self._data_cache:
            return self._data_cache[cache_key]
        
        # Fetch data
        df = self.data_processor.fetch_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            market=market,
            data_type=data_type,
            resolution=resolution,
        )
        
        if df.empty:
            return df
        
        # Add technical indicators
        df = self.data_processor.add_technical_indicators(df)
        
        # Cache
        self._data_cache[cache_key] = df
        
        return df
    
    def _run_backtest_on_env(
        self,
        env: SSIStockTradingEnv,
        model: Any,
    ) -> Dict[str, float]:
        """Run backtest on an environment with a model."""
        obs, info = env.reset()
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
        
        return env.get_metrics()
    
    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._data_cache.clear()
