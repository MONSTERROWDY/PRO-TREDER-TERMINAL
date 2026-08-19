import streamlit as st
import streamlit.components.v1 as components

# 1. Streamlit Page Configuration
st.set_page_config(
    page_title="Veer Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide default Streamlit headers & footers for native app feel
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding: 0rem !important;}
</style>
""", unsafe_allow_html=True)

# 2. Complete Veer Pro Trading Terminal Application (HTML + Tailwind + JS Engine)
FULL_TERMINAL_HTML = """
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Veer Pro Terminal</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Lucide Icons -->
    <script src="https://unpkg.com/lucide@latest"></script>
    <!-- TradingView Lightweight Charts -->
    <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        body { background-color: #0b0e14; color: #e1e7ef; font-family: sans-serif; }
        .card { background-color: #121824; border: 1px solid #1e293b; }
        .tab-active { border-bottom: 2px solid #3b82f6; color: #3b82f6; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    </style>
</head>
<body class="pb-20">

    <!-- TOP HEADER -->
    <header class="flex items-center justify-between p-4 border-b border-slate-800">
        <div class="flex items-center gap-3">
            <i data-lucide="menu" class="w-6 h-6 text-slate-400 cursor-pointer"></i>
            <div class="flex items-center gap-2">
                <i data-lucide="zap" class="w-6 h-6 text-amber-400 fill-amber-400"></i>
                <span class="font-bold text-lg text-white">Veer Pro <span class="text-xs font-normal text-slate-400">Terminal</span></span>
            </div>
        </div>
        <div class="flex items-center gap-4">
            <i data-lucide="star" class="w-5 h-5 text-slate-400 cursor-pointer"></i>
            <i data-lucide="edit-3" class="w-5 h-5 text-slate-400 cursor-pointer"></i>
            <i data-lucide="more-vertical" class="w-5 h-5 text-slate-400 cursor-pointer"></i>
        </div>
    </header>

    <!-- TICKER BAR -->
    <div class="flex gap-2 overflow-x-auto p-3 text-xs border-b border-slate-800/50 no-scrollbar">
        <div class="card p-2 rounded flex-1 min-w-[120px]">
            <div class="flex justify-between items-center text-slate-400">
                <span class="font-bold text-white">BTCUSDT</span>
            </div>
            <div class="flex justify-between items-center mt-1">
                <span>$68,417.51</span>
                <span class="text-emerald-400">+1.23%</span>
            </div>
        </div>
        <div class="card p-2 rounded flex-1 min-w-[120px]">
            <div class="flex justify-between items-center text-slate-400">
                <span class="font-bold text-white">🔥 SOLUSDT</span>
            </div>
            <div class="flex justify-between items-center mt-1">
                <span>$145.06</span>
                <span class="text-emerald-400">+2.45%</span>
            </div>
        </div>
        <div class="card p-2 rounded flex-1 min-w-[120px]">
            <div class="flex justify-between items-center text-slate-400">
                <span class="font-bold text-white">ETHUSDT</span>
            </div>
            <div class="flex justify-between items-center mt-1">
                <span>$3,540.49</span>
                <span class="text-emerald-400">+1.78%</span>
            </div>
        </div>
    </div>

    <!-- MARKET SELECTOR -->
    <div class="flex gap-2 p-3 overflow-x-auto text-sm no-scrollbar">
        <span class="text-slate-400 self-center mr-1">Market</span>
        <select class="bg-slate-800 text-white px-3 py-1.5 rounded border border-slate-700 text-sm focus:outline-none">
            <option>SOLUSDT</option>
            <option>BTCUSDT</option>
            <option>ETHUSDT</option>
        </select>
        <button class="bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded border border-slate-700">BTC</button>
        <button class="bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded border border-slate-700">ETH</button>
        <button class="bg-blue-600 text-white px-3 py-1.5 rounded">SOL</button>
        <button class="bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded border border-slate-700">XAU</button>
        <button class="bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded border border-slate-700">NIFTY</button>
    </div>

    <!-- MAIN TABS -->
    <div class="flex border-b border-slate-800 text-xs font-medium text-slate-400">
        <button onclick="switchTab('dashboard')" id="tab-dashboard" class="flex-1 py-3 text-center tab-active flex flex-col items-center gap-1">
            <i data-lucide="layout-grid" class="w-4 h-4"></i> Dashboard
        </button>
        <button onclick="switchTab('chart')" id="tab-chart" class="flex-1 py-3 text-center flex flex-col items-center gap-1">
            <i data-lucide="candlestick-chart" class="w-4 h-4"></i> Chart
        </button>
        <button onclick="switchTab('signals')" id="tab-signals" class="flex-1 py-3 text-center flex flex-col items-center gap-1">
            <i data-lucide="target" class="w-4 h-4"></i> Signals
        </button>
        <button onclick="switchTab('accuracy')" id="tab-accuracy" class="flex-1 py-3 text-center flex flex-col items-center gap-1">
            <i data-lucide="trophy" class="w-4 h-4"></i> Accuracy
        </button>
        <button onclick="openVipModal()" class="flex-1 py-3 text-center flex flex-col items-center gap-1 text-amber-400">
            <i data-lucide="crown" class="w-4 h-4"></i> VIP
        </button>
    </div>

    <!-- MAIN CONTENT -->
    <main class="p-3">
        <!-- DASHBOARD VIEW -->
        <div id="view-dashboard" class="space-y-3">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <!-- Signal Configuration -->
                <div class="card p-4 rounded-xl space-y-3">
                    <div class="flex items-center gap-2 font-semibold text-sm">
                        <i data-lucide="settings" class="w-4 h-4 text-blue-400"></i> Signal Configuration
                    </div>
                    <div>
                        <label class="text-xs text-slate-400">Category</label>
                        <select class="w-full bg-slate-900 border border-slate-700 text-xs p-2.5 rounded mt-1">
                            <option>Crypto Top Major</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-xs text-slate-400">Asset</label>
                        <select class="w-full bg-slate-900 border border-slate-700 text-xs p-2.5 rounded mt-1">
                            <option>BTCUSDT</option>
                            <option>SOLUSDT</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-xs text-slate-400">Timeframe</label>
                        <select class="w-full bg-slate-900 border border-slate-700 text-xs p-2.5 rounded mt-1">
                            <option>1s</option>
                            <option>1m</option>
                            <option>5m</option>
                        </select>
                    </div>
                </div>

                <!-- Risk Management -->
                <div class="card p-4 rounded-xl space-y-4">
                    <div class="flex items-center gap-2 font-semibold text-sm">
                        <i data-lucide="shield" class="w-4 h-4 text-blue-400"></i> Risk Management
                    </div>
                    <div>
                        <label class="text-xs text-slate-400">Account Balance ($)</label>
                        <div class="flex items-center bg-slate-900 border border-slate-700 rounded mt-1 overflow-hidden">
                            <input type="text" id="balance" value="10000.00" class="bg-transparent px-3 py-2 text-xs w-full focus:outline-none">
                            <button onclick="adjustBalance(-500)" class="px-3 py-2 text-slate-400 hover:bg-slate-800 border-l border-slate-700">-</button>
                            <button onclick="adjustBalance(500)" class="px-3 py-2 text-slate-400 hover:bg-slate-800 border-l border-slate-700">+</button>
                        </div>
                    </div>
                    <div>
                        <div class="flex justify-between text-xs mb-1">
                            <span class="text-slate-400">Risk Per Trade (%)</span>
                            <span id="risk-val" class="font-bold">1.00%</span>
                        </div>
                        <input type="range" min="0.1" max="5" step="0.1" value="1" oninput="document.getElementById('risk-val').innerText = this.value + '%'" class="w-full h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer">
                    </div>
                </div>
            </div>

            <!-- AI Signal Generator -->
            <div class="card p-4 rounded-xl text-center space-y-3">
                <div class="flex justify-between items-center text-xs">
                    <span class="font-bold flex items-center gap-1"><i data-lucide="sparkles" class="w-4 h-4 text-blue-400"></i> Institutional AI Signals</span>
                    <span id="vip-status-badge" class="text-amber-400 font-semibold cursor-pointer" onclick="openVipModal()">👑 VIP Status: Standard User</span>
                </div>
                
                <button onclick="generateSignal()" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 text-sm shadow-lg shadow-blue-600/30">
                    <i data-lucide="zap" class="w-4 h-4 fill-white"></i> GENERATE ACCURATE SIGNAL
                </button>

                <div class="grid grid-cols-5 gap-1 pt-2 text-center text-xs">
                    <div class="bg-slate-900/60 p-2 rounded">
                        <div class="text-slate-400 text-[10px]">Total Signals</div>
                        <div class="font-bold mt-1">128</div>
                    </div>
                    <div class="bg-slate-900/60 p-2 rounded">
                        <div class="text-slate-400 text-[10px]">Win Rate</div>
                        <div class="font-bold text-emerald-400 mt-1">87.6%</div>
                    </div>
                    <div class="bg-slate-900/60 p-2 rounded">
                        <div class="text-slate-400 text-[10px]">Accuracy</div>
                        <div class="font-bold text-amber-400 mt-1">High</div>
                    </div>
                    <div class="bg-slate-900/60 p-2 rounded">
                        <div class="text-slate-400 text-[10px]">Active Signals</div>
                        <div class="font-bold text-blue-400 mt-1">3</div>
                    </div>
                    <div class="bg-slate-900/60 p-2 rounded">
                        <div class="text-slate-400 text-[10px]">Profit Factor</div>
                        <div class="font-bold text-emerald-400 mt-1">2.45</div>
                    </div>
                </div>
            </div>

            <!-- Active Signals List -->
            <div class="card p-4 rounded-xl space-y-3">
                <div class="flex justify-between items-center">
                    <span class="font-bold text-sm">Active Signals</span>
                    <button class="text-xs bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded border border-slate-700 text-slate-300">View All</button>
                </div>

                <div class="space-y-2 text-xs">
                    <div class="bg-slate-900/80 p-2.5 rounded-lg flex items-center justify-between border border-slate-800">
                        <div class="flex items-center gap-2">
                            <span class="font-bold">SOLUSDT</span>
                            <span class="bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded text-[10px] font-bold">BUY</span>
                        </div>
                        <div class="text-slate-400">Entry: <span class="text-white">143.50</span></div>
                        <div class="text-slate-400">TP: <span class="text-white">148.20</span></div>
                        <div class="text-slate-400">SL: <span class="text-white">140.10</span></div>
                        <div class="flex items-center gap-1 text-[10px] text-slate-500">
                            <span>18:17:45</span>
                            <span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
                        </div>
                    </div>
                    <div class="bg-slate-900/80 p-2.5 rounded-lg flex items-center justify-between border border-slate-800">
                        <div class="flex items-center gap-2">
                            <span class="font-bold">BTCUSDT</span>
                            <span class="bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded text-[10px] font-bold">BUY</span>
                        </div>
                        <div class="text-slate-400">Entry: <span class="text-white">68400.00</span></div>
                        <div class="text-slate-400">TP: <span class="text-white">69250.00</span></div>
                        <div class="text-slate-400">SL: <span class="text-white">67680.00</span></div>
                        <div class="flex items-center gap-1 text-[10px] text-slate-500">
                            <span>18:16:20</span>
                            <span class="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- LIVE CHART VIEW -->
        <div id="view-chart" class="hidden card p-3 rounded-xl space-y-3">
            <div class="flex justify-between items-center text-xs">
                <span class="font-bold text-sm">SOL/USDT Real-Time Chart</span>
                <span class="text-emerald-400">● Live Streaming</span>
            </div>
            <div id="tv-chart" class="w-full h-[450px] rounded border border-slate-800 overflow-hidden"></div>
        </div>
    </main>

    <!-- VIP PRICING & PROMO CODE MODAL -->
    <div id="vip-modal" class="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50 hidden">
        <div class="card p-5 rounded-2xl w-full max-w-sm space-y-4 relative border-amber-500/30">
            <button onclick="closeVipModal()" class="absolute top-3 right-3 text-slate-400 hover:text-white">✕</button>
            
            <div class="text-center space-y-1">
                <i data-lucide="crown" class="w-10 h-10 text-amber-400 mx-auto"></i>
                <h3 class="font-bold text-lg text-white">Veer Pro VIP Access</h3>
                <p class="text-xs text-slate-400">अनलिमिटेड सिग्नल्स और प्रीमियम इंडिकेटर्स अनलॉक करें</p>
            </div>

            <div class="space-y-2 text-xs">
                <div class="border border-slate-700 bg-slate-900/50 p-3 rounded-lg flex justify-between items-center">
                    <div>
                        <div class="font-bold text-white">Monthly Plan</div>
                        <div class="text-slate-400">30 Days Unlimited Signals</div>
                    </div>
                    <div class="font-bold text-amber-400 text-base">₹999 / mo</div>
                </div>
                <div class="border border-amber-500/50 bg-amber-500/10 p-3 rounded-lg flex justify-between items-center relative">
                    <span class="absolute -top-2 right-2 bg-amber-500 text-black font-bold text-[9px] px-1.5 py-0.5 rounded">BEST VALUE</span>
                    <div>
                        <div class="font-bold text-white">Lifetime Access</div>
                        <div class="text-slate-400">One time payment</div>
                    </div>
                    <div class="font-bold text-amber-400 text-base">₹2,999</div>
                </div>
            </div>

            <!-- Promo Code System -->
            <div class="space-y-1.5 pt-2 border-t border-slate-800">
                <label class="text-xs text-slate-300 font-semibold">प्रोमो कोड (Free Access):</label>
                <div class="flex gap-2">
                    <input type="text" id="promo-input" placeholder="e.g. FREEVIP" class="bg-slate-900 border border-slate-700 text-xs px-3 py-2 rounded flex-1 uppercase focus:outline-none focus:border-amber-400">
                    <button onclick="applyPromo()" class="bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs px-3 py-2 rounded">Apply</button>
                </div>
                <p id="promo-msg" class="text-[11px] hidden"></p>
            </div>

            <button onclick="alert('Redirecting to Payment Gateway...')" class="w-full bg-amber-500 hover:bg-amber-400 text-black font-bold py-2.5 rounded-lg text-xs">
                Buy VIP Access Now
            </button>
        </div>
    </div>

    <!-- BOTTOM NAVBAR -->
    <nav class="fixed bottom-0 left-0 right-0 bg-[#0d121d] border-t border-slate-800 flex justify-around py-2 text-[10px] text-slate-400 z-40">
        <button onclick="switchTab('dashboard')" class="flex flex-col items-center gap-1 text-blue-400">
            <i data-lucide="zap" class="w-5 h-5"></i>
            <span>Terminal</span>
        </button>
        <button onclick="switchTab('chart')" class="flex flex-col items-center gap-1">
            <i data-lucide="candlestick-chart" class="w-5 h-5"></i>
            <span>Chart</span>
        </button>
        <button onclick="switchTab('signals')" class="flex flex-col items-center gap-1">
            <i data-lucide="target" class="w-5 h-5"></i>
            <span>Signals</span>
        </button>
        <button onclick="switchTab('accuracy')" class="flex flex-col items-center gap-1">
            <i data-lucide="trophy" class="w-5 h-5"></i>
            <span>Accuracy</span>
        </button>
        <button onclick="openVipModal()" class="flex flex-col items-center gap-1 text-amber-400">
            <i data-lucide="crown" class="w-5 h-5"></i>
            <span>VIP</span>
        </button>
    </nav>

    <script>
        lucide.createIcons();

        function switchTab(tabName) {
            document.getElementById('view-dashboard').classList.add('hidden');
            document.getElementById('view-chart').classList.add('hidden');

            if(tabName === 'dashboard' || tabName === 'signals' || tabName === 'accuracy') {
                document.getElementById('view-dashboard').classList.remove('hidden');
            } else if(tabName === 'chart') {
                document.getElementById('view-chart').classList.remove('hidden');
                initChart();
            }
        }

        let chartInitialized = false;
        function initChart() {
            if(chartInitialized) return;
            chartInitialized = true;

            const chartContainer = document.getElementById('tv-chart');
            const chart = LightweightCharts.createChart(chartContainer, {
                layout: { backgroundColor: '#121824', textColor: '#cbd5e1' },
                grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
                timeScale: { timeVisible: true, secondsVisible: false }
            });

            const candlestickSeries = chart.addCandlestickSeries({
                upColor: '#10b981', downColor: '#ef4444',
                borderVisible: false, wickUpColor: '#10b981', wickDownColor: '#ef4444'
            });

            candlestickSeries.setData([
                { time: '2026-08-15', open: 140.0, high: 142.5, low: 139.0, close: 141.2 },
                { time: '2026-08-16', open: 141.2, high: 144.0, low: 140.5, close: 143.8 },
                { time: '2026-08-17', open: 143.8, high: 146.0, low: 142.0, close: 142.5 },
                { time: '2026-08-18', open: 142.5, high: 147.2, low: 142.0, close: 145.06 }
            ]);
        }

        function adjustBalance(val) {
            let el = document.getElementById('balance');
            let curr = parseFloat(el.value) || 0;
            el.value = (curr + val).toFixed(2);
        }

        function openVipModal() {
            document.getElementById('vip-modal').classList.remove('hidden');
        }

        function closeVipModal() {
            document.getElementById('vip-modal').classList.add('hidden');
        }

        function applyPromo() {
            const code = document.getElementById('promo-input').value.trim().toUpperCase();
            const msg = document.getElementById('promo-msg');
            msg.classList.remove('hidden');

            if(code === 'FREEVIP' || code === 'VEERPRO100') {
                msg.className = "text-[11px] text-emerald-400 mt-1";
                msg.innerText = "✓ Promo code applied! VIP Access Unlocked for Free.";
                document.getElementById('vip-status-badge').innerText = "👑 VIP Status: Unlimited Signals (Active)";
                setTimeout(closeVipModal, 1500);
            } else {
                msg.className = "text-[11px] text-red-400 mt-1";
                msg.innerText = "❌ Invalid Promo Code. Try FREEVIP";
            }
        }

        function generateSignal() {
            alert('Generating fresh AI Signal based on current market strategy...');
        }
    </script>
</body>
</html>
"""

# 3. Render Dashboard via Streamlit Component
components.html(FULL_TERMINAL_HTML, height=900, scrolling=True)
