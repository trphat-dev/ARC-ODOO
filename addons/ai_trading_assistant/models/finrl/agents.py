# -*- coding: utf-8 -*-
"""
DRL Agent Factory for FinRL

Provides a unified interface for creating, training, and using
DRL agents from Stable-Baselines3.
"""

import json
import logging
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import numpy as np

from .constants import (
    DRL_ALGORITHMS,
    DEFAULT_TRAINING_PARAMS,
    MODEL_FILE_EXTENSIONS,
)

_logger = logging.getLogger(__name__)

# Stable-Baselines3 import with detailed error handling
SB3_AVAILABLE = False
SB3_AGENTS: Dict[str, Type] = {}

try:
    from stable_baselines3 import PPO, A2C, SAC, TD3, DDPG
    from stable_baselines3.common.callbacks import (
        BaseCallback,
        CallbackList,
        CheckpointCallback,
        EvalCallback,
    )
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.vec_env import DummyVecEnv
    
    SB3_AVAILABLE = True
    SB3_AGENTS = {
        'ppo': PPO,
        'a2c': A2C,
        'sac': SAC,
        'td3': TD3,
        'ddpg': DDPG,
    }
    IMPORT_ERROR = None
except ImportError as e:
    IMPORT_ERROR = str(e)
    _logger.warning(f'Stable-Baselines3 not available: {e}')


class TrainingCallback(BaseCallback if SB3_AVAILABLE else object):
    """
    Custom callback for tracking training progress.
    
    Reports progress to an optional callback function for UI updates.
    """
    
    def __init__(
        self,
        total_timesteps: int,
        progress_callback: Optional[callable] = None,
        update_interval: int = 1000,
        verbose: int = 0,
    ):
        """
        Initialize the callback.
        
        Args:
            total_timesteps: Total training timesteps
            progress_callback: Function to call with progress updates
            update_interval: Timesteps between progress updates
            verbose: Verbosity level
        """
        if SB3_AVAILABLE:
            super().__init__(verbose)
        self.total_timesteps = total_timesteps
        self.progress_callback = progress_callback
        self.update_interval = update_interval
        self.last_update = 0
    
    def _on_step(self) -> bool:
        """Called at each training step."""
        if self.progress_callback and self.n_calls - self.last_update >= self.update_interval:
            steps = min(self.n_calls, self.total_timesteps)
            progress = min(100.0, (steps / self.total_timesteps) * 100)
            self.progress_callback(progress, steps, self.total_timesteps)
            self.last_update = self.n_calls
        return True


