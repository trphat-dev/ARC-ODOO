# -*- coding: utf-8 -*-
"""
Hyperparameter Tuner for FinRL using Optuna

Production-ready implementation with:
- Search spaces for all DRL algorithms (PPO, A2C, SAC, TD3, DDPG)
- Proper evaluation using backtest metrics
- Early stopping and pruning
- Result persistence
"""

import logging
import os
from typing import Dict, Any, Optional, Callable
import numpy as np

_logger = logging.getLogger(__name__)

try:
    import optuna
    from optuna.pruners import MedianPruner
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    _logger.warning("Optuna not available. Install: pip install optuna")

from .agents import DRLAgentFactory
from .constants import DRL_ALGORITHMS


# Algorithm-specific hyperparameter search spaces
SEARCH_SPACES = {
    'ppo': {
        'learning_rate': ('float_log', 1e-5, 1e-3),
        'n_steps': ('categorical', [128, 256, 512, 1024, 2048]),
        'batch_size': ('categorical', [32, 64, 128, 256]),
        'n_epochs': ('int', 3, 30),
        'gamma': ('float', 0.9, 0.9999),
        'gae_lambda': ('float', 0.9, 0.99),
        'clip_range': ('float', 0.1, 0.4),
        'ent_coef': ('float_log', 1e-8, 0.1),
        'vf_coef': ('float', 0.1, 0.9),
        'max_grad_norm': ('float', 0.3, 1.0),
    },
    'a2c': {
        'learning_rate': ('float_log', 1e-5, 1e-3),
        'n_steps': ('categorical', [5, 8, 16, 32]),
        'gamma': ('float', 0.9, 0.9999),
        'gae_lambda': ('float', 0.9, 0.99),
        'ent_coef': ('float_log', 1e-8, 0.1),
        'vf_coef': ('float', 0.1, 0.9),
        'max_grad_norm': ('float', 0.3, 1.0),
        'normalize_advantage': ('categorical', [True, False]),
    },
    'sac': {
        'learning_rate': ('float_log', 1e-5, 1e-3),
        'buffer_size': ('categorical', [10000, 50000, 100000, 500000]),
        'learning_starts': ('int', 100, 10000),
        'batch_size': ('categorical', [64, 128, 256, 512]),
        'tau': ('float', 0.001, 0.1),
        'gamma': ('float', 0.9, 0.9999),
        'train_freq': ('int', 1, 16),
        'gradient_steps': ('int', 1, 4),
        'ent_coef': ('categorical', ['auto', 0.1, 0.01]),
    },
    'td3': {
        'learning_rate': ('float_log', 1e-5, 1e-3),
        'buffer_size': ('categorical', [10000, 50000, 100000, 500000]),
        'learning_starts': ('int', 100, 10000),
        'batch_size': ('categorical', [64, 128, 256, 512]),
        'tau': ('float', 0.001, 0.1),
        'gamma': ('float', 0.9, 0.9999),
        'train_freq': ('int', 1, 16),
        'policy_delay': ('int', 1, 4),
        'target_policy_noise': ('float', 0.1, 0.5),
        'target_noise_clip': ('float', 0.3, 0.7),
    },
    'ddpg': {
        'learning_rate': ('float_log', 1e-5, 1e-3),
        'buffer_size': ('categorical', [10000, 50000, 100000, 500000]),
        'learning_starts': ('int', 100, 10000),
        'batch_size': ('categorical', [64, 128, 256]),
        'tau': ('float', 0.001, 0.1),
        'gamma': ('float', 0.9, 0.9999),
        'train_freq': ('int', 1, 16),
    },
}


