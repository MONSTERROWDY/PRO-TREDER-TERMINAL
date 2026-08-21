# ============================================================
# VEER PRO TERMINAL
# Multi-Market AI Trading + Paper Trading Dashboard
# Secure Persistent Session Version
# ============================================================

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go


# ============================================================
# 1. PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Veer Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 2. GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
        radial-gradient(
            circle at 50% 0%,
            #171b23 0%,
            #0b0e11 45%,
            #07090c 100%
        );
    }

    html, body, [class*="css"] {
        font-family: Inter, Arial, sans-serif;
    }

    h1,h2,h3,h4,h5,h6 {
        color:#f5f5f5 !important;
    }

    p,label,span {
        color:#c8ccd3;
    }

    .main-title {
        font-size:34px;
        font-weight:900;
        color:#fcd535;
    }

    .subtitle {
        color:#848e9c;
        font-size:13px;
    }

    .card {
        background:linear-gradient(145deg,#181c24,#101318);
        border:1px solid #2b313a;
        border-radius:14px;
        padding:18px;
        margin-bottom:12px;
    }

    .metric-title {
        color:#848e9c;
        font-size:12px;
        text-transform:uppercase;
    }

    .metric-value {
        color:#fff;
        font-size:24px;
        font-weight:800;
    }

    .green {
        color:#0ecb81 !important;
        font-weight:800;
    }

    .red {
        color:#f6465d !important;
        font-weight:800;
    }

    .yellow {
        color:#fcd535 !important;
        font-weight:800;
    }

    .signal {
        border:1px solid #fcd535;
        background:linear-gradient(145deg,#241e0b,#12100a);
        border-radius:14px;
        padding:20px;
    }

    .signal-title {
        color:#fcd535;
        font-size:22px;
        font-weight:900;
    }

    .vip {
        border:1px solid #fcd535;
        border-radius:10px;
        padding:12px;
        text-align:center;
        background:#211b08;
        color:#fcd535;
        font-weight:800;
    }

    .stButton > button {
        width:100%;
        min-height:42px;
        border-radius:8px;
        font-weight:800;
        border:1px solid #2b313a;
        background:linear-gradient(135deg,#fcd535,#f0b90b);
        color:#0b0e11;
    }

    .stButton > button:hover {
        background:#fff;
        color:#000;
    }

    input, textarea {
        background-color:#0d1014 !important;
        color:#fff !important;
    }

    [data-testid="stSidebar"] {
        background:linear-gradient(180deg,#101318,#080a0d);
        border-right:1px solid #242932;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. DATABASE
# ============================================================

DB_FILE = "users_database.db"


def db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def hash_password(password):
    salt = secrets.token_hex(16)

    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        120000,
    ).hex()

    return f"{salt}${hashed}"


def verify_password(password, stored):
    if not stored:
        return False

    # Old database compatibility
    if "$" not in stored:
        return secrets.compare_digest(
            password,
            stored
        )

    try:
        salt, expected = stored.split("$", 1)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            120000,
        ).hex()

        return secrets.compare_digest(
            actual,
            expected
        )

    except Exception:
        return False


def init_db():

    conn = db()
    cur = conn.cursor()

    # ---------------- USERS ----------------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            username TEXT,
            avatar TEXT,
            tier TEXT DEFAULT 'Free User',
            created_at TEXT
        )
        """
    )

    # ---------------- SESSIONS ----------------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
        """
    )

    # ---------------- ORDERS ----------------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            symbol TEXT,
            side TEXT,
            order_type TEXT,
            price REAL,
            quantity REAL,
            total REAL,
            status TEXT,
            created_at TEXT
        )
        """
    )

    # ---------------- PORTFOLIO ----------------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS portfolio (
            email TEXT,
            symbol TEXT,
            quantity REAL,
            avg_price REAL,
            PRIMARY KEY(email,symbol)
        )
        """
    )

    # ---------------- WATCHLIST ----------------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            email TEXT,
            symbol TEXT,
            PRIMARY KEY(email,symbol)
        )
        """
    )

    # ---------------- ALERTS ----------------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            symbol TEXT,
            condition TEXT,
            target REAL,
            active INTEGER DEFAULT 1
        )
        """
    )

    # ---------------- TRANSACTIONS ----------------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            type TEXT,
            amount REAL,
            note TEXT,
            created_at TEXT
        )
        """
    )

    # ---------------- PROMO ----------------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            duration TEXT,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        )
        """
    )

    # ---------------- ADMIN ----------------

    cur.execute(
        "SELECT email,password FROM users WHERE email=?",
        ("admin@gmail.com",)
    )

    admin = cur.fetchone()

    if not admin:

        cur.execute(
            """
            INSERT INTO users
            (email,password,name,username,avatar,tier,created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                "admin@gmail.com",
                hash_password("password123"),
                "Pro Master",
                "admin_master",
                "",
                "Premium Member (Lifetime)",
                datetime.now().isoformat(),
            )
        )

    else:

        # Upgrade old plain-text admin password
        if "$" not in admin[1]:

            cur.execute(
                """
                UPDATE users
                SET password=?
                WHERE email=?
                """,
                (
                    hash_password(admin[1]),
                    "admin@gmail.com",
                )
            )

    # ---------------- PROMO CODES ----------------

    promos = [
        ("VEER3DAYS", "3 Days"),
        ("VEERPREMIUM30", "30 Days"),
        ("VEERPREMIUM1Y", "1 Year"),
        ("VEERLIFETIME", "Lifetime"),
    ]

    for code, duration in promos:

        cur.execute(
            "SELECT code FROM promo_codes WHERE code=?",
            (code,)
        )

        if not cur.fetchone():

            cur.execute(
                """
                INSERT INTO promo_codes
                (code,duration,max_uses,used_count,active)
                VALUES(?,?,?,?,?)
                """,
                (
                    code,
                    duration,
                    1,
                    0,
                    1,
                )
            )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# 4. USER FUNCTIONS
# ============================================================

def get_user(email):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT email,password,name,username,avatar,tier
        FROM users
        WHERE email=?
        """,
        (email.strip().lower(),)
    )

    row = cur.fetchone()

    conn.close()

    return row


