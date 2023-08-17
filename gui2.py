import backtrader as bt
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import threading
import random
import pandas as pd
from forex_python.converter import CurrencyRates
from tradingview_ta import TA_Handler, Interval, Exchange

class MyStrategy(bt.Strategy):
    params = (
        ('sma_period', 20),
        ('rsi_period', 14),
        ('macd_fast', 12),
        ('macd_slow', 26),
        ('macd_signal', 9),
        ('atr_period', 14),
        ('stoch_period', 14),
        ('stoch_smooth', 3),
        ('bb_period', 20),
        ('bb_dev', 2),
    )

    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=self.params.sma_period)
        self.rsi = bt.indicators.RelativeStrengthIndex(period=self.params.rsi_period)
        self.macd = bt.indicators.MACD(
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal,
        )
        self.atr = bt.indicators.AverageTrueRange(period=self.params.atr_period)
        self.stoch = bt.indicators.Stochastic(period=self.params.stoch_period, period_dfast=self.params.stoch_smooth)
        self.bbands = bt.indicators.BollingerBands(period=self.params.bb_period, devfactor=self.params.bb_dev)

    def next(self):
        if self.data.close[0] > self.sma[0] and self.rsi[0] > 70:
            self.sell()

        elif self.data.close[0] < self.sma[0] and self.rsi[0] < 30:
            self.buy()


class BacktestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Backtest GUI")

        self.run_button = ttk.Button(root, text="Run Backtest", command=self.run_thread)
        self.run_button.pack()

        self.time_periods = ["1 Day", "1 Week", "1 Month", "3 Months", "6 Months", "1 Year"]
        self.time_period_var = tk.StringVar(value="1 Month")

        self.time_period_label = tk.Label(root, text="Select Time Period:")
        self.time_period_label.pack()

        self.time_period_option_menu = tk.OptionMenu(root, self.time_period_var, *self.time_periods)
        self.time_period_option_menu.pack()

        self.update_button = ttk.Button(root, text="Update Chart", command=self.update_chart)
        self.update_button.pack()

        self.strategy_label = tk.Label(root, text="Enter Strategy (buy/sell):")
        self.strategy_label.pack()

        self.strategy_entry = tk.Entry(root)
        self.strategy_entry.pack()

        self.currency_label = tk.Label(root, text="Currency Exchange Rates:")
        self.currency_label.pack()

        self.currency_rates = tk.Label(root, text="Fetching...")
        self.currency_rates.pack()

        self.figure = plt.figure(figsize=(10, 6))
        self.ax = self.figure.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack()

    def fetch_tradingview_data(self, symbol, timeframe):
        interval = None
        if timeframe == "1 Day":
            interval = Interval.INTERVAL_1_DAY
        elif timeframe == "1 Week":
            interval = Interval.INTERVAL_1_WEEK

        handler = TA_Handler(
            symbol=symbol,
            exchange=Exchange.BITFINEX,
            screener="crypto",
            interval=interval,
            timeout=10
        )

        df = handler.get_pandas()
        df['datetime'] = df.index
        return df

    def update_chart(self):
        selected_period = self.time_period_var.get()
        symbol = "BTCUSD"

        new_data = self.fetch_tradingview_data(symbol, selected_period)

        self.ax.clear()
        self.ax.plot(new_data['datetime'], new_data['close'], label="Price")
        self.ax.legend()
        self.canvas.draw()

    def run_thread(self):
        self.run_button.config(state="disabled")
        self.plot_results(None)
        self.fetch_currency_rates()
        self.thread = threading.Thread(target=self.run_backtest)
        self.thread.start()

    def run_backtest(self):
        data = bt.feeds.PandasData(dataname=self.fetch_tradingview_data("BTCUSD", "1 Day"))

        cerebro = bt.Cerebro()
        cerebro.adddata(data)
        cerebro.addstrategy(MyStrategy)
        cerebro.broker.set_cash(100000)
        cerebro.broker.setcommission(commission=0.001)

        cerebro.run()

        self.plot_results(cerebro)

    def plot_results(self, cerebro):
        self.ax.clear()
        if cerebro:
            self.ax.plot(cerebro.datas[0].datetime.get(), cerebro.datas[0].close.get(), label="Price")
            self.ax.legend()
        self.canvas.draw()

    def fetch_currency_rates(self):
        c = CurrencyRates()
        usd_to_eur = c.get_rate('USD', 'EUR')
        usd_to_gbp = c.get_rate('USD', 'GBP')
        usd_to_jpy = c.get_rate('USD', 'JPY')
        self.currency_rates.config(text=f"USD to EUR: {usd_to_eur:.4f}, USD to GBP: {usd_to_gbp:.4f}, USD to JPY: {usd_to_jpy:.4f}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BacktestApp(root)
    root.mainloop()
        