class HyperparameterTuner:
    """
    Auto-tuner for DRL hyperparameters using Optuna.
    
    Target metrics:
    - Primary: Sharpe Ratio
    - Secondary: Total Return, Max Drawdown
    """
    
    def __init__(
        self,
        env_factory: Callable,
        eval_env_factory: Callable,
        algorithm: str = 'ppo',
        n_trials: int = 20,
        total_timesteps: int = 50000,
        study_name: Optional[str] = None,
        storage: Optional[str] = None,
        n_startup_trials: int = 5,
        n_warmup_steps: int = 10000,
    ):
        """
        Initialize the tuner.
        
        Args:
            env_factory: Function returning the training environment
            eval_env_factory: Function returning the evaluation environment
            algorithm: DRL algorithm to tune (ppo, a2c, sac, td3, ddpg)
            n_trials: Number of optimization trials
            total_timesteps: Training timesteps per trial
            study_name: Name for the Optuna study (for persistence)
            storage: Database URL for study persistence (e.g., 'sqlite:///optuna.db')
            n_startup_trials: Number of random trials before TPE kicks in
            n_warmup_steps: Steps before pruning can happen
        """
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna is required. Install: pip install optuna")
            
        self.env_factory = env_factory
        self.eval_env_factory = eval_env_factory
        self.algorithm = algorithm.lower()
        self.n_trials = n_trials
        self.total_timesteps = total_timesteps
        self.study_name = study_name or f"finrl_{algorithm}_study"
        self.storage = storage
        self.n_startup_trials = n_startup_trials
        self.n_warmup_steps = n_warmup_steps
        
        # Validate algorithm
        if self.algorithm not in SEARCH_SPACES:
            raise ValueError(f"Algorithm '{algorithm}' not supported. Available: {list(SEARCH_SPACES.keys())}")
        
        self.best_params = None
        self.best_value = None
        
    def optimize(self) -> Dict[str, Any]:
        """
        Run the hyperparameter optimization.
        
        Returns:
            Dictionary with best hyperparameters
        """
        _logger.info(f"Starting Optuna optimization for {self.algorithm.upper()}")
        _logger.info(f"Trials: {self.n_trials}, Timesteps per trial: {self.total_timesteps}")
        
        # Create study with TPE sampler and median pruner
        sampler = TPESampler(n_startup_trials=self.n_startup_trials)
        pruner = MedianPruner(n_startup_trials=self.n_startup_trials, n_warmup_steps=self.n_warmup_steps)
        
        study = optuna.create_study(
            study_name=self.study_name,
            storage=self.storage,
            direction="maximize",  # Maximize Sharpe ratio
            sampler=sampler,
            pruner=pruner,
            load_if_exists=True,
        )
        
        # Run optimization
        study.optimize(
            self._objective,
            n_trials=self.n_trials,
            show_progress_bar=True,
            gc_after_trial=True,
        )
        
        self.best_params = study.best_params
        self.best_value = study.best_value
        
        _logger.info(f"Optimization complete!")
        _logger.info(f"Best Sharpe Ratio: {self.best_value:.4f}")
        _logger.info(f"Best Parameters: {self.best_params}")
        
        return {
            'best_params': self.best_params,
            'best_value': self.best_value,
            'n_trials': len(study.trials),
            'algorithm': self.algorithm,
        }
    
    def _objective(self, trial: Any) -> float:
        """
        Optuna objective function.
        
        Args:
            trial: Optuna trial object
        
        Returns:
            Sharpe ratio (or negative value on failure)
        """
        # Suggest hyperparameters
        params = self._suggest_params(trial)
        
        _logger.debug(f"Trial {trial.number}: Testing params {params}")
        
        try:
            # Create environments
            train_env = self.env_factory()
            eval_env = self.eval_env_factory()
            
            # Initialize agent factory
            import tempfile
            temp_dir = os.path.join(tempfile.gettempdir(), f'finrl_optuna_trial_{trial.number}')
            agent_factory = DRLAgentFactory(
                algorithm=self.algorithm,
                model_dir=temp_dir,
                tensorboard_log=None,  # Disable TB for speed
            )
            
            # Train model
            model, training_info = agent_factory.train(
                env=DRLAgentFactory.wrap_env(train_env),
                total_timesteps=self.total_timesteps,
                custom_params=params,
                eval_env=None,  # Skip built-in eval for speed
                verbose=0,
            )
            
            # Evaluate on held-out environment
            sharpe = self._evaluate_model(model, eval_env)
            
            # Report intermediate value for pruning
            if OPTUNA_AVAILABLE:
                trial.report(sharpe, step=self.total_timesteps)
                
                # Check if trial should be pruned
                if trial.should_prune():
                    # We need to access optuna.TrialPruned dynamically to avoid NameError if import failed
                    # But if OPTUNA_AVAILABLE is false, we won't get here.
                    import optuna
                    raise optuna.TrialPruned()
            
            _logger.info(f"Trial {trial.number}: Sharpe = {sharpe:.4f}")
            return sharpe
            
        except Exception as e:
            # Handle TrialPruned explicitly if optuna is available
            if OPTUNA_AVAILABLE:
                import optuna
                if isinstance(e, optuna.TrialPruned):
                    raise
            
            _logger.warning(f"Trial {trial.number} failed: {e}", exc_info=True)
            return -10.0  # Large negative for failed trials
        finally:
            # Cleanup
            try:
                import shutil
                import tempfile
                # Reconstruct path to be safe (variable scope)
                temp_dir = os.path.join(tempfile.gettempdir(), f'finrl_optuna_trial_{trial.number}')
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except:
                pass
    
    def _evaluate_model(self, model, eval_env) -> float:
        """
        Evaluate trained model on evaluation environment.
        
        Args:
            model: Trained SB3 model
            eval_env: Evaluation environment
            
        Returns:
            Sharpe ratio
        """
        obs, _ = eval_env.reset()
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, terminated, truncated, _ = eval_env.step(action)
            done = terminated or truncated
        
        # Get metrics from environment
        metrics = eval_env.get_metrics()
        sharpe = metrics.get('sharpe_ratio', 0.0)
        total_return = metrics.get('total_return', 0.0)
        max_dd = metrics.get('max_drawdown', 0.0)
        
        # Penalize negative returns and high drawdowns
        if total_return < 0:
            sharpe -= 1.0
        if max_dd > 0.2:  # >20% drawdown
            sharpe -= 0.5
            
        return float(sharpe)
    
    def _suggest_params(self, trial: Any) -> Dict[str, Any]:
        """
        Suggest hyperparameters based on algorithm's search space.
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Dictionary of suggested hyperparameters
        """
        search_space = SEARCH_SPACES.get(self.algorithm, {})
        params = {}
        
        for param_name, config in search_space.items():
            param_type = config[0]
            
            if param_type == 'float':
                params[param_name] = trial.suggest_float(param_name, config[1], config[2])
            elif param_type == 'float_log':
                params[param_name] = trial.suggest_float(param_name, config[1], config[2], log=True)
            elif param_type == 'int':
                params[param_name] = trial.suggest_int(param_name, config[1], config[2])
            elif param_type == 'categorical':
                params[param_name] = trial.suggest_categorical(param_name, config[1])
        
        return params
    
    def get_study_dataframe(self) -> Any:
        """
        Get study results as a DataFrame for analysis.
        
        Returns:
            pandas DataFrame with trial results
        """
        if not OPTUNA_AVAILABLE:
            return None
            
        try:
            study = optuna.load_study(
                study_name=self.study_name,
                storage=self.storage,
            )
            return study.trials_dataframe()
        except:
            return None


def create_tuner(
    env_factory: Callable,
    eval_env_factory: Callable,
    algorithm: str = 'ppo',
    n_trials: int = 20,
    total_timesteps: int = 50000,
) -> HyperparameterTuner:
    """
    Factory function to create a HyperparameterTuner.
    
    Args:
        env_factory: Function returning training environment
        eval_env_factory: Function returning evaluation environment
        algorithm: DRL algorithm name
        n_trials: Number of optimization trials
        total_timesteps: Training timesteps per trial
        
    Returns:
        Configured HyperparameterTuner instance
    """
    return HyperparameterTuner(
        env_factory=env_factory,
        eval_env_factory=eval_env_factory,
        algorithm=algorithm,
        n_trials=n_trials,
        total_timesteps=total_timesteps,
    )
