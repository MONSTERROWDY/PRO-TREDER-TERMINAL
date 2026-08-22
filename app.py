# ============================================================

import os
import sqlite3
import hashlib
import secrets
import time
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
# 2. CONSTANTS
# ============================================================

DB_FILE = "users_database.db"

APP_NAME = "VEER PRO TERMINAL"

BINANCE_API = "https://api.binance.com"

SESSION_DAYS = 30

DEFAULT_DEMO_BALANCE = 100000.0

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

TIMEFRAMES = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1H": "1h",
    "4H": "4h",
    "1D": "1d",
    "1W": "1w",
}


# ============================================================
# 3. GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background:
        radial-gradient(
            circle at 50% 0%,
            #171b23 0%,
            #0b0e11 42%,
            #06080b 100%
        );
    }

    html, body, [class*="css"] {
        font-family: Inter, Arial, sans-serif;
    }

    h1,h2,h3,h4,h5,h6 {
        color: #f5f5f5 !important;
    }

    p, label, span {
        color: #c8ccd3;
    }

    [data-testid="stSidebar"] {
        background:
        linear-gradient(
            180deg,
            #101318,
            #07090c
        );

        border-right:
        1px solid #242932;
    }

    .topbar {
        background:
        linear-gradient(
            135deg,
            #181c24,
            #0d1015
        );

        border:
        1px solid #2b313a;

        border-radius:
        14px;

        padding:
        18px 22px;

        margin-bottom:
        16px;
    }

    .brand {
        color:
        #fcd535;

        font-size:
        28px;

        font-weight:
        950;

        letter-spacing:
        -0.5px;
    }

    .brand-sub {
        color:
        #848e9c;

        font-size:
        12px;
    }

    .card {
        background:
        linear-gradient(
            145deg,
            #181c24,
            #101318
        );

        border:
        1px solid #2b313a;

        border-radius:
        14px;

        padding:
        18px;

        margin-bottom:
        12px;
    }

    .metric-title {
        color:
        #848e9c;

        font-size:
        11px;

        text-transform:
        uppercase;

        letter-spacing:
        .8px;
    }

    .metric-value {
        color:
        #ffffff;

        font-size:
        23px;

        font-weight:
        900;

        margin-top:
        4px;
    }

    .green {
        color:
        #0ecb81 !important;

        font-weight:
        800;
    }

    .red {
        color:
        #f6465d !important;

        font-weight:
        800;
    }

    .yellow {
        color:
        #fcd535 !important;

        font-weight:
        800;
    }

    .muted {
        color:
        #848e9c !important;

        font-size:
        12px;
    }

    .live-badge {
        display:
        inline-block;

        padding:
        5px 10px;

        border-radius:
        20px;

        border:
        1px solid #0ecb81;

        color:
        #0ecb81;

        background:
        rgba(14,203,129,.08);

        font-size:
        11px;

        font-weight:
        900;
    }

    .real-badge {
        display:
        inline-block;

        padding:
        6px 12px;

        border-radius:
        20px;

        border:
        1px solid #f6465d;

        color:
        #f6465d;

        background:
        rgba(246,70,93,.08);

        font-size:
        11px;

        font-weight:
        900;
    }

    .demo-badge {
        display:
        inline-block;

        padding:
        6px 12px;

        border-radius:
        20px;

        border:
        1px solid #fcd535;

        color:
        #fcd535;

        background:
        rgba(252,213,53,.08);

        font-size:
        11px;

        font-weight:
        900;
    }

    .signal {
        background:
        linear-gradient(
            145deg,
            #241e0b,
            #12100a
        );

        border:
        1px solid #fcd535;

        border-radius:
        14px;

        padding:
        20px;

        box-shadow:
        0 0 25px rgba(252,213,53,.08);
    }

    .signal-title {
        color:
        #fcd535;

        font-size:
        23px;

        font-weight:
        950;
    }

    .signal-score {
        color:
        #ffffff;

        font-size:
        35px;

        font-weight:
        950;
    }

    .auth-card {
        background:
        linear-gradient(
            145deg,
            #181c24,
            #090b0e
        );

        border:
        1px solid #2b313a;

        border-top:
        3px solid #fcd535;

        border-radius:
        18px;

        padding:
        30px;

        box-shadow:
        0 20px 60px rgba(0,0,0,.7);
    }

    .stButton > button {
        width:
        100%;

        min-height:
        42px;

        border-radius:
        8px;

        font-weight:
        850;

        border:
        1px solid #2b313a;

        background:
        linear-gradient(
            135deg,
            #fcd535,
            #f0b90b
        );

        color:
        #0b0e11;
    }

    .stButton > button:hover {
        background:
        #ffffff;

        color:
        #000000;
    }

    input,
    textarea {
        background-color:
        #0d1014 !important;

        color:
        #ffffff !important;
    }

    div[data-baseweb="select"] > div {
        background-color:
        #0d1014 !important;

        border-color:
        #2b313a !important;
    }

    .warning-box {
        background:
        rgba(246,70,93,.07);

        border:
        1px solid rgba(246,70,93,.4);

        border-radius:
        10px;

        padding:
        14px;

        color:
        #f6465d;
    }

    .success-box {
        background:
        rgba(14,203,129,.07);

        border:
        1px solid rgba(14,203,129,.4);

        border-radius:
        10px;

        padding:
        14px;

        color:
        #0ecb81;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. DATABASE
# ============================================================

def get_db():
    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False,
        timeout=10,
    )


