# -*- coding: utf-8 -*-
"""
FinRL Service for Odoo Integration

Provides Odoo abstract model service for FinRL operations,
replacing the previous freqtrade_service.py.
"""

import base64
import gzip
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FinRLService(models.AbstractModel):
    """
    Odoo service adapter for FinRL operations.
    
    Provides methods for:
    - Training DRL agents
    - Running backtests
    - Generating predictions
    - Model management
    """
    
    _name = 'ai.finrl.service'
    _description = 'FinRL Service Adapter'
    
    # =========================================================================
    # Public API
    # =========================================================================
    
    def run_training(
        self,
        strategy: Any,
        date_from: fields.Date,
        date_to: fields.Date,
        progress_callback: Optional[callable] = None,
        initial_balance: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Run FinRL training for a strategy.
        
        Args:
            strategy: ai.strategy record
            date_from: Training start date
            date_to: Training end date
            progress_callback: Optional progress update function
            initial_balance: Optional real account balance override
        
        Returns:
            Training results with metrics
        """
        self._validate_dates(date_from, date_to)
        config = strategy.config_id
        if not config:
            raise UserError(_('Strategy must be linked to an AI Trading Configuration.'))
        
        # Get SSI client
        ssi_client = self._build_ssi_client(config)
        
        # Get FinRL client
        finrl_client = self._get_finrl_client(config, ssi_client, strategy.model_type)
        
        # Get securities
        securities = self._get_training_securities(strategy)
        symbols = [s.symbol for s in securities]
        
        if not symbols:
            raise UserError(_('No securities found for strategy.'))
        
        # Get training parameters from strategy/config
        training_params = self._get_training_params(strategy, config)
        
        _logger.info(
            f'Starting FinRL training for {len(symbols)} symbols '
            f'from {date_from} to {date_to}'
        )
        
        try:
            # 1. Hyperparameter Tuning (Optuna)
            if config.enable_optuna:
                if strategy.model_type == 'auto':
                    _logger.info("Auto (Tournament) Mode selected: Optuna tuning is skipped. Tournament will run with default parameters for fair comparison.")
                else:
                    _logger.info("Optuna enabled: Running hyperparameter optimization...")
                    if progress_callback:
                        progress_callback(0, 0, 0) # Trigger initial notification
                        
                    best_params = finrl_client.tune(
                        symbols=symbols,
                        start_date=str(date_from),
                        end_date=str(date_to),
                        algorithm=strategy.model_type,
                        total_timesteps=config.optuna_timesteps or 20000,
                        n_trials=config.optuna_trials or 10,
                        market=strategy.market,
                        data_type=strategy.data_type,
                        initial_balance=initial_balance,
                    )
                    if best_params:
                        _logger.info(f"Optuna Optimization complete. Best params: {best_params}")
                        # Update training_params with best_params
                        if 'hyperparameters' not in training_params:
                            training_params['hyperparameters'] = {}
                        training_params['hyperparameters'].update(best_params)
            
            # 2. Main Training
            if strategy.model_type == 'ensemble':
                # Sequential Ensemble Training (Tournament Mode)
                algorithms = []
                if strategy.use_algo_ppo: algorithms.append('ppo')
                if strategy.use_algo_a2c: algorithms.append('a2c')
                if strategy.use_algo_sac: algorithms.append('sac')
                if strategy.use_algo_td3: algorithms.append('td3')
                if strategy.use_algo_ddpg: algorithms.append('ddpg')
                
                if not algorithms:
                    raise UserError(_("Please select at least one algorithm for Ensemble training."))
                
                ensemble_models = []
                aggregated_metrics = {
                    'total_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'volatility': 0.0,
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'profit_factor': 0.0,
                    'training_duration_seconds': 0.0,
                }
                
                base_model_name = self._generate_model_name(strategy)
                
                for idx, alg in enumerate(algorithms):
                    _logger.info(f"Ensemble Tournament: Training {alg.upper()} ({idx+1}/{len(algorithms)})...")
                    
                    # Custom progress callback wrapper
                    # Maps 0-100% of this alg to a slice of total progress
                    # e.g. 5 algorithms: 0-20%, 20-40%, etc.
                    def ensemble_progress(prog, step, total):
                        chunk_size = 100.0 / len(algorithms)
                        base_progress = idx * chunk_size
                        scaled_progress = base_progress + (prog * (chunk_size / 100.0))
                        if progress_callback:
                            progress_callback(scaled_progress, step, total)
                            
                    alg_result = finrl_client.train(
                        symbols=symbols,
                        start_date=str(date_from),
                        end_date=str(date_to),
                        algorithm=alg,
                        market=strategy.market,
                        data_type=strategy.data_type,
                        resolution=strategy.intraday_resolution or '1',
                        total_timesteps=training_params.get('total_timesteps'),
                        custom_params=training_params.get('hyperparameters'),
                        action_space_type='continuous', # Ensemble works best with continuous/comparable actions
                        progress_callback=ensemble_progress,
                        initial_balance=initial_balance,
                    )
                    
                    # Aggregate Metrics (Simple Average for now, or take Best?)
                    # For ensemble, we really care about the FINAL ensemble performance, 
                    # but we can sum duration and track individual stats if needed.
                    metrics = alg_result.get('metrics', {})
                    aggregated_metrics['training_duration_seconds'] += alg_result.get('training_duration_seconds', 0)
                    
                    # Save individual model with specific name
                    alg_model_name = f"{base_model_name}_{alg}"
                    alg_model_path = finrl_client.save_model(alg_model_name)
                    
                    # Load model object to list for EnsembleAgent
                    # We need the actual model object, not just path. 
                    # FinRLClient.agent_factory.model has the current one.
                    if finrl_client.agent_factory and finrl_client.agent_factory.model:
                        ensemble_models.append(finrl_client.agent_factory.model)
                
                # Create Ensemble Agent
                from .finrl.agents import EnsembleAgent
                ensemble_agent = EnsembleAgent(ensemble_models, voting='soft')
                
                # Save Ensemble
                ensemble_path = os.path.join(finrl_client.model_dir, base_model_name)
                ensemble_agent.save(ensemble_path)
                
                # Final Backtest with Ensemble to get REAL metrics
                # We need to load the ensemble into the client or run backtest manually
                # FinRLClient doesn't natively support loading EnsembleAgent in backtest() yet 
                # strictly by path unless we modify load_model (which we did verify support for folders/configs)
                
                # Let's use the client to run backtest, passing the path.
                # Our client.load_model supports checking for _ensemble_config.json
                # So we just pass the base name/path.
                
                backtest_result = finrl_client.backtest(
                    symbols=symbols,
                    start_date=str(date_from),
                    end_date=str(date_to),
                    model_name_or_path=ensemble_path, # Pass path to ensemble
                    market=strategy.market,
                    data_type=strategy.data_type,
                    action_space_type='continuous',
                    mode='simple',
                )
                
                final_metrics = backtest_result.get('metrics', {})
                result = {
                    'model_path': ensemble_path + ".zip", # Mock zip extension for Odoo compatibility
                    'model_name': base_model_name,
                    'algorithm': 'ensemble',
                    'training_samples': alg_result.get('training_samples', 0), # Same for all
                    'training_duration_seconds': aggregated_metrics['training_duration_seconds'],
                    'metrics': final_metrics,
                    'params': training_params,
                }
                
            else:
                # Standard Single Model Training
                result = finrl_client.train(
                    symbols=symbols,
                    start_date=str(date_from),
                    end_date=str(date_to),
                    algorithm=strategy.model_type,
                    market=strategy.market,
                    data_type=strategy.data_type,
                    resolution=strategy.intraday_resolution or '1',
                    total_timesteps=training_params.get('total_timesteps'),
                    custom_params=training_params.get('hyperparameters'),
                    action_space_type=training_params.get('action_space_type', 'discrete'),
                    progress_callback=progress_callback,
                    initial_balance=initial_balance,
                )
                
                # Save model
                model_name = self._generate_model_name(strategy)
                model_path = finrl_client.save_model(model_name)
                result['model_path'] = model_path
                result['model_name'] = model_name
            
            # Convert metrics to training record format
            metrics = result.get('metrics', {})
            
            # Debug logging to trace metrics
            _logger.info(f"Training result metrics: {metrics}")
            _logger.info(f"Total return: {metrics.get('total_return', 'N/A')}")
            _logger.info(f"Sharpe ratio: {metrics.get('sharpe_ratio', 'N/A')}")
            _logger.info(f"N trades: {metrics.get('n_trades', 'N/A')}")
            _logger.info(f"Win rate: {metrics.get('win_rate', 'N/A')}")
            
            return {
                'cumulative_reward': metrics.get('total_return', 0.0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0.0),
                'max_drawdown': metrics.get('max_drawdown', 0.0),
                'total_trades': metrics.get('n_trades', 0),
                'volatility': metrics.get('volatility', 0.0),
                'final_portfolio_value': metrics.get('final_portfolio_value', 0.0),
                'win_rate': metrics.get('win_rate', 0.0),
                'profit_factor': metrics.get('profit_factor', 0.0),
                'winning_trades': metrics.get('winning_trades', 0),
                'losing_trades': metrics.get('losing_trades', 0),
                'training_duration_seconds': result.get('training_duration_seconds', 0),
                'training_samples': result.get('training_samples', 0),
                'algorithm': result.get('algorithm'),
                'model_path': result.get('model_path'),
                'model_name': result.get('model_name'),
                'params': result.get('params', {}),
                'log': f"Training completed for {len(symbols)} symbols with {result.get('training_samples', 0)} samples",
            }
            
        except Exception as e:
            _logger.error(f'FinRL training failed: {e}', exc_info=True)
            raise UserError(_('FinRL training failed: %s') % str(e))
    
    def run_training_per_symbol(
        self,
        strategy: Any,
        date_from: fields.Date,
        date_to: fields.Date,
        progress_callback: Optional[callable] = None,
        initial_balance: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Run FinRL training for each symbol individually.
        
        This method trains a separate model for each symbol in the strategy,
        enabling more accurate per-symbol predictions for index-based strategies.
        
        Args:
            strategy: ai.strategy record
            date_from: Training start date
            date_to: Training end date
            progress_callback: Optional progress update function
            initial_balance: Optional real account balance override
        
        Returns:
            Training results with per-symbol model paths and aggregated metrics
        """
        self._validate_dates(date_from, date_to)
        config = strategy.config_id
        if not config:
            raise UserError(_('Strategy must be linked to an AI Trading Configuration.'))
        
        # Get SSI client
        ssi_client = self._build_ssi_client(config)
        
        # Get securities
        securities = self._get_training_securities(strategy)
        
        if not securities:
            raise UserError(_('No securities found for strategy.'))
        
        # Get training parameters
        training_params = self._get_training_params(strategy, config)
        
        _logger.info(
            f'Starting per-symbol FinRL training for {len(securities)} symbols '
            f'from {date_from} to {date_to}'
        )
        
        # Results aggregation
        symbol_results = {}
        aggregated_metrics = {
            'cumulative_reward': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'total_trades': 0,
            'win_rate': 0.0,
            'training_duration_seconds': 0.0,
            'training_samples': 0,
        }
        
        total_symbols = len(securities)
        
        for idx, security in enumerate(securities):
            symbol = security.symbol
            _logger.info(f'Training symbol {idx+1}/{total_symbols}: {symbol}')
            
            try:
                # Progress callback for this symbol
                def symbol_progress(prog, step, total):
                    if progress_callback:
                        # Map symbol progress to overall progress
                        base_progress = (idx / total_symbols) * 100
                        symbol_contrib = (1 / total_symbols) * prog
                        overall_progress = base_progress + symbol_contrib
                        progress_callback(overall_progress, step, total)
                
                # Get fresh FinRL client for each symbol
                finrl_client = self._get_finrl_client(config, ssi_client, strategy.model_type)
                
                # Train single symbol
                result = finrl_client.train(
                    symbols=[symbol],  # Single symbol
                    start_date=str(date_from),
                    end_date=str(date_to),
                    algorithm=strategy.model_type,
                    market=strategy.market,
                    data_type=strategy.data_type,
                    resolution=strategy.intraday_resolution or '1',
                    total_timesteps=training_params.get('total_timesteps'),
                    custom_params=training_params.get('hyperparameters'),
                    action_space_type=training_params.get('action_space_type', 'discrete'),
                    progress_callback=symbol_progress,
                    initial_balance=initial_balance,
                )
                
                # Save model with symbol-specific name
                model_name = f"strategy_{strategy.id}_{symbol}_{strategy.model_type}_{datetime.now().strftime('%Y%m%d')}"
                model_path = finrl_client.save_model(model_name)
                
                # Store per-symbol result
                metrics = result.get('metrics', {})
                symbol_results[symbol] = {
                    'model_path': model_path,
                    'model_name': model_name,
                    'security_id': security.id,
                    'cumulative_reward': metrics.get('total_return', 0.0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0.0),
                    'max_drawdown': metrics.get('max_drawdown', 0.0),
                    'total_trades': metrics.get('n_trades', 0),
                    'win_rate': metrics.get('win_rate', 0.0),
                    'training_samples': result.get('training_samples', 0),
                }
                
                # Aggregate metrics
                aggregated_metrics['cumulative_reward'] += metrics.get('total_return', 0.0)
                aggregated_metrics['sharpe_ratio'] += metrics.get('sharpe_ratio', 0.0)
                aggregated_metrics['max_drawdown'] = max(
                    aggregated_metrics['max_drawdown'], 
                    metrics.get('max_drawdown', 0.0)
                )
                aggregated_metrics['total_trades'] += metrics.get('n_trades', 0)
                aggregated_metrics['win_rate'] += metrics.get('win_rate', 0.0)
                aggregated_metrics['training_duration_seconds'] += result.get('training_duration_seconds', 0)
                aggregated_metrics['training_samples'] += result.get('training_samples', 0)
                
                _logger.info(f'Completed training for {symbol}: Sharpe={metrics.get("sharpe_ratio", 0):.4f}')
                
            except Exception as e:
                _logger.error(f'Failed to train symbol {symbol}: {e}', exc_info=True)
                symbol_results[symbol] = {
                    'error': str(e),
                    'security_id': security.id,
                }
        
        # Average the rate-based metrics
        if total_symbols > 0:
            aggregated_metrics['cumulative_reward'] /= total_symbols
            aggregated_metrics['sharpe_ratio'] /= total_symbols
            aggregated_metrics['win_rate'] /= total_symbols
        
        return {
            'symbol_results': symbol_results,
            'aggregated_metrics': aggregated_metrics,
            'cumulative_reward': aggregated_metrics['cumulative_reward'],
            'sharpe_ratio': aggregated_metrics['sharpe_ratio'],
            'max_drawdown': aggregated_metrics['max_drawdown'],
            'total_trades': aggregated_metrics['total_trades'],
            'win_rate': aggregated_metrics['win_rate'],
            'training_duration_seconds': aggregated_metrics['training_duration_seconds'],
            'training_samples': aggregated_metrics['training_samples'],
            'algorithm': strategy.model_type,
            'params': training_params,
            'log': f"Per-symbol training completed for {len(symbol_results)} symbols",
        }
    
    def run_backtest(
        self,
        strategy: Any,
        date_from: fields.Date,
        date_to: fields.Date,
        mode: str = 'simple',
        benchmark_symbol: Optional[str] = None,
        n_monte_carlo: Optional[int] = None,
        n_walk_forward_windows: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run FinRL backtest for a strategy.
        
        Args:
            strategy: ai.strategy record
            date_from: Backtest start date
            date_to: Backtest end date
            mode: 'simple', 'walk_forward', or 'monte_carlo'
            benchmark_symbol: Symbol for benchmark comparison
            n_monte_carlo: Number of Monte Carlo simulations
            n_walk_forward_windows: Number of WFA windows
        
        Returns:
            Backtest results with comprehensive metrics
        """
        self._validate_dates(date_from, date_to)
        config = strategy.config_id
        if not config:
            raise UserError(_('Strategy must be linked to an AI Trading Configuration.'))
        
        # Get SSI client
        ssi_client = self._build_ssi_client(config)
        
        # Get FinRL client
        finrl_client = self._get_finrl_client(config, ssi_client, strategy.model_type)
        
        # Load model if available
        model_path = self._get_latest_model_path(strategy)
        if model_path:
            finrl_client.load_model(model_path, algorithm=strategy.model_type)
        else:
            raise UserError(_('No trained model found for strategy. Please train the model first.'))
        
        # Get securities
        securities = self._get_training_securities(strategy)
        symbols = [s.symbol for s in securities]
        
        _logger.info(
            f'Starting FinRL {mode} backtest for {len(symbols)} symbols '
            f'from {date_from} to {date_to}'
        )
        
        try:
            result = finrl_client.backtest(
                symbols=symbols,
                start_date=str(date_from),
                end_date=str(date_to),
                market=strategy.market,
                data_type=strategy.data_type,
                mode=mode,
                benchmark_symbol=benchmark_symbol,
                n_monte_carlo=n_monte_carlo,
                n_walk_forward_windows=n_walk_forward_windows,
            )
            
            metrics = result.get('metrics', {})
            
            # Build standardized response
            response = {
                'total_return': metrics.get('total_return', 0.0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0.0),
                'sortino_ratio': metrics.get('sortino_ratio', 0.0),
                'calmar_ratio': metrics.get('calmar_ratio', 0.0),
                'max_drawdown': metrics.get('max_drawdown', 0.0),
                'volatility': metrics.get('volatility', 0.0),
                'total_trades': metrics.get('total_trades', 0),
                'win_rate': metrics.get('win_rate', 0.0),
                'profit_factor': metrics.get('profit_factor', 0.0),
                'alpha': metrics.get('alpha', 0.0),
                'beta': metrics.get('beta', 0.0),
                'var_95': metrics.get('var_95', 0.0),
                'cvar_95': metrics.get('cvar_95', 0.0),
                'profit_pct': metrics.get('total_return', 0.0) * 100,
                'wins': self._count_winning_trades(result.get('trades', [])),
                'losses': self._count_losing_trades(result.get('trades', [])),
                'portfolio_values': result.get('portfolio_values', []),
                'trades': result.get('trades', []),
                'metrics': metrics,  # Full metrics dict
            }
            
            # Add mode-specific results
            if result.get('walk_forward_results'):
                response['walk_forward_results'] = result['walk_forward_results']
                response['wfa_consistency'] = metrics.get('wfa_consistency', 0.0)
            
            if result.get('monte_carlo'):
                response['monte_carlo'] = result['monte_carlo']
            
            if result.get('benchmark'):
                response['benchmark'] = result['benchmark']
            
            return response
            
        except Exception as e:
            _logger.error(f'FinRL backtest failed: {e}', exc_info=True)
            raise UserError(_('FinRL backtest failed: %s') % str(e))
    
    def generate_prediction(
        self,
        strategy: Any,
        security: Any,
    ) -> Dict[str, Any]:
        """
        Generate prediction for a security using trained model.
        
        For index mode strategies, uses the symbol-specific model if available.
        For manual mode, uses the shared portfolio model.
        
        Args:
            strategy: ai.strategy record
            security: ssi.securities record
        
        Returns:
            Prediction with signal and confidence
        """
        config = strategy.config_id
        if not config:
            raise UserError(_('Strategy must be linked to an AI Trading Configuration.'))
        
        # Get SSI client
        ssi_client = self._build_ssi_client(config)
        
        # Get FinRL client
        finrl_client = self._get_finrl_client(config, ssi_client, strategy.model_type)
        
        # Determine model path - prefer per-symbol model for index mode
        model_path = None
        symbol = security.symbol
        
        # Try to get symbol-specific model from latest training
        if hasattr(strategy, 'selection_mode') and strategy.selection_mode == 'index':
            training_record = self.env['ai.model.training'].search([
                ('strategy_id', '=', strategy.id),
                ('state', '=', 'completed'),
            ], order='create_date desc', limit=1)
            
            if training_record and training_record.symbol_results_json:
                try:
                    symbol_results = json.loads(training_record.symbol_results_json)
                    if symbol in symbol_results and symbol_results[symbol].get('model_path'):
                        model_path = symbol_results[symbol]['model_path']
                        _logger.info(f'Using per-symbol model for {symbol}: {model_path}')
                except (json.JSONDecodeError, KeyError) as e:
                    _logger.warning(f'Failed to parse symbol_results_json: {e}')
        
        # Fallback to strategy-level model
        if not model_path:
            model_path = self._get_latest_model_path(strategy)
        
        if model_path:
            finrl_client.load_model(model_path, algorithm=strategy.model_type)
        else:
            raise UserError(_('No trained model found. Please train the model first.'))
        
        try:
            result = finrl_client.predict(
                symbol=symbol,
                market=security.market,
                lookback_days=200,
            )
            
            return {
                'signal': result.get('signal', 'hold'),
                'confidence': result.get('confidence', 0.0),
                'action_value': result.get('action_value', 0.0),
                'current_price': result.get('current_price', 0.0),
                'prediction_date': result.get('prediction_date'),
            }
            
        except Exception as e:
            _logger.error(f'FinRL prediction failed for {security.symbol}: {e}', exc_info=True)
            # Return hold signal on error
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'action_value': 0.0,
                'current_price': 0.0,
                'error': str(e),
            }
    
    # =========================================================================
    # Internal Helpers
    # =========================================================================
    
    def _validate_dates(self, date_from, date_to) -> None:
        """Validate date range."""
        if not date_from or not date_to:
            raise UserError(_('Both start and end dates are required.'))
        if date_from >= date_to:
            raise UserError(_('Start date must be before end date.'))
    
    def _build_ssi_client(self, config) -> Any:
        """Build SSI client from config."""
        if not config.ssi_config_id:
            raise UserError(_('SSI API configuration is required.'))
        
        try:
            from .ssi_client import SSIClient
        except ImportError as e:
            raise UserError(_('Cannot import SSIClient: %s') % str(e))
        
        return SSIClient(config=config.ssi_config_id, env=self.env)
    
    def _get_finrl_client(self, config, ssi_client, algorithm: str) -> Any:
        """Get FinRL client instance."""
        try:
            from .finrl import FinRLClient
        except ImportError as e:
            raise UserError(
                _('FinRL is not installed. Please install: pip install finrl stable-baselines3. Error: %s') % str(e)
            )
        
        # Get model directory from config or use default
        model_dir = self._get_model_directory(config)
        tensorboard_log = self._get_tensorboard_directory(config)
        
        return FinRLClient(
            ssi_client=ssi_client,
            model_dir=model_dir,
            tensorboard_log=tensorboard_log,
            algorithm=algorithm,
        )
    
    def _get_model_directory(self, config) -> str:
        """Get model directory from config."""
        if hasattr(config, 'finrl_model_dir') and config.finrl_model_dir:
            return os.path.expanduser(config.finrl_model_dir)
        return os.path.expanduser('~/.finrl/models')
    
    def _get_tensorboard_directory(self, config) -> str:
        """Get TensorBoard log directory from config."""
        if hasattr(config, 'finrl_tensorboard_log') and config.finrl_tensorboard_log:
            return os.path.expanduser(config.finrl_tensorboard_log)
        return os.path.expanduser('~/.finrl/logs')
    
    def _get_training_params(self, strategy, config) -> Dict[str, Any]:
        """Get training parameters from strategy and config."""
        params = {}
        
        # Timesteps: Always use full data mode (0 = dynamic based on data length in client.py)
        params['total_timesteps'] = 0
        
        # Learning rate
        hyperparameters = {}
        if hasattr(config, 'learning_rate') and config.learning_rate:
            hyperparameters['learning_rate'] = config.learning_rate
        
        if hyperparameters:
            params['hyperparameters'] = hyperparameters
        
        # Action space type
        if hasattr(strategy, 'action_space_type') and strategy.action_space_type:
            params['action_space_type'] = strategy.action_space_type
        elif strategy.model_type == 'ensemble':
            # Force continuous to support DDPG, SAC, TD3 in ensemble
            params['action_space_type'] = 'continuous'
        else:
            params['action_space_type'] = 'discrete'
        
        return params
    
    def _get_training_securities(self, strategy) -> Any:
        """Get securities for training based on selection mode."""
        # Use effective_security_ids which respects selection_mode (manual/index)
        securities = getattr(strategy, 'effective_security_ids', None)
        if securities is None:
            # Fallback for backward compatibility
            securities = strategy.security_ids
        
        if not securities:
            securities = self.env['ssi.securities'].search([
                ('market', '=', strategy.market),
                ('is_active', '=', True),
            ])
        
        if not securities:
            raise UserError(
                _('No securities found for market %s. Please sync securities from SSI API first.') 
                % strategy.market
            )
        
        return securities
    
    def _get_latest_model_path(self, strategy) -> Optional[str]:
        """Get path to latest trained model for strategy."""
        # Check if model_path is stored in strategy
        if hasattr(strategy, 'model_path') and strategy.model_path:
            if os.path.exists(strategy.model_path):
                return strategy.model_path
        
        # Check training records
        training_records = self.env['ai.model.training'].search([
            ('strategy_id', '=', strategy.id),
            ('state', '=', 'completed'),
        ], order='create_date desc', limit=1)
        
        if training_records and training_records.model_path:
            if os.path.exists(training_records.model_path):
                return training_records.model_path
        
        # Try default path
        config = strategy.config_id
        if config:
            model_dir = Path(self._get_model_directory(config))
            # Look for any model matching strategy
            pattern = f"strategy_{strategy.id}_*.zip"
            matches = sorted(model_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
            if matches:
                return str(matches[0])
        
        return None
    
    def _count_winning_trades(self, trades: List[Dict]) -> int:
        """Count profitable trades."""
        wins = 0
        for trade in trades:
            if trade.get('action') == 'sell':
                # Simple check: if proceeds > 0, consider it a completed trade
                if trade.get('proceeds', 0) > 0:
                    wins += 1
        return wins
    
    def _count_losing_trades(self, trades: List[Dict]) -> int:
        """Count losing trades."""
        # For simplicity, count all sells as potential losses/wins
        sells = [t for t in trades if t.get('action') == 'sell']
        return max(0, len(sells) - self._count_winning_trades(trades))
    
    def _generate_model_name(self, strategy) -> str:
        """Generate a unique model name for a strategy.
        
        Args:
            strategy: ai.strategy record
            
        Returns:
            Unique model name string
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"strategy_{strategy.id}_{strategy.model_type}_{timestamp}"

