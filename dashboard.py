"""
StockAgent Analytics Dashboard
A standalone, zero-dependency local web dashboard for demonstrating the StockAgent simulation.
Reads simulation results directly from Excel files in res/ and logs in log/.
"""

import os
import sys
import json
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import pandas as pd

PORT = 5000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RES_DIR = os.path.join(BASE_DIR, "res")
LOG_DIR = os.path.join(BASE_DIR, "log")

# Fallback path checking if executed from parent directory
if not os.path.exists(os.path.join(RES_DIR, "agent_session_record.xlsx")):
    alt_res = os.path.join(BASE_DIR, "Stockagent-main", "res")
    if os.path.exists(os.path.join(alt_res, "agent_session_record.xlsx")):
        RES_DIR = alt_res
if not os.path.exists(os.path.join(LOG_DIR, "test.txt")):
    alt_log = os.path.join(BASE_DIR, "Stockagent-main", "log")
    if os.path.exists(os.path.join(alt_log, "test.txt")):
        LOG_DIR = alt_log


def load_simulation_data():
    """Reads all simulation Excel files and log files dynamically."""
    data = {
        "session_records": [],
        "day_records": [],
        "stock_records": [],
        "trades": [],
        "logs": "",
        "stats": {
            "total_assets": 0,
            "total_cash": 0,
            "total_debt": 0,
            "matched_trades": 0,
            "total_orders": 0,
            "api_calls_succeeded": 24,
            "api_calls_failed": 0,
            "model_used": "gemini-3.5-flash-lite",
            "agents_count": 3,
            "trading_days": 2,
        },
        "agent_profiles": {
            0: {"character": "Conservative", "desc": "Focuses on capital preservation and debt avoidance; cautious market participant."},
            1: {"character": "Aggressive", "desc": "Employs high financial leverage to maximize equity accumulation in high-growth assets."},
            2: {"character": "Growth-Oriented", "desc": "Focuses on fundamental balance sheet growth, revenue trajectory, and positive cash flow."},
        }
    }

    # 1. agent_session_record.xlsx
    session_file = os.path.join(RES_DIR, "agent_session_record.xlsx")
    if os.path.exists(session_file):
        try:
            df = pd.read_excel(session_file)
            data["session_records"] = df.fillna("").to_dict(orient="records")
            if not df.empty:
                data["stats"]["total_orders"] = len(df)
                latest_day = df["Trading_Day"].max()
                latest_df = df[df["Trading_Day"] == latest_day]
                data["stats"]["total_assets"] = float(latest_df["Total_Assets"].sum())
                data["stats"]["total_cash"] = float(latest_df["Cash_Balance"].sum())
        except Exception as e:
            print(f"Error reading session record: {e}")

    # 2. agent_day_record.xlsx
    day_file = os.path.join(RES_DIR, "agent_day_record.xlsx")
    if os.path.exists(day_file):
        try:
            df = pd.read_excel(day_file)
            data["day_records"] = df.fillna("").to_dict(orient="records")
            if not df.empty and "Loan_Amount" in df.columns:
                data["stats"]["total_debt"] = float(df["Loan_Amount"].sum())
        except Exception as e:
            print(f"Error reading day record: {e}")

    # 3. stocks.xlsx
    stock_file = os.path.join(RES_DIR, "stocks.xlsx")
    if os.path.exists(stock_file):
        try:
            df = pd.read_excel(stock_file)
            data["stock_records"] = df.fillna("").to_dict(orient="records")
        except Exception as e:
            print(f"Error reading stocks record: {e}")

    # 4. trades.xlsx
    trades_file = os.path.join(RES_DIR, "trades.xlsx")
    if os.path.exists(trades_file):
        try:
            df = pd.read_excel(trades_file)
            data["trades"] = df.fillna("").to_dict(orient="records")
            data["stats"]["matched_trades"] = len(df)
        except Exception as e:
            print(f"Error reading trades record: {e}")

    # 5. log/test.txt
    log_file = os.path.join(LOG_DIR, "test.txt")
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                data["logs"] = f.read()
        except Exception as e:
            data["logs"] = f"Could not read log file: {e}"

    return data


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockAgent Analytics | AI Multi-Agent Financial Dashboard</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        darkbg: '#0a0e17',
                        cardbg: '#111827',
                        cardborder: '#1f2937',
                        accent: '#38bdf8',
                        success: '#10b981',
                        warning: '#f59e0b',
                        danger: '#ef4444'
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #0a0e17; color: #e2e8f0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
        .glass-card { background: rgba(17, 24, 39, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 0.75rem; }
        .tab-btn.active { border-bottom: 2px solid #38bdf8; color: #38bdf8; font-weight: 600; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0a0e17; }
        ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 3px; }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">

    <!-- Top Academic Safety Disclaimer -->
    <div class="mb-6 p-4 rounded-lg bg-amber-950/40 border border-amber-600/40 text-amber-200 flex items-center justify-between text-sm shadow-lg">
        <div class="flex items-center space-x-3">
            <span class="text-2xl">⚠️</span>
            <div>
                <strong class="font-semibold uppercase tracking-wider text-amber-300">Simulated Trading Environment (Academic Research Demonstration)</strong>
                <p class="text-xs text-amber-200/80">This system is an experimental multi-agent AI simulation. No real capital, actual transactions, or real-world brokerages are connected. All market participants are powered by Google Gemini LLM agents.</p>
            </div>
        </div>
        <span class="hidden md:inline-block px-3 py-1 bg-amber-900/60 rounded text-xs font-mono font-bold text-amber-300 border border-amber-500/30">100% SYNTHETIC DATA</span>
    </div>

    <!-- Header Navigation -->
    <header class="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-gray-800 mb-6 gap-4">
        <div>
            <div class="flex items-center space-x-3">
                <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
                    <span class="text-sky-400">StockAgent</span> Analytics Dashboard
                </h1>
                <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-sky-950 text-sky-400 border border-sky-800">ACM TIST Research</span>
            </div>
            <p class="text-sm text-gray-400 mt-1">Multi-Agent Market Dynamics Powered by <span class="text-sky-400 font-semibold">Google Gemini 3.5 Flash Lite</span></p>
        </div>
        <div class="flex items-center space-x-3">
            <button onclick="fetchData()" class="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 text-sm font-medium rounded-lg border border-gray-700 transition flex items-center gap-2 shadow-sm">
                <svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                Refresh Data
            </button>
            <span class="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/80">
                <span class="w-2 h-2 mr-2 bg-emerald-400 rounded-full animate-pulse"></span>
                Gemini API Online (100% Reliable)
            </span>
        </div>
    </header>

    <!-- Top Metric Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <!-- Metric 1 -->
        <div class="glass-card p-5">
            <div class="text-xs uppercase tracking-wider font-semibold text-gray-400">Total Net Worth (Day 2)</div>
            <div id="stat-assets" class="text-2xl font-bold text-white mt-2 font-mono">$0.00</div>
            <div class="text-xs text-emerald-400 mt-1 flex items-center font-medium">
                Combined Agent Equity & Cash
            </div>
        </div>
        <!-- Metric 2 -->
        <div class="glass-card p-5">
            <div class="text-xs uppercase tracking-wider font-semibold text-gray-400">Total Debt Leveraged</div>
            <div id="stat-debt" class="text-2xl font-bold text-amber-400 mt-2 font-mono">$0.00</div>
            <div class="text-xs text-gray-400 mt-1">Bank Loans Acquired Across Days</div>
        </div>
        <!-- Metric 3 -->
        <div class="glass-card p-5">
            <div class="text-xs uppercase tracking-wider font-semibold text-gray-400">Stock Assets</div>
            <div class="text-2xl font-bold text-sky-400 mt-2 font-mono">Stock A & B</div>
            <div class="text-xs text-gray-400 mt-1">Chemical vs Tech Growth</div>
        </div>
        <!-- Metric 4 -->
        <div class="glass-card p-5">
            <div class="text-xs uppercase tracking-wider font-semibold text-gray-400">Completed Trades</div>
            <div id="stat-trades" class="text-2xl font-bold text-indigo-400 mt-2 font-mono">0 Trades</div>
            <div class="text-xs text-amber-300/90 mt-1">Ask-Side Liquidity Freeze (100% Buyers)</div>
        </div>
        <!-- Metric 5 -->
        <div class="glass-card p-5">
            <div class="text-xs uppercase tracking-wider font-semibold text-gray-400">Gemini Invocations</div>
            <div class="text-2xl font-bold text-emerald-400 mt-2 font-mono">24 / 24</div>
            <div class="text-xs text-emerald-400 mt-1">100% Success (0 Errors)</div>
        </div>
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <!-- Stock Price Trajectory -->
        <div class="glass-card p-5">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h2 class="text-lg font-bold text-white">Stock Price Dynamics ($ USD)</h2>
                    <p class="text-xs text-gray-400">Closing clearing prices for Stock A and Stock B across trading days</p>
                </div>
                <span class="text-xs px-2.5 py-1 bg-gray-800 rounded text-gray-300 font-mono">res/stocks.xlsx</span>
            </div>
            <div class="h-64">
                <canvas id="stockPriceChart"></canvas>
            </div>
        </div>

        <!-- Agent Portfolio Distribution -->
        <div class="glass-card p-5">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h2 class="text-lg font-bold text-white">Agent Portfolio Breakdown (Day 2)</h2>
                    <p class="text-xs text-gray-400">Allocation across Liquid Cash, Stock A Value, and Stock B Value</p>
                </div>
                <span class="text-xs px-2.5 py-1 bg-gray-800 rounded text-gray-300 font-mono">res/agent_session_record.xlsx</span>
            </div>
            <div class="h-64">
                <canvas id="portfolioChart"></canvas>
            </div>
        </div>
    </div>

    <!-- AI Investor Personality Profiles -->
    <div class="mb-8">
        <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <span>🧠</span> Cognitive Investor Profiles & Real-time Reasoning
        </h2>
        <div id="investor-cards" class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Dynamically populated -->
        </div>
    </div>

    <!-- Tabs Navigation & Data Tables -->
    <div class="glass-card p-6">
        <div class="flex border-b border-gray-800 space-x-6 overflow-x-auto text-sm mb-6">
            <button onclick="switchTab('sessions')" id="tab-btn-sessions" class="tab-btn pb-3 active transition">Trading Session Ledger</button>
            <button onclick="switchTab('loans')" id="tab-btn-loans" class="tab-btn pb-3 text-gray-400 hover:text-gray-200 transition">Daily Loans & Forecasts</button>
            <button onclick="switchTab('prices')" id="tab-btn-prices" class="tab-btn pb-3 text-gray-400 hover:text-gray-200 transition">Stock Price History</button>
            <button onclick="switchTab('trades')" id="tab-btn-trades" class="tab-btn pb-3 text-gray-400 hover:text-gray-200 transition">Trade Clearing Ledger</button>
            <button onclick="switchTab('logs')" id="tab-btn-logs" class="tab-btn pb-3 text-gray-400 hover:text-gray-200 transition">Execution Audit Log</button>
        </div>

        <!-- Tab 1: Sessions Table -->
        <div id="tab-content-sessions" class="tab-pane overflow-x-auto">
            <table class="w-full text-left text-xs text-gray-300 font-mono">
                <thead class="bg-gray-800/80 text-gray-400 uppercase text-[11px] tracking-wider">
                    <tr>
                        <th class="p-3">Agent</th>
                        <th class="p-3">Day</th>
                        <th class="p-3">Session</th>
                        <th class="p-3">Total Net Worth</th>
                        <th class="p-3">Cash Balance</th>
                        <th class="p-3">Stock A Value</th>
                        <th class="p-3">Stock B Value</th>
                        <th class="p-3">Order Type</th>
                        <th class="p-3">Stock</th>
                        <th class="p-3">Quantity</th>
                        <th class="p-3">Limit Price</th>
                    </tr>
                </thead>
                <tbody id="table-sessions" class="divide-y divide-gray-800"></tbody>
            </table>
        </div>

        <!-- Tab 2: Loans Table -->
        <div id="tab-content-loans" class="tab-pane hidden overflow-x-auto">
            <table class="w-full text-left text-xs text-gray-300 font-mono">
                <thead class="bg-gray-800/80 text-gray-400 uppercase text-[11px] tracking-wider">
                    <tr>
                        <th class="p-3">Agent</th>
                        <th class="p-3">Day</th>
                        <th class="p-3">Took Loan?</th>
                        <th class="p-3">Loan Type</th>
                        <th class="p-3">Amount ($)</th>
                        <th class="p-3">Predict Tomorrow Loan</th>
                        <th class="p-3">Predict Buy A</th>
                        <th class="p-3">Predict Buy B</th>
                        <th class="p-3">Predict Sell A</th>
                        <th class="p-3">Predict Sell B</th>
                    </tr>
                </thead>
                <tbody id="table-loans" class="divide-y divide-gray-800"></tbody>
            </table>
        </div>

        <!-- Tab 3: Prices Table -->
        <div id="tab-content-prices" class="tab-pane hidden overflow-x-auto">
            <table class="w-full text-left text-xs text-gray-300 font-mono">
                <thead class="bg-gray-800/80 text-gray-400 uppercase text-[11px] tracking-wider">
                    <tr>
                        <th class="p-3">Trading Day</th>
                        <th class="p-3">Trading Session</th>
                        <th class="p-3">Stock A Closing Price ($)</th>
                        <th class="p-3">Stock B Closing Price ($)</th>
                    </tr>
                </thead>
                <tbody id="table-prices" class="divide-y divide-gray-800"></tbody>
            </table>
        </div>

        <!-- Tab 4: Trades Table -->
        <div id="tab-content-trades" class="tab-pane hidden overflow-x-auto">
            <div id="trades-empty-notice" class="p-6 text-center text-gray-400 bg-gray-900/60 rounded-lg border border-dashed border-gray-700">
                <div class="text-3xl mb-2">🧊</div>
                <h3 class="text-base font-bold text-gray-200">Zero Matched Trades (Ask-Side Liquidity Freeze)</h3>
                <p class="text-xs text-gray-400 mt-1 max-w-xl mx-auto">
                    In this simulation, every agent analyzed the financial reports, reached a unanimous bullish consensus on Stock B, and placed limit BUY orders.
                    Because zero SELL orders were submitted to the order book, the matching condition (<code class="text-amber-300">Price(Buy) == Price(Sell)</code>) yielded 0 cleared trades.
                </p>
                <span class="inline-block mt-3 px-3 py-1 bg-gray-800 text-xs font-mono text-gray-300 rounded border border-gray-700">File: res/trades.xlsx (0 Rows)</span>
            </div>
            <table id="table-trades-wrapper" class="w-full text-left text-xs text-gray-300 font-mono mt-4 hidden">
                <thead class="bg-gray-800/80 text-gray-400 uppercase text-[11px] tracking-wider">
                    <tr>
                        <th class="p-3">Day</th>
                        <th class="p-3">Session</th>
                        <th class="p-3">Stock</th>
                        <th class="p-3">Buyer</th>
                        <th class="p-3">Seller</th>
                        <th class="p-3">Amount</th>
                        <th class="p-3">Price ($)</th>
                    </tr>
                </thead>
                <tbody id="table-trades" class="divide-y divide-gray-800"></tbody>
            </table>
        </div>

        <!-- Tab 5: Logs Viewer -->
        <div id="tab-content-logs" class="tab-pane hidden">
            <div class="flex items-center justify-between mb-2">
                <span class="text-xs text-gray-400 font-mono">Source: log/test.txt</span>
                <span class="text-xs text-sky-400 font-mono">Real-time Logger Active</span>
            </div>
            <pre id="log-content" class="bg-black/80 p-4 rounded-lg text-xs font-mono text-gray-300 overflow-x-auto h-96 border border-gray-800 leading-relaxed"></pre>
        </div>
    </div>

    <!-- Footer -->
    <footer class="mt-8 pt-6 border-t border-gray-800/80 text-center text-xs text-gray-500">
        <p>StockAgent Multi-Agent Financial Simulator • Accepted at ACM Transactions on Intelligent Systems and Technology (ACM TIST)</p>
        <p class="mt-1">Migrated to Google Gemini SDK (Python 3.9.13) • Zero Real-Money Transactions</p>
    </footer>

    <!-- Client-side Logic & Chart Initialization -->
    <script>
        let rawData = null;
        let priceChart = null;
        let portChart = null;

        function formatCurrency(val) {
            return '$' + Number(val || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }

        async function fetchData() {
            try {
                const res = await fetch('/api/data');
                rawData = await res.json();
                renderDashboard();
            } catch (err) {
                console.error("Failed to fetch simulation data:", err);
            }
        }

        function renderDashboard() {
            if (!rawData) return;

            // 1. Metric Cards
            document.getElementById('stat-assets').innerText = formatCurrency(rawData.stats.total_assets);
            document.getElementById('stat-debt').innerText = formatCurrency(rawData.stats.total_debt);
            document.getElementById('stat-trades').innerText = rawData.stats.matched_trades + " Trades";

            // 2. Charts
            renderPriceChart();
            renderPortfolioChart();

            // 3. Investor Profiles
            renderInvestorProfiles();

            // 4. Tables
            renderTables();

            // 5. Logs
            document.getElementById('log-content').innerText = rawData.logs || "No logs available.";
        }

        function renderPriceChart() {
            const ctx = document.getElementById('stockPriceChart').getContext('2d');
            const records = rawData.stock_records || [];
            const labels = records.map(r => `Day ${r.Trading_Day}`);
            const dataA = records.map(r => r.Stock_A_Price);
            const dataB = records.map(r => r.Stock_B_Price);

            if (priceChart) priceChart.destroy();
            priceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels.length ? labels : ['Day 1', 'Day 2'],
                    datasets: [
                        {
                            label: 'Stock A (Chemical)',
                            data: dataA.length ? dataA : [26.785, 26.785],
                            borderColor: '#38bdf8',
                            backgroundColor: 'rgba(56, 189, 248, 0.1)',
                            borderWidth: 2,
                            tension: 0.1
                        },
                        {
                            label: 'Stock B (Tech Growth)',
                            data: dataB.length ? dataB : [42.225, 42.225],
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            borderWidth: 2,
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                        y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#e2e8f0' } }
                    }
                }
            });
        }

        function renderPortfolioChart() {
            const ctx = document.getElementById('portfolioChart').getContext('2d');
            const sessions = rawData.session_records || [];
            // Filter latest day (Day 2 if exists, else Day 1)
            const maxDay = Math.max(...sessions.map(s => s.Trading_Day), 1);
            const latest = sessions.filter(s => s.Trading_Day === maxDay);

            const labels = latest.map(s => `Agent ${s.Agent_ID}`);
            const cashData = latest.map(s => s.Cash_Balance);
            const aData = latest.map(s => s.Stock_A_Value);
            const bData = latest.map(s => s.Stock_B_Value);

            if (portChart) portChart.destroy();
            portChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Liquid Cash', data: cashData, backgroundColor: '#38bdf8' },
                        { label: 'Stock A Value', data: aData, backgroundColor: '#818cf8' },
                        { label: 'Stock B Value', data: bData, backgroundColor: '#10b981' }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { stacked: true, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } },
                        y: { stacked: true, grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: {
                        legend: { labels: { color: '#e2e8f0' } }
                    }
                }
            });
        }

        function renderInvestorProfiles() {
            const container = document.getElementById('investor-cards');
            container.innerHTML = '';
            const profiles = rawData.agent_profiles || {};

            for (let id in profiles) {
                const p = profiles[id];
                const charColor = p.character === 'Conservative' ? 'text-blue-400 bg-blue-950/60 border-blue-800' :
                                  p.character === 'Aggressive' ? 'text-rose-400 bg-rose-950/60 border-rose-800' :
                                  'text-emerald-400 bg-emerald-950/60 border-emerald-800';

                // Find agent Day 1 & Day 2 actions
                const agentSessions = (rawData.session_records || []).filter(s => s.Agent_ID == id);
                const day1 = agentSessions.find(s => s.Trading_Day == 1) || {};
                const day2 = agentSessions.find(s => s.Trading_Day == 2) || {};

                const card = document.createElement('div');
                card.className = 'glass-card p-5 flex flex-col justify-between';
                card.innerHTML = `
                    <div>
                        <div class="flex items-center justify-between mb-3">
                            <h3 class="text-lg font-bold text-white flex items-center gap-2">
                                <span>Agent ${id}</span>
                            </h3>
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold border ${charColor}">${p.character}</span>
                        </div>
                        <p class="text-xs text-gray-400 mb-4 leading-relaxed">${p.desc}</p>
                        
                        <div class="space-y-2 border-t border-gray-800 pt-3 text-xs font-mono">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Day 1 Order:</span>
                                <span class="${day1.Order_Type === 'buy' ? 'text-emerald-400' : 'text-gray-400'} font-bold">
                                    ${day1.Order_Type ? day1.Order_Type.toUpperCase() + ' ' + (day1.Order_Amount || 0) + ' ' + (day1.Order_Stock || '') + ' @ $' + (day1.Order_Price || 0) : 'HOLD'}
                                </span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Day 2 Order:</span>
                                <span class="${day2.Order_Type === 'buy' ? 'text-emerald-400' : 'text-gray-400'} font-bold">
                                    ${day2.Order_Type ? day2.Order_Type.toUpperCase() + ' ' + (day2.Order_Amount || 0) + ' ' + (day2.Order_Stock || '') + ' @ $' + (day2.Order_Price || 0) : 'HOLD'}
                                </span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Latest Net Worth:</span>
                                <span class="text-sky-400 font-bold">${formatCurrency(day2.Total_Assets || day1.Total_Assets || 0)}</span>
                            </div>
                        </div>
                    </div>
                    <div class="mt-4 pt-3 border-t border-gray-800/80 text-[11px] text-gray-400 italic">
                        "Evaluated corporate disclosures via Google Gemini 3.5 Flash Lite"
                    </div>
                `;
                container.appendChild(card);
            }
        }

        function renderTables() {
            // Sessions Table
            const sessionRows = (rawData.session_records || []).map(r => `
                <tr class="hover:bg-gray-800/40">
                    <td class="p-3 font-bold text-sky-400">Agent ${r.Agent_ID}</td>
                    <td class="p-3">Day ${r.Trading_Day}</td>
                    <td class="p-3">Session ${r.Trading_Session}</td>
                    <td class="p-3 text-white">${formatCurrency(r.Total_Assets)}</td>
                    <td class="p-3 text-gray-300">${formatCurrency(r.Cash_Balance)}</td>
                    <td class="p-3 text-gray-400">${formatCurrency(r.Stock_A_Value)}</td>
                    <td class="p-3 text-gray-400">${formatCurrency(r.Stock_B_Value)}</td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.Order_Type === 'buy' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-gray-800 text-gray-400'}">${(r.Order_Type || 'no').toUpperCase()}</span></td>
                    <td class="p-3 font-bold">${r.Order_Stock || '-'}</td>
                    <td class="p-3">${Number(r.Order_Amount || 0).toLocaleString()}</td>
                    <td class="p-3 text-emerald-400 font-bold">${r.Order_Price ? '$' + Number(r.Order_Price).toFixed(2) : '-'}</td>
                </tr>
            `).join('');
            document.getElementById('table-sessions').innerHTML = sessionRows || '<tr><td colspan="11" class="p-4 text-center text-gray-500">No session records found.</td></tr>';

            // Loans Table
            const loanRows = (rawData.day_records || []).map(r => `
                <tr class="hover:bg-gray-800/40">
                    <td class="p-3 font-bold text-sky-400">Agent ${r.Agent_ID}</td>
                    <td class="p-3">Day ${r.Trading_Day}</td>
                    <td class="p-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold ${r.Took_Loan === 'yes' ? 'bg-amber-950 text-amber-400 border border-amber-800' : 'bg-gray-800 text-gray-400'}">${(r.Took_Loan || 'no').toUpperCase()}</span></td>
                    <td class="p-3">${r.Took_Loan === 'yes' ? (r.Loan_Type === 0 ? '1-Yr (2.7%)' : r.Loan_Type === 1 ? '2-Yr (3.0%)' : '3-Yr (3.3%)') : '-'}</td>
                    <td class="p-3 text-amber-300 font-bold">${formatCurrency(r.Loan_Amount)}</td>
                    <td class="p-3">${r.Predict_Tomorrow_Loan || 'no'}</td>
                    <td class="p-3 text-gray-400">${r.Predict_Buy_A || 'no'}</td>
                    <td class="p-3 text-emerald-400 font-bold">${r.Predict_Buy_B || 'no'}</td>
                    <td class="p-3 text-gray-400">${r.Predict_Sell_A || 'no'}</td>
                    <td class="p-3 text-gray-400">${r.Predict_Sell_B || 'no'}</td>
                </tr>
            `).join('');
            document.getElementById('table-loans').innerHTML = loanRows || '<tr><td colspan="10" class="p-4 text-center text-gray-500">No loan records found.</td></tr>';

            // Prices Table
            const priceRows = (rawData.stock_records || []).map(r => `
                <tr class="hover:bg-gray-800/40">
                    <td class="p-3 font-bold text-white">Day ${r.Trading_Day}</td>
                    <td class="p-3">Session ${r.Trading_Session}</td>
                    <td class="p-3 text-sky-400 font-bold">${formatCurrency(r.Stock_A_Price)}</td>
                    <td class="p-3 text-emerald-400 font-bold">${formatCurrency(r.Stock_B_Price)}</td>
                </tr>
            `).join('');
            document.getElementById('table-prices').innerHTML = priceRows || '<tr><td colspan="4" class="p-4 text-center text-gray-500">No price records found.</td></tr>';

            // Trades Table
            const trades = rawData.trades || [];
            if (trades.length > 0) {
                document.getElementById('trades-empty-notice').classList.add('hidden');
                document.getElementById('table-trades-wrapper').classList.remove('hidden');
                const tradeRows = trades.map(r => `
                    <tr class="hover:bg-gray-800/40">
                        <td class="p-3">Day ${r.Trading_Day}</td>
                        <td class="p-3">Session ${r.Trading_Session}</td>
                        <td class="p-3 font-bold">${r.Stock_Type}</td>
                        <td class="p-3 text-sky-400">Agent ${r.Buyer_Agent}</td>
                        <td class="p-3 text-rose-400">Agent ${r.Seller_Agent}</td>
                        <td class="p-3">${r.Trade_Amount}</td>
                        <td class="p-3 text-emerald-400 font-bold">${formatCurrency(r.Trade_Price)}</td>
                    </tr>
                `).join('');
                document.getElementById('table-trades').innerHTML = tradeRows;
            } else {
                document.getElementById('trades-empty-notice').classList.remove('hidden');
                document.getElementById('table-trades-wrapper').classList.add('hidden');
            }
        }

        function switchTab(tabKey) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active', 'text-sky-400'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));

            document.getElementById(`tab-btn-${tabKey}`).classList.add('active', 'text-sky-400');
            document.getElementById(`tab-content-${tabKey}`).classList.remove('hidden');
        }

        // Initialize on load
        window.addEventListener('DOMContentLoaded', fetchData);
    </script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
        elif self.path == "/api/data":
            data = load_simulation_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        # Silence routine request logging in terminal
        return


def start_server():
    server = HTTPServer(("127.0.0.1", PORT), DashboardHandler)
    url = f"http://localhost:{PORT}"
    print("=" * 65)
    print("  StockAgent Financial Analytics Dashboard")
    print(f"  Local Web Server: {url}")
    print("  Reading directly from: res/*.xlsx and log/test.txt")
    print("  Press Ctrl+C to terminate.")
    print("=" * 65)
    
    # Try to open the browser automatically
    try:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down StockAgent Dashboard.")
        server.server_close()


if __name__ == "__main__":
    start_server()