def init_db():

    conn = get_db()
    cur = conn.cursor()

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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
        """
    )

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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_accounts (
            email TEXT PRIMARY KEY,
            balance REAL DEFAULT 100000,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_positions (
            email TEXT,
            symbol TEXT,
            quantity REAL,
            avg_price REAL,
            PRIMARY KEY(email, symbol)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS demo_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            symbol TEXT,
            side TEXT,
            quantity REAL,
            price REAL,
            total REAL,
            status TEXT,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            email TEXT,
            symbol TEXT,
            PRIMARY KEY(email, symbol)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            symbol TEXT,
            target REAL,
            direction TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        SELECT email
        FROM users
        WHERE email=?
        """,
        ("admin@gmail.com",)
    )

    if not cur.fetchone():

        cur.execute(
            """
            INSERT INTO users
            (
                email,
                password,
                name,
                username,
                avatar,
                tier,
                created_at
            )
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

    promos = [
        ("VEER3DAYS", "3 Days"),
        ("VEERPREMIUM30", "30 Days"),
        ("VEERPREMIUM1Y", "1 Year"),
        ("VEERLIFETIME", "Lifetime"),
    ]

    for code, duration in promos:

        cur.execute(
            """
            SELECT code
            FROM promo_codes
            WHERE code=?
            """,
            (code,)
        )

        if not cur.fetchone():

            cur.execute(
                """
                INSERT INTO promo_codes
                (
                    code,
                    duration,
                    max_uses,
                    used_count,
                    active
                )
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


def hash_password(password):

    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        120000,
    ).hex()

    return f"{salt}${digest}"


def verify_password(password, stored):

    if not stored:
        return False

    # Compatibility with old database
    if "$" not in stored:
        return secrets.compare_digest(
            password,
            stored,
        )

    try:

        salt, expected = stored.split(
            "$",
            1,
        )

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            120000,
        ).hex()

        return secrets.compare_digest(
            actual,
            expected,
        )

    except Exception:

        return False


init_db()


# ============================================================
# 5. USER FUNCTIONS
# ============================================================

def get_user(email):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            email,
            password,
            name,
            username,
            avatar,
            tier
        FROM users
        WHERE email=?
        """,
        (
            email.strip().lower(),
        )
    )

    row = cur.fetchone()

    conn.close()

    return row


def register_user(
    email,
    password,
    name,
    username,
):

    try:

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users
            (
                email,
                password,
                name,
                username,
                avatar,
                tier,
                created_at
            )
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                email.strip().lower(),
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

    except Exception:

        return False


def update_profile(
    email,
    name,
    username,
    avatar,
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET name=?,
            username=?,
            avatar=?
        WHERE email=?
        """,
        (
            name.strip(),
            username.strip(),
            avatar.strip(),
            email,
        )
    )

    conn.commit()
    conn.close()


# ============================================================
# 6. SESSION SYSTEM
# ============================================================

def create_session(email):

    raw_token = secrets.token_urlsafe(48)

    token_hash = hashlib.sha256(
        raw_token.encode()
    ).hexdigest()

    expiry = (
        time.time()
        +
        SESSION_DAYS * 24 * 60 * 60
    )

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM sessions
        WHERE email=?
        """,
        (email,)
    )

    cur.execute(
        """
        INSERT INTO sessions
        (
            token_hash,
            email,
            expires_at
        )
        VALUES(?,?,?)
        """,
        (
            token_hash,
            email,
            expiry,
        )
    )

    conn.commit()
    conn.close()

    return raw_token


def get_session_email(token):

    if not token:
        return None

    try:

        token_hash = hashlib.sha256(
            token.encode()
        ).hexdigest()

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT email,expires_at
            FROM sessions
            WHERE token_hash=?
            """,
            (token_hash,)
        )

        row = cur.fetchone()

        if not row:

            conn.close()
            return None

        email, expiry = row

        if float(expiry) < time.time():

            cur.execute(
                """
                DELETE FROM sessions
                WHERE token_hash=?
                """,
                (token_hash,)
            )

            conn.commit()
            conn.close()

            return None

        conn.close()

        return email

    except Exception:

        return None


def destroy_session():

    token = st.query_params.get(
        "session"
    )

    if token:

        try:

            token_hash = hashlib.sha256(
                token.encode()
            ).hexdigest()

            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                """
                DELETE FROM sessions
                WHERE token_hash=?
                """,
                (token_hash,)
            )

            conn.commit()
            conn.close()

        except Exception:
            pass

    try:
        del st.query_params["session"]
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
            None,
        )


# ============================================================
# 7. RESTORE LOGIN
# ============================================================

def restore_login():

    if st.session_state.get(
        "logged_in",
        False,
    ):

        return True

    token = st.query_params.get(
        "session",
        "",
    )

    email = get_session_email(
        token
    )

    if not email:

        st.session_state.logged_in = False

        return False

    user = get_user(email)

    if not user:

        st.session_state.logged_in = False

        return False

    st.session_state.logged_in = True
    st.session_state.current_user_email = user[0]
    st.session_state.current_user_name = user[2]
    st.session_state.username = (
        user[3]
        if user[3]
        else "trader"
    )
    st.session_state.avatar = user[4] or ""
    st.session_state.user_tier = (
        user[5]
        if user[5]
        else "Free User"
    )

    return True


