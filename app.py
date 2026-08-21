import datetime as dt
import hashlib
import html
import json
import secrets
import smtplib
import sqlite3
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import pandas as pd
import requests
import streamlit as st


# ============================================================
# VEER PRO TERMINAL
# Secure Streamlit Trading Dashboard
# ============================================================

APP_NAME = "Veer Pro Terminal"

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Veer Pro Terminal | AI Trading Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SETTINGS / SECRETS
# ============================================================

def secret_value(key: str, default: str = "") -> str:
    """
    Reads Streamlit secrets safely.
    Falls back to environment variables if available.
    """
    try:
        value = st.secrets.get(key, default)
        if value is not None:
            return str(value)
    except Exception:
        pass

    try:
        import os
        return os.getenv(key, default)
    except Exception:
        return default


ADMIN_EMAIL = secret_value("ADMIN_EMAIL", "admin@gmail.com").strip().lower()
SMTP_HOST = secret_value("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(secret_value("SMTP_PORT", "587"))
SMTP_USER = secret_value("SMTP_USER", "")
SMTP_PASSWORD = secret_value("SMTP_PASSWORD", "")

UPI_ID = secret_value("UPI_ID", "")
UPI_NAME = secret_value("UPI_NAME", "VEER PRO TRADER")

DATABASE_FILE = "veer_pro_terminal.db"

OTP_EXPIRY_SECONDS = 5 * 60
OTP_RESEND_COOLDOWN = 45
OTP_MAX_ATTEMPTS = 5

FREE_SIGNALS_PER_DAY = 2


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background:
        radial-gradient(circle at 50% 0%, #151922 0%, #080a0d 55%, #050608 100%)
        !important;
}

html, body, [class*="css"] {
    font-family: Arial, sans-serif;
}

h1, h2, h3, h4, h5, h6 {
    color: #f1f3f5 !important;
}

p, label, span {
    color: #d7dce2;
}

/* SIDEBAR */

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b0e12 0%, #080a0d 100%);
    border-right: 1px solid #242a33;
}

/* CARDS */