def register_user(
    email,
    password,
    name,
    username
):

    try:

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users
            (email,password,name,username,avatar,tier,created_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                email.lower().strip(),
                hash_password(password),
                name.strip(),
                username.strip(),
                "",
                "Free User",
                datetime.now().isoformat(),
            )
        )

        conn.commit()
        conn.close()

        return True

    except sqlite3.IntegrityError:

        return False


def update_profile(
    email,
    name,
    username,
    avatar
):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET name=?,username=?,avatar=?
        WHERE email=?
        """,
        (
            name,
            username,
            avatar,
            email,
        )
    )

    conn.commit()
    conn.close()


# ============================================================
# 5. PERSISTENT LOGIN SESSION
# ============================================================

def token_hash(token):

    return hashlib.sha256(
        token.encode()
    ).hexdigest()


def create_session(email):

    # Random secure token
    raw_token = secrets.token_urlsafe(48)

    hashed = token_hash(raw_token)

    created = datetime.utcnow()

    expires = created + timedelta(days=30)

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO sessions
        (token_hash,email,created_at,expires_at,active)
        VALUES(?,?,?,?,1)
        """,
        (
            hashed,
            email,
            created.isoformat(),
            expires.isoformat(),
        )
    )

    conn.commit()
    conn.close()

    return raw_token


