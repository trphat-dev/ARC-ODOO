# -*- coding: utf-8 -*-
"""
FinRL Constants and Configuration Mappings

Centralized configuration for DRL algorithms, technical indicators,
and training parameters. No hardcoded values in other modules.
"""

from typing import Dict, Any, List

# =============================================================================
# Moving Average Configuration (Golden Cross / Death Cross)
# =============================================================================

MA_CONFIGS: Dict[str, Dict[str, int]] = {
    'standard': {'short_period': 50, 'long_period': 200},  # Most common
    'fast': {'short_period': 20, 'long_period': 50},       # Short-term trading
    'slow': {'short_period': 100, 'long_period': 200},     # Long-term investing
}

# Signal types for MA crossovers
SIGNAL_GOLDEN_CROSS = 'golden_cross'  # Bullish: short MA crosses above long MA
SIGNAL_DEATH_CROSS = 'death_cross'    # Bearish: short MA crosses below long MA
SIGNAL_NONE = 'none'

# Minimum data required for reliable MA signals
MIN_PERIODS_FOR_SIGNAL = 200

# =============================================================================
# DRL Algorithm Configuration (All Supported Algorithms)
# =============================================================================

DRL_ALGORITHMS: Dict[str, Dict[str, Any]] = {
    'ppo': {
        'name': 'Proximal Policy Optimization',
        'class_name': 'PPO',
        'policy': 'MlpPolicy',
        'description': 'Stable, general-purpose algorithm. Works with both discrete and continuous actions.',
        'supports_discrete': True,
        'supports_continuous': True,
        'default_params': {
            'learning_rate': 3e-4,
            'n_steps': 2048,
            'batch_size': 128,  # Increased for speed
            'n_epochs': 10,
            'gamma': 0.99,
            'gae_lambda': 0.95,
            'clip_range': 0.2,
            'ent_coef': 0.01,
            'vf_coef': 0.5,
            'max_grad_norm': 0.5,
            'policy_kwargs': {'net_arch': [64, 64]},  # Lighter network
        },
    },
    'a2c': {
        'name': 'Advantage Actor-Critic',
        'class_name': 'A2C',
        'policy': 'MlpPolicy',
        'description': 'Synchronous version of A3C. Fast training, good for simpler problems.',
        'supports_discrete': True,
        'supports_continuous': True,
        'default_params': {
            'learning_rate': 7e-4,
            'n_steps': 5,
            'gamma': 0.99,
            'gae_lambda': 1.0,
            'ent_coef': 0.01,
            'vf_coef': 0.25,
            'max_grad_norm': 0.5,
            'rms_prop_eps': 1e-5,
        },
    },
    'sac': {
        'name': 'Soft Actor-Critic',
        'class_name': 'SAC',
        'policy': 'MlpPolicy',
        'description': 'Off-policy algorithm with entropy regularization. Continuous actions only.',
        'supports_discrete': False,
        'supports_continuous': True,
        'default_params': {
            'learning_rate': 3e-4,
            'buffer_size': 100000,
            'learning_starts': 1000,
            'batch_size': 256,
            'tau': 0.005,
            'gamma': 0.99,
            'ent_coef': 'auto',
            'train_freq': 1,
            'gradient_steps': 1,
        },
    },
    'td3': {
        'name': 'Twin Delayed DDPG',
        'class_name': 'TD3',
        'policy': 'MlpPolicy',
        'description': 'Improved DDPG with twin Q-networks. Continuous actions only.',
        'supports_discrete': False,
        'supports_continuous': True,
        'default_params': {
            'learning_rate': 3e-4,
            'buffer_size': 100000,
            'learning_starts': 1000,
            'batch_size': 256,
            'tau': 0.005,
            'gamma': 0.99,
            'train_freq': 1,
            'gradient_steps': 1,
            'policy_delay': 2,
            'target_policy_noise': 0.2,
            'target_noise_clip': 0.5,
        },
    },
    'ddpg': {
        'name': 'Deep Deterministic Policy Gradient',
        'class_name': 'DDPG',
        'policy': 'MlpPolicy',
        'description': 'Off-policy algorithm for continuous actions. Predecessor of TD3.',
        'supports_discrete': False,
        'supports_continuous': True,
        'default_params': {
            'learning_rate': 1e-3,
            'buffer_size': 100000,
            'learning_starts': 1000,
            'batch_size': 256,
            'tau': 0.005,
            'gamma': 0.99,
            'train_freq': 1,
            'gradient_steps': 1,
        },
    },
    'ensemble': {
        'name': 'Ensemble (Multiple Models)',
        'class_name': 'EnsembleAgent',
        'policy': 'MlpPolicy',
        'description': 'Ensemble of multiple DRL algorithms (PPO, A2C, and optionally SAC, TD3, DDPG for continuous actions).',
        'supports_discrete': True,
        'supports_continuous': True,
        'default_params': {
            # Ensemble uses individual algorithm params
            'voting': 'soft',
        },
    },
}

# =============================================================================
# Action Space Configuration
# =============================================================================

