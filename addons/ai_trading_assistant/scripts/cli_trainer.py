import os
import argparse
import pandas as pd
import numpy as np
import time
import json
import sys
import zipfile

# ─── Vietnam Stock Market Trading Constants ───
# Must match ai_strategy.py constants
VN_HMAX = 10_000              # Max shares per action (HOSE standard lot)
VN_INITIAL_CAPITAL = 100_000_000    # Starting capital: 100 Million VND
VN_BUY_COST_PCT = 0.0015      # Broker commission ~0.15%
VN_SELL_COST_PCT = 0.0025      # Broker 0.15% + PIT/VAT ~0.10%
VN_REWARD_SCALING = 1e-8       # Scale down 100M VND rewards to ~1.0 range

# ─── Default Indicators (synced with inference engine) ───
DEFAULT_INDICATORS = [
    "macd", "boll_ub", "boll_lb", "rsi_30", "cci_30", "dx_30",
    "close_30_sma", "close_60_sma",
    # Extended indicators for better signal quality
    "close_10_sma",   # EMA proxy (SMA10 ≈ fast trend)
    "close_50_sma",   # SMA50 (slow trend)
    "rsi_14",         # RSI(14) standard
]

# ─── Algorithm Hyperparameters ───
ALGO_CONFIGS = {
    'ppo': {
        "learning_rate": 5e-5,          # FIX: Lower LR to prevent NaN explosion
        "batch_size": 128,
        "ent_coef": 0.005,              # FIX: Lower entropy for more stable learning
        "n_steps": 1024,                # FIX: Smaller rollout to reduce numerical accumulation
        "gamma": 0.99,
        "max_grad_norm": 0.5,           # FIX: Gradient clipping
        "clip_range": 0.2,
    },
    'a2c': {
        "learning_rate": 3e-4,          # FIX: Lower LR
        "n_steps": 5,
        "gamma": 0.99,
        "ent_coef": 0.005,
        "max_grad_norm": 0.5,           # FIX: Gradient clipping
    },
    'ddpg': {
        "learning_rate": 1e-4,          # FIX: Lower LR
        "batch_size": 128,
        "gamma": 0.99,
        "buffer_size": 50_000,
    },
}

DEFAULT_EPOCHS = 10_000

# Ép buộc Windows Terminal in ra tiếng Việt (UTF-8) không bị lỗi charmap
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# ══════════════════════════════════════════════════════
# Data Fetching
# ══════════════════════════════════════════════════════
def _get_ssi_client(ssi_id, ssi_secret, api_url):
    """Helper: create SSI fc_md_client."""
    try:
        from ssi_fc_data import fc_md_client
    except ImportError:
        raise ImportError("Bắt buộc cài đặt ssi-fc-data: pip install ssi-fc-data")

    class Config:
        consumerID = ssi_id
        consumerSecret = ssi_secret
        url = api_url
        stream_url = api_url

    return fc_md_client.MarketDataClient(Config()), Config()


def fetch_all_tickers_from_ssi(ssi_id, ssi_secret, api_url):
    """Lấy danh sách tất cả các mã CK trực tiếp từ SSI API (HOSE+HNX+UPCOM)"""
    print("[*] Fetching ALL tickers from SSI API...")
    from ssi_fc_data import model

    client, config = _get_ssi_client(ssi_id, ssi_secret, api_url)
    all_tickers = []

    for market in ['HOSE', 'HNX', 'UPCOM']:
        page_index = 1
        while True:
            try:
                req = model.securities(market, page_index, 1000)
                res = client.securities(config, req)
                data = res if isinstance(res, dict) else json.loads(res)

                if str(data.get('status')) == '200' or data.get('message', '').lower() == 'success':
                    items = data.get('data', [])
                    if not items:
                        break
                    tickers = [t.get('Symbol') for t in items if t.get('Symbol')]
                    all_tickers.extend(tickers)
                    if len(items) < 1000:
                        break
                    page_index += 1
                    time.sleep(1)
                elif str(data.get('status')) == '429' or "too many" in data.get('message', '').lower():
                    print(f"[!] {market} bị giới hạn tần suất (Rate Limit 429), đang chờ 3s...")
                    time.sleep(3)
                    continue
                else:
                    print(f"[-] {market} ngưng tải do API phản hồi: {data.get('message')}")
                    break
            except Exception as e:
                print(f"[!] Bỏ qua {market} trang {page_index} do lỗi gọi API: {e}")
                break
        time.sleep(1)

    return list(set(all_tickers))


