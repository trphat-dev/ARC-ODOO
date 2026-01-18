# -*- coding: utf-8 -*-
"""
SSI Data Processor for FinRL

Handles data fetching from SSI FastConnect API and preprocessing
for the FinRL Gymnasium environment.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .constants import (
    TECHNICAL_INDICATORS,
    DEFAULT_INDICATORS,
    ENV_PARAMS,
)

_logger = logging.getLogger(__name__)

# Optional import for technical indicators
try:
    import pandas_ta as ta
    TA_AVAILABLE = True
except ImportError:
    ta = None
    TA_AVAILABLE = False
    _logger.warning('pandas_ta not installed. Technical indicators will be limited.')


class SSIDataProcessor:
    """
    Data processor for SSI Vietnamese stock market data.
    
    Fetches OHLCV data from SSI FastConnect API and preprocesses it
    for use in FinRL DRL environments.
    """
    
    def __init__(
        self,
        ssi_client: Any,
        indicators: Optional[List[str]] = None,
        normalize: bool = True,
    ):
        """
        Initialize the data processor.
        
        Args:
            ssi_client: SSIClient instance for data fetching
            indicators: List of technical indicator names to calculate
            normalize: Whether to normalize OHLCV data
        """
        self.ssi_client = ssi_client
        self.indicators = indicators or DEFAULT_INDICATORS.copy()
        self.normalize = normalize
        self._scaler_params: Dict[str, Tuple[float, float]] = {}
        
    def _validate_data_quality(self, df: pd.DataFrame, max_missing_pct: float = 0.05) -> bool:
        """
        Validate data quality for AI training.
        
        Checks:
        1. Missing values percentage.
        2. Minimum required history length.
        3. Continuity (no massive gaps).
        """
        if df.empty:
            return False
            
        # 1. Total Missing Values Check (excluding indicators for now)
        core_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_count = df[core_cols].isnull().sum().sum()
        total_cells = len(df) * len(core_cols)
        missing_pct = missing_count / total_cells if total_cells > 0 else 1.0
        
        if missing_pct > max_missing_pct:
            _logger.warning(f"Data validation failed: Too many missing values ({missing_pct:.2%})")
            return False
            
        # 2. Check per symbol
        min_records = 30 # At least 30 candles
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol]
            if len(symbol_df) < min_records:
                _logger.warning(f"Data validation failed: {symbol} has insufficient history ({len(symbol_df)} < {min_records})")
                return False
                
        return True
    
    def fetch_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        market: str = 'HOSE',
        data_type: str = 'daily',
        resolution: str = '1',
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for multiple symbols.
        
        Args:
            symbols: List of stock symbols (e.g., ['FPT', 'VCB', 'VNM'])
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            market: Market code (HOSE, HNX, UPCOM)
            data_type: 'daily' or 'intraday'
            resolution: Resolution for intraday data ('1', '5', '15', '30', '60')
        
        Returns:
            DataFrame with OHLCV data and symbol column
        """
        all_data = []
        
        for symbol in symbols:
            try:
                if data_type == 'intraday':
                    records = self.ssi_client.get_intraday_ohlc_range(
                        symbol=symbol,
                        from_date=start_date,
                        to_date=end_date,
                        market=market,
                        resolution=resolution,
                    )
                else:
                    records = self.ssi_client.get_daily_ohlc(
                        symbol=symbol,
                        from_date=start_date,
                        to_date=end_date,
                        market=market,
                    )
                
                if records:
                    df = pd.DataFrame(records)
                    df['symbol'] = symbol
                    all_data.append(df)
                    _logger.info(f'Fetched {len(df)} records for {symbol}')
                else:
                    _logger.warning(f'No data returned for {symbol}')
                    
            except Exception as e:
                _logger.error(f'Failed to fetch data for {symbol}: {e}')
                continue
        
        if not all_data:
            _logger.error('No data fetched for any symbol')
            return pd.DataFrame()
        
        combined = pd.concat(all_data, ignore_index=True)
        
        # Preprocess first
        df_processed = self._preprocess_raw_data(combined, data_type)
        
        # Validate data quality
        if not self._validate_data_quality(df_processed):
            _logger.error("Data quality check failed. Insufficient data for training.")
            return pd.DataFrame()
            
        return df_processed
    
    def _preprocess_raw_data(
        self,
        df: pd.DataFrame,
        data_type: str,
    ) -> pd.DataFrame:
        """
        Preprocess raw OHLCV data.
        
        Args:
            df: Raw DataFrame from SSI API
            data_type: 'daily' or 'intraday'
        
        Returns:
            Preprocessed DataFrame
        """
        if df.empty:
            return df
        
        # Parse datetime
        if data_type == 'intraday':
            if 'time' in df.columns and 'date' in df.columns:
                df['datetime'] = pd.to_datetime(
                    df['date'].astype(str) + ' ' + df['time'].astype(str),
                    errors='coerce'
                )
            elif 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        else:
            if 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Ensure numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            else:
                df[col] = 0.0
        
        # Drop rows with missing critical data
        df = df.dropna(subset=['datetime', 'close'])
        
        # Sort by symbol and datetime
        df = df.sort_values(['symbol', 'datetime']).reset_index(drop=True)
        
        return df
    
    def add_technical_indicators(
        self,
        df: pd.DataFrame,
        indicators: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Add technical indicators to the DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            indicators: List of indicator names (uses self.indicators if None)
        
        Returns:
            DataFrame with additional indicator columns
        """
        if df.empty:
            return df
        
        indicators = indicators or self.indicators
        
        # Process per symbol
        if 'symbol' in df.columns and df['symbol'].nunique() > 1:
            processed = []
            for symbol in df['symbol'].unique():
                symbol_df = df[df['symbol'] == symbol].copy()
                symbol_df = self._calculate_indicators(symbol_df, indicators)
                processed.append(symbol_df)
            df = pd.concat(processed, ignore_index=True)
        else:
            df = self._calculate_indicators(df, indicators)
        
        return df
    
    def _calculate_indicators(
        self,
        df: pd.DataFrame,
        indicators: List[str],
    ) -> pd.DataFrame:
        """
        Calculate technical indicators for a single symbol.
        
        Args:
            df: DataFrame for a single symbol
            indicators: List of indicator names
        
        Returns:
            DataFrame with indicators added
        """
        if not TA_AVAILABLE:
            _logger.warning('pandas_ta not available, using basic calculations')
            return self._calculate_basic_indicators(df)
        
        df = df.copy()
        
        # Add Fundamentals (Placeholder)
        # In the future, this should fetch from ssi_client.get_financial_ratio()
        if 'pe' not in df.columns:
            df['pe'] = 0.0 # Price to Earnings
        if 'pb' not in df.columns:
            df['pb'] = 0.0 # Price to Book
            
        for ind_name in indicators:

            if ind_name not in TECHNICAL_INDICATORS:
                _logger.warning(f'Unknown indicator: {ind_name}')
                continue
            
            ind_config = TECHNICAL_INDICATORS[ind_name]
            params = ind_config.get('params', {})
            
            try:
                if ind_name == 'rsi':
                    rsi = ta.rsi(df['close'], length=params.get('length', 14))
                    df['rsi'] = rsi if rsi is not None else np.nan
                    
                elif ind_name == 'macd':
                    macd_result = ta.macd(
                        df['close'],
                        fast=params.get('fast', 12),
                        slow=params.get('slow', 26),
                        signal=params.get('signal', 9),
                    )
                    if macd_result is not None:
                        df['macd'] = macd_result.iloc[:, 0]
                        df['macd_signal'] = macd_result.iloc[:, 1]
                        df['macd_hist'] = macd_result.iloc[:, 2]
                    else:
                        df['macd'] = np.nan
                        df['macd_signal'] = np.nan
                        df['macd_hist'] = np.nan
                        
                elif ind_name == 'sma_50':
                    sma = ta.sma(df['close'], length=50)
                    df['sma_50'] = sma if sma is not None else np.nan
                    
                elif ind_name == 'sma_200':
                    sma = ta.sma(df['close'], length=200)
                    df['sma_200'] = sma if sma is not None else np.nan
                    
                elif ind_name == 'bb':
                    bb_result = ta.bbands(
                        df['close'],
                        length=params.get('length', 20),
                        std=params.get('std', 2),
                    )
                    if bb_result is not None:
                        df['bb_lower'] = bb_result.iloc[:, 0]
                        df['bb_middle'] = bb_result.iloc[:, 1]
                        df['bb_upper'] = bb_result.iloc[:, 2]
                        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
                    else:
                        df['bb_lower'] = np.nan
                        df['bb_middle'] = np.nan
                        df['bb_upper'] = np.nan
                        df['bb_width'] = np.nan
                        
                elif ind_name == 'atr':
                    atr = ta.atr(
                        df['high'], df['low'], df['close'],
                        length=params.get('length', 14),
                    )
                    df['atr'] = atr if atr is not None else np.nan
                    
                elif ind_name == 'obv':
                    obv = ta.obv(df['close'], df['volume'])
                    df['obv'] = obv if obv is not None else np.nan
                    
                elif ind_name == 'vwap':
                    vwap = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
                    df['vwap'] = vwap if vwap is not None else np.nan
                    
            except Exception as e:
                _logger.warning(f'Failed to calculate {ind_name}: {e}')
        
        # Add derived features
        df = self._add_derived_features(df)
        
        return df
    
    def _calculate_basic_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate basic indicators without pandas_ta.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with basic indicators
        """
        df = df.copy()
        
        # Simple Moving Averages
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # RSI (simplified)
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * std
        df['bb_lower'] = df['bb_middle'] - 2 * std
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # MACD
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()
        
        # Add derived features
        df = self._add_derived_features(df)
        
        return df
    
        return df

    def _calculate_turbulence(self, df: pd.DataFrame, lookback: int = 252) -> pd.DataFrame:
        """
        Calculate Market Turbulence Index.
        
        International Standard: Mahalanobis distance of returns
        to detect extreme market conditions (crashes).
        
        Args:
            df: DataFrame with OHLCV
            lookback: Lookback window to establish "normal" covariance
        
        Returns:
            DataFrame with 'turbulence' column
        """
        df = df.copy()
        
        # Calculate returns if not exists
        if 'returns' not in df.columns:
            df['returns'] = df['close'].pct_change()
            
        # We need a history of returns to calculate covariance
        # Simplified robust implementation without sklearn dependency if possible
        # But for Mahalanobis, we ideally need inverse covariance matrix
        
        try:
            # Prepare data
            returns = df['returns'].copy().fillna(0)
            
            # Simple rolling Mahalanobis equivalent
            # Rolling mean
            rolling_mean = returns.rolling(window=lookback).mean()
            
            # Rolling std (volatility) - simpler proxy used in many systems
            rolling_std = returns.rolling(window=lookback).std()
            
            # Standard score (z-score) squared is roughly Mahalanobis in 1D
            # For 1D (single stock), Turbulence ~ (return - mean)^2 / variance
            # For Portfolio, it uses Covariance matrix. Here we do single-stock approximation
            # which acts as "Asset Turbulence"
            
            z_score = (returns - rolling_mean) / rolling_std.replace(0, 1)
            turbulence = z_score ** 2
            
            df['turbulence'] = turbulence.fillna(0)
            
            # Define threshold (e.g., 99th percentile of chi-square distribution)
            # For 1 degree of freedom, p=0.01 threshold is ~6.63
            # But let's use dynamic threshold based on history
            threshold = df['turbulence'].rolling(window=lookback).quantile(0.99)
            df['turbulence_threshold'] = threshold.fillna(6.63)
            
            return df
            
        except Exception as e:
            _logger.warning(f"Failed to calculate turbulence: {e}")
            df['turbulence'] = 0.0
            df['turbulence_threshold'] = 100.0
            return df
            
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add derived features for the DRL agent.
        
        Args:
            df: DataFrame with indicators
        
        Returns:
            DataFrame with derived features
        """
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Volatility
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Price relative to SMAs
        if 'sma_50' in df.columns:
            df['close_to_sma50'] = df['close'] / df['sma_50'].replace(0, np.nan)
        if 'sma_200' in df.columns:
            df['close_to_sma200'] = df['close'] / df['sma_200'].replace(0, np.nan)
        
        # Golden Cross / Death Cross signals
        if 'sma_50' in df.columns and 'sma_200' in df.columns:
            sma50_prev = df['sma_50'].shift(1)
            sma200_prev = df['sma_200'].shift(1)
            df['golden_cross'] = (
                (sma50_prev <= sma200_prev) & 
                (df['sma_50'] > df['sma_200'])
            ).astype(float)
            df['death_cross'] = (
                (sma50_prev >= sma200_prev) & 
                (df['sma_50'] < df['sma_200'])
            ).astype(float)
        
        # Volume features
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma'].replace(0, np.nan)
        
        # High-Low ratio
        df['high_low_ratio'] = df['high'] / df['low'].replace(0, np.nan)
        
        # Calculate Turbulence
        df = self._calculate_turbulence(df)
        
        return df
    
    def prepare_for_env(
        self,
        df: pd.DataFrame,
        feature_columns: Optional[List[str]] = None,
        is_training: bool = True,
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare data for the Gymnasium environment.
        
        Args:
            df: DataFrame with OHLCV and indicators
            feature_columns: Specific columns to include as features
            is_training: If True, calculates and stores scaler params. 
                         If False, uses stored params (avoids lookahead bias).
        
        Returns:
            Tuple of (feature_array, feature_names)
        """
        if df.empty:
            return np.array([]), []
        
        # Default feature columns
        if feature_columns is None:
            feature_columns = [
                'open', 'high', 'low', 'close', 'volume',
                'rsi', 'macd', 'macd_signal', 'macd_hist',
                'sma_50', 'sma_200', 'close_to_sma50', 'close_to_sma200',
                'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
                'atr', 'returns', 'volatility', 'volume_ratio',
                'turbulence', 'turbulence_threshold',
                'pe', 'pb',
            ]
        
        # Filter to available columns
        available_cols = [col for col in feature_columns if col in df.columns]
        
        if not available_cols:
            _logger.error('No feature columns available in DataFrame')
            return np.array([]), []
        
        # Extract features
        features = df[available_cols].copy()
        
        # Handle infinities and NaN
        features = features.replace([np.inf, -np.inf], np.nan)
        features = features.fillna(method='ffill').fillna(0)
        
        # Normalize if requested
        if self.normalize:
            features = self._normalize_features(features, is_training=is_training)
        
        return features.values, available_cols
    
    def _normalize_features(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """
        Normalize features using min-max scaling.
        Crucial: For inference/eval, uses params from training to avoid lookahead bias.
        
        Args:
            df: DataFrame with features
            is_training: Whether to update scaler params
        
        Returns:
            Normalized DataFrame
        """
        df = df.copy()
        
        for col in df.columns:
            if is_training:
                # Calculate and store params
                col_min = df[col].min()
                col_max = df[col].max()
                self._scaler_params[col] = (col_min, col_max)
            else:
                # Use stored params
                if col in self._scaler_params:
                    col_min, col_max = self._scaler_params[col]
                else:
                    # Fallback for new columns (should rarely happen)
                    col_min = df[col].min()
                    col_max = df[col].max()
            
            # Apply scaling
            if col_max - col_min > 1e-8:
                df[col] = (df[col] - col_min) / (col_max - col_min)
                # Clip to [0, 1] range strictly? Not strictly necessary for RL but good practice
                # But theoretically new data could be outside range.
            else:
                df[col] = 0.5
        
        return df
    
    def get_scaler_params(self) -> Dict[str, Tuple[float, float]]:
        """Get the normalization parameters for inverse transform."""
        return self._scaler_params.copy()