class DRLAgentFactory:
    """
    Factory for creating and managing DRL agents.
    
    Supports PPO, A2C, SAC, TD3, DDPG from Stable-Baselines3.
    """
    
    def __init__(
        self,
        algorithm: str = 'ppo',
        model_dir: Optional[str] = None,
        tensorboard_log: Optional[str] = None,
    ):
        """
        Initialize the agent factory.
        
        Args:
            algorithm: DRL algorithm name (ppo, a2c, sac, td3, ddpg)
            model_dir: Directory for saving models
            tensorboard_log: Directory for TensorBoard logs
        """
        if not SB3_AVAILABLE:
            raise ImportError(
                f'Stable-Baselines3 is required. '
                f'Error: {IMPORT_ERROR}. '
                'Install with: pip install stable-baselines3'
            )
        
        self.algorithm = algorithm.lower()
        if self.algorithm not in DRL_ALGORITHMS:
            raise ValueError(
                f'Unknown algorithm: {algorithm}. '
                f'Available: {list(DRL_ALGORITHMS.keys())}'
            )
        
        self.model_dir = Path(model_dir or '~/.finrl/models').expanduser()
        self.tensorboard_log = Path(tensorboard_log or '~/.finrl/logs').expanduser()
        
        # Ensure directories exist
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.tensorboard_log.mkdir(parents=True, exist_ok=True)
        
        self.model: Optional[Any] = None
        self.training_metadata: Dict[str, Any] = {}
    
    @property
    def agent_class(self) -> Type:
        """Get the Stable-Baselines3 agent class."""
        return SB3_AGENTS[self.algorithm]
    
    @property
    def algorithm_config(self) -> Dict[str, Any]:
        """Get the algorithm configuration."""
        return DRL_ALGORITHMS[self.algorithm]
    
    def create_agent(
        self,
        env: Any,
        custom_params: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
    ) -> Any:
        """
        Create a new DRL agent.
        
        Args:
            env: Gymnasium environment
            custom_params: Custom hyperparameters to override defaults
            seed: Random seed for reproducibility
        
        Returns:
            Configured DRL agent
        """
        # Get default parameters
        params = self.algorithm_config['default_params'].copy()
        
        # Override with custom parameters
        if custom_params:
            params.update(custom_params)
        
        # Get policy name
        policy = self.algorithm_config.get('policy', 'MlpPolicy')
        
        # Create agent
        self.model = self.agent_class(
            policy=policy,
            env=env,
            tensorboard_log=str(self.tensorboard_log),
            seed=seed,
            verbose=1,
            **params,
        )
        
        _logger.info(
            f'Created {self.algorithm.upper()} agent with policy {policy}'
        )
        
        return self.model
    
    def train(
        self,
        env: Any,
        total_timesteps: Optional[int] = None,
        eval_env: Optional[Any] = None,
        eval_freq: int = 1000,
        n_eval_episodes: int = 5,
        progress_callback: Optional[callable] = None,
        custom_params: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Train a DRL agent.
        
        Args:
            env: Training environment
            total_timesteps: Number of training timesteps
            eval_env: Evaluation environment (optional)
            eval_freq: Evaluation frequency in timesteps
            n_eval_episodes: Number of evaluation episodes
            progress_callback: Function for progress updates
            custom_params: Custom hyperparameters
            seed: Random seed
        
        Returns:
            Tuple of (trained_model, training_info)
        """
        # total_timesteps is expected to be set by caller (client.py sets it based on data length)
        
        # Create agent if not exists
        if self.model is None:
            self.create_agent(env, custom_params, seed)
        
        # Build callbacks
        callbacks = []
        
        # Progress callback
        callbacks.append(
            TrainingCallback(
                total_timesteps=total_timesteps,
                progress_callback=progress_callback,
            )
        )
        
        # Evaluation callback
        if eval_env is not None:
            eval_callback = EvalCallback(
                eval_env,
                best_model_save_path=str(self.model_dir / 'best'),
                log_path=str(self.tensorboard_log),
                eval_freq=eval_freq,
                n_eval_episodes=n_eval_episodes,
                deterministic=True,
            )
            callbacks.append(eval_callback)
        
        # Checkpoint callback
        checkpoint_callback = CheckpointCallback(
            save_freq=max(1, total_timesteps // 10),
            save_path=str(self.model_dir / 'checkpoints'),
            name_prefix=f'{self.algorithm}_checkpoint',
        )
        callbacks.append(checkpoint_callback)
        
        # Train
        start_time = datetime.utcnow()
        _logger.info(f'Starting training for {total_timesteps} timesteps')
        
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=CallbackList(callbacks),
            progress_bar=True,
        )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Record metadata
        self.training_metadata = {
            'algorithm': self.algorithm,
            'total_timesteps': total_timesteps,
            'training_duration_seconds': duration,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'params': custom_params or self.algorithm_config['default_params'],
        }
        
        _logger.info(f'Training completed in {duration:.1f}s')
        
        return self.model, self.training_metadata
    
    def predict(
        self,
        observation: np.ndarray,
        deterministic: bool = True,
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Get action prediction from the trained model.
        
        Args:
            observation: Current observation
            deterministic: Whether to use deterministic policy
        
        Returns:
            Tuple of (action, state)
        """
        if self.model is None:
            raise ValueError('No model loaded. Train or load a model first.')
        
        action, state = self.model.predict(observation, deterministic=deterministic)
        return action, state

    def predict_proba(
        self,
        observation: np.ndarray,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[float]]:
        """
        Get action prediction AND probability/confidence from the trained model.
        
        International Standard: Uses the policy's probability distribution.
        
        Args:
            observation: Current observation
        
        Returns:
            Tuple of (action, state, confidence_score)
        """
        if self.model is None:
            raise ValueError('No model loaded. Train or load a model first.')
            
        # Standard prediction
        action, state = self.model.predict(observation, deterministic=True)
        
        confidence = 0.0
        try:
            # Access probability distribution from the policy
            # Note: This requires the observation to be converted to tensor if not handled by helper
            import torch
            
            # SB3 models usually handle numpy->tensor conversion in predict(), but for accessing policy directly we might need help.
            # However, model.policy.get_distribution(obs_as_tensor) is the way.
            # Using model.policy.obs_to_tensor
            obs_tensor, _ = self.model.policy.obs_to_tensor(observation)
            distribution = self.model.policy.get_distribution(obs_tensor)
            
            # Robustly check distribution type
            if hasattr(distribution, 'distribution') and hasattr(distribution.distribution, 'probs'):
                # Categorical (Discrete)
                probs = distribution.distribution.probs
                # Get probability of the chosen action
                # action might be scalar or array
                if isinstance(action, np.ndarray):
                    act_idx = int(action.item())
                else:
                    act_idx = int(action)
                    
                confidence = float(probs[0][act_idx].item()) # probs is usuall [batch, n_actions]
                
            elif hasattr(distribution, 'distribution') and hasattr(distribution.distribution, 'stddev'):
                # Diagonal Gaussian (Continuous)
                # Confidence is inverse of uncertainty (stddev)
                # This is trickier, but generally lower stddev = higher confidence
                # Let's fallback to action magnitude for continuous as "Trend Conviction"
                # But we can check stddev to see if model is "unsure"
                std = distribution.distribution.stddev.mean().item()
                # If std is low, high confidence. If std is high, low confidence.
                # Heuristic mapping: Ref std usually 1.0 at start
                confidence = max(0.0, min(1.0, 1.0 - std))
            else:
                # Fallback
                confidence = 0.0
                
        except Exception as e:
            _logger.warning(f'Failed to extract policy probability: {e}')
            confidence = 0.0
            
        return action, state, confidence
    
    def save(
        self,
        name: str,
        include_replay_buffer: bool = False,
    ) -> str:
        """
        Save the trained model.
        
        Args:
            name: Model name (without extension)
            include_replay_buffer: Whether to save replay buffer (for off-policy algorithms)
        
        Returns:
            Path to saved model
        """
        if self.model is None:
            raise ValueError('No model to save. Train a model first.')
        
        model_path = self.model_dir / f'{name}{MODEL_FILE_EXTENSIONS["model"]}'
        metadata_path = self.model_dir / f'{name}{MODEL_FILE_EXTENSIONS["metadata"]}'
        
        # Save model
        self.model.save(str(model_path.with_suffix('')))
        _logger.info(f'Model saved to {model_path}')
        
        # Save replay buffer for off-policy algorithms
        if include_replay_buffer and self.algorithm in ('sac', 'td3', 'ddpg'):
            if hasattr(self.model, 'replay_buffer') and self.model.replay_buffer is not None:
                buffer_path = self.model_dir / f'{name}{MODEL_FILE_EXTENSIONS["replay_buffer"]}'
                with open(buffer_path, 'wb') as f:
                    pickle.dump(self.model.replay_buffer, f)
                _logger.info(f'Replay buffer saved to {buffer_path}')
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(self.training_metadata, f, indent=2, default=str)
        _logger.info(f'Metadata saved to {metadata_path}')
        
        return str(model_path)
    
    def load(
        self,
        name_or_path: str,
        env: Optional[Any] = None,
    ) -> Any:
        """
        Load a trained model.
        
        Args:
            name_or_path: Model name or full path
            env: Environment for the model (optional)
        
        Returns:
            Loaded model
        """
        # Determine path
        model_path = Path(name_or_path)
        if not model_path.is_file():
            # Try in model directory
            model_path = self.model_dir / f'{name_or_path}{MODEL_FILE_EXTENSIONS["model"]}'
        
        if not model_path.exists():
            raise FileNotFoundError(f'Model not found: {model_path}')
        
        # Load model
        self.model = self.agent_class.load(
            str(model_path.with_suffix('')),
            env=env,
        )
        _logger.info(f'Model loaded from {model_path}')
        
        # Load metadata if available
        metadata_path = model_path.with_name(
            model_path.stem.replace('.zip', '') + MODEL_FILE_EXTENSIONS['metadata']
        )
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.training_metadata = json.load(f)
        
        return self.model
    
    def get_available_algorithms(self) -> Dict[str, str]:
        """
        Get available DRL algorithms with descriptions.
        
        Returns:
            Dictionary mapping algorithm name to description
        """
        return {
            name: config['description']
            for name, config in DRL_ALGORITHMS.items()
        }
    
    @staticmethod
    def wrap_env(env: Any) -> Any:
        """
        Wrap environment for Stable-Baselines3 compatibility.
        
        Args:
            env: Raw environment
        
        Returns:
            Wrapped environment
        """
        if not SB3_AVAILABLE:
            return env
        
        # Wrap with Monitor for logging
        env = Monitor(env)
        
        env = DummyVecEnv([lambda: env])
        
        return env


class EnsembleAgent:
    """
    Ensemble Agent that combines predictions from multiple models.
    
    Implements a voting/averaging mechanism to reduce variance and improve
    robustness of trading decisions.
    
    Strategies:
    - soft_vote: Average the probability/action values (default)
    - hard_vote: Majority class vote (for discrete actions)
    """
    
    def __init__(self, models: List[Any], voting: str = 'soft'):
        """
        Initialize the Ensemble Agent.
        
        Args:
            models: List of loaded Stable-Baselines3 models
            voting: 'soft' (average) or 'hard' (majority)
        """
        self.models = models
        self.voting = voting
        
    def predict(
        self, 
        observation: np.ndarray, 
        deterministic: bool = True
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Predict aggregate action.
        
        Args:
            observation: Current observation
            deterministic: Whether to use deterministic mode
            
        Returns:
            Tuple of (aggregated_action, None)
        """
        actions = []
        for model in self.models:
            action, _ = model.predict(observation, deterministic=deterministic)
            actions.append(action)
            
        if not actions:
            return np.array([1]), None  # Default Hold
            
        # Stack actions: Shape (n_models, n_envs, action_dim) or (n_models, n_envs)
        # Assuming single env for inference usually
        stacked_actions = np.stack(actions)
        
        if self.voting == 'soft':
            # Average the action values
            # For continuous: simple mean
            # For discrete: PPO outputs class index. Averaging indices sucks.
            # We need to distinguish discrete vs continuous based on action shape/type
            
            # Check if discrete (scalar integers)
            if np.issubdtype(stacked_actions.dtype, np.integer) or (
                stacked_actions.ndim > 1 and stacked_actions.shape[-1] == 1
            ):
                 # Discrete Hard Vote is safer than averaging indices
                 # Use mode (majority vote)
                 from scipy import stats
                 mode_result = stats.mode(stacked_actions, axis=0)
                 final_action = mode_result.mode[0] if hasattr(mode_result, 'mode') else mode_result[0]
            else:
                # Continuous: Average
                final_action = np.mean(stacked_actions, axis=0)
                
        else: # Hard vote
             # Majority vote
             from scipy import stats
             mode_result = stats.mode(stacked_actions, axis=0)
             final_action = mode_result.mode[0] if hasattr(mode_result, 'mode') else mode_result[0]
             
        return final_action, None
        
    def save(self, path: str):
        """
        Save ensemble models to a directory.
        
        Args:
            path: Base path/directory to save models
        """
        import os
        import json
        
        # Create directory if looks like a path and not a file
        base_dir = os.path.dirname(path)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            
        # We save models with suffixes
        config = {'models': [], 'voting': self.voting}
        
        for i, model in enumerate(self.models):
            # Extract alg name if possible
            alg_name = model.__class__.__name__.lower()
            model_name = f"{os.path.basename(path)}_{alg_name}_{i}"
            save_path = os.path.join(base_dir, model_name)
            
            model.save(save_path)
            config['models'].append({
                'alg': alg_name,
                'path': model_name + ".zip"
            })
            
        # Save config
        config_path = path + "_ensemble_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
    @classmethod
    def load(cls, path: str, env: Any = None) -> 'EnsembleAgent':
        """
        Load ensemble from path.
        
        Args:
            path: Base path to load from
            env: Environment (optional)
            
        Returns:
            Loaded EnsembleAgent
        """
        import os
        import json
        
        config_path = path + "_ensemble_config.json"
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Ensemble config not found at {config_path}")
            
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        models = []
        base_dir = os.path.dirname(path)
        
        for model_cfg in config['models']:
            alg_name = model_cfg['alg']
            model_path = os.path.join(base_dir, model_cfg['path'])
            
            agent_cls = SB3_AGENTS.get(alg_name.lower())
            if not agent_cls:
                continue
                
            # Load model
            model = agent_cls.load(model_path, env=env)
            models.append(model)
            
        return cls(models=models, voting=config.get('voting', 'soft'))