def validate_session(raw_token):

    if not raw_token:
        return None

    try:

        hashed = token_hash(raw_token)

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT email,expires_at
            FROM sessions
            WHERE token_hash=?
            AND active=1
            """,
            (hashed,)
        )

        row = cur.fetchone()

        if not row:

            conn.close()
            return None

        email, expires_at = row

        if datetime.utcnow() > datetime.fromisoformat(
            expires_at
        ):

            cur.execute(
                """
                UPDATE sessions
                SET active=0
                WHERE token_hash=?
                """,
                (hashed,)
            )

            conn.commit()
            conn.close()

            return None

        conn.close()

        return email

    except Exception:

        return None


def destroy_session():

    raw_token = st.query_params.get(
        "session",
        ""
    )

    if raw_token:

        try:

            conn = db()
            cur = conn.cursor()

            cur.execute(
                """
                UPDATE sessions
                SET active=0
                WHERE token_hash=?
                """,
                (token_hash(raw_token),)
            )

            conn.commit()
            conn.close()

        except Exception:
            pass

    # Remove token from browser URL
    try:
        st.query_params.clear()
    except Exception:
        pass

    for key in [
        "logged_in",
        "current_user_email",
        "current_user_name",
        "username",
        "avatar",
        "user_tier",
    ]:

        st.session_state.pop(
            key,
            None
        )


def restore_session():

    # Already logged in in current Streamlit session
    if st.session_state.get(
        "logged_in",
        False
    ):
        return True

    # Restore from persistent secure random token
    raw_token = st.query_params.get(
        "session",
        ""
    )

    if not raw_token:

        return False

    email = validate_session(
        raw_token
    )

    if not email:

        try:
            st.query_params.clear()
        except Exception:
            pass

        return False

    user = get_user(email)

    if not user:

        return False

    st.session_state.logged_in = True
    st.session_state.current_user_email = user[0]
    st.session_state.current_user_name = user[2]
    st.session_state.username = (
        user[3] or "trader"
    )
    st.session_state.avatar = (
        user[4] or ""
    )
    st.session_state.user_tier = (
        user[5] or "Free User"
    )

    return True


# ============================================================
# 6. MARKET DATA
# ============================================================

CRYPTO_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOTUSDT",
]


def fetch_crypto():

    try:

        response = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            timeout=5
        )

        if response.status_code != 200:
            return {}

        data = response.json()

        result = {}

        wanted = set(
            CRYPTO_SYMBOLS
        )

        for item in data:

            symbol = item["symbol"]

            if symbol not in wanted:
                continue

            result[symbol] = {
                "price": float(
                    item["lastPrice"]
                ),
                "change": float(
                    item["priceChangePercent"]
                ),
                "volume": float(
                    item["quoteVolume"]
                ),
            }

        return result

    except Exception:

        return {}


def fallback_markets():

    return {

        "BTCUSDT": {
            "price": 68417.51,
            "change": 1.23,
            "volume": 0
        },

        "ETHUSDT": {
            "price": 3540.49,
            "change": -0.45,
            "volume": 0
        },

        "BNBUSDT": {
            "price": 610.25,
            "change": 0.72,
            "volume": 0
        },

        "SOLUSDT": {
            "price": 145.06,
            "change": 2.45,
            "volume": 0
        },

        "XRPUSDT": {
            "price": 0.61,
            "change": 1.20,
            "volume": 0
        },

        "ADAUSDT": {
            "price": 0.42,
            "change": 0.75,
            "volume": 0
        },

        "DOGEUSDT": {
            "price": 0.14,
            "change": 1.10,
            "volume": 0
        },

        "RELIANCE": {
            "price": 2980.50,
            "change": 0.85,
            "volume": 0
        },

        "TATASTEEL": {
            "price": 158.20,
            "change": -0.40,
            "volume": 0
        },

        "NIFTY": {
            "price": 24780.00,
            "change": 0.62,
            "volume": 0
        },

        "SENSEX": {
            "price": 81100.00,
            "change": 0.41,
            "volume": 0
        },

        "AAPL": {
            "price": 224.50,
            "change": 1.12,
            "volume": 0
        },

        "TSLA": {
            "price": 245.80,
            "change": -1.45,
            "volume": 0
        },

        "NVDA": {
            "price": 128.40,
            "change": 3.25,
            "volume": 0
        },

        "EURUSD": {
            "price": 1.0924,
            "change": 0.15,
            "volume": 0
        },

        "GBPUSD": {
            "price": 1.3012,
            "change": -0.22,
            "volume": 0
        },

        "USDJPY": {
            "price": 147.50,
            "change": 0.45,
            "volume": 0
        },

        "GOLD": {
            "price": 2512.40,
            "change": 0.50,
            "volume": 0
        },

        "SILVER": {
            "price": 29.30,
            "change": 0.71,
            "volume": 0
        },

        "CRUDEOIL": {
            "price": 76.20,
            "change": -1.10,
            "volume": 0
        },
    }


@st.cache_data(ttl=15)
def get_market_data():

    data = fallback_markets()

    live = fetch_crypto()

    if live:
        data.update(live)

    return data


MARKETS = get_market_data()


# ============================================================
# 7. CHART DATA
# ============================================================

@st.cache_data(ttl=30)
def get_chart_data(symbol):

    if symbol.endswith("USDT"):

        try:

            response = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={
                    "symbol": symbol,
                    "interval": "1h",
                    "limit": 100
                },
                timeout=5
            )

            if response.status_code == 200:

                rows = response.json()

                df = pd.DataFrame(
                    rows,
                    columns=[
                        "time",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                        "x1",
                        "x2",
                        "x3",
                        "x4",
                        "x5",
                        "x6",
                    ]
                )

                for col in [
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume"
                ]:

                    df[col] = df[
                        col
                    ].astype(float)

                df["time"] = pd.to_datetime(
                    df["time"],
                    unit="ms"
                )

                return df

        except Exception:
            pass

    base = MARKETS.get(
        symbol,
        {"price": 100}
    )["price"]

    rows = []

    price = base

    for i in range(100):

        price *= (
            1 +
            ((i % 7) - 3) / 1000
        )

        rows.append(
            {
                "time":
                    datetime.now()
                    - timedelta(
                        hours=100-i
                    ),

                "open":
                    price * .997,

                "high":
                    price * 1.006,

                "low":
                    price * .994,

                "close":
                    price,

                "volume":
                    1000 + i * 10
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 8. TECHNICAL INDICATORS
# ============================================================

def calculate_indicators(df):

    df = df.copy()

    df["EMA20"] = (
        df["close"]
        .ewm(span=20)
        .mean()
    )

    df["EMA50"] = (
        df["close"]
        .ewm(span=50)
        .mean()
    )

    delta = df["close"].diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.rolling(
        14
    ).mean()

    avg_loss = loss.rolling(
        14
    ).mean()

    rs = (
        avg_gain /
        avg_loss.replace(
            0,
            1e-9
        )
    )

    df["RSI"] = (
        100 -
        100 / (1 + rs)
    )

    ema12 = (
        df["close"]
        .ewm(span=12)
        .mean()
    )

    ema26 = (
        df["close"]
        .ewm(span=26)
        .mean()
    )

    df["MACD"] = (
        ema12 - ema26
    )

    df["Signal"] = (
        df["MACD"]
        .ewm(span=9)
        .mean()
    )

    mid = (
        df["close"]
        .rolling(20)
        .mean()
    )

    std = (
        df["close"]
        .rolling(20)
        .std()
    )

    df["BB_UPPER"] = (
        mid + 2 * std
    )

    df["BB_LOWER"] = (
        mid - 2 * std
    )

    return df


def ai_analysis(df):

    df = calculate_indicators(df)

    last = df.iloc[-1]

    score = 50
    reasons = []

    if last["EMA20"] > last["EMA50"]:

        score += 15

        reasons.append(
            "EMA20 is above EMA50."
        )

    else:

        score -= 15

        reasons.append(
            "EMA20 is below EMA50."
        )

    if last["RSI"] < 30:

        score += 10

        reasons.append(
            "RSI indicates oversold conditions."
        )

    elif last["RSI"] > 70:

        score -= 10

        reasons.append(
            "RSI indicates overbought conditions."
        )

    else:

        score += 5

        reasons.append(
            "RSI is in a neutral momentum zone."
        )

    if last["MACD"] > last["Signal"]:

        score += 10

        reasons.append(
            "MACD momentum is positive."
        )

    else:

        score -= 10

        reasons.append(
            "MACD momentum is negative."
        )

    score = max(
        0,
        min(
            100,
            int(score)
        )
    )

    if score >= 80:
        signal = "STRONG BUY"

    elif score >= 65:
        signal = "BUY"

    elif score >= 55:
        signal = "HOLD / BULLISH"

    elif score >= 45:
        signal = "HOLD"

    elif score >= 30:
        signal = "SELL"

    else:
        signal = "STRONG SELL"

    return {
        "score": score,
        "signal": signal,
        "rsi": float(last["RSI"]),
        "macd": float(last["MACD"]),
        "ema20": float(last["EMA20"]),
        "ema50": float(last["EMA50"]),
        "reasons": reasons,
    }


# ============================================================
# 9. PAPER TRADING
# ============================================================

def get_positions(email):

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT symbol,quantity,avg_price
        FROM portfolio
        WHERE email=?
        AND quantity > 0
        """,
        (email,)
    )

    rows = cur.fetchall()

    conn.close()

    return rows