# ============================================================
# 8. BINANCE LIVE MARKET DATA
# ============================================================

@st.cache_data(ttl=10)
def fetch_live_market():

    try:

        response = requests.get(
            f"{BINANCE_API}/api/v3/ticker/24hr",
            timeout=5,
        )

        response.raise_for_status()

        raw = response.json()

        wanted = set(
            CRYPTO_SYMBOLS
        )

        result = {}

        for item in raw:

            symbol = item.get(
                "symbol"
            )

            if symbol not in wanted:
                continue

            try:

                result[symbol] = {
                    "price":
                        float(
                            item["lastPrice"]
                        ),

                    "change":
                        float(
                            item["priceChangePercent"]
                        ),

                    "volume":
                        float(
                            item["quoteVolume"]
                        ),

                    "high":
                        float(
                            item["highPrice"]
                        ),

                    "low":
                        float(
                            item["lowPrice"]
                        ),

                    "source":
                        "Binance Live",
                }

            except Exception:

                continue

        return result

    except Exception:

        return {}


def get_live_price(symbol):

    data = fetch_live_market()

    item = data.get(symbol)

    if not item:

        return None

    return item["price"]


# ============================================================
# 9. LIVE CANDLE DATA
# ============================================================

@st.cache_data(ttl=10)
def get_candles(
    symbol,
    interval,
    limit=200,
):

    try:

        response = requests.get(
            f"{BINANCE_API}/api/v3/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            },
            timeout=7,
        )

        response.raise_for_status()

        rows = response.json()

        if not rows:

            return pd.DataFrame()

        df = pd.DataFrame(
            rows,
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "trades",
                "buy_base",
                "buy_quote",
                "ignore",
            ],
        )

        for col in [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

        df["time"] = pd.to_datetime(
            df["time"],
            unit="ms",
        )

        return df[
            [
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        ]

    except Exception:

        return pd.DataFrame()


# ============================================================
# 10. TECHNICAL INDICATORS
# ============================================================

def calculate_indicators(df):

    if df.empty:

        return df

    df = df.copy()

    df["EMA20"] = (
        df["close"]
        .ewm(
            span=20,
            adjust=False,
        )
        .mean()
    )

    df["EMA50"] = (
        df["close"]
        .ewm(
            span=50,
            adjust=False,
        )
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
        avg_gain
        /
        avg_loss.replace(
            0,
            1e-10,
        )
    )

    df["RSI"] = (
        100
        -
        (
            100
            /
            (1 + rs)
        )
    )

    ema12 = (
        df["close"]
        .ewm(
            span=12,
            adjust=False,
        )
        .mean()
    )

    ema26 = (
        df["close"]
        .ewm(
            span=26,
            adjust=False,
        )
        .mean()
    )

    df["MACD"] = (
        ema12 - ema26
    )

    df["MACD_SIGNAL"] = (
        df["MACD"]
        .ewm(
            span=9,
            adjust=False,
        )
        .mean()
    )

    middle = (
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
        middle + 2 * std
    )

    df["BB_LOWER"] = (
        middle - 2 * std
    )

    return df


# ============================================================
# 11. LIVE SIGNAL ENGINE
# ============================================================

def generate_live_analysis(df):

    if df.empty or len(df) < 60:

        return {
            "available": False,
            "signal": "NO SIGNAL",
            "score": None,
            "entry": None,
            "stop": None,
            "target1": None,
            "target2": None,
            "rsi": None,
            "reasons": [
                "Live candle data unavailable."
            ],
        }

    df = calculate_indicators(
        df
    )

    last = df.iloc[-1]

    values = [
        last["close"],
        last["EMA20"],
        last["EMA50"],
        last["RSI"],
        last["MACD"],
        last["MACD_SIGNAL"],
    ]

    if any(
        pd.isna(v)
        for v in values
    ):

        return {
            "available": False,
            "signal": "NO SIGNAL",
            "score": None,
            "entry": None,
            "stop": None,
            "target1": None,
            "target2": None,
            "rsi": None,
            "reasons": [
                "Insufficient live data for analysis."
            ],
        }

    price = float(
        last["close"]
    )

    score = 50

    reasons = []

    bullish = 0
    bearish = 0

    if (
        last["EMA20"]
        >
        last["EMA50"]
    ):

        score += 15
        bullish += 1

        reasons.append(
            "EMA20 is above EMA50."
        )

    else:

        score -= 15
        bearish += 1

        reasons.append(
            "EMA20 is below EMA50."
        )

    if (
        last["MACD"]
        >
        last["MACD_SIGNAL"]
    ):

        score += 12
        bullish += 1

        reasons.append(
            "MACD momentum is positive."
        )

    else:

        score -= 12
        bearish += 1

        reasons.append(
            "MACD momentum is negative."
        )

    rsi = float(
        last["RSI"]
    )

    if 45 <= rsi <= 65:

        score += 5

        reasons.append(
            "RSI is in a balanced momentum zone."
        )

    elif rsi < 30:

        score += 8
        bullish += 1

        reasons.append(
            "RSI is oversold."
        )

    elif rsi > 70:

        score -= 8
        bearish += 1

        reasons.append(
            "RSI is overbought."
        )

    else:

        reasons.append(
            "RSI does not show an extreme condition."
        )

    if (
        last["close"]
        >
        last["BB_UPPER"]
    ):

        score -= 5
        bearish += 1

        reasons.append(
            "Price is above the upper Bollinger Band."
        )

    elif (
        last["close"]
        <
        last["BB_LOWER"]
    ):

        score += 5
        bullish += 1

        reasons.append(
            "Price is below the lower Bollinger Band."
        )

    score = max(
        0,
        min(
            100,
            int(score),
        ),
    )

    # Only show directional signals when
    # there is enough agreement.
    if (
        score >= 75
        and bullish >= 2
    ):

        signal = "BUY"

        entry = price

        stop = min(
            float(last["EMA50"]),
            price * 0.985,
        )

        risk = max(
            entry - stop,
            entry * 0.005,
        )

        target1 = entry + risk * 1.5
        target2 = entry + risk * 2.5

    elif (
        score <= 25
        and bearish >= 2
    ):

        signal = "SELL"

        entry = price

        stop = max(
            float(last["EMA50"]),
            price * 1.015,
        )

        risk = max(
            stop - entry,
            entry * 0.005,
        )

        target1 = entry - risk * 1.5
        target2 = entry - risk * 2.5

    else:

        signal = "NO SIGNAL"

        entry = None
        stop = None
        target1 = None
        target2 = None

    return {
        "available": True,
        "signal": signal,
        "score": score,
        "entry": entry,
        "stop": stop,
        "target1": target1,
        "target2": target2,
        "rsi": rsi,
        "reasons": reasons,
    }


# ============================================================
# 12. DEMO ACCOUNT
# ============================================================

def ensure_demo_account(email):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT email
        FROM demo_accounts
        WHERE email=?
        """,
        (email,)
    )

    if not cur.fetchone():

        cur.execute(
            """
            INSERT INTO demo_accounts
            (
                email,
                balance,
                created_at
            )
            VALUES(?,?,?)
            """,
            (
                email,
                DEFAULT_DEMO_BALANCE,
                datetime.now().isoformat(),
            )
        )

    conn.commit()
    conn.close()


def get_demo_balance(email):

    ensure_demo_account(
        email
    )

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT balance
        FROM demo_accounts
        WHERE email=?
        """,
        (email,)
    )

    row = cur.fetchone()

    conn.close()

    return (
        float(row[0])
        if row
        else DEFAULT_DEMO_BALANCE
    )


def get_demo_positions(email):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            symbol,
            quantity,
            avg_price
        FROM demo_positions
        WHERE email=?
        AND quantity > 0
        """,
        (email,)
    )

    rows = cur.fetchall()

    conn.close()

    return rows


def execute_demo_order(
    email,
    symbol,
    side,
    quantity,
    price,
):

    try:

        quantity = float(
            quantity
        )

        price = float(
            price
        )

        if (
            quantity <= 0
            or price <= 0
        ):

            return False, "Invalid order."

        total = (
            quantity
            *
            price
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT balance
            FROM demo_accounts
            WHERE email=?
            """,
            (email,)
        )

        balance_row = cur.fetchone()

        balance = (
            float(balance_row[0])
            if balance_row
            else DEFAULT_DEMO_BALANCE
        )

        cur.execute(
            """
            SELECT quantity,avg_price
            FROM demo_positions
            WHERE email=?
            AND symbol=?
            """,
            (
                email,
                symbol,
            )
        )

        position = cur.fetchone()

        current_qty = (
            float(position[0])
            if position
            else 0.0
        )

        current_avg = (
            float(position[1])
            if position
            else 0.0
        )

        if side == "BUY":

            if total > balance:

                conn.close()

                return (
                    False,
                    "Insufficient demo balance."
                )

            new_qty = (
                current_qty
                +
                quantity
            )

            new_avg = (
                (
                    current_qty
                    *
                    current_avg
                )
                +
                (
                    quantity
                    *
                    price
                )
            ) / new_qty

            cur.execute(
                """
                INSERT INTO demo_positions
                (
                    email,
                    symbol,
                    quantity,
                    avg_price
                )
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
                    new_avg,
                )
            )

            new_balance = (
                balance - total
            )

        elif side == "SELL":

            if quantity > current_qty:

                conn.close()

                return (
                    False,
                    "Insufficient demo position."
                )

            new_qty = (
                current_qty
                -
                quantity
            )

            if new_qty <= 0:

                cur.execute(
                    """
                    DELETE FROM demo_positions
                    WHERE email=?
                    AND symbol=?
                    """,
                    (
                        email,
                        symbol,
                    )
                )

            else:

                cur.execute(
                    """
                    UPDATE demo_positions
                    SET quantity=?
                    WHERE email=?
                    AND symbol=?
                    """,
                    (
                        new_qty,
                        email,
                        symbol,
                    )
                )

            new_balance = (
                balance + total
            )

        else:

            conn.close()

            return (
                False,
                "Invalid side."
            )

        cur.execute(
            """
            UPDATE demo_accounts
            SET balance=?
            WHERE email=?
            """,
            (
                new_balance,
                email,
            )
        )

        cur.execute(
            """
            INSERT INTO demo_orders
            (
                email,
                symbol,
                side,
                quantity,
                price,
                total,
                status,
                created_at
            )
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                email,
                symbol,
                side,
                quantity,
                price,
                total,
                "FILLED",
                datetime.now().isoformat(),
            )
        )

        conn.commit()
        conn.close()

        return (
            True,
            f"Demo {side} order filled."
        )

    except Exception as e:

        return (
            False,
            str(e)
        )