.ticker-card {
    background: linear-gradient(145deg, #171a20, #20252d);
    border: 1px solid #2b313a;
    border-radius: 12px;
    padding: 14px;
    text-align: center;
    box-shadow: 0 8px 25px rgba(0,0,0,.35);
}

.ticker-card:hover {
    border-color: #fcd535;
}

.ticker-symbol {
    font-weight: 700;
    font-size: 12px;
    color: #8b95a5 !important;
}

.ticker-price {
    font-size: 19px;
    font-weight: 800;
    color: #ffffff !important;
    margin-top: 4px;
}

.ticker-green {
    color: #0ecb81 !important;
    font-weight: 700;
}

.ticker-red {
    color: #f6465d !important;
    font-weight: 700;
}

/* AUTH */

.auth-card {
    background: linear-gradient(145deg, #171b22, #090b0f);
    border: 1px solid #2d3440;
    border-top: 3px solid #fcd535;
    border-radius: 18px;
    padding: 38px;
    box-shadow: 0 25px 60px rgba(0,0,0,.65);
}

/* VIP */

.vip-banner {
    background:
        linear-gradient(135deg, #2d250c, #171204);
    border: 1px solid #fcd535;
    border-radius: 14px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
    box-shadow: 0 0 25px rgba(252,213,53,.15);
}

.vip-title {
    color: #fcd535 !important;
    font-size: 22px;
    font-weight: 900;
}

/* SIGNAL */

.signal-box {
    background: linear-gradient(145deg, #181b22, #111419);
    border: 1px solid #39404b;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 8px 30px rgba(0,0,0,.3);
}

/* METRIC */

.metric-box {
    background: #171a20;
    border: 1px solid #2b313a;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}

/* INPUT */

.stTextInput input,
.stNumberInput input {
    background-color: #0b0e11 !important;
    color: white !important;
    border: 1px solid #303641 !important;
}

.stTextInput input:focus,
.stNumberInput input:focus {
    border-color: #fcd535 !important;
}

/* BUTTON */

.stButton > button,
.stLinkButton > a {
    border-radius: 9px !important;
    min-height: 44px;
    font-weight: 800 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #fcd535, #f0b90b) !important;
    color: #080a0d !important;
    border: none !important;
}

.stButton > button:hover {
    background: #ffffff !important;
}

/* TABS */

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    background: #171a20;
    border-radius: 8px;
    border: 1px solid #2b313a;
    padding: 10px 18px;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #fcd535, #f0b90b) !important;
    color: #080a0d !important;
}

/* SMALL TEXT */

.small-muted {
    color: #87909e !important;
    font-size: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():
    conn = sqlite3.connect(
        DATABASE_FILE,
        timeout=20,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():

    conn = get_db_connection()

    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            avatar TEXT,
            role TEXT DEFAULT 'user',
            tier TEXT DEFAULT 'Free User',
            subscription_start TEXT,
            subscription_expiry TEXT,
            created_at TEXT NOT NULL,
            last_login TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            duration_type TEXT NOT NULL,
            duration_days INTEGER,
            is_used INTEGER DEFAULT 0,
            used_by TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS otp_sessions (
            email TEXT PRIMARY KEY,
            otp_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            attempts INTEGER DEFAULT 0
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            plan TEXT NOT NULL,
            amount REAL NOT NULL,
            utr TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'Pending',
            submitted_at TEXT NOT NULL,
            reviewed_at TEXT,
            reviewed_by TEXT
        )
        """
    )

    # Ensure admin account exists.
    now = dt.datetime.utcnow().isoformat()

    cur.execute(
        "SELECT id FROM users WHERE lower(email)=?",
        (ADMIN_EMAIL,),
    )

    admin = cur.fetchone()

    if not admin:
        cur.execute(
            """
            INSERT INTO users
            (
                email,
                name,
                username,
                avatar,
                role,
                tier,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ADMIN_EMAIL,
                "Pro Master",
                "admin_master",
                "",
                "admin",
                "Premium Member (Lifetime)",
                now,
            ),
        )
    else:
        cur.execute(
            """
            UPDATE users
            SET role='admin',
                tier='Premium Member (Lifetime)'
            WHERE lower(email)=?
            """,
            (ADMIN_EMAIL,),
        )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_user(email: str):
    email = email.strip().lower()

    conn = get_db_connection()

    row = conn.execute(
        """
        SELECT *
        FROM users
        WHERE lower(email)=?
        """,
        (email,),
    ).fetchone()

    conn.close()

    return row


def create_user(email: str, name: str):
    email = email.strip().lower()

    existing = get_user(email)

    if existing:
        return existing

    clean_name = name.strip() if name else "Trader"

    username_base = (
        "".join(
            ch.lower()
            for ch in clean_name
            if ch.isalnum()
        )
        or "trader"
    )

    username = username_base

    conn = get_db_connection()

    counter = 1

    while True:
        exists = conn.execute(
            "SELECT id FROM users WHERE lower(username)=?",
            (username.lower(),),
        ).fetchone()

        if not exists:
            break

        username = f"{username_base}{counter}"
        counter += 1

    now = dt.datetime.utcnow().isoformat()

    conn.execute(
        """
        INSERT INTO users
        (
            email,
            name,
            username,
            avatar,
            role,
            tier,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email,
            clean_name,
            username,
            "",
            "admin" if email == ADMIN_EMAIL else "user",
            "Premium Member (Lifetime)"
            if email == ADMIN_EMAIL
            else "Free User",
            now,
        ),
    )

    conn.commit()

    row = conn.execute(
        "SELECT * FROM users WHERE lower(email)=?",
        (email,),
    ).fetchone()

    conn.close()

    return row


def update_profile(email, name, username, avatar):

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE users
        SET name=?,
            username=?,
            avatar=?
        WHERE lower(email)=lower(?)
        """,
        (
            name.strip(),
            username.strip(),
            avatar.strip(),
            email.strip(),
        ),
    )

    conn.commit()
    conn.close()


# ============================================================
# SUBSCRIPTION
# ============================================================

def parse_duration_days(duration_type):

    mapping = {
        "3 Days": 3,
        "30 Days": 30,
        "1 Year": 365,
        "Lifetime Unlimited": None,
        "Lifetime": None,
    }

    return mapping.get(duration_type)


def activate_subscription(email, duration_type):

    now = dt.datetime.utcnow()

    days = parse_duration_days(duration_type)

    if days is None:
        expiry = None
    else:
        expiry = now + dt.timedelta(days=days)

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE users
        SET tier=?,
            subscription_start=?,
            subscription_expiry=?
        WHERE lower(email)=lower(?)
        """,
        (
            f"Premium Member ({duration_type})",
            now.isoformat(),
            expiry.isoformat() if expiry else None,
            email,
        ),
    )

    conn.commit()
    conn.close()


def subscription_is_active(user):

    if not user:
        return False

    tier = user["tier"] or ""

    if user["role"] == "admin":
        return True

    if "Premium" not in tier:
        return False

    if "Lifetime" in tier:
        return True

    expiry = user["subscription_expiry"]

    if not expiry:
        return False

    try:
        expiry_dt = dt.datetime.fromisoformat(expiry)

        if dt.datetime.utcnow() < expiry_dt:
            return True

    except Exception:
        return False

    # Automatically downgrade expired subscription.
    conn = get_db_connection()

    conn.execute(
        """
        UPDATE users
        SET tier='Free User',
            subscription_start=NULL,
            subscription_expiry=NULL
        WHERE id=?
        """,
        (user["id"],),
    )

    conn.commit()
    conn.close()

    return False


def get_current_user():

    email = st.session_state.get("current_user_email")

    if not email:
        return None

    user = get_user(email)

    if not user:
        return None

    subscription_is_active(user)

    return get_user(email)


# ============================================================
# OTP
# ============================================================

def hash_otp(otp: str):

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def send_email_otp(receiver_email, otp):

    if not SMTP_USER or not SMTP_PASSWORD:
        return False, (
            "SMTP is not configured. Add SMTP_USER and "
            "SMTP_PASSWORD in Streamlit Secrets."
        )

    try:

        msg = MIMEMultipart()

        msg["From"] = SMTP_USER
        msg["To"] = receiver_email
        msg["Subject"] = "Veer Pro Terminal - Login OTP"

        body = f"""
Hello Trader,

Your Veer Pro Terminal verification code is:

{otp}

This OTP will expire in 5 minutes.

Maximum verification attempts are limited.

If you did not request this code, you can safely ignore this email.

Veer Pro Terminal Security
"""

        msg.attach(
            MIMEText(body, "plain")
        )

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=20,
        ) as server:

            server.starttls()

            server.login(
                SMTP_USER,
                SMTP_PASSWORD,
            )

            server.sendmail(
                SMTP_USER,
                receiver_email,
                msg.as_string(),
            )

        return True, "OTP sent successfully."

    except Exception as exc:

        return False, f"Email delivery failed: {exc}"


def request_otp(email, name):

    email = email.strip().lower()

    now = dt.datetime.utcnow()

    conn = get_db_connection()

    previous = conn.execute(
        """
        SELECT created_at
        FROM otp_sessions
        WHERE lower(email)=?
        """,
        (email,),
    ).fetchone()

    if previous:

        try:
            previous_time = dt.datetime.fromisoformat(
                previous["created_at"]
            )

            elapsed = (
                now - previous_time
            ).total_seconds()

            if elapsed < OTP_RESEND_COOLDOWN:

                remaining = int(
                    OTP_RESEND_COOLDOWN - elapsed
                )

                conn.close()

                return False, (
                    f"Please wait {remaining} seconds "
                    "before requesting another OTP."
                )

        except Exception:
            pass

    otp = str(
        secrets.randbelow(900000) + 100000
    )

    success, message = send_email_otp(
        email,
        otp,
    )

    if not success:

        conn.close()

        return False, message

    created = now.isoformat()
    expires = (
        now
        + dt.timedelta(
            seconds=OTP_EXPIRY_SECONDS
        )
    ).isoformat()

    conn.execute(
        """
        INSERT INTO otp_sessions
        (
            email,
            otp_hash,
            created_at,
            expires_at,
            attempts
        )
        VALUES (?, ?, ?, ?, 0)
        ON CONFLICT(email)
        DO UPDATE SET
            otp_hash=excluded.otp_hash,
            created_at=excluded.created_at,
            expires_at=excluded.expires_at,
            attempts=0
        """,
        (
            email,
            hash_otp(otp),
            created,
            expires,
        ),
    )

    conn.commit()
    conn.close()

    st.session_state.otp_email = email
    st.session_state.otp_name = (
        name.strip()
        if name.strip()
        else "Trader"
    )

    return True, "OTP sent successfully."


def verify_otp(email, entered_otp):

    email = email.strip().lower()

    conn = get_db_connection()

    row = conn.execute(
        """
        SELECT *
        FROM otp_sessions
        WHERE lower(email)=?
        """,
        (email,),
    ).fetchone()

    if not row:

        conn.close()

        return False, "OTP session not found."

    now = dt.datetime.utcnow()

    try:

        expires = dt.datetime.fromisoformat(
            row["expires_at"]
        )

    except Exception:

        conn.close()

        return False, "Invalid OTP session."

    if now >= expires:

        conn.execute(
            "DELETE FROM otp_sessions WHERE lower(email)=?",
            (email,),
        )

        conn.commit()
        conn.close()

        return False, "OTP expired. Please request a new OTP."

    attempts = int(row["attempts"])

    if attempts >= OTP_MAX_ATTEMPTS:

        conn.execute(
            "DELETE FROM otp_sessions WHERE lower(email)=?",
            (email,),
        )

        conn.commit()
        conn.close()

        return False, (
            "Too many incorrect attempts. "
            "Please request a new OTP."
        )

    entered_hash = hash_otp(
        entered_otp.strip()
    )

    if not secrets.compare_digest(
        entered_hash,
        row["otp_hash"],
    ):

        conn.execute(
            """
            UPDATE otp_sessions
            SET attempts=attempts+1
            WHERE lower(email)=?
            """,
            (email,),
        )

        conn.commit()

        new_attempts = attempts + 1

        conn.close()

        remaining = max(
            0,
            OTP_MAX_ATTEMPTS - new_attempts,
        )

        return False, (
            f"Incorrect OTP. {remaining} attempts remaining."
        )

    conn.execute(
        "DELETE FROM otp_sessions WHERE lower(email)=?",
        (email,),
    )

    conn.commit()
    conn.close()

    return True, "OTP verified."


# ============================================================
# SESSION
# ============================================================

def login_user(email, name):

    user = create_user(
        email,
        name,
    )

    if not user:
        return False

    now = dt.datetime.utcnow().isoformat()

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE users
        SET last_login=?
        WHERE lower(email)=lower(?)
        """,
        (
            now,
            email,
        ),
    )

    conn.commit()
    conn.close()

    st.session_state.logged_in = True
    st.session_state.current_user_email = email

    return True


def logout_user():

    keys_to_delete = list(
        st.session_state.keys()
    )

    for key in keys_to_delete:
        del st.session_state[key]

    st.rerun()


# ============================================================
# MARKET DATA
# ============================================================

CRYPTO_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
]


@st.cache_data(ttl=5, show_spinner=False)
def fetch_crypto_prices():

    fallback = {
        "BTCUSDT": {
            "price": 0,
            "change": 0,
        },
        "ETHUSDT": {
            "price": 0,
            "change": 0,
        },
        "SOLUSDT": {
            "price": 0,
            "change": 0,
        },
        "BNBUSDT": {
            "price": 0,
            "change": 0,
        },
        "XRPUSDT": {
            "price": 0,
            "change": 0,
        },
        "ADAUSDT": {
            "price": 0,
            "change": 0,
        },
        "DOGEUSDT": {
            "price": 0,
            "change": 0,
        },
    }

    try:

        response = requests.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={
                "symbols": json.dumps(
                    CRYPTO_SYMBOLS
                )
            },
            timeout=5,
        )

        response.raise_for_status()

        data = response.json()

        result = {}

        for item in data:

            result[item["symbol"]] = {
                "price": float(
                    item["lastPrice"]
                ),
                "change": float(
                    item["priceChangePercent"]
                ),
            }

        return {
            **fallback,
            **result,
        }

    except Exception:

        return fallback


def get_market_prices():

    crypto = fetch_crypto_prices()

    return {
        **crypto,

        # Reference/demo values.
        # These are intentionally NOT labelled live.
        "EURUSD": {
            "price": 1.0924,
            "change": 0.15,
        },
        "GBPUSD": {
            "price": 1.3012,
            "change": -0.22,
        },
        "USDJPY": {
            "price": 147.50,
            "change": 0.45,
        },
        "AAPL": {
            "price": 224.50,
            "change": 1.12,
        },
        "TSLA": {
            "price": 245.80,
            "change": -1.45,
        },
        "NVDA": {
            "price": 128.40,
            "change": 3.25,
        },
        "RELIANCE": {
            "price": 2980.50,
            "change": 0.85,
        },
        "TATASTEEL": {
            "price": 158.20,
            "change": -0.40,
        },
        "NIFTY": {
            "price": 24780.00,
            "change": 0.62,
        },
        "GOLD": {
            "price": 2512.40,
            "change": 0.50,
        },
        "CRUDEOIL": {
            "price": 76.20,
            "change": -1.10,
        },
    }


# ============================================================
# CHART DATA / SIMPLE SIGNAL ENGINE
# ============================================================

@st.cache_data(ttl=15, show_spinner=False)
def fetch_binance_klines(symbol, interval, limit=150):

    try:

        response = requests.get(
            "https://api.binance.com/api/v3/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            },
            timeout=8,
        )

        response.raise_for_status()

        raw = response.json()

        rows = []

        for candle in raw:

            rows.append(
                {
                    "time": dt.datetime.fromtimestamp(
                        candle[0] / 1000
                    ),
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                }
            )

        return pd.DataFrame(rows)

    except Exception:

        return pd.DataFrame()


def calculate_rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.rolling(
        period
    ).mean()

    avg_loss = loss.rolling(
        period
    ).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        1e-9,
    )

    return 100 - (
        100 / (1 + rs)
    )


def generate_crypto_signal(symbol):

    df = fetch_binance_klines(
        symbol,
        "15m",
        150,
    )

    if df.empty or len(df) < 50:

        return {
            "direction": "NO DATA",
            "confidence": 0,
            "entry": 0,
            "sl": 0,
            "tp1": 0,
            "tp2": 0,
            "reason": "Market data unavailable.",
        }

    df["sma20"] = df["close"].rolling(20).mean()
    df["sma50"] = df["close"].rolling(50).mean()
    df["rsi"] = calculate_rsi(
        df["close"]
    )

    last = df.iloc[-1]

    price = float(last["close"])
    sma20 = float(last["sma20"])
    sma50 = float(last["sma50"])
    rsi = float(last["rsi"])

    score = 0

    reasons = []

    if price > sma20:
        score += 1
        reasons.append(
            "Price above SMA20"
        )

    if sma20 > sma50:
        score += 1
        reasons.append(
            "SMA20 above SMA50"
        )

    if rsi > 50:
        score += 1
        reasons.append(
            "RSI above 50"
        )

    if rsi < 70:
        score += 1
        reasons.append(
            "RSI not overbought"
        )

    if score >= 3:

        direction = "BUY / LONG"

        sl = price * 0.985
        tp1 = price * 1.025
        tp2 = price * 1.05

    elif score <= 1:

        direction = "SELL / SHORT"

        sl = price * 1.015
        tp1 = price * 0.975
        tp2 = price * 0.95

    else:

        direction = "WAIT"

        sl = price
        tp1 = price
        tp2 = price

    confidence = int(
        min(
            95,
            max(
                50,
                55 + score * 10,
            ),
        )
    )

    return {
        "direction": direction,
        "confidence": confidence,
        "entry": price,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rsi": rsi,
        "reason": ", ".join(reasons),
    }


# ============================================================
# AUTH SCREEN
# ============================================================

def show_auth_screen():

    st.markdown(
        "<br><br>",
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns(
        [1, 1.4, 1]
    )

    with center:

        st.markdown(
            """
            <div class="auth-card">
                <div style="text-align:center;">
                    <div style="
                        font-size:32px;
                        font-weight:900;
                        color:#fcd535;
                    ">
                        ⚡ VEER PRO
                    </div>

                    <div style="
                        font-size:20px;
                        font-weight:800;
                        color:#ffffff;
                    ">
                        TERMINAL
                    </div>

                    <div class="small-muted">
                        Secure Email OTP Authentication
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                text-align:center;
                margin:20px 0;
                color:#9aa3af;
                font-size:13px;
            ">
                Enter your email to receive a secure
                6-digit verification code.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form(
            "request_otp_form"
        ):

            email = st.text_input(
                "Email Address",
                placeholder="name@example.com",
            )

            name = st.text_input(
                "Full Name",
                placeholder="Your name",
            )

            send_btn = st.form_submit_button(
                "📩 Send Secure OTP",
                use_container_width=True,
            )

            if send_btn:

                email_clean = (
                    email.strip().lower()
                )

                if (
                    not email_clean
                    or "@" not in email_clean
                    or "." not in email_clean.split("@")[-1]
                ):

                    st.error(
                        "Please enter a valid email address."
                    )

                else:

                    ok, message = request_otp(
                        email_clean,
                        name,
                    )

                    if ok:

                        st.session_state.show_verify = True

                        st.success(
                            "OTP sent successfully. "
                            "Check your inbox."
                        )

                    else:

                        st.error(message)

        if st.session_state.get(
            "show_verify",
            False,
        ):

            st.markdown("---")

            otp_email = st.session_state.get(
                "otp_email",
                "",
            )

            st.info(
                f"OTP sent to: {otp_email}"
            )

            with st.form(
                "verify_otp_form"
            ):

                entered = st.text_input(
                    "6-Digit OTP",
                    type="password",
                    max_chars=6,
                    placeholder="••••••",
                )

                verify_btn = st.form_submit_button(
                    "🚀 Verify & Login",
                    use_container_width=True,
                )

                if verify_btn:

                    if (
                        not entered.isdigit()
                        or len(entered) != 6
                    ):

                        st.error(
                            "Enter the 6-digit OTP."
                        )

                    else:

                        ok, message = verify_otp(
                            otp_email,
                            entered,
                        )

                        if ok:

                            login_user(
                                otp_email,
                                st.session_state.get(
                                    "otp_name",
                                    "Trader",
                                ),
                            )

                            st.session_state.pop(
                                "show_verify",
                                None,
                            )

                            st.session_state.pop(
                                "otp_email",
                                None,
                            )

                            st.session_state.pop(
                                "otp_name",
                                None,
                            )

                            st.rerun()

                        else:

                            st.error(message)

        st.markdown(
            """
                <div style="
                    border-top:1px solid #2b313a;
                    margin-top:25px;
                    padding-top:15px;
                    text-align:center;
                    color:#737d8c;
                    font-size:11px;
                ">
                    Secure OTP authentication •
                    No password stored
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# INITIAL SESSION
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

if "signals_used" not in st.session_state:

    st.session_state.signals_used = 0

if "signal_date" not in st.session_state:

    st.session_state.signal_date = (
        dt.date.today().isoformat()
    )


# Reset daily free signal count.
today = dt.date.today().isoformat()

if (
    st.session_state.signal_date
    != today
):

    st.session_state.signal_date = today
    st.session_state.signals_used = 0


if not st.session_state.logged_in:

    show_auth_screen()

    st.stop()


# ============================================================
# CURRENT USER
# ============================================================

current_user = get_current_user()

if not current_user:

    logout_user()

is_admin = (
    current_user["role"] == "admin"
)

is_vip = subscription_is_active(
    current_user
)

current_tier = (
    current_user["tier"]
    if is_vip
    else "Free User"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    if is_vip:

        st.markdown(
            """
            <div style="
                background:linear-gradient(135deg,#2d250c,#151104);
                border:1px solid #fcd535;
                border-radius:10px;
                padding:12px;
                text-align:center;
                margin-bottom:15px;
            ">
                <div style="
                    color:#fcd535;
                    font-weight:900;
                ">
                    👑 VIP MEMBER
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 👤 Profile")

    avatar = (
        current_user["avatar"]
        or ""
    )

    if avatar.startswith(
        ("http://", "https://")
    ):

        try:
            st.image(
                avatar,
                width=80,
            )
        except Exception:
            pass

    st.write(
        f"**Name:** {current_user['name']}"
    )

    st.write(
        f"**Username:** @{current_user['username']}"
    )

    st.write(
        f"**Login:** {current_user['email']}"
    )

    st.write(
        f"**Tier:** `{current_tier}`"
    )

    if (
        current_user["subscription_expiry"]
        and "Lifetime" not in current_tier
    ):

        try:

            expiry = dt.datetime.fromisoformat(
                current_user["subscription_expiry"]
            )

            remaining = (
                expiry - dt.datetime.utcnow()
            )

            st.caption(
                f"Subscription remaining: "
                f"{max(0, remaining.days)} days"
            )

        except Exception:
            pass

    with st.expander(
        "✏️ Edit Profile"
    ):

        with st.form(
            "profile_form"
        ):

            new_name = st.text_input(
                "Full Name",
                value=current_user["name"],
            )

            new_username = st.text_input(
                "Username",
                value=current_user["username"],
            )

            new_avatar = st.text_input(
                "Avatar URL",
                value=current_user["avatar"] or "",
            )

            update = st.form_submit_button(
                "Update Profile",
                use_container_width=True,
            )

            if update:

                if not new_username.strip():

                    st.error(
                        "Username cannot be empty."
                    )

                else:

                    try:

                        update_profile(
                            current_user["email"],
                            new_name,
                            new_username,
                            new_avatar,
                        )

                        st.success(
                            "Profile updated."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "Username is already in use."
                        )

    st.markdown("---")

    # ========================================================
    # PROMO CODE
    # ========================================================

    st.markdown(
        "### 🎟️ Redeem Premium Code"
    )

    promo_code = st.text_input(
        "Promo Code",
        key="promo_code_input",
    )

    if st.button(
        "🎁 Redeem Code",
        use_container_width=True,
    ):

        code = (
            promo_code.strip().upper()
        )

        if not code:

            st.warning(
                "Enter a promo code."
            )

        else:

            conn = get_db_connection()

            row = conn.execute(
                """
                SELECT *
                FROM promo_codes
                WHERE code=?
                AND is_used=0
                """,
                (code,),
            ).fetchone()

            if not row:

                conn.close()

                st.error(
                    "Invalid or already-used code."
                )

            else:

                valid = True

                if row["expires_at"]:

                    try:

                        expires = dt.datetime.fromisoformat(
                            row["expires_at"]
                        )

                        if dt.datetime.utcnow() >= expires:
                            valid = False

                    except Exception:
                        valid = False

                if not valid:

                    conn.close()

                    st.error(
                        "This promo code has expired."
                    )

                else:

                    duration = row[
                        "duration_type"
                    ]

                    conn.execute(
                        """
                        UPDATE promo_codes
                        SET is_used=1,
                            used_by=?
                        WHERE code=?
                        AND is_used=0
                        """,
                        (
                            current_user["email"],
                            code,
                        ),
                    )

                    conn.commit()
                    conn.close()

                    activate_subscription(
                        current_user["email"],
                        duration,
                    )

                    st.success(
                        f"Premium activated: {duration}"
                    )

                    st.rerun()

    # ========================================================
    # ADMIN
    # ========================================================

    if is_admin:

        st.markdown("---")

        st.markdown(
            "### 🛠️ Admin Control Center"
        )

        conn = get_db_connection()

        users = conn.execute(
            """
            SELECT
                id,
                email,
                name,
                username,
                role,
                tier,
                subscription_expiry
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()

        payments = conn.execute(
            """
            SELECT *
            FROM payment_requests
            ORDER BY id DESC
            """
        ).fetchall()

        promos = conn.execute(
            """
            SELECT *
            FROM promo_codes
            ORDER BY id DESC
            """
        ).fetchall()

        conn.close()

        # ----------------------------------------------------
        # USER MANAGEMENT
        # ----------------------------------------------------

        with st.expander(
            "👥 Users"
        ):

            if users:

                users_df = pd.DataFrame(
                    [
                        dict(u)
                        for u in users
                    ]
                )

                st.dataframe(
                    users_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No users."
                )

        # ----------------------------------------------------
        # DIRECT SUBSCRIPTION
        # ----------------------------------------------------

        with st.expander(
            "⚡ Direct Subscription"
        ):

            if users:

                email_list = [
                    u["email"]
                    for u in users
                ]

                target_email = st.selectbox(
                    "Select User",
                    email_list,
                    key="admin_target_email",
                )

                duration = st.selectbox(
                    "Subscription",
                    [
                        "3 Days",
                        "30 Days",
                        "1 Year",
                        "Lifetime Unlimited",
                    ],
                    key="admin_duration",
                )

                if st.button(
                    "🚀 Grant Subscription",
                    use_container_width=True,
                ):

                    activate_subscription(
                        target_email,
                        duration,
                    )

                    st.success(
                        f"Subscription granted to "
                        f"{target_email}"
                    )

                    st.rerun()

        # ----------------------------------------------------
        # PAYMENT APPROVAL
        # ----------------------------------------------------

        with st.expander(
            "💳 Payment / UTR Requests"
        ):

            pending = [
                p
                for p in payments
                if p["status"] == "Pending"
            ]

            if not pending:

                st.info(
                    "No pending payment requests."
                )

            for payment in pending:

                st.markdown(
                    f"""
                    <div class="signal-box">
                        <b>User:</b> {html.escape(payment['email'])}<br>
                        <b>Plan:</b> {html.escape(payment['plan'])}<br>
                        <b>Amount:</b> ₹{payment['amount']:,.2f}<br>
                        <b>UTR:</b> {html.escape(payment['utr'])}<br>
                        <b>Status:</b> Pending
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                c1, c2 = st.columns(2)

                with c1:

                    if st.button(
                        "✅ Approve",
                        key=f"approve_{payment['id']}",
                        use_container_width=True,
                    ):

                        activate_subscription(
                            payment["email"],
                            payment["plan"],
                        )

                        conn = get_db_connection()

                        conn.execute(
                            """
                            UPDATE payment_requests
                            SET status='Approved',
                                reviewed_at=?,
                                reviewed_by=?
                            WHERE id=?
                            """,
                            (
                                dt.datetime.utcnow().isoformat(),
                                current_user["email"],
                                payment["id"],
                            ),
                        )

                        conn.commit()
                        conn.close()

                        st.success(
                            "Payment approved."
                        )

                        st.rerun()

                with c2:

                    if st.button(
                        "❌ Reject",
                        key=f"reject_{payment['id']}",
                        use_container_width=True,
                    ):

                        conn = get_db_connection()

                        conn.execute(
                            """
                            UPDATE payment_requests
                            SET status='Rejected',
                                reviewed_at=?,
                                reviewed_by=?
                            WHERE id=?
                            """,
                            (
                                dt.datetime.utcnow().isoformat(),
                                current_user["email"],
                                payment["id"],
                            ),
                        )

                        conn.commit()
                        conn.close()

                        st.warning(
                            "Payment rejected."
                        )

                        st.rerun()

        # ----------------------------------------------------
        # PROMO MANAGEMENT
        # ----------------------------------------------------

        with st.expander(
            "🎟️ Promo Code Generator"
        ):

            new_code = st.text_input(
                "Code",
                key="admin_new_code",
            )

            promo_duration = st.selectbox(
                "Duration",
                [
                    "3 Days",
                    "30 Days",
                    "1 Year",
                    "Lifetime Unlimited",
                ],
                key="admin_promo_duration",
            )

            if st.button(
                "➕ Create Single-Use Code",
                use_container_width=True,
            ):

                code = (
                    new_code.strip().upper()
                )

                if not code:

                    st.warning(
                        "Enter a code."
                    )

                else:

                    try:

                        conn = get_db_connection()

                        days = parse_duration_days(
                            promo_duration
                        )

                        expires = None

                        if days:

                            expires = (
                                dt.datetime.utcnow()
                                + dt.timedelta(
                                    days=days
                                )
                            ).isoformat()

                        conn.execute(
                            """
                            INSERT INTO promo_codes
                            (
                                code,
                                duration_type,
                                duration_days,
                                is_used,
                                created_at,
                                expires_at
                            )
                            VALUES (?, ?, ?, 0, ?, ?)
                            """,
                            (
                                code,
                                promo_duration,
                                days,
                                dt.datetime.utcnow().isoformat(),
                                expires,
                            ),
                        )

                        conn.commit()
                        conn.close()

                        st.success(
                            f"Created: {code}"
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "That promo code already exists."
                        )

        # ----------------------------------------------------
        # PAYMENT HISTORY
        # ----------------------------------------------------

        with st.expander(
            "📜 Payment History"
        ):

            if payments:

                payment_df = pd.DataFrame(
                    [
                        dict(p)
                        for p in payments
                    ]
                )

                st.dataframe(
                    payment_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No payment history."
                )

    st.markdown("---")

    if st.button(
        "🚪 Sign Out",
        use_container_width=True,
    ):

        logout_user()


# ============================================================
# VIP BANNER
# ============================================================

if is_vip:

    st.markdown(
        """
        <div class="vip-banner">
            <div class="vip-title">
                👑 VEER PRO VIP TERMINAL
            </div>
            <div style="
                color:#c7ccd4;
                font-size:13px;
                margin-top:6px;
            ">
                Premium features are active.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER
# ============================================================

st.title(
    "⚡ Veer Pro Terminal"
)

st.caption(
    "AI-assisted market research, risk management and charting terminal"
)


# ============================================================
# TICKERS
# ============================================================

market_prices = get_market_prices()

tc1, tc2, tc3, tc4, tc5 = st.columns(5)


def ticker_card(
    container,
    symbol,
    price,
    change,
    prefix="",
    suffix="",
    label_suffix="",
):

    cls = (
        "ticker-green"
        if change >= 0
        else "ticker-red"
    )

    sign = (
        "+"
        if change >= 0
        else ""
    )

    with container:

        st.markdown(
            f"""
            <div class="ticker-card">

                <div class="ticker-symbol">
                    {html.escape(symbol)}
                    {html.escape(label_suffix)}
                </div>

                <div class="ticker-price">
                    {prefix}{price:,.2f}{suffix}
                </div>

                <div class="{cls}">
                    {sign}{change:.2f}%
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


btc = market_prices["BTCUSDT"]

ticker_card(
    tc1,
    "BTC/USDT",
    btc["price"],
    btc["change"],
    "$",
    "",
    " • LIVE",
)

eth = market_prices["ETHUSDT"]

ticker_card(
    tc2,
    "ETH/USDT",
    eth["price"],
    eth["change"],
    "$",
    "",
    " • LIVE",
)

eur = market_prices["EURUSD"]

ticker_card(
    tc3,
    "EUR/USD",
    eur["price"],
    eur["change"],
    "",
    "",
    " • REFERENCE",
)

rel = market_prices["RELIANCE"]

ticker_card(
    tc4,
    "RELIANCE",
    rel["price"],
    rel["change"],
    "₹",
    "",
    " • REFERENCE",
)

gold = market_prices["GOLD"]

ticker_card(
    tc5,
    "GOLD",
    gold["price"],
    gold["change"],
    "$",
    "",
    " • REFERENCE",
)


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# TABS
# ============================================================

tab_dash, tab_risk, tab_chart, tab_signal, tab_plans = st.tabs(
    [
        "⚙️ Dashboard",
        "🛡️ Risk Master",
        "📊 Global Chart",
        "🎯 AI Research Signal",
        "👑 Plans",
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

with tab_dash:

    left, right = st.columns(
        2,
        gap="large",
    )

    with left:

        st.markdown(
            "### ⚙️ Market Configuration"
        )

        market_category = st.selectbox(
            "Market Category",
            [
                "FOREX",
                "CRYPTO",
                "STOCKS",
                "INDICES",
                "COMMODITIES",
                "FUTURES",
                "OPTIONS",
                "BONDS",
                "INTEREST RATES",
            ],
        )

        asset_map = {

            "FOREX": [
                "FX:EURUSD",
                "FX:GBPUSD",
                "FX:USDJPY",
                "FX:AUDUSD",
                "FX:USDCAD",
                "FX:NZDUSD",
                "FX:USDCHF",
                "FX:EURGBP",
                "FX:EURJPY",
                "FX:GBPJPY",
            ],

            "CRYPTO": [
                "BINANCE:BTCUSDT",
                "BINANCE:ETHUSDT",
                "BINANCE:SOLUSDT",
                "BINANCE:BNBUSDT",
                "BINANCE:XRPUSDT",
                "BINANCE:ADAUSDT",
                "BINANCE:DOGEUSDT",
                "BINANCE:AVAXUSDT",
                "BINANCE:DOTUSDT",
                "BINANCE:LINKUSDT",
            ],

            "STOCKS": [
                "NASDAQ:AAPL",
                "NASDAQ:TSLA",
                "NASDAQ:NVDA",
                "NASDAQ:MSFT",
                "NASDAQ:AMZN",
                "NYSE:JPM",
                "NYSE:V",
                "NSE:RELIANCE",
                "NSE:TCS",
                "NSE:INFY",
            ],

            "INDICES": [
                "SP:SPX",
                "NASDAQ:NDX",
                "DJ:DJI",
                "TVC:VIX",
                "INDEX:NIFTY",
                "BSE:SENSEX",
                "INDEX:BANKNIFTY",
            ],

            "COMMODITIES": [
                "COMEX:GC1!",
                "NYMEX:CL1!",
                "COMEX:SI1!",
                "MCX:GOLD",
                "MCX:SILVER",
                "MCX:CRUDEOIL",
            ],

            "FUTURES": [
                "CME:ES1!",
                "CME:NQ1!",
                "COMEX:GC1!",
                "NYMEX:CL1!",
            ],

            "OPTIONS": [
                "NSE:NIFTY",
                "NSE:BANKNIFTY",
                "NASDAQ:AAPL",
            ],

            "BONDS": [
                "TVC:US10Y",
                "TVC:GB10Y",
                "TVC:DE10Y",
            ],

            "INTEREST RATES": [
                "ECONOMICS:USINTR",
                "ECONOMICS:ININTR",
            ],
        }

        selected_asset = st.selectbox(
            "Select Asset",
            asset_map[market_category],
        )

        timeframe = st.selectbox(
            "Research Timeframe",
            [
                "1m",
                "5m",
                "15m",
                "1h",
                "4h",
                "1D",
            ],
            index=2,
        )

    with right:

        st.markdown(
            "### 🛡️ Capital Risk Control"
        )

        balance = st.number_input(
            "Account Balance",
            min_value=0.0,
            value=10000.0,
            step=500.0,
        )

        risk_pct = st.slider(
            "Maximum Risk Per Trade (%)",
            min_value=0.1,
            max_value=5.0,
            value=1.0,
            step=0.1,
        )

        max_risk = (
            balance
            * risk_pct
            / 100
        )

        st.markdown(
            f"""
            <div class="metric-box">

                <div class="small-muted">
                    Maximum Planned Risk
                </div>

                <div style="
                    color:#f6465d;
                    font-size:26px;
                    font-weight:900;
                ">
                    {max_risk:,.2f}
                </div>

                <div class="small-muted">
                    This is a risk budget, not a loss guarantee.
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.warning(
            "No trading system can guarantee zero losses. "
            "Use stop-losses and position sizing."
        )


# ============================================================
# RISK CALCULATOR
# ============================================================

with tab_risk:

    st.markdown(
        "### 🛡️ Advanced Risk & Position Size Calculator"
    )

    c1, c2 = st.columns(2)

    with c1:

        capital = st.number_input(
            "Trading Capital",
            min_value=0.0,
            value=50000.0,
            step=1000.0,
            key="risk_capital",
        )

        risk = st.slider(
            "Risk Per Trade (%)",
            0.1,
            5.0,
            1.0,
            0.1,
            key="risk_percent",
        )

        entry = st.number_input(
            "Entry Price",
            min_value=0.0,
            value=100.0,
            step=0.5,
            key="entry_price",
        )

        stop = st.number_input(
            "Stop Loss Price",
            min_value=0.0,
            value=97.0,
            step=0.5,
            key="stop_price",
        )

        rr = st.selectbox(
            "Risk / Reward",
            [
                "1 : 1.5",
                "1 : 2",
                "1 : 3",
                "1 : 5",
            ],
        )

    risk_amount = (
        capital
        * risk
        / 100
    )

    price_distance = abs(
        entry - stop
    )

    quantity = (
        risk_amount / price_distance
        if price_distance > 0
        else 0
    )

    rr_multiplier = float(
        rr.split(":")[1].strip()
    )

    profit_target = (
        risk_amount
        * rr_multiplier
    )

    if entry > stop:

        direction = "LONG / BUY"

        target = (
            entry
            + price_distance
            * rr_multiplier
        )

    elif entry < stop:

        direction = "SHORT / SELL"

        target = (
            entry
            - price_distance
            * rr_multiplier
        )

    else:

        direction = "INVALID SETUP"
        target = entry

    with c2:

        st.markdown(
            "### 📊 Calculation"
        )

        m1, m2 = st.columns(2)

        with m1:

            st.metric(
                "Risk Amount",
                f"{risk_amount:,.2f}",
            )

            st.metric(
                "Position Size",
                f"{quantity:,.2f}",
            )

        with m2:

            st.metric(
                "Target Price",
                f"{target:,.2f}",
            )

            st.metric(
                "Potential Profit",
                f"{profit_target:,.2f}",
            )

        st.markdown(
            f"""
            <div class="signal-box">

                <h4>
                    {direction}
                </h4>

                <p>
                    Planned risk:
                    <b>{risk:.2f}%</b>
                </p>

                <p>
                    Maximum planned loss:
                    <b>{risk_amount:,.2f}</b>
                </p>

                <p>
                    Position size:
                    <b>{quantity:,.2f}</b>
                </p>

                <p>
                    Target:
                    <b>{target:,.2f}</b>
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# TRADINGVIEW CHART
# ============================================================

with tab_chart:

    st.markdown(
        "### 📊 Global TradingView Chart"
    )

    st.info(
        "TradingView chart is used for visualization. "
        "The chart itself does not execute trades."
    )

    chart_symbol = st.text_input(
        "TradingView Symbol",
        value=selected_asset,
        key="tv_symbol",
    )

    tv_interval_map = {
        "1 Minute": "1",
        "5 Minutes": "5",
        "15 Minutes": "15",
        "1 Hour": "60",
        "4 Hours": "240",
        "Daily": "D",
    }

    chart_interval_label = st.selectbox(
        "Chart Timeframe",
        list(tv_interval_map.keys()),
        index=2,
    )

    chart_interval = tv_interval_map[
        chart_interval_label
    ]

    safe_symbol = html.escape(
        chart_symbol.strip()
    )

    chart_html = f"""
    <div
        class="tradingview-widget-container"
        style="height:600px;width:100%;"
    >

        <div
            id="tradingview_chart"
            style="height:100%;width:100%;"
        ></div>

        <script
            type="text/javascript"
            src="https://s3.tradingview.com/tv.js">
        </script>

        <script type="text/javascript">

        new TradingView.widget({{
            "width":"100%",
            "height":600,
            "symbol":"{safe_symbol}",
            "interval":"{chart_interval}",
            "timezone":"Etc/UTC",
            "theme":"dark",
            "style":"1",
            "locale":"en",
            "toolbar_bg":"#0b0e11",
            "enable_publishing":false,
            "allow_symbol_change":true,
            "container_id":"tradingview_chart"
        }});

        </script>

    </div>
    """

    st.components.v1.html(
        chart_html,
        height=620,
    )


# ============================================================
# SIGNAL ENGINE
# ============================================================

with tab_signal:

    st.markdown(
        "### 🎯 AI-Assisted Research Signal"
    )

    st.warning(
        "This is an educational/rule-based research signal. "
        "It does NOT guarantee profit, 0% loss, or any fixed win rate."
    )

    if is_vip:

        st.success(
            "👑 Premium research access active."
        )

    else:

        remaining = max(
            0,
            FREE_SIGNALS_PER_DAY
            - st.session_state.signals_used,
        )

        st.info(
            f"Free daily research signals remaining: "
            f"{remaining}/{FREE_SIGNALS_PER_DAY}"
        )

    if st.button(
        "🚀 Generate Research Signal",
        use_container_width=True,
    ):

        if (
            not is_vip
            and st.session_state.signals_used
            >= FREE_SIGNALS_PER_DAY
        ):

            st.error(
                "Daily free signal limit reached."
            )

        else:

            if not is_vip:

                st.session_state.signals_used += 1

            raw = selected_asset.split(
                " "
            )[0]

            if raw.startswith(
                "BINANCE:"
            ):

                symbol = raw.replace(
                    "BINANCE:",
                    "",
                )

                signal = generate_crypto_signal(
                    symbol
                )

                if signal["direction"] == "NO DATA":

                    st.error(
                        signal["reason"]
                    )

                else:

                    direction = signal[
                        "direction"
                    ]

                    if "BUY" in direction:

                        direction_emoji = "🟢"

                    elif "SELL" in direction:

                        direction_emoji = "🔴"

                    else:

                        direction_emoji = "🟡"

                    st.markdown(
                        f"""
                        <div class="signal-box">

                            <h3>
                                {direction_emoji}
                                {direction}
                            </h3>

                            <p>
                                <b>Asset:</b>
                                {html.escape(selected_asset)}
                            </p>

                            <p>
                                <b>Research Confidence:</b>
                                {signal['confidence']}%
                            </p>

                            <p>
                                <b>Entry Reference:</b>
                                {signal['entry']:,.4f}
                            </p>

                            <p>
                                <b>Stop Loss Reference:</b>
                                {signal['sl']:,.4f}
                            </p>

                            <p>
                                <b>TP1:</b>
                                {signal['tp1']:,.4f}
                            </p>

                            <p>
                                <b>TP2:</b>
                                {signal['tp2']:,.4f}
                            </p>

                            <p>
                                <b>RSI:</b>
                                {signal['rsi']:.2f}
                            </p>

                            <p>
                                <b>Confluence:</b>
                                {html.escape(signal['reason'])}
                            </p>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            else:

                st.info(
                    "Detailed automated signal calculations "
                    "are currently enabled for Binance crypto assets. "
                    "Use the TradingView chart for other markets."
                )


# ============================================================
# SUBSCRIPTION PLANS
# ============================================================

with tab_plans:

    st.markdown(
        "### 👑 Veer Pro Premium Plans"
    )

    st.caption(
        "Payment is submitted for manual/admin verification. "
        "Entering a UTR alone does not activate Premium."
    )

    plans = [
        (
            "⚡ 3-Day Trial",
            "₹199",
            "3 Days",
            199.0,
        ),
        (
            "🔥 Monthly Pro",
            "₹999",
            "30 Days",
            999.0,
        ),
        (
            "👑 Annual Premium",
            "₹7,999",
            "1 Year",
            7999.0,
        ),
        (
            "💎 Lifetime VIP",
            "₹50,000",
            "Lifetime Unlimited",
            50000.0,
        ),
    ]

    columns = st.columns(4)

    for index, plan in enumerate(
        plans
    ):

        title, price, duration, amount = plan

        with columns[index]:

            st.markdown(
                f"""
                <div class="metric-box">

                    <h4>
                        {title}
                    </h4>

                    <h2>
                        {price}
                    </h2>

                    <p class="small-muted">
                        {duration}
                    </p>

                    <hr>

                    <p>
                        ✔️ Premium charts
                    </p>

                    <p>
                        ✔️ Risk calculator
                    </p>

                    <p>
                        ✔️ Research signals
                    </p>

                </div>
                """,
                unsafe_allow_html=True,
            )

            if UPI_ID:

                upi_link = (
                    "upi://pay?"
                    f"pa={UPI_ID}"
                    f"&pn={UPI_NAME.replace(' ', '%20')}"
                    f"&am={amount:.2f}"
                    "&cu=INR"
                )

                st.link_button(
                    f"📲 Pay {price}",
                    upi_link,
                    use_container_width=True,
                )

            else:

                st.info(
                    "UPI not configured."
                )

    st.markdown("---")

    st.markdown(
        "### 🔐 Submit Payment Reference"
    )

    st.write(
        "Payment करने के बाद अपना UTR/transaction reference submit करें. "
        "Admin verification के बाद subscription activate होगा."
    )

    plan_names = [
        p[2]
        for p in plans
    ]

    selected_plan = st.selectbox(
        "Paid Plan",
        plan_names,
        key="payment_plan",
    )

    selected_amount = next(
        p[3]
        for p in plans
        if p[2] == selected_plan
    )

    utr = st.text_input(
        "UTR / Transaction Reference",
        max_chars=50,
        key="payment_utr",
    )

    if st.button(
        "📨 Submit Payment for Verification",
        use_container_width=True,
    ):

        clean_utr = utr.strip()

        if len(clean_utr) < 8:

            st.error(
                "Please enter a valid transaction reference."
            )

        else:

            conn = get_db_connection()

            existing = conn.execute(
                """
                SELECT id
                FROM payment_requests
                WHERE utr=?
                """,
                (clean_utr,),
            ).fetchone()

            if existing:

                conn.close()

                st.error(
                    "This UTR has already been submitted."
                )

            else:

                try:

                    conn.execute(
                        """
                        INSERT INTO payment_requests
                        (
                            email,
                            plan,
                            amount,
                            utr,
                            status,
                            submitted_at
                        )
                        VALUES (?, ?, ?, ?, 'Pending', ?)
                        """,
                        (
                            current_user["email"],
                            selected_plan,
                            selected_amount,
                            clean_utr,
                            dt.datetime.utcnow().isoformat(),
                        ),
                    )

                    conn.commit()
                    conn.close()

                    st.success(
                        "Payment submitted successfully. "
                        "Admin verification is pending."
                    )

                except sqlite3.IntegrityError:

                    conn.close()

                    st.error(
                        "This transaction reference already exists."
                    )


# ============================================================
# USER PAYMENT STATUS
# ============================================================

st.markdown("---")

conn = get_db_connection()

my_payments = conn.execute(
    """
    SELECT
        plan,
        amount,
        utr,
        status,
        submitted_at
    FROM payment_requests
    WHERE lower(email)=lower(?)
    ORDER BY id DESC
    LIMIT 10
    """,
    (current_user["email"],),
).fetchall()

conn.close()

if my_payments:

    with st.expander(
        "📜 My Payment Requests"
    ):

        st.dataframe(
            pd.DataFrame(
                [
                    dict(p)
                    for p in my_payments
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Veer Pro Terminal is an educational and research platform. "
    "Market data may be delayed or unavailable. "
    "Trading and investing involve risk. "
    "No profit, accuracy, or zero-loss guarantee is provided."
)