def execute_paper_order(
    email,
    symbol,
    side,
    quantity,
    price
):

    quantity = float(quantity)
    price = float(price)

    if quantity <= 0:
        return False, "Quantity must be greater than zero."

    if price <= 0:
        return False, "Invalid market price."

    total = quantity * price

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT quantity,avg_price
        FROM portfolio
        WHERE email=? AND symbol=?
        """,
        (
            email,
            symbol
        )
    )

    row = cur.fetchone()

    current_qty = (
        row[0] if row else 0
    )

    current_avg = (
        row[1] if row else 0
    )

    # ---------------- BUY ----------------

    if side == "BUY":

        new_qty = (
            current_qty +
            quantity
        )

        new_avg = (
            (
                current_qty *
                current_avg
            ) +
            (
                quantity *
                price
            )
        ) / new_qty

        cur.execute(
            """
            INSERT INTO portfolio
            (email,symbol,quantity,avg_price)
            VALUES(?,?,?,?)
            ON CONFLICT(email,symbol)
            DO UPDATE SET
            quantity=excluded.quantity,
            avg_price=excluded.avg_price
            """,
            (
                email,
                symbol,
                new_qty,
                new_avg
            )
        )

    # ---------------- SELL ----------------

    elif side == "SELL":

        if current_qty < quantity:

            conn.close()

            return (
                False,
                "Insufficient paper position."
            )

        new_qty = (
            current_qty -
            quantity
        )

        if new_qty <= 0:

            cur.execute(
                """
                DELETE FROM portfolio
                WHERE email=? AND symbol=?
                """,
                (
                    email,
                    symbol
                )
            )

        else:

            cur.execute(
                """
                UPDATE portfolio
                SET quantity=?
                WHERE email=? AND symbol=?
                """,
                (
                    new_qty,
                    email,
                    symbol
                )
            )

    else:

        conn.close()

        return False, "Invalid order side."

    # Order history

    cur.execute(
        """
        INSERT INTO orders
        (email,symbol,side,order_type,price,
        quantity,total,status,created_at)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            email,
            symbol,
            side,
            "MARKET",
            price,
            quantity,
            total,
            "FILLED",
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()

    return (
        True,
        f"{side} order executed successfully."
    )