# ============================================================
# 13. WATCHLIST
# ============================================================

def get_watchlist(email):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT symbol
        FROM watchlist
        WHERE email=?
        ORDER BY symbol
        """,
        (email,)
    )

    rows = cur.fetchall()

    conn.close()

    return [
        row[0]
        for row in rows
    ]


def toggle_watchlist(
    email,
    symbol,
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT symbol
        FROM watchlist
        WHERE email=?
        AND symbol=?
        """,
        (
            email,
            symbol,
        )
    )

    exists = cur.fetchone()

    if exists:

        cur.execute(
            """
            DELETE FROM watchlist
            WHERE email=?
            AND symbol=?
            """,
            (
                email,
                symbol,
            )
        )

    else:

        cur.execute(
            """
            INSERT OR IGNORE INTO watchlist
            (
                email,
                symbol
            )
            VALUES(?,?)
            """,
            (
                email,
                symbol,
            )
        )

    conn.commit()
    conn.close()


# ============================================================
# 14. PRICE ALERTS
# ============================================================

def add_alert(
    email,
    symbol,
    target,
    direction,
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO alerts
        (
            email,
            symbol,
            target,
            direction,
            active,
            created_at
        )
        VALUES(?,?,?,?,?,?)
        """,
        (
            email,
            symbol,
            float(target),
            direction,
            1,
            datetime.now().isoformat(),
        )
    )

    conn.commit()
    conn.close()


def get_alerts(email):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            symbol,
            target,
            direction,
            active
        FROM alerts
        WHERE email=?
        ORDER BY id DESC
        """,
        (email,)
    )

    rows = cur.fetchall()

    conn.close()

    return rows


