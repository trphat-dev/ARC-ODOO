# -*- coding: utf-8 -*-
"""
FinRL Integration Package for AI Trading Assistant

This package provides Deep Reinforcement Learning capabilities for
Vietnamese stock trading via SSI FastConnect API integration.

Components:
- ssi_env: Custom Gymnasium environment for SSI market
- data_processor: Data preprocessing and feature engineering
- agents: DRL agent factory (PPO, A2C, SAC, TD3, DDPG)
- client: High-level FinRL client wrapper
- backtest_engine: International-standard backtest engine
- tuner: Optuna hyperparameter tuner
"""

from .constants import (
    # DRL Configuration
    DRL_ALGORITHMS,
    ACTION_SPACE_TYPES,
    REWARD_SCALING,
    DEFAULT_TRAINING_PARAMS,
    TECHNICAL_INDICATORS,
    ENV_PARAMS,
    BACKTEST_CONFIG,
    # MA Configuration (Golden Cross / Death Cross)
    MA_CONFIGS,
    SIGNAL_GOLDEN_CROSS,
    SIGNAL_DEATH_CROSS,
    SIGNAL_NONE,
    MIN_PERIODS_FOR_SIGNAL,
)
from .data_processor import SSIDataProcessor
from .ssi_env import SSIStockTradingEnv
from .agents import DRLAgentFactory
from .client import FinRLClient
from .backtest_engine import BacktestEngine, BacktestResult, create_backtest_engine
from .tuner import HyperparameterTuner, create_tuner, SEARCH_SPACES

__all__ = [
    # DRL Constants
    'DRL_ALGORITHMS',
    'ACTION_SPACE_TYPES',
    'REWARD_SCALING',
    'DEFAULT_TRAINING_PARAMS',
    'TECHNICAL_INDICATORS',
    'ENV_PARAMS',
    'BACKTEST_CONFIG',
    # MA Constants
    'MA_CONFIGS',
    'SIGNAL_GOLDEN_CROSS',
    'SIGNAL_DEATH_CROSS',
    'SIGNAL_NONE',
    'MIN_PERIODS_FOR_SIGNAL',
    # Classes
    'SSIDataProcessor',
    'SSIStockTradingEnv',
    'DRLAgentFactory',
    'FinRLClient',
    'BacktestEngine',
    'BacktestResult',
    'create_backtest_engine',
    # Tuner
    'HyperparameterTuner',
    'create_tuner',
    'SEARCH_SPACES',
]