# ============================================================
# 10. AUTH SCREEN
# ============================================================

def auth_screen():

    st.markdown(
        "<br><br>",
        unsafe_allow_html=True
    )

    left, center, right = st.columns(
        [1, 1.5, 1]
    )

    with center:

        st.markdown(
            """
            <div class="card"
            style="padding:35px;
            border-top:3px solid #fcd535;">

            <div style="
            text-align:center;
            font-size:28px;
            font-weight:900;
            color:#fcd535;">
            ⚡ VEER PRO TERMINAL
            </div>

            <div style="
            text-align:center;
            color:#848e9c;
            margin-top:5px;">
            Multi-Market AI Trading Platform
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        login_tab, register_tab = st.tabs(
            [
                "🔐 Sign In",
                "📝 Create Account"
            ]
        )

        with login_tab:

            with st.form(
                "login_form"
            ):

                email = st.text_input(
                    "Email"
                )

                password = st.text_input(
                    "Password",
                    type="password"
                )

                submitted = st.form_submit_button(
                    "ACCESS TERMINAL"
                )

                if submitted:

                    user = get_user(
                        email
                    )

                    if user and verify_password(
                        password,
                        user[1]
                    ):

                        # Create persistent session
                        token = create_session(
                            user[0]
                        )

                        st.session_state.logged_in = True
                        st.session_state.current_user_email = user[0]
                        st.session_state.current_user_name = user[2]
                        st.session_state.username = (
                            user[3] or "trader"
                        )
                        st.session_state.avatar = (
                            user[4] or ""
                        )
                        st.session_state.user_tier = (
                            user[5] or "Free User"
                        )

                        # IMPORTANT:
                        # Random token, NOT email/password
                        st.query_params[
                            "session"
                        ] = token

                        st.rerun()

                    else:

                        st.error(
                            "Invalid email or password."
                        )

        with register_tab:

            with st.form(
                "register_form"
            ):

                name = st.text_input(
                    "Full Name"
                )

                username = st.text_input(
                    "Trading Username"
                )

                email = st.text_input(
                    "Email"
                )

                password = st.text_input(
                    "Password",
                    type="password"
                )

                confirm = st.text_input(
                    "Confirm Password",
                    type="password"
                )

                submitted = st.form_submit_button(
                    "CREATE ACCOUNT"
                )

                if submitted:

                    if not all([
                        name.strip(),
                        username.strip(),
                        email.strip(),
                        password
                    ]):

                        st.warning(
                            "Please fill all fields."
                        )

                    elif len(password) < 6:

                        st.warning(
                            "Password must be at least 6 characters."
                        )

                    elif password != confirm:

                        st.warning(
                            "Passwords do not match."
                        )

                    else:

                        success = register_user(
                            email,
                            password,
                            name,
                            username
                        )

                        if success:

                            st.success(
                                "Account created. Please sign in."
                            )

                        else:

                            st.error(
                                "Email is already registered."
                            )


# ============================================================
# 11. RESTORE LOGIN
# ============================================================

if not restore_session():

    auth_screen()

    st.stop()


# ============================================================
# 12. SIDEBAR
# ============================================================

with st.sidebar:

    tier = st.session_state.get(
        "user_tier",
        "Free User"
    )

    is_vip = (
        "Premium" in tier
        or "Lifetime" in tier
    )

    if is_vip:

        st.markdown(
            """
            <div class="vip">
            👑 VIP ELITE MEMBER
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        "### 👤 Profile"
    )

    st.write(
        f"**Name:** "
        f"{st.session_state.current_user_name}"
    )

    st.write(
        f"**Username:** "
        f"@{st.session_state.username}"
    )

    st.write(
        f"**Email:** "
        f"{st.session_state.current_user_email}"
    )

    st.write(
        f"**Tier:** `{tier}`"
    )

    with st.expander(
        "✏️ Edit Profile"
    ):

        with st.form(
            "profile_form"
        ):

            new_name = st.text_input(
                "Name",
                value=st.session_state.current_user_name
            )

            new_username = st.text_input(
                "Username",
                value=st.session_state.username
            )

            new_avatar = st.text_input(
                "Avatar URL",
                value=st.session_state.avatar
            )

            if st.form_submit_button(
                "Update Profile"
            ):

                update_profile(
                    st.session_state.current_user_email,
                    new_name,
                    new_username,
                    new_avatar
                )

                st.session_state.current_user_name = new_name
                st.session_state.username = new_username
                st.session_state.avatar = new_avatar

                st.success(
                    "Profile updated."
                )

                st.rerun()

    st.markdown("---")

    # Logout
    if st.button(
        "🚪 Logout"
    ):

        destroy_session()

        st.rerun()

    st.markdown("---")

    # Promo

    st.markdown(
        "### 👑 Premium"
    )

    promo = st.text_input(
        "Promo Code"
    )

    if st.button(
        "Redeem Promo"
    ):

        code = promo.strip().upper()

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT duration,max_uses,
            used_count,active
            FROM promo_codes
            WHERE code=?
            """,
            (code,)
        )

        row = cur.fetchone()

        if not row:

            st.error(
                "Invalid promo code."
            )

        elif not row[3]:

            st.error(
                "Promo code inactive."
            )

        elif row[2] >= row[1]:

            st.error(
                "Promo code already used."
            )

        else:

            duration = row[0]

            new_tier = (
                f"Premium Member ({duration})"
            )

            cur.execute(
                """
                UPDATE users
                SET tier=?
                WHERE email=?
                """,
                (
                    new_tier,
                    st.session_state.current_user_email
                )
            )

            cur.execute(
                """
                UPDATE promo_codes
                SET used_count=used_count+1
                WHERE code=?
                """,
                (code,)
            )

            conn.commit()

            st.session_state.user_tier = new_tier

            st.success(
                f"Premium activated: {duration}"
            )

            st.rerun()

        conn.close()


# ============================================================
# 13. MAIN DASHBOARD
# ============================================================

st.markdown(
    '<div class="main-title">'
    '⚡ VEER PRO TERMINAL'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Multi-Market AI Analytics • Paper Trading • '
    'Portfolio Intelligence'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# 14. TOP MARKET TICKERS
# ============================================================

top_symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "NIFTY",
    "GOLD",
    "AAPL",
]


cols = st.columns(
    len(top_symbols)
)

for col, symbol in zip(
    cols,
    top_symbols
):

    data = MARKETS.get(
        symbol
    )

    if not data:
        continue

    change = data["change"]

    with col:

        st.markdown(
            f"""
            <div class="card"
            style="text-align:center">

            <div class="metric-title">
            {symbol}
            </div>

            <div class="metric-value">
            {data['price']:,.4f}
            </div>

            <div class="
            {'green' if change >= 0 else 'red'}">

            {change:+.2f}%

            </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# 15. NAVIGATION