# ============================================================
# 15. AUTH SCREEN
# ============================================================

def show_auth():

    st.markdown(
        "<br><br>",
        unsafe_allow_html=True,
    )

    left, center, right = st.columns(
        [1, 1.5, 1]
    )

    with center:

        st.markdown(
            """
            <div class="auth-card">

            <div style="
                text-align:center;
                color:#fcd535;
                font-size:30px;
                font-weight:950;
            ">
                ⚡ VEER PRO TERMINAL
            </div>

            <div style="
                text-align:center;
                color:#848e9c;
                font-size:13px;
                margin-top:6px;
                margin-bottom:25px;
            ">
                Live Multi-Market Trading Intelligence
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        login_tab, register_tab = st.tabs(
            [
                "🔐 SIGN IN",
                "📝 CREATE ACCOUNT",
            ]
        )

        with login_tab:

            with st.form(
                "login_form"
            ):

                email = st.text_input(
                    "Email",
                    placeholder="name@example.com",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                )

                submit = st.form_submit_button(
                    "ACCESS TERMINAL"
                )

                if submit:

                    user = get_user(
                        email.strip().lower()
                    )

                    if (
                        user
                        and verify_password(
                            password,
                            user[1],
                        )
                    ):

                        token = create_session(
                            user[0]
                        )

                        st.query_params[
                            "session"
                        ] = token

                        st.session_state.logged_in = True
                        st.session_state.current_user_email = user[0]
                        st.session_state.current_user_name = user[2]
                        st.session_state.username = user[3] or "trader"
                        st.session_state.avatar = user[4] or ""
                        st.session_state.user_tier = user[5] or "Free User"

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
                    "Username"
                )

                email = st.text_input(
                    "Email"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                )

                submit = st.form_submit_button(
                    "CREATE ACCOUNT"
                )

                if submit:

                    if (
                        not name.strip()
                        or not username.strip()
                        or not email.strip()
                        or len(password) < 6
                    ):

                        st.warning(
                            "Please complete all fields. Password must be at least 6 characters."
                        )

                    elif register_user(
                        email,
                        password,
                        name,
                        username,
                    ):

                        token = create_session(
                            email.strip().lower()
                        )

                        st.query_params[
                            "session"
                        ] = token

                        user = get_user(
                            email
                        )

                        st.session_state.logged_in = True
                        st.session_state.current_user_email = user[0]
                        st.session_state.current_user_name = user[2]
                        st.session_state.username = user[3] or "trader"
                        st.session_state.avatar = ""
                        st.session_state.user_tier = user[5] or "Free User"

                        st.rerun()

                    else:

                        st.error(
                            "This email is already registered."
                        )

        st.markdown(
            """
            <div style="
                text-align:center;
                color:#848e9c;
                font-size:11px;
                margin-top:20px;
            ">
                Live market data only • No fabricated prices
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# 16. LOGIN CHECK
# ============================================================

if not restore_login():

    show_auth()

    st.stop()


# ============================================================
# 17. CURRENT USER
# ============================================================

EMAIL = st.session_state.current_user_email

ensure_demo_account(
    EMAIL
)


# ============================================================
# 18. SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="
            color:#fcd535;
            font-size:20px;
            font-weight:950;
        ">
            ⚡ VEER PRO
        </div>

        <div class="muted">
            Trading Terminal
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown(
        "### 👤 Account"
    )

    st.write(
        f"**{st.session_state.current_user_name}**"
    )

    st.caption(
        "@"
        +
        st.session_state.get(
            "username",
            "trader",
        )
    )

    st.caption(
        st.session_state.user_tier
    )

    st.divider()

    page = st.radio(
        "Terminal",
        [
            "📊 Dashboard",
            "📈 Markets",
            "⭐ Watchlist",
            "💼 Portfolio",
            "📝 Orders",
            "🔔 Alerts",
            "👤 Profile",
        ],
    )

    st.divider()

    st.markdown(
        "### 🔌 Trading Connection"
    )

    st.markdown(
        """
        <div class="warning-box">
        REAL MONEY LIVE<br><br>
        Official broker/exchange API connection required.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "No fake real-money orders are generated."
    )

    st.divider()

    if st.button(
        "🚪 Logout"
    ):

        destroy_session()

        st.rerun()


# ============================================================
# 19. HEADER
# ============================================================

st.markdown(
    """
    <div class="topbar">

        <div class="brand">
            ⚡ VEER PRO TERMINAL
        </div>

        <div class="brand-sub">
            Live Market Intelligence • TradingView-style workspace
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 20. LOAD LIVE DATA
# ============================================================

MARKET_DATA = fetch_live_market()


# ============================================================
# 21. DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    st.markdown(
        "## Market Dashboard"
    )

    if not MARKET_DATA:

        st.error(
            "LIVE MARKET DATA UNAVAILABLE"
        )

        st.info(
            "No verified market data is currently available. "
            "The terminal will not display fabricated prices."
        )

        st.stop()

    # --------------------------------------------------------
    # TICKERS
    # --------------------------------------------------------

    ticker_symbols = [
        s
        for s in [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "SOLUSDT",
            "XRPUSDT",
            "DOGEUSDT",
        ]
        if s in MARKET_DATA
    ]

    cols = st.columns(
        len(ticker_symbols)
    )

    for col, symbol in zip(
        cols,
        ticker_symbols,
    ):

        item = MARKET_DATA[
            symbol
        ]

        change = item[
            "change"
        ]

        cls = (
            "green"
            if change >= 0
            else "red"
        )

        with col:

            st.markdown(
                f"""
                <div class="card">

                    <div class="metric-title">
                        {symbol}
                    </div>

                    <div class="metric-value">
                        {item["price"]:,.6f}
                    </div>

                    <div class="{cls}">
                        {change:+.2f}%
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # MAIN WORKSPACE
    # --------------------------------------------------------

    left, right = st.columns(
        [2.2, 1]
    )

    with left:

        selected_symbol = st.selectbox(
            "Market",
            list(
                MARKET_DATA.keys()
            ),
            index=0,
        )

        timeframe = st.selectbox(
            "Timeframe",
            list(
                TIMEFRAMES.keys()
            ),
            index=4,
        )

        df = get_candles(
            selected_symbol,
            TIMEFRAMES[
                timeframe
            ],
        )

        if df.empty:

            st.warning(
                "NO LIVE CHART DATA AVAILABLE"
            )

        else:

            analysis = generate_live_analysis(
                df
            )

            chart_df = calculate_indicators(
                df
            )

            fig = go.Figure()

            fig.add_trace(
                go.Candlestick(
                    x=chart_df["time"],
                    open=chart_df["open"],
                    high=chart_df["high"],
                    low=chart_df["low"],
                    close=chart_df["close"],
                    name=selected_symbol,
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=chart_df["time"],
                    y=chart_df["EMA20"],
                    name="EMA 20",
                    line=dict(
                        width=1.3
                    ),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=chart_df["time"],
                    y=chart_df["EMA50"],
                    name="EMA 50",
                    line=dict(
                        width=1.3
                    ),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=chart_df["time"],
                    y=chart_df["BB_UPPER"],
                    name="BB Upper",
                    line=dict(
                        width=1,
                        dash="dot",
                    ),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=chart_df["time"],
                    y=chart_df["BB_LOWER"],
                    name="BB Lower",
                    line=dict(
                        width=1,
                        dash="dot",
                    ),
                )
            )

            fig.update_layout(
                height=620,
                template="plotly_dark",
                paper_bgcolor="#0b0e11",
                plot_bgcolor="#0b0e11",
                margin=dict(
                    l=10,
                    r=10,
                    t=30,
                    b=10,
                ),
                xaxis_rangeslider_visible=False,
                legend=dict(
                    orientation="h",
                    y=1.02,
                ),
                hovermode="x unified",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    with right:

        st.markdown(
            "### 🤖 LIVE ANALYSIS"
        )

        if (
            not df.empty
        ):

            analysis = generate_live_analysis(
                df
            )

            if analysis[
                "signal"
            ] == "BUY":

                st.markdown(
                    """
                    <div class="signal">
                    <div class="signal-title">
                    🟢 BUY
                    </div>
                    <div class="muted">
                    Live market analysis
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            elif analysis[
                "signal"
            ] == "SELL":

                st.markdown(
                    """
                    <div class="signal">
                    <div class="signal-title">
                    🔴 SELL
                    </div>
                    <div class="muted">
                    Live market analysis
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    """
                    <div class="signal">
                    <div class="signal-title">
                    ⚪ NO SIGNAL
                    </div>
                    <div class="muted">
                    Market conditions do not meet the signal threshold.
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if analysis[
                "available"
            ]:

                st.metric(
                    "Confidence Score",
                    f'{analysis["score"]}/100',
                )

                st.metric(
                    "RSI",
                    f'{analysis["rsi"]:.2f}',
                )

                if analysis[
                    "entry"
                ]:

                    st.markdown(
                        f"""
                        <div class="card">

                        <div class="metric-title">
                        ENTRY
                        </div>

                        <div class="metric-value">
                        {analysis["entry"]:,.6f}
                        </div>

                        <div class="metric-title">
                        STOP LOSS
                        </div>

                        <div class="metric-value">
                        {analysis["stop"]:,.6f}
                        </div>

                        <div class="metric-title">
                        TARGET 1
                        </div>

                        <div class="metric-value">
                        {analysis["target1"]:,.6f}
                        </div>

                        <div class="metric-title">
                        TARGET 2
                        </div>

                        <div class="metric-value">
                        {analysis["target2"]:,.6f}
                        </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                for reason in analysis[
                    "reasons"
                ]:

                    st.caption(
                        "• "
                        +
                        reason
                    )

            else:

                st.warning(
                    "NO SIGNAL / DATA UNAVAILABLE"
                )

        st.divider()

        st.markdown(
            "### 🔄 DATA STATUS"
        )

        st.markdown(
            """
            <span class="live-badge">
            ● LIVE MARKET DATA
            </span>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Source: Binance public market API"
        )

    # --------------------------------------------------------
    # TRADING MODE
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "## Trading"
    )

    mode = st.radio(
        "Trading Mode",
        [
            "REAL MONEY LIVE",
            "DEMO TRADE",
        ],
        horizontal=True,
    )

    if mode == "REAL MONEY LIVE":

        st.markdown(
            """
            <div class="warning-box">

            <b>REAL MONEY LIVE</b>

            <br><br>

            Broker/exchange connection is not configured.

            <br><br>

            No real order will be submitted and no fake
            fill will be shown.

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info(
            "Connect an official broker/exchange API before enabling real-money execution."
        )

    else:

        st.markdown(
            """
            <div class="success-box">

            <b>DEMO TRADE</b>

            <br>

            Orders use the current verified live market price,
            but the account balance is virtual.

            </div>
            """,
            unsafe_allow_html=True,
        )

        live_price = get_live_price(
            selected_symbol
        )

        if live_price:

            st.write(
                f"Live price: **{live_price:,.6f}**"
            )

            order_col1, order_col2 = st.columns(
                2
            )

            with order_col1:

                side = st.selectbox(
                    "Side",
                    [
                        "BUY",
                        "SELL",
                    ],
                )

                quantity = st.number_input(
                    "Quantity",
                    min_value=0.000001,
                    value=0.001,
                    step=0.001,
                    format="%.6f",
                )

            with order_col2:

                st.metric(
                    "Order Value",
                    f"{live_price * quantity:,.2f}",
                )

                if st.button(
                    f"EXECUTE DEMO {side}"
                ):

                    success, message = execute_demo_order(
                        EMAIL,
                        selected_symbol,
                        side,
                        quantity,
                        live_price,
                    )

                    if success:

                        st.success(
                            message
                        )

                        st.rerun()

                    else:

                        st.error(
                            message
                        )

        else:

            st.warning(
                "Live price unavailable. Demo order disabled."
            )


# ============================================================
# 22. MARKETS
# ============================================================

elif page == "📈 Markets":

    st.markdown(
        "## Live Markets"
    )

    if not MARKET_DATA:

        st.error(
            "NO VERIFIED MARKET DATA AVAILABLE"
        )

        st.stop()

    rows = []

    for symbol, item in MARKET_DATA.items():

        rows.append(
            {
                "Symbol": symbol,
                "Price": item["price"],
                "24H %": item["change"],
                "24H Volume": item["volume"],
                "High": item["high"],
                "Low": item["low"],
                "Source": item["source"],
            }
        )

    df_market = pd.DataFrame(
        rows
    )

    st.dataframe(
        df_market,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 23. WATCHLIST
# ============================================================

elif page == "⭐ Watchlist":

    st.markdown(
        "## ⭐ Watchlist"
    )

    watchlist = get_watchlist(
        EMAIL
    )

    if not watchlist:

        st.info(
            "Your watchlist is empty."
        )

    else:

        for symbol in watchlist:

            item = MARKET_DATA.get(
                symbol
            )

            if not item:

                st.warning(
                    f"{symbol}: LIVE DATA UNAVAILABLE"
                )

                continue

            col1, col2, col3 = st.columns(
                [2, 2, 1]
            )

            with col1:

                st.write(
                    f"**{symbol}**"
                )

            with col2:

                change = item[
                    "change"
                ]

                st.write(
                    f"{item['price']:,.6f} | "
                    f"{change:+.2f}%"
                )

            with col3:

                if st.button(
                    "Remove",
                    key=f"remove_{symbol}",
                ):

                    toggle_watchlist(
                        EMAIL,
                        symbol,
                    )

                    st.rerun()

    st.divider()

    add_symbol = st.selectbox(
        "Add market",
        list(
            MARKET_DATA.keys()
        ),
    )

    if st.button(
        "⭐ Add to Watchlist"
    ):

        toggle_watchlist(
            EMAIL,
            add_symbol,
        )

        st.rerun()


# ============================================================
# 24. PORTFOLIO
# ============================================================

elif page == "💼 Portfolio":

    st.markdown(
        "## 💼 Portfolio"

    )

    balance = get_demo_balance(
        EMAIL
    )

    positions = get_demo_positions(
        EMAIL
    )

    st.metric(
        "Demo Available Balance",
        f"{balance:,.2f}",
    )

    if not positions:

        st.info(
            "No demo positions."
        )

    else:

        rows = []

        total_value = 0

        for symbol, qty, avg in positions:

            price = get_live_price(
                symbol
            )

            if price is None:

                continue

            value = (
                qty * price
            )

            pnl = (
                price - avg
            ) * qty

            total_value += value

            rows.append(
                {
                    "Symbol": symbol,
                    "Quantity": qty,
                    "Average Price": avg,
                    "Live Price": price,
                    "Value": value,
                    "P&L": pnl,
                }
            )

        if rows:

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

            st.metric(
                "Open Position Value",
                f"{total_value:,.2f}",
            )


# ============================================================
# 25. ORDERS
# ============================================================

elif page == "📝 Orders":

    st.markdown(
        "## 📝 Demo Order History"
    )

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            symbol,
            side,
            quantity,
            price,
            total,
            status,
            created_at
        FROM demo_orders
        WHERE email=?
        ORDER BY id DESC
        LIMIT 200
        """,
        (EMAIL,)
    )

    orders = cur.fetchall()

    conn.close()

    if not orders:

        st.info(
            "No demo orders yet."
        )

    else:

        df_orders = pd.DataFrame(
            orders,
            columns=[
                "ID",
                "Symbol",
                "Side",
                "Quantity",
                "Price",
                "Total",
                "Status",
                "Time",
            ],
        )

        st.dataframe(
            df_orders,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 26. ALERTS
# ============================================================

elif page == "🔔 Alerts":

    st.markdown(
        "## 🔔 Price Alerts"
    )

    if not MARKET_DATA:

        st.warning(
            "Live market data unavailable."
        )

    else:

        symbol = st.selectbox(
            "Market",
            list(
                MARKET_DATA.keys()
            ),
        )

        current = MARKET_DATA[
            symbol
        ]["price"]

        st.write(
            f"Current live price: **{current:,.6f}**"
        )

        target = st.number_input(
            "Target Price",
            min_value=0.000001,
            value=float(current),
        )

        direction = st.selectbox(
            "Condition",
            [
                "ABOVE",
                "BELOW",
            ],
        )

        if st.button(
            "🔔 Create Alert"
        ):

            add_alert(
                EMAIL,
                symbol,
                target,
                direction,
            )

            st.success(
                "Alert created."
            )

    st.divider()

    alerts = get_alerts(
        EMAIL
    )

    if alerts:

        alert_df = pd.DataFrame(
            alerts,
            columns=[
                "ID",
                "Symbol",
                "Target",
                "Condition",
                "Active",
            ],
        )

        st.dataframe(
            alert_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No alerts."
        )


# ============================================================
# 27. PROFILE
# ============================================================

elif page == "👤 Profile":

    st.markdown(
        "## 👤 Profile"
    )

    with st.form(
        "profile_form"
    ):

        name = st.text_input(
            "Full Name",
            value=st.session_state.current_user_name,
        )

        username = st.text_input(
            "Username",
            value=st.session_state.get(
                "username",
                "trader",
            ),
        )

        avatar = st.text_input(
            "Avatar URL",
            value=st.session_state.get(
                "avatar",
                "",
            ),
        )

        if st.form_submit_button(
            "SAVE PROFILE"
        ):

            update_profile(
                EMAIL,
                name,
                username,
                avatar,
            )

            st.session_state.current_user_name = name
            st.session_state.username = username
            st.session_state.avatar = avatar

            st.success(
                "Profile updated."
            )

    st.divider()

    st.markdown(
        "### Account"
    )

    st.write(
        f"Email: **{EMAIL}**"
    )

    st.write(
        f"Tier: **{st.session_state.user_tier}**"
    )

    st.write(
        "Session persistence: **Enabled**"
    )


# ============================================================
# 28. ADMIN PANEL
# ============================================================

if EMAIL == "admin@gmail.com":

    st.sidebar.divider()

    with st.sidebar.expander(
        "🛠️ ADMIN"
    ):

        st.caption(
            "Admin account"
        )

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                email,
                name,
                username,
                tier,
                created_at
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
                        "Tier",
                        "Created",
                    ],
                ),
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# 29. AUTO REFRESH BUTTON
# ============================================================

st.sidebar.divider()

if st.sidebar.button(
    "🔄 Refresh Live Market"
):

    fetch_live_market.clear()
    get_candles.clear()

    st.rerun()


# ============================================================
# END
# ============================================================