def fetch_data_from_ssi(ticker_symbol, from_date, to_date, ssi_id, ssi_secret, api_url):
    """Lấy trực tiếp dữ liệu OHLCV từ SSI qua API để backtest/train"""
    from ssi_fc_data import model

    client, config = _get_ssi_client(ssi_id, ssi_secret, api_url)
    req = model.daily_ohlc(ticker_symbol, from_date, to_date, 1, 9999, True)
    res = client.daily_ohlc(config, req)

    data = res if isinstance(res, dict) else json.loads(res)
    if str(data.get('status')) == '200' or data.get('message', '').lower() == 'success':
        candles = data.get('data', [])
        if not candles:
            raise ValueError(f"Không có dữ liệu trả về cho {ticker_symbol}")

        df = pd.DataFrame(candles)
        df.rename(columns={
            'TradingDate': 'date', 'Open': 'open', 'High': 'high',
            'Low': 'low', 'Close': 'close', 'Volume': 'volume'
        }, inplace=True)

        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df.dropna(subset=numeric_cols, inplace=True)

        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
        df['tic'] = ticker_symbol
        df = df[['date', 'tic', 'open', 'high', 'low', 'close', 'volume']]
        df.sort_values('date', ascending=True, inplace=True)
        return df

    raise ValueError(f"Lỗi gọi API SSI: {data.get('message')}")


# ══════════════════════════════════════════════════════
# Backtest Helper
# ══════════════════════════════════════════════════════
def _backtest_model(trained_model, df, env_kwargs):
    """Run a backtest on given df, return (sharpe, return_pct, max_drawdown)."""
    from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv

    env = StockTradingEnv(df=df, **env_kwargs)
    obs = env.reset()
    if isinstance(obs, tuple):
        obs = obs[0]

    account_values = [VN_INITIAL_CAPITAL]
    done = False
    while not done:
        action, _ = trained_model.predict(obs, deterministic=True)
        result = env.step(action)
        obs = result[0]
        done = result[2]
        if isinstance(obs, tuple):
            obs = obs[0]
        if hasattr(env, 'asset_memory') and env.asset_memory:
            account_values.append(env.asset_memory[-1])
        else:
            account_values.append(account_values[-1])

    series = pd.Series(account_values)
    daily_ret = series.pct_change().dropna()
    sharpe = float((daily_ret.mean() / daily_ret.std() * np.sqrt(252)) if daily_ret.std() > 0 else 0.0)
    total_return = float(((account_values[-1] / VN_INITIAL_CAPITAL) - 1) * 100)
    max_dd = float(((series - series.cummax()) / series.cummax() * 100).min())

    return sharpe, total_return, max_dd