ACTION_SPACE_TYPES: Dict[str, Dict[str, Any]] = {
    'discrete': {
        'name': 'Discrete',
        'description': 'Buy/Hold/Sell actions only',
        'n_actions': 3,
        'action_mapping': {
            0: 'sell',
            1: 'hold',
            2: 'buy',
        },
    },
    'continuous': {
        'name': 'Continuous',
        'description': 'Position sizing from -1 (full sell) to +1 (full buy)',
        'low': -1.0,
        'high': 1.0,
    },
}

# =============================================================================
# Technical Indicators
# =============================================================================

TECHNICAL_INDICATORS: Dict[str, Dict[str, Any]] = {
    'rsi': {
        'name': 'Relative Strength Index',
        'params': {'length': 14},
        'normalization': {'min': 0, 'max': 100},
    },
    'macd': {
        'name': 'MACD',
        'params': {'fast': 12, 'slow': 26, 'signal': 9},
        'components': ['macd', 'macd_signal', 'macd_hist'],
    },
    'sma_50': {
        'name': 'Simple Moving Average 50',
        'params': {'length': 50},
    },
    'sma_200': {
        'name': 'Simple Moving Average 200',
        'params': {'length': 200},
    },
    'bb': {
        'name': 'Bollinger Bands',
        'params': {'length': 20, 'std': 2},
        'components': ['bb_upper', 'bb_middle', 'bb_lower', 'bb_width'],
    },
    'atr': {
        'name': 'Average True Range',
        'params': {'length': 14},
    },
    'obv': {
        'name': 'On Balance Volume',
        'params': {},
    },
    'vwap': {
        'name': 'Volume Weighted Average Price',
        'params': {},
    },
}

# Default indicators to use if not specified
DEFAULT_INDICATORS: List[str] = ['rsi', 'macd', 'sma_50', 'sma_200', 'bb', 'atr']

# =============================================================================
# Training Parameters
# =============================================================================

DEFAULT_TRAINING_PARAMS: Dict[str, Any] = {
    'total_timesteps': 50_000,
    'eval_freq': 1000,
    'n_eval_episodes': 5,
    'deterministic_eval': True,
    'verbose': 1,
    'seed': None,  # Random seed, None for random
}

# =============================================================================
# Environment Parameters
# =============================================================================

ENV_PARAMS: Dict[str, Any] = {
    # Initial portfolio settings
    'initial_balance': 1_000_000_000,  # 1B VND (Fund Simulation)
    'max_shares_per_trade': 100000,
    'lot_size': 1,  # Reduced to 1 for smoother ML training (Odd Lot simulation)
    
    # Transaction costs (Vietnamese market)
    'buy_cost_pct': 0.0015,  # 0.15% buy commission
    'sell_cost_pct': 0.0015,  # 0.15% sell commission
    'tax_sell_pct': 0.001,  # 0.1% selling tax
    
    # Slippage simulation (configurable, not hardcoded)
    'slippage_max_pct': 0.001,  # 0.1% max slippage for order execution
    
    # Risk management
    'stop_loss_pct': 0.07,  # 7% max loss per trade (Vietnamese ceiling/floor)
    'take_profit_pct': 0.07,  # 7% take profit
    
    # Reward scaling
    'reward_scaling': 1e-4,
    
    # Observation normalization
    'normalize_obs': True,
    'normalize_reward': True,
}

# =============================================================================
# Reward Configuration
# =============================================================================

REWARD_SCALING: Dict[str, float] = {
    'portfolio_return': 1.0,
    'sharpe_bonus': 0.1,
    'drawdown_penalty': 0.5,
    'transaction_penalty': 0.01,
    'holding_bonus': 0.001,
}

# =============================================================================
# Market Hours (Vietnamese Stock Exchange)
# =============================================================================

MARKET_HOURS: Dict[str, str] = {
    'morning_open': '09:00',
    'morning_close': '11:30',
    'afternoon_open': '13:00',
    'afternoon_close': '15:00',
    'timezone': 'Asia/Ho_Chi_Minh',
}

# =============================================================================
# Model Save/Load Configuration
# =============================================================================

MODEL_FILE_EXTENSIONS: Dict[str, str] = {
    'model': '.zip',
    'replay_buffer': '_replay_buffer.pkl',
    'normalizer': '_normalizer.pkl',
    'metadata': '_metadata.json',
}

# =============================================================================
# Backtest Configuration (International Standard)
# =============================================================================

BACKTEST_CONFIG: Dict[str, Any] = {
    # Walk-Forward Analysis
    'walk_forward_windows': 5,          # Number of rolling windows
    'wfa_train_ratio': 0.7,             # Train vs test ratio per window
    
    # Monte Carlo Simulation
    'monte_carlo_simulations': 1000,    # Number of simulations
    'confidence_level': 0.95,           # For VaR/CVaR (95%)
    
    # Market Parameters
    'risk_free_rate': 0.02,             # 2% annual (VN T-bills approximation)
    'trading_days_per_year': 252,       # Vietnamese market
    
    # Validation
    'min_samples_per_window': 30,       # Minimum samples for valid window
    'min_trades_for_monte_carlo': 5,    # Minimum trades for MC simulation
}