# ============================================================

tabs = st.tabs(
    [
        "🏠 Dashboard",
        "📊 Markets",
        "🤖 AI Signals",
        "💼 Paper Trading",
        "📈 Portfolio",
        "⭐ Watchlist",
        "🔔 Alerts",
        "⚙️ Account",
    ]
)


# ============================================================
# 16. DASHBOARD
# ============================================================

with tabs[0]:

    st.subheader(
        "Market Overview"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Crypto",
            len(CRYPTO_SYMBOLS)
        )

    with c2:
        st.metric(
            "Markets",
            len(MARKETS)
        )

    with c3:
        st.metric(
            "Account",
            "Premium"
            if is_vip
            else "Free"
        )

    with c4:
        st.metric(
            "Mode",
            "PAPER"
        )

    st.info(
        "Paper Trading Mode — no real money is being traded."
    )

    symbol = st.selectbox(
        "Select Market",
        list(MARKETS.keys())
    )

    df = get_chart_data(
        symbol
    )

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=symbol
        )
    )

    fig.update_layout(
        height=500,
        template="plotly_dark",
        margin=dict(
            l=10,
            r=10,
            t=30,
            b=10
        ),
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# 17. MARKETS
# ============================================================

with tabs[1]:

    st.subheader(
        "📊 Multi-Market Terminal"
    )

    rows = []

    for symbol, data in MARKETS.items():

        rows.append(
            {
                "Symbol": symbol,
                "Price": data["price"],
                "24h Change %": data["change"],
                "Volume": data["volume"],
            }
        )

    market_df = pd.DataFrame(
        rows
    )

    st.dataframe(
        market_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 18. AI SIGNALS
# ============================================================

with tabs[2]:

    st.subheader(
        "🤖 AI Technical Signal Engine"
    )

    signal_symbol = st.selectbox(
        "Select Asset",
        list(MARKETS.keys()),
        key="signal_symbol"
    )

    signal_df = get_chart_data(
        signal_symbol
    )

    analysis = ai_analysis(
        signal_df
    )

    st.markdown(
        f"""
        <div class="signal">

        <div class="signal-title">
        {analysis['signal']}
        </div>

        <h3>
        AI Confidence:
        {analysis['score']}%
        </h3>

        <p>
        RSI:
        {analysis['rsi']:.2f}
        </p>

        <p>
        MACD:
        {analysis['macd']:.6f}
        </p>

        <p>
        EMA20:
        {analysis['ema20']:.4f}
        </p>

        <p>
        EMA50:
        {analysis['ema50']:.4f}
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "### Signal Reasoning"
    )

    for reason in analysis[
        "reasons"
    ]:

        st.write(
            "• " + reason
        )

    st.warning(
        "AI signals are analytical indicators, "
        "not guaranteed financial advice."
    )


# ============================================================
# 19. PAPER TRADING
# ============================================================

with tabs[3]:

    st.subheader(
        "💼 Paper Trading"
    )

    col1, col2 = st.columns(2)

    with col1:

        order_symbol = st.selectbox(
            "Asset",
            list(MARKETS.keys()),
            key="order_symbol"
        )

        order_side = st.selectbox(
            "Side",
            ["BUY", "SELL"]
        )

        quantity = st.number_input(
            "Quantity",
            min_value=0.000001,
            value=1.0,
            step=1.0
        )

    with col2:

        current_price = MARKETS[
            order_symbol
        ]["price"]

        st.metric(
            "Current Price",
            f"{current_price:,.4f}"
        )

        total = (
            quantity *
            current_price
        )

        st.metric(
            "Order Value",
            f"{total:,.2f}"
        )

        if st.button(
            "🚀 Execute Paper Order"
        ):

            success, message = (
                execute_paper_order(
                    st.session_state.current_user_email,
                    order_symbol,
                    order_side,
                    quantity,
                    current_price
                )
            )

            if success:
                st.success(
                    message
                )
            else:
                st.error(
                    message
                )


# ============================================================
# 20. PORTFOLIO
# ============================================================

with tabs[4]:

    st.subheader(
        "📈 Paper Portfolio"
    )

    positions = get_positions(
        st.session_state.current_user_email
    )

    if not positions:

        st.info(
            "Your paper portfolio is empty."
        )

    else:

        portfolio_rows = []

        total_value = 0

        for symbol, qty, avg in positions:

            price = MARKETS.get(
                symbol,
                {"price": avg}
            )["price"]

            value = (
                qty *
                price
            )

            pnl = (
                price -
                avg
            ) * qty

            total_value += value

            portfolio_rows.append(
                {
                    "Symbol": symbol,
                    "Quantity": qty,
                    "Avg Price": avg,
                    "Current Price": price,
                    "Value": value,
                    "P&L": pnl,
                }
            )

        st.metric(
            "Portfolio Value",
            f"{total_value:,.2f}"
        )

        st.dataframe(
            pd.DataFrame(
                portfolio_rows
            ),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 21. WATCHLIST
# ============================================================

with tabs[5]:

    st.subheader(
        "⭐ Watchlist"
    )

    email = (
        st.session_state.current_user_email
    )

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT symbol
        FROM watchlist
        WHERE email=?
        """,
        (email,)
    )

    watch_rows = cur.fetchall()

    conn.close()

    watch_symbols = [
        r[0]
        for r in watch_rows
    ]

    selected = st.selectbox(
        "Select Asset",
        list(MARKETS.keys()),
        key="watch_select"
    )

    if st.button(
        "⭐ Add to Watchlist"
    ):

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR IGNORE INTO watchlist
            (email,symbol)
            VALUES(?,?)
            """,
            (
                email,
                selected
            )
        )

        conn.commit()
        conn.close()

        st.success(
            "Added to watchlist."
        )

        st.rerun()

    if watch_symbols:

        for symbol in watch_symbols:

            data = MARKETS.get(
                symbol
            )

            if data:

                st.write(
                    f"**{symbol}** — "
                    f"{data['price']:,.4f} — "
                    f"{data['change']:+.2f}%"
                )

    else:

        st.info(
            "No assets in watchlist."
        )


# ============================================================
# 22. ALERTS
# ============================================================

with tabs[6]:

    st.subheader(
        "🔔 Price Alerts"
    )

    email = (
        st.session_state.current_user_email
    )

    alert_symbol = st.selectbox(
        "Asset",
        list(MARKETS.keys()),
        key="alert_symbol"
    )

    condition = st.selectbox(
        "Condition",
        [
            "ABOVE",
            "BELOW"
        ]
    )

    target = st.number_input(
        "Target Price",
        min_value=0.000001,
        value=float(
            MARKETS[
                alert_symbol
            ]["price"]
        )
    )

    if st.button(
        "🔔 Create Alert"
    ):

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO alerts
            (email,symbol,condition,target,active)
            VALUES(?,?,?,?,1)
            """,
            (
                email,
                alert_symbol,
                condition,
                target
            )
        )

        conn.commit()
        conn.close()

        st.success(
            "Alert created."
        )

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT symbol,condition,target,active
        FROM alerts
        WHERE email=?
        ORDER BY id DESC
        """,
        (email,)
    )

    alerts = cur.fetchall()

    conn.close()

    if alerts:

        st.dataframe(
            pd.DataFrame(
                alerts,
                columns=[
                    "Symbol",
                    "Condition",
                    "Target",
                    "Active"
                ]
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No alerts created."
        )


# ============================================================
# 23. ACCOUNT
# ============================================================

with tabs[7]:

    st.subheader(
        "⚙️ Account"
    )

    st.write(
        f"**Name:** "
        f"{st.session_state.current_user_name}"
    )

    st.write(
        f"**Username:** "
        f"@{st.session_state.username}"
    )

    st.write(
        f"**Email:** "
        f"{st.session_state.current_user_email}"
    )

    st.write(
        f"**Membership:** "
        f"{st.session_state.user_tier}"
    )

    st.info(
        "Your login session is stored using a "
        "random session token rather than your email "
        "or password."
    )

    st.warning(
        "This terminal is currently configured for "
        "paper trading. Real-money broker execution "
        "should only be added through official broker APIs "
        "with proper authentication and risk controls."
    )


# ============================================================
# 24. ADMIN PANEL
# ============================================================

if (
    st.session_state.current_user_email
    == "admin@gmail.com"
):

    st.sidebar.markdown("---")

    st.sidebar.markdown(
        "### 🛠️ Admin Panel"
    )

    with st.sidebar.expander(
        "👥 Users"
    ):

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT email,name,username,tier
            FROM users
            ORDER BY email
            """
        )

        users = cur.fetchall()

        conn.close()

        if users:

            st.dataframe(
                pd.DataFrame(
                    users,
                    columns=[
                        "Email",
                        "Name",
                        "Username",
                        "Tier"
                    ]
                ),
                use_container_width=True,
                hide_index=True
            )

    with st.sidebar.expander(
        "👑 Grant Premium"
    ):

        if users:

            emails = [
                u[0]
                for u in users
            ]

            target = st.selectbox(
                "User",
                emails,
                key="admin_user"
            )

            tier = st.selectbox(
                "Tier",
                [
                    "Free User",
                    "Premium Member (3 Days)",
                    "Premium Member (30 Days)",
                    "Premium Member (1 Year)",
                    "Premium Member (Lifetime)",
                ],
                key="admin_tier"
            )

            if st.button(
                "🚀 Grant Access"
            ):

                conn = db()
                cur = conn.cursor()

                cur.execute(
                    """
                    UPDATE users
                    SET tier=?
                    WHERE email=?
                    """,
                    (
                        tier,
                        target
                    )
                )

                conn.commit()
                conn.close()

                st.success(
                    "Subscription updated."
                )