# ══════════════════════════════════════════════════════
# Main Training Pipeline
# ══════════════════════════════════════════════════════
def train_model(ticker_input, algorithm="ppo", epochs=10000,
                from_date="01/01/2020", to_date="31/12/2023",
                ssi_id=None, ssi_secret=None, api_url=None, indicators=None):

    if not indicators:
        indicators = DEFAULT_INDICATORS

    if not ssi_id or not ssi_secret:
        raise ValueError("Yêu cầu cung cấp ssi-consumer-id và ssi-consumer-secret!")

    if ticker_input.upper() == 'ALL':
        tickers = fetch_all_tickers_from_ssi(ssi_id, ssi_secret, api_url)
    else:
        tickers = [t.strip().upper() for t in ticker_input.split(',')]

    print(f"=========== BẮT ĐẦU HUẤN LUYỆN FINRL: {len(tickers)} MÃ | {algorithm.upper()} ===========")

    # ──── 1. Fetch Data ────
    df_list = []
    total = len(tickers)
    last_error = ""

    print(f"[*] Tải dữ liệu từ SSI ({from_date} - {to_date}):")
    for i, tic in enumerate(tickers, 1):
        try:
            percent = (i / total) * 100
            bar_len = 20
            filled_len = int(bar_len * i // total)
            bar = '█' * filled_len + '-' * (bar_len - filled_len)
            print(f'\r[{bar}] {percent:.1f}% ({i}/{total}) Tải: {tic:<6}   ', end='', flush=True)

            df = fetch_data_from_ssi(tic, from_date, to_date, ssi_id, ssi_secret, api_url)
            time.sleep(0.5)
            df_list.append(df)
        except Exception as e:
            last_error = str(e)

    sys.stdout.write('\n[+] Hoàn tất kéo tất cả dữ liệu!\n')

    if not df_list:
        raise ValueError(f"Không tải được dữ liệu cho bất kì mã nào. Lỗi cuối: {last_error}")

    full_df = pd.concat(df_list, ignore_index=True)
    full_df.sort_values(by=['date', 'tic'], ascending=True, inplace=True)
    full_df.reset_index(drop=True, inplace=True)
    print(f"[*] Total DataFrame shape: {full_df.shape}")

    # ──── 2. Dimension Alignment ────
    print("[*] Đang đồng bộ hóa độ dài dữ liệu (Dimension Alignment) & Xử lý nến thiếu (Forward Fill)...")

    all_dates = sorted(full_df['date'].unique())
    total_market_days = len(all_dates)

    tic_counts = full_df['tic'].value_counts()
    min_required_days = int(total_market_days * 0.7)
    valid_tics = tic_counts[tic_counts >= min_required_days].index.tolist()

    dropped_count = len(tic_counts) - len(valid_tics)
    if dropped_count > 0:
        print(f"[!] Loại bỏ {dropped_count} mã cổ phiếu do dữ liệu quá ít (<70% chu kỳ).")

    full_df = full_df[full_df['tic'].isin(valid_tics)].copy()

    print(f"[*] Đang xử lý lấp đầy dữ liệu cho {len(valid_tics)} mã cổ phiếu...")
    df_pivot = full_df.pivot(index='date', columns='tic', values=['open', 'high', 'low', 'close', 'volume'])
    df_pivot = df_pivot.ffill().bfill()
    full_df = df_pivot.stack(level='tic', future_stack=True).reset_index()
    full_df = full_df.sort_values(['date', 'tic']).reset_index(drop=True)
    print(f"[*] Dữ liệu hợp lệ: {len(valid_tics)} Mã x {len(all_dates)} Ngày.")

    # ──── 3. Feature Engineering ────
    print(f"[*] Feature Engineering... : {indicators}")

    try:
        try:
            from finrl.meta.preprocessor.preprocessors import FeatureEngineer
        except ImportError:
            from finrl.meta.preprocessor.feature_engineer import FeatureEngineer

        from finrl.meta.env_stock_trading.env_stocktrading import StockTradingEnv
        from finrl.agents.stablebaselines3.models import DRLAgent
        from stable_baselines3.common.logger import configure
        from stable_baselines3.common.callbacks import EvalCallback
        try:
            from stable_baselines3.common.callbacks import StopTrainingOnNoModelImprovement as StopTrainingOnNoImprovement
        except ImportError:
            try:
                from stable_baselines3.common.callbacks import StopTrainingOnNoImprovement
            except ImportError:
                StopTrainingOnNoImprovement = None
    except ImportError as e:
        raise ImportError(f"Lỗi Import FinRL: {e}. pip install git+https://github.com/AI4Finance-Foundation/FinRL.git stable-baselines3 gymnasium")

    fe = FeatureEngineer(
        use_technical_indicator=True,
        tech_indicator_list=indicators,
        use_vix=False,         # FIX #1: Tắt VIX Mỹ — không có ý nghĩa cho thị trường VN
        use_turbulence=False,
        user_defined_feature=False
    )
    processed_df = fe.preprocess_data(full_df)
    processed_df = processed_df.sort_values(['date', 'tic'], ignore_index=True)
    processed_df.index = processed_df.date.factorize()[0]

    # ──── 4. Train / Validation / Trade Split (70/15/15) ────  FIX #5
    dates = processed_df['date'].unique()
    n = len(dates)
    split_train = int(n * 0.70)
    split_val = int(n * 0.85)
    # Safety: ensure each split has at least 1 day
    split_train = max(split_train, 1)
    split_val = max(split_val, split_train + 1)
    if split_val >= n:
        split_val = n - 1

    train_date = dates[split_train]
    val_date = dates[split_val]

    train_df = processed_df[processed_df['date'] <= train_date].copy()
    val_df = processed_df[(processed_df['date'] > train_date) & (processed_df['date'] <= val_date)].copy()
    trade_df = processed_df[processed_df['date'] > val_date].copy()

    for df_part in [train_df, val_df, trade_df]:
        df_part.sort_values(['date', 'tic'], ignore_index=True, inplace=True)
        df_part.index = df_part.date.factorize()[0]

    print(f"[*] Train : {train_df['date'].min()} -> {train_df['date'].max()} ({len(train_df)} rows)")
    print(f"[*] Valid : {val_df['date'].min()} -> {val_df['date'].max()} ({len(val_df)} rows)")
    print(f"[*] Trade : {trade_df['date'].min()} -> {trade_df['date'].max()} ({len(trade_df)} rows)")

    # ──── 5. Create Environment ────
    stock_dimension = int(len(processed_df.tic.unique()))
    state_space = int(1 + 2 * stock_dimension + len(indicators) * stock_dimension)

    env_kwargs = {
        "hmax": VN_HMAX,
        "initial_amount": VN_INITIAL_CAPITAL,
        "num_stock_shares": [0] * stock_dimension,
        "buy_cost_pct": [VN_BUY_COST_PCT] * stock_dimension,
        "sell_cost_pct": [VN_SELL_COST_PCT] * stock_dimension,
        "state_space": state_space,
        "stock_dim": stock_dimension,
        "tech_indicator_list": list(indicators),
        "action_space": stock_dimension,
        "reward_scaling": VN_REWARD_SCALING
    }

    # ──── 6. Dynamic Neural Network Sizing ────  FIX #4
    if stock_dimension <= 5:
        net_arch = [dict(pi=[128, 128], vf=[128, 128])]
    elif stock_dimension <= 50:
        net_arch = [dict(pi=[256, 256], vf=[256, 256])]
    else:
        net_arch = [dict(pi=[512, 256], vf=[512, 256])]

    print(f"[*] Network architecture: {net_arch[0]} (stock_dim={stock_dimension})")

    # ──── 7. Determine Algorithms to Train ────  FIX #3
    _epochs = int(epochs)
    algo_lower = algorithm.lower()
    if algo_lower == 'all':
        algorithms_to_train = ['ppo', 'a2c', 'ddpg']
    else:
        algorithms_to_train = [algo_lower]

    print(f"[*] Algorithms to train: {[a.upper() for a in algorithms_to_train]}")

    # ──── 8. Train + Backtest Each Algorithm ────
    results = {}

    for current_algo in algorithms_to_train:
        print(f"\n{'─'*50}")
        print(f"[*] Training {current_algo.upper()} for {_epochs} timesteps...")

        model_kwargs = ALGO_CONFIGS.get(current_algo, {}).copy()  # FIX #7
        print(f"[*] Hyperparameters: {model_kwargs}")

        start_time = time.time()

        # Fresh environment for each algorithm
        e_train_gym = StockTradingEnv(df=train_df, **env_kwargs)
        env_train, _ = e_train_gym.get_sb_env()
        agent = DRLAgent(env=env_train)

        # Policy kwargs (only PPO/A2C use policy_kwargs with net_arch)
        policy_kwargs = dict(net_arch=net_arch) if current_algo in ['ppo', 'a2c'] else {}

        if policy_kwargs:
            model = agent.get_model(model_name=current_algo, model_kwargs=model_kwargs, policy_kwargs=policy_kwargs)
        else:
            model = agent.get_model(model_name=current_algo, model_kwargs=model_kwargs)

        model.verbose = 0

        # FIX #6: EvalCallback with early stopping on validation set
        eval_env = None
        eval_callback = None
        try:
            e_val_gym = StockTradingEnv(df=val_df, **env_kwargs)
            eval_env, _ = e_val_gym.get_sb_env()
            if StopTrainingOnNoImprovement is not None:
                stop_cb = StopTrainingOnNoImprovement(
                    max_no_improvement_evals=5,
                    min_evals=10,
                    verbose=1
                )
            else:
                stop_cb = None
            eval_callback = EvalCallback(
                eval_env,
                best_model_save_path=f"./tmp_eval_{current_algo}/",
                eval_freq=max(_epochs // 20, 500),
                n_eval_episodes=1,
                callback_after_eval=stop_cb,
                verbose=0
            )
            print(f"[*] EvalCallback enabled: eval every {max(_epochs // 20, 500)} steps, early stop after 5 no-improvement evals.")
        except Exception as e:
            print(f"[!] EvalCallback setup failed ({e}), training without early stopping.")
            eval_callback = None

        if eval_callback:
            # Use SB3's native .learn() with callback (DRLAgent.train_model doesn't support callback)
            model.learn(total_timesteps=_epochs, tb_log_name=current_algo, callback=eval_callback)
            trained_model = model
        else:
            trained_model = agent.train_model(
                model=model,
                tb_log_name=current_algo,
                total_timesteps=_epochs
            )

        elapsed = (time.time() - start_time) / 60
        print(f"[*] {current_algo.upper()} training completed in {elapsed:.2f} min.")

        # Backtest on TRADE set
        print(f"[*] Backtesting {current_algo.upper()} on trade set...")
        sharpe, ret_pct, max_dd = _backtest_model(trained_model, trade_df, env_kwargs)
        print(f"[*] {current_algo.upper()} Results: Sharpe={sharpe:.2f}, Return={ret_pct:.2f}%, MaxDD={max_dd:.2f}%")

        results[current_algo] = {
            'model': trained_model,
            'sharpe': sharpe,
            'return_pct': ret_pct,
            'max_drawdown': max_dd,
            'training_time': f"{elapsed:.2f} phút",
            'model_kwargs': model_kwargs,
        }

        # Cleanup eval temp dir
        try:
            import shutil
            shutil.rmtree(f"./tmp_eval_{current_algo}/", ignore_errors=True)
        except Exception:
            pass

    # ──── 9. Select Best Algorithm ────
    if len(results) > 1:
        print(f"\n{'='*50}")
        print("[*] SO SÁNH CÁC THUẬT TOÁN:")
        print(f"{'='*50}")
        print(f"{'Algorithm':<10} {'Sharpe':>8} {'Return%':>10} {'MaxDD%':>10}")
        print("-" * 40)
        for algo, r in results.items():
            print(f"{algo.upper():<10} {r['sharpe']:>8.2f} {r['return_pct']:>9.2f}% {r['max_drawdown']:>9.2f}%")

        best_algo = max(results, key=lambda x: results[x]['sharpe'])
        print(f"\n[★] Thuật toán tốt nhất: {best_algo.upper()} (Sharpe = {results[best_algo]['sharpe']:.2f})")
    else:
        best_algo = algorithms_to_train[0]

    best = results[best_algo]
    trained_model = best['model']

    print(f"\n{'='*50}")
    print(f"[*] XUẤT MODEL: {best_algo.upper()}")
    print(f"{'='*50}")

    # ──── 10. Save Model ────
    final_tickers = valid_tics if ticker_input.upper() == "ALL" else tickers
    if len(final_tickers) == 1:
        prefix = final_tickers[0]
    else:
        # Use actual ticker names (max 5 in filename to avoid path length issues)
        name_part = "_".join(final_tickers[:5])
        if len(final_tickers) > 5:
            name_part += f"_+{len(final_tickers)-5}"
        prefix = name_part
    save_path = os.path.abspath(f"./{prefix}_{best_algo}")
    os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)

    trained_model.save(save_path)
    zip_path = f"{save_path}.zip"

    # Embed history data for inference context
    history_data = []
    for tic in full_df['tic'].unique():
        tic_df = full_df[full_df['tic'] == tic].tail(150)
        for _, row in tic_df.iterrows():
            history_data.append({
                'tic': str(row.get('tic', tic)),
                'date': str(row['date'].strftime('%Y-%m-%d') if hasattr(row.get('date'), 'strftime') else row.get('date', '')),
                'open': float(row.get('open', 0.0)),
                'high': float(row.get('high', 0.0)),
                'low': float(row.get('low', 0.0)),
                'close': float(row.get('close', 0.0)),
                'volume': float(row.get('volume', 0.0))
            })

    # Metadata with ALL algorithm comparison results
    all_algos_results = {}
    for algo, r in results.items():
        all_algos_results[algo] = {
            'sharpe': r['sharpe'], 'return_pct': r['return_pct'],
            'max_drawdown': r['max_drawdown'], 'training_time': r['training_time']
        }

    metadata = {
        "algorithm": str(best_algo),
        "evaluated_algorithms": ", ".join([str(a).upper() for a in algorithms_to_train]),
        "algorithm_comparison": all_algos_results,
        "ticker_ids": [str(t) for t in final_tickers],
        "epochs": _epochs,
        "learning_rate": best['model_kwargs'].get("learning_rate", 0),
        "batch_size": best['model_kwargs'].get("batch_size", 0),
        "ent_coef": best['model_kwargs'].get("ent_coef", 0),
        "sharpe_ratio": float(best['sharpe']),
        "expected_return": float(best['return_pct']),
        "max_drawdown": float(best['max_drawdown']),
        "training_time": str(best['training_time']),
        "framework_version": "FinRL 0.3.8 / SB3",
        "date_range": f"{from_date} to {to_date}",
        "data_split": "70/15/15 (train/validation/trade)",
        "network_arch": str(net_arch[0]),
        "use_vix": False,
        "indicators": list(indicators),
        "history_data": history_data
    }
    with zipfile.ZipFile(zip_path, 'a') as zf:
        zf.writestr('metadata.json', json.dumps(metadata, indent=4))

    print(f"[SUCCESS] Model và Metadata đã được lưu tại {zip_path}")
    print("=========== HOÀN TẤT ===========")


# ══════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AI Trading Assistant - CLI Trainer Independent')
    parser.add_argument('--ticker', type=str, default=None, help='Ticker Symbol (VD: FPT, hoặc "FPT,HPG", hoặc "ALL")')
    parser.add_argument('--algo', type=str, default=None, help='DRL Algorithm (ppo, a2c, ddpg, hoặc ALL)')
    parser.add_argument('--epochs', type=int, default=None, help='Total timesteps')
    parser.add_argument('--from-date', type=str, default=None, help='Từ ngày (DD/MM/YYYY)')
    parser.add_argument('--to-date', type=str, default=None, help='Đến ngày (DD/MM/YYYY)')
    parser.add_argument('--indicators', type=str, default=None, help='Chỉ báo, cách nhau bởi dấu phẩy')
    parser.add_argument('--batch-size', type=int, default=100, help='Số mã mỗi batch khi train ALL (default: 100)')

    parser.add_argument('--ssi-client', type=str, default=os.environ.get('SSI_CLIENT_ID', ''), help='SSI Consumer ID')
    parser.add_argument('--ssi-secret', type=str, default=os.environ.get('SSI_CLIENT_SECRET', ''), help='SSI Consumer Secret')
    parser.add_argument('--ssi-url', type=str, default=os.environ.get('SSI_API_URL', 'https://fc-data.ssi.com.vn/'), help='SSI API URL')

    args = parser.parse_args()

    print("\n" + "="*50)
    print(" === CHƯƠNG TRÌNH HUẤN LUYỆN AI ĐẦU TƯ CHỨNG KHOÁN === ")
    print("="*50 + "\n")

    ticker = args.ticker
    algo = args.algo
    epochs_input = args.epochs
    from_date = args.from_date
    to_date = args.to_date

    if not ticker:
        ticker = input("> Nhập [Mã Chứng Khoán] (VD: FPT, hoặc ALL, Enter=ALL): ").strip() or "ALL"

    if not algo:
        algo = input("> Nhập [Thuật toán AI] (ppo, a2c, ddpg, ALL, Enter=ALL): ").strip() or "ALL"

    if not epochs_input:
        epochs_str = input(f"> Nhập [Epochs/Timesteps] (Enter={DEFAULT_EPOCHS}): ").strip()
        epochs = int(epochs_str) if epochs_str.isdigit() else DEFAULT_EPOCHS
    else:
        epochs = epochs_input

    if not from_date:
        from_date = input("> Nhập [Từ Ngày] (DD/MM/YYYY, Enter=25/02/2025): ").strip() or "25/02/2025"

    if not to_date:
        to_date = input("> Nhập [Đến Ngày] (DD/MM/YYYY, Enter=25/02/2026): ").strip() or "25/02/2026"

    indicator_list = None
    if args.indicators:
        indicator_list = [x.strip() for x in args.indicators.split(',') if x.strip()]

    ssi_client = args.ssi_client
    if not ssi_client:
        ssi_client = input("> Nhập [SSI Consumer ID]: ").strip()
        if not ssi_client:
            print("[ERROR] Bắt buộc phải nhập SSI Consumer ID!")
            sys.exit(1)

    ssi_secret = args.ssi_secret
    if not ssi_secret:
        import getpass
        ssi_secret = getpass.getpass("> Nhập [SSI Consumer Secret]: ").strip()
        if not ssi_secret:
            print("[ERROR] Bắt buộc phải nhập SSI Consumer Secret!")
            sys.exit(1)

    # ──── Batch Training for ALL tickers ────
    if ticker.upper() == "ALL":
        batch_size = args.batch_size
        print(f"\n[*] Chế độ BATCH: Tải danh sách tất cả mã từ SSI...")
        all_tickers = fetch_all_tickers_from_ssi(ssi_client, ssi_secret, args.ssi_url)
        total_tickers = len(all_tickers)
        total_batches = (total_tickers + batch_size - 1) // batch_size

        print(f"[*] Tổng: {total_tickers} mã → {total_batches} batch x {batch_size} mã/batch")
        print(f"{'='*50}\n")

        failed_batches = []
        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, total_tickers)
            batch_tickers = all_tickers[start:end]
            batch_name = f"BATCH_{batch_idx+1:03d}"
            batch_ticker_str = ",".join(batch_tickers)

            print(f"\n{'='*60}")
            print(f"[BATCH {batch_idx+1}/{total_batches}] {batch_name}: {batch_ticker_str}")
            print(f"{'='*60}")

            try:
                train_model(batch_ticker_str, algo, epochs, from_date, to_date,
                            ssi_client, ssi_secret, args.ssi_url, indicator_list)
            except Exception as e:
                print(f"[ERROR] Batch {batch_name} thất bại: {e}")
                failed_batches.append((batch_name, str(e)))
                continue

        # Summary
        print(f"\n{'='*60}")
        print(f"[TỔNG KẾT] {total_batches - len(failed_batches)}/{total_batches} batch thành công")
        if failed_batches:
            print(f"[!] Batch thất bại:")
            for name, err in failed_batches:
                print(f"    - {name}: {err}")
        print(f"{'='*60}")

    else:
        # Single ticker or comma-separated list
        try:
            train_model(ticker, algo, epochs, from_date, to_date, ssi_client, ssi_secret, args.ssi_url, indicator_list)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[ERROR] Quá trình huấn luyện thất bại: {str(e)}")
            sys.exit(1)

