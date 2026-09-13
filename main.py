import os
import json
import hmac
import hashlib
import urllib.parse
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import asyncpg
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_URL = (os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not PUBLIC_URL:
    raise RuntimeError("PUBLIC_URL / RENDER_EXTERNAL_URL is not set")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

WEBHOOK_PATH = "/telegram/webhook"
WEBHOOK_URL = PUBLIC_URL + WEBHOOK_PATH

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_pool = None
app = FastAPI()


# ============================================================
# TEST DATA
# ============================================================
# Correct answers stay on the server.
# The Mini App receives only question text + options.
# This prevents the browser from receiving the answer key.

QUESTIONS = [
    {
        "id": 1,
        "q": "Ketma-ketlikni davom ettir: 2, 4, 8, 16, ?",
        "a": ["24", "30", "32", "36"],
        "correct": 2,
    },
    {
        "id": 2,
        "q": "Agar barcha ZAKOlar aqlli bo'lsa, Ali ZAKO bo'lsa, Ali qanday?",
        "a": ["Tez", "Aqlli", "Kuchli", "Bilmaymiz"],
        "correct": 1,
    },
    {
        "id": 3,
        "q": "3 ta mashina 3 daqiqada 3 ta detal ishlab chiqaradi. 1 mashina 3 daqiqada nechta detal ishlab chiqaradi?",
        "a": ["1", "2", "3", "9"],
        "correct": 0,
    },
    {
        "id": 4,
        "q": "Ketma-ketlik: 1, 1, 2, 3, 5, 8, ?",
        "a": ["11", "12", "13", "15"],
        "correct": 2,
    },
    {
        "id": 5,
        "q": "5 ta sham yonib turibdi. 2 tasi o'chirildi. Nechta sham qoldi?",
        "a": ["2", "3", "5", "0"],
        "correct": 2,
    },
    {
        "id": 6,
        "q": "Agar kecha yakshanba bo'lgan bo'lsa, ertadan keyingi kun qaysi kun?",
        "a": ["Seshanba", "Chorshanba", "Payshanba", "Juma"],
        "correct": 1,
    },
    {
        "id": 7,
        "q": "10 ning yarmi + 10 ning yarmi nechaga teng?",
        "a": ["5", "10", "15", "20"],
        "correct": 1,
    },
    {
        "id": 8,
        "q": "Qaysi biri boshqalardan farq qiladi?",
        "a": ["Olma", "Nok", "Sabzi", "Shaftoli"],
        "correct": 2,
    },
    {
        "id": 9,
        "q": "Bir odam 5-qavatdan lift bilan tushdi. Keyin 3-qavatga piyoda chiqdi. Nega?",
        "a": [
            "Lift buzilgan",
            "Sport qilmoqchi",
            "Bo'yi lift tugmasiga yetmaydi",
            "Bilmaymiz",
        ],
        "correct": 2,
    },
    {
        "id": 10,
        "q": "Agar 2 + 3 = 10, 3 + 4 = 21 bo'lsa, 4 + 5 = ?",
        "a": ["30", "36", "40", "45"],
        "correct": 1,
    },
]

QUESTION_BY_ID = {item["id"]: item for item in QUESTIONS}

# Secret used only to sign a short-lived test token.
# It is derived from the bot token, so no extra Render variable is needed.
TOKEN_SECRET = hmac.new(
    b"ZAKO_TEST_TOKEN",
    BOT_TOKEN.encode("utf-8"),
    hashlib.sha256,
).digest()


# ============================================================
# TELEGRAM INIT DATA
# ============================================================

def validate_telegram_init_data(init_data: str):
    """Validate Telegram Mini App initData and return the user object."""

    if not init_data:
        return None

    try:
        parsed = urllib.parse.parse_qs(
            init_data,
            keep_blank_values=True,
            strict_parsing=True,
        )

        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None

        data_check_items = []

        for key in sorted(parsed):
            if key == "hash":
                continue

            values = parsed[key]
            if values:
                data_check_items.append(f"{key}={values[0]}")

        data_check_string = "\n".join(data_check_items)

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        user_json = parsed.get("user", [None])[0]
        if not user_json:
            return None

        user = json.loads(user_json)

        if not isinstance(user, dict) or not user.get("id"):
            return None

        return user

    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def telegram_user_from_request(request: Request, body: dict | None = None):
    init_data = request.headers.get("X-Telegram-Init-Data")

    if not init_data and body:
        init_data = body.get("initData", "")

    return validate_telegram_init_data(init_data or "")


# ============================================================
# TEST TOKEN
# ============================================================

def create_test_token(user_id: int, question_ids: list[int]):
    payload = {
        "uid": user_id,
        "q": question_ids,
        "exp": int(datetime.now(timezone.utc).timestamp()) + 30 * 60,
        "nonce": secrets.token_hex(8),
    }

    encoded = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    payload_b64 = urllib.parse.quote_from_bytes(encoded)

    signature = hmac.new(
        TOKEN_SECRET,
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def verify_test_token(token: str, user_id: int):
    try:
        payload_b64, signature = token.rsplit(".", 1)

        expected = hmac.new(
            TOKEN_SECRET,
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            return None

        payload = json.loads(
            urllib.parse.unquote_to_bytes(payload_b64).decode("utf-8")
        )

        if int(payload.get("uid")) != int(user_id):
            return None

        if int(payload.get("exp", 0)) < int(
            datetime.now(timezone.utc).timestamp()
        ):
            return None

        question_ids = payload.get("q")

        if not isinstance(question_ids, list):
            return None

        if len(question_ids) != len(QUESTIONS):
            return None

        if set(question_ids) != set(QUESTION_BY_ID):
            return None

        return payload

    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return None


# ============================================================
# DATABASE
# ============================================================

async def init_db():
    global db_pool

    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=5,
        command_timeout=10,
    )

    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                best_score INTEGER NOT NULL DEFAULT 0,
                tests_taken INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
                test_type TEXT NOT NULL DEFAULT 'iq',
                score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
                correct_answers INTEGER NOT NULL CHECK (correct_answers >= 0),
                total_questions INTEGER NOT NULL CHECK (total_questions > 0),
                total_time_seconds REAL NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # Safe migration for the table created by an earlier ZAKO build.
        await conn.execute("""
            ALTER TABLE test_results
            ADD COLUMN IF NOT EXISTS test_type TEXT NOT NULL DEFAULT 'iq'
        """)

        await conn.execute("""
            ALTER TABLE test_results
            ADD COLUMN IF NOT EXISTS total_time_seconds REAL NOT NULL DEFAULT 0
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_test_results_user
            ON test_results (telegram_id, created_at DESC)
        """)

        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_best_score
            ON users (best_score DESC, tests_taken ASC, updated_at ASC)
        """)


async def close_db():
    global db_pool

    if db_pool is not None:
        await db_pool.close()
        db_pool = None


async def upsert_user(user: dict):
    telegram_id = int(user["id"])

    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (
                telegram_id,
                username,
                first_name
            )
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_id)
            DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                updated_at = NOW()
        """,
            telegram_id,
            user.get("username"),
            user.get("first_name", ""),
        )

    return telegram_id


# ============================================================
# BOT
# ============================================================

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 ZAKO'NI OCHISH",
                    web_app=WebAppInfo(url=PUBLIC_URL),
                )
            ]
        ]
    )

    await message.answer(
        "🧠 <b>ZAKO</b>\n\n"
        "O'zingni sinab ko'r.\n"
        "Qanchalik ZAKOsan?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ============================================================
# MINI APP HTML
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="theme-color" content="#090b0f">
<title>ZAKO</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>

<style>
* {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

html, body {
    margin: 0;
    padding: 0;
    background: #090b0f;
    color: #f5f7fa;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                 "Segoe UI", sans-serif;
}

body {
    min-height: 100vh;
}

button {
    font-family: inherit;
    cursor: pointer;
}

button:disabled {
    opacity: 1;
}

.app,
.test-screen,
.result-screen,
.profile-screen,
.ranking-screen {
    min-height: 100vh;
}

.app {
    padding: 26px 20px 115px;
}

.logo {
    font-size: 40px;
    font-weight: 900;
    letter-spacing: 6px;
    margin-bottom: 78px;
}

.eyebrow,
.section-title,
.small-title,
.result-label {
    color: #8994a5;
    font-weight: 800;
    letter-spacing: 3px;
}

.eyebrow {
    font-size: 15px;
    margin-bottom: 15px;
}

.hero h1 {
    font-size: 56px;
    line-height: .95;
    letter-spacing: -3px;
    margin: 0 0 24px;
}

.hero p {
    color: #9aa4b2;
    font-size: 20px;
    line-height: 1.5;
    margin: 0 0 28px;
}

.primary {
    width: 100%;
    border: 0;
    border-radius: 25px;
    background: #fff;
    color: #090b0f;
    padding: 22px 18px;
    font-size: 19px;
    font-weight: 900;
}

.score-card,
.test-card,
.duel,
.profile-card,
.rank-row {
    background: #11151a;
    border: 1px solid #252b34;
}

.score-card {
    margin-top: 28px;
    padding: 27px;
    border-radius: 25px;
}

.small-title {
    font-size: 14px;
}

.score {
    font-size: 58px;
    font-weight: 900;
    margin: 20px 0 8px;
}

.muted {
    color: #758092;
}

.section {
    margin-top: 38px;
}

.section-title {
    font-size: 17px;
    margin-bottom: 16px;
}

.test-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.test-card {
    border-radius: 23px;
    padding: 22px 17px;
}

.test-icon {
    font-size: 32px;
    margin-bottom: 16px;
}

.test-name {
    font-size: 19px;
    font-weight: 850;
}

.test-desc {
    color: #747f90;
    font-size: 13px;
    margin-top: 6px;
}

.duel {
    margin-top: 18px;
    padding: 24px;
    border-radius: 25px;
}

.duel h2 {
    margin: 0 0 9px;
}

.duel p {
    color: #7d8796;
    margin: 0 0 20px;
    line-height: 1.45;
}

.secondary,
.home {
    width: 100%;
    border: 1px solid #353c47;
    border-radius: 17px;
    background: transparent;
    color: white;
    padding: 15px;
    font-weight: 800;
}

.bottom {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    height: 88px;
    padding-bottom: env(safe-area-inset-bottom);
    background: rgba(9,11,15,.97);
    border-top: 1px solid #20252d;
    display: flex;
    justify-content: space-around;
    align-items: center;
    z-index: 20;
}

.nav {
    width: 33.33%;
    text-align: center;
    color: #697382;
    font-size: 13px;
}

.nav.active {
    color: white;
}

.nav-icon {
    font-size: 27px;
    display: block;
    margin-bottom: 4px;
}


/* TEST */

.test-screen {
    display: none;
    padding: 26px 20px 45px;
}

.test-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 35px;
}

.back {
    border: 0;
    background: transparent;
    color: #9aa4b2;
    font-size: 17px;
    padding: 0;
}

.timer {
    background: #161b22;
    border: 1px solid #2a313b;
    padding: 9px 15px;
    border-radius: 14px;
    font-weight: 900;
}

.progress {
    height: 5px;
    background: #1d222a;
    border-radius: 20px;
    overflow: hidden;
    margin-bottom: 35px;
}

.progress-bar {
    height: 100%;
    width: 0%;
    background: white;
    transition: width .2s;
}

.question-number {
    color: #8994a5;
    font-weight: 800;
    letter-spacing: 3px;
    font-size: 13px;
}

.question {
    font-size: 30px;
    line-height: 1.15;
    font-weight: 850;
    margin: 15px 0 30px;
}

.answers {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.answer {
    width: 100%;
    text-align: left;
    background: #11151a;
    border: 1px solid #2a313b;
    color: white;
    border-radius: 19px;
    padding: 19px;
    font-size: 17px;
    font-weight: 700;
}

.answer:active {
    transform: scale(.98);
}

.answer.correct {
    background: #18351f;
    border-color: #3f9c55;
}

.answer.wrong {
    background: #3a1919;
    border-color: #b34b4b;
}


/* RESULT */

.result-screen {
    display: none;
    padding: 40px 20px 50px;
    text-align: center;
}

.result-label {
    font-size: 14px;
}

.result-score {
    font-size: 100px;
    line-height: 1;
    font-weight: 950;
    margin: 30px 0 10px;
}

.result-level {
    font-size: 27px;
    font-weight: 900;
    margin-bottom: 15px;
}

.result-text {
    color: #8994a5;
    font-size: 17px;
    line-height: 1.5;
    margin-bottom: 35px;
}

.result-buttons {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.share {
    width: 100%;
    background: white;
    color: #090b0f;
    border: 0;
    border-radius: 18px;
    padding: 18px;
    font-size: 17px;
    font-weight: 900;
}


/* PROFILE / RANKING */

.profile-screen,
.ranking-screen {
    display: none;
    padding: 30px 20px 115px;
}

.page-title {
    font-size: 34px;
    font-weight: 900;
    margin: 0 0 24px;
}

.profile-card {
    border-radius: 25px;
    padding: 25px;
}

.avatar {
    width: 62px;
    height: 62px;
    border-radius: 50%;
    background: white;
    color: #090b0f;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    font-weight: 900;
    margin-bottom: 18px;
}

.profile-name {
    font-size: 25px;
    font-weight: 900;
}

.profile-username {
    color: #758092;
    margin-top: 5px;
}

.profile-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 24px;
}

.stat {
    background: #0c0f13;
    border-radius: 18px;
    padding: 18px;
}

.stat-label {
    color: #758092;
    font-size: 12px;
    letter-spacing: 2px;
    font-weight: 800;
}

.stat-value {
    font-size: 28px;
    font-weight: 900;
    margin-top: 8px;
}

.rank-row {
    border-radius: 19px;
    padding: 17px;
    display: flex;
    align-items: center;
    gap: 13px;
    margin-bottom: 10px;
}

.rank-number {
    width: 34px;
    color: #8994a5;
    font-weight: 900;
}

.rank-user {
    flex: 1;
    min-width: 0;
}

.rank-name {
    font-weight: 800;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.rank-meta {
    color: #687384;
    font-size: 12px;
    margin-top: 4px;
}

.rank-score {
    font-size: 20px;
    font-weight: 900;
}

.loading {
    color: #758092;
    text-align: center;
    padding: 30px 0;
}

.error {
    color: #b9c1cd;
    text-align: center;
    padding: 30px 0;
}
</style>
</head>

<body>

<div class="app" id="home">
    <div class="logo">ZAKO</div>

    <div class="hero">
        <div class="eyebrow">O'ZINGNI SINAB KO'R</div>

        <h1>Qanchalik<br>ZAKOsan?</h1>

        <p>
            Aqlingni sinab ko'r.
            Natijangni do'stlaring bilan solishtir.
        </p>

        <button class="primary" onclick="startTest()">
            🧠 AQL TESTINI BOSHLASH
        </button>
    </div>

    <div class="score-card">
        <div class="small-title">SENING ZAKO SCORE'ING</div>
        <div class="score" id="homeScore">—</div>
        <div class="muted" id="homeScoreText">
            Birinchi testdan keyin ochiladi
        </div>
    </div>

    <div class="section">
        <div class="section-title">SINAB KO'R</div>

        <div class="test-grid">
            <div class="test-card">
                <div class="test-icon">🧠</div>
                <div class="test-name">Aql</div>
                <div class="test-desc">Mantiq va fikrlash</div>
            </div>

            <div class="test-card">
                <div class="test-icon">⚡</div>
                <div class="test-name">Tezlik</div>
                <div class="test-desc">Qanchalik tez fikrlaysan?</div>
            </div>

            <div class="test-card">
                <div class="test-icon">🧩</div>
                <div class="test-name">Xotira</div>
                <div class="test-desc">Eslab qolish kuchi</div>
            </div>

            <div class="test-card">
                <div class="test-icon">👑</div>
                <div class="test-name">Liderlik</div>
                <div class="test-desc">Qaror qabul qilish</div>
            </div>
        </div>
    </div>

    <div class="duel">
        <h2>⚔️ DO'STINGNI YENG</h2>

        <p>
            Natijangni do'stingga yubor.
            Kim aqlliroq ekanini bilib oling.
        </p>

        <button class="secondary" onclick="shareChallenge()">
            DO'STIMNI CHAQIRISH
        </button>
    </div>
</div>


<div class="test-screen" id="test">
    <div class="test-top">
        <button class="back" onclick="goHome()">← Chiqish</button>
        <div class="timer" id="timer">15</div>
    </div>

    <div class="progress">
        <div class="progress-bar" id="progressBar"></div>
    </div>

    <div class="question-number" id="questionNumber">
        SAVOL 1 / 10
    </div>

    <div class="question" id="question">Savol</div>
    <div class="answers" id="answers"></div>
</div>


<div class="result-screen" id="result">
    <div class="result-label">SENING NATIJANG</div>

    <div class="result-score" id="resultScore">0</div>
    <div class="result-level" id="resultLevel">ZAKO</div>

    <div class="result-text" id="resultText">
        Natijang tayyor.
    </div>

    <div class="result-buttons">
        <button class="share" onclick="shareResult()">
            🚀 NATIJAMNI ULASHISH
        </button>

        <button class="home" onclick="goHome()">
            BOSH SAHIFAGA
        </button>
    </div>
</div>


<div class="profile-screen" id="profile">
    <h1 class="page-title">👤 Profil</h1>

    <div class="profile-card">
        <div class="avatar" id="profileAvatar">Z</div>

        <div class="profile-name" id="profileName">ZAKO</div>
        <div class="profile-username" id="profileUsername"></div>

        <div class="profile-stats">
            <div class="stat">
                <div class="stat-label">BEST SCORE</div>
                <div class="stat-value" id="profileScore">0</div>
            </div>

            <div class="stat">
                <div class="stat-label">TESTLAR</div>
                <div class="stat-value" id="profileTests">0</div>
            </div>
        </div>
    </div>
</div>


<div class="ranking-screen" id="ranking">
    <h1 class="page-title">🏆 Reyting</h1>
    <div id="rankingList">
        <div class="loading">Yuklanmoqda...</div>
    </div>
</div>


<div class="bottom">
    <div class="nav active" id="navHome" onclick="showPage('home')">
        <span class="nav-icon">🏠</span>
        Bosh sahifa
    </div>

    <div class="nav" id="navRanking" onclick="showPage('ranking')">
        <span class="nav-icon">🏆</span>
        Reyting
    </div>

    <div class="nav" id="navProfile" onclick="showPage('profile')">
        <span class="nav-icon">👤</span>
        Profil
    </div>
</div>


<script>
const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();

let current = 0;
let totalTime = 0;
let questionStarted = 0;
let timerInterval = null;
let timeLeft = 15;

let testToken = "";
let testQuestions = [];
let answersGiven = [];
let testFinished = false;


function apiHeaders() {
    return {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": tg.initData || ""
    };
}


function showPage(page) {
    clearInterval(timerInterval);

    document.getElementById("home").style.display = "none";
    document.getElementById("test").style.display = "none";
    document.getElementById("result").style.display = "none";
    document.getElementById("profile").style.display = "none";
    document.getElementById("ranking").style.display = "none";

    if (page === "home") {
        document.getElementById("home").style.display = "block";
    }

    if (page === "profile") {
        document.getElementById("profile").style.display = "block";
        loadProfile();
    }

    if (page === "ranking") {
        document.getElementById("ranking").style.display = "block";
        loadRanking();
    }

    document.querySelectorAll(".nav").forEach(
        nav => nav.classList.remove("active")
    );

    const navMap = {
        home: "navHome",
        ranking: "navRanking",
        profile: "navProfile"
    };

    document.getElementById(navMap[page]).classList.add("active");
}


async function startTest() {
    clearInterval(timerInterval);

    try {
        const response = await fetch("/api/test/start", {
            method: "POST",
            headers: apiHeaders(),
            body: JSON.stringify({
                initData: tg.initData || ""
            })
        });

        const data = await response.json();

        if (!data.ok) {
            alert("Testni boshlashda xato. Telegram ichidan qayta urinib ko'r.");
            return;
        }

        testToken = data.testToken;
        testQuestions = data.questions;
        answersGiven = [];
        current = 0;
        totalTime = 0;
        testFinished = false;

        document.getElementById("home").style.display = "none";
        document.getElementById("profile").style.display = "none";
        document.getElementById("ranking").style.display = "none";
        document.getElementById("result").style.display = "none";
        document.getElementById("test").style.display = "block";

        showQuestion();

    } catch (error) {
        console.error(error);
        alert("Internet ulanishida xato. Qayta urinib ko'r.");
    }
}


function showQuestion() {
    clearInterval(timerInterval);

    const q = testQuestions[current];

    document.getElementById("questionNumber").innerText =
        `SAVOL ${current + 1} / ${testQuestions.length}`;

    document.getElementById("question").innerText = q.q;

    document.getElementById("progressBar").style.width =
        `${(current / testQuestions.length) * 100}%`;

    const answers = document.getElementById("answers");
    answers.innerHTML = "";

    q.a.forEach((answer, index) => {
        const button = document.createElement("button");

        button.className = "answer";
        button.innerText = answer;

        button.onclick = () => chooseAnswer(index, button);

        answers.appendChild(button);
    });

    timeLeft = 15;
    questionStarted = Date.now();

    document.getElementById("timer").innerText = timeLeft;

    timerInterval = setInterval(() => {
        timeLeft--;

        document.getElementById("timer").innerText = timeLeft;

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            chooseAnswer(-1, null);
        }
    }, 1000);
}


function chooseAnswer(index, clickedButton) {
    clearInterval(timerInterval);

    const buttons = document.querySelectorAll(".answer");

    buttons.forEach(button => {
        button.disabled = true;
    });

    const elapsed = Math.min(
        15,
        Math.max(0, (Date.now() - questionStarted) / 1000)
    );

    totalTime += elapsed;

    answersGiven.push({
        questionId: testQuestions[current].id,
        answerIndex: index,
        timeSeconds: Number(elapsed.toFixed(2))
    });

    if (clickedButton) {
        clickedButton.classList.add("wrong");
    }

    setTimeout(() => {
        current++;

        if (current >= testQuestions.length) {
            finishTest();
        } else {
            showQuestion();
        }
    }, 350);
}


async function finishTest() {
    if (testFinished) return;

    testFinished = true;
    clearInterval(timerInterval);

    document.getElementById("test").style.display = "none";
    document.getElementById("result").style.display = "block";

    document.getElementById("resultScore").innerText = "…";
    document.getElementById("resultLevel").innerText = "HISOBLANMOQDA";
    document.getElementById("resultText").innerText =
        "Natijang serverda tekshirilmoqda.";

    try {
        const response = await fetch("/api/test/submit", {
            method: "POST",
            headers: apiHeaders(),
            body: JSON.stringify({
                initData: tg.initData || "",
                testToken: testToken,
                answers: answersGiven
            })
        });

        const data = await response.json();

        if (!data.ok) {
            document.getElementById("resultScore").innerText = "—";
            document.getElementById("resultLevel").innerText = "XATO";
            document.getElementById("resultText").innerText =
                data.error || "Natijani saqlashda xato.";
            return;
        }

        const score = data.score;

        localStorage.setItem("zako_score", String(score));

        document.getElementById("resultScore").innerText = score;

        if (score >= 90) {
            document.getElementById("resultLevel").innerText =
                "🧠 ZAKO DARAJASI";
            document.getElementById("resultText").innerText =
                `Juda kuchli natija. ${data.correctAnswers}/10 ta savol to'g'ri.`;
        } else if (score >= 75) {
            document.getElementById("resultLevel").innerText =
                "🥇 KUCHLI";
            document.getElementById("resultText").innerText =
                `Mantiqiy fikrlashing yaxshi. ${data.correctAnswers}/10 ta savol to'g'ri.`;
        } else if (score >= 55) {
            document.getElementById("resultLevel").innerText =
                "🥈 YAXSHI";
            document.getElementById("resultText").innerText =
                `Yomon emas. ${data.correctAnswers}/10 ta savol to'g'ri.`;
        } else {
            document.getElementById("resultLevel").innerText =
                "🥉 BOSHLANG'ICH";
            document.getElementById("resultText").innerText =
                `Bu hali boshlanishi. ${data.correctAnswers}/10 ta savol to'g'ri.`;
        }

    } catch (error) {
        console.error(error);

        document.getElementById("resultScore").innerText = "—";
        document.getElementById("resultLevel").innerText = "ALOQA XATOSI";
        document.getElementById("resultText").innerText =
            "Natijani serverga yuborib bo'lmadi. Internetni tekshir.";
    }
}


async function loadProfile() {
    try {
        const response = await fetch("/api/me", {
            headers: {
                "X-Telegram-Init-Data": tg.initData || ""
            }
        });

        const data = await response.json();

        if (!data.ok) {
            return;
        }

        const user = data.user || {};
        const name = user.first_name || "ZAKO";

        document.getElementById("profileName").innerText = name;

        document.getElementById("profileAvatar").innerText =
            name.charAt(0).toUpperCase();

        document.getElementById("profileUsername").innerText =
            user.username ? "@" + user.username : "";

        document.getElementById("profileScore").innerText =
            data.best_score || 0;

        document.getElementById("profileTests").innerText =
            data.tests_taken || 0;

        document.getElementById("homeScore").innerText =
            data.best_score || "—";

        document.getElementById("homeScoreText").innerText =
            data.best_score
                ? "Eng yuqori natijang"
                : "Birinchi testdan keyin ochiladi";

    } catch (error) {
        console.error("Profile error:", error);
    }
}


async function loadRanking() {
    const list = document.getElementById("rankingList");

    list.innerHTML =
        '<div class="loading">Yuklanmoqda...</div>';

    try {
        const response = await fetch("/api/ranking");
        const data = await response.json();

        if (!data.ok || !data.users.length) {
            list.innerHTML =
                '<div class="loading">Hozircha reyting bo\'sh.</div>';
            return;
        }

        list.innerHTML = "";

        data.users.forEach((user, index) => {
            const row = document.createElement("div");
            row.className = "rank-row";

            const number = document.createElement("div");
            number.className = "rank-number";
            number.innerText = index + 1;

            const info = document.createElement("div");
            info.className = "rank-user";

            const name = document.createElement("div");
            name.className = "rank-name";
            name.innerText =
                user.first_name ||
                (user.username ? "@" + user.username : "ZAKO");

            const meta = document.createElement("div");
            meta.className = "rank-meta";
            meta.innerText = `${user.tests_taken} ta test`;

            info.appendChild(name);
            info.appendChild(meta);

            const score = document.createElement("div");
            score.className = "rank-score";
            score.innerText = user.best_score;

            row.appendChild(number);
            row.appendChild(info);
            row.appendChild(score);

            list.appendChild(row);
        });

    } catch (error) {
        console.error("Ranking error:", error);

        list.innerHTML =
            '<div class="error">Reytingni yuklashda xato.</div>';
    }
}


function goHome() {
    clearInterval(timerInterval);

    document.getElementById("test").style.display = "none";
    document.getElementById("result").style.display = "none";
    document.getElementById("profile").style.display = "none";
    document.getElementById("ranking").style.display = "none";
    document.getElementById("home").style.display = "block";

    document.querySelectorAll(".nav").forEach(
        nav => nav.classList.remove("active")
    );

    document.getElementById("navHome").classList.add("active");

    loadProfile();
}


function shareResult() {
    const score =
        localStorage.getItem("zako_score") || "0";

    const text =
        `🧠 Men ZAKO testidan ${score}/100 oldim!\n\n` +
        `Qani, senchi? O'zingni sinab ko'r.`;

    const url =
        "https://t.me/share/url?url=" +
        encodeURIComponent(window.location.origin) +
        "&text=" +
        encodeURIComponent(text);

    if (tg.openTelegramLink) {
        tg.openTelegramLink(url);
    } else {
        window.open(url, "_blank");
    }
}


function shareChallenge() {
    const text =
        "🧠 Men ZAKO testini topshirdim.\n" +
        "Meni yenga olasanmi? 😏";

    const url =
        "https://t.me/share/url?url=" +
        encodeURIComponent(window.location.origin) +
        "&text=" +
        encodeURIComponent(text);

    if (tg.openTelegramLink) {
        tg.openTelegramLink(url);
    } else {
        window.open(url, "_blank");
    }
}


loadProfile();
</script>

</body>
</html>
"""


# ============================================================
# API
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(HTML)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "zako-bot",
        "database": db_pool is not None,
    }


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()

    update = types.Update.model_validate(
        data,
        context={"bot": bot},
    )

    await dp.feed_update(bot, update)

    return {"ok": True}


@app.post("/api/test/start")
async def start_test(request: Request):
    body = await request.json()

    user = telegram_user_from_request(request, body)

    if not user:
        return {
            "ok": False,
            "error": "Telegram userni tasdiqlab bo'lmadi.",
        }

    telegram_id = await upsert_user(user)

    # Random order for each attempt.
    question_ids = [item["id"] for item in QUESTIONS]
    # Deterministic enough for the request; no answer key is exposed.
    import random
    random.shuffle(question_ids)

    test_token = create_test_token(
        telegram_id,
        question_ids,
    )

    questions_for_client = [
        {
            "id": question_id,
            "q": QUESTION_BY_ID[question_id]["q"],
            "a": QUESTION_BY_ID[question_id]["a"],
        }
        for question_id in question_ids
    ]

    return {
        "ok": True,
        "testToken": test_token,
        "questions": questions_for_client,
    }


@app.post("/api/test/submit")
async def submit_test(request: Request):
    body = await request.json()

    user = telegram_user_from_request(request, body)

    if not user:
        return {
            "ok": False,
            "error": "Telegram userni tasdiqlab bo'lmadi.",
        }

    telegram_id = int(user["id"])

    test_token = body.get("testToken", "")
    token_data = verify_test_token(
        test_token,
        telegram_id,
    )

    if not token_data:
        return {
            "ok": False,
            "error": "Test sessiyasi yaroqsiz yoki muddati o'tgan.",
        }

    answers = body.get("answers")

    if not isinstance(answers, list):
        return {
            "ok": False,
            "error": "Javoblar noto'g'ri yuborildi.",
        }

    # Exactly one answer per question is expected.
    if len(answers) != len(QUESTIONS):
        return {
            "ok": False,
            "error": "Test to'liq yakunlanmagan.",
        }

    expected_ids = token_data["q"]
    received_ids = []

    correct_answers = 0
    total_time = 0.0

    for position, item in enumerate(answers):
        if not isinstance(item, dict):
            return {
                "ok": False,
                "error": "Javob formati noto'g'ri.",
            }

        try:
            question_id = int(item["questionId"])
            answer_index = int(item["answerIndex"])
            time_seconds = float(item["timeSeconds"])
        except (KeyError, TypeError, ValueError):
            return {
                "ok": False,
                "error": "Javob ma'lumotlari noto'g'ri.",
            }

        if question_id != expected_ids[position]:
            return {
                "ok": False,
                "error": "Test tartibi o'zgartirilgan.",
            }

        if question_id in received_ids:
            return {
                "ok": False,
                "error": "Bir savol takrorlangan.",
            }

        if not -1 <= answer_index < 4:
            return {
                "ok": False,
                "error": "Javob varianti noto'g'ri.",
            }

        if not 0 <= time_seconds <= 15.5:
            return {
                "ok": False,
                "error": "Vaqt qiymati noto'g'ri.",
            }

        received_ids.append(question_id)
        total_time += min(15.0, max(0.0, time_seconds))

        correct_index = QUESTION_BY_ID[question_id]["correct"]

        if answer_index == correct_index:
            correct_answers += 1

    # 70% accuracy + 30% speed.
    accuracy_points = (
        correct_answers / len(QUESTIONS)
    ) * 70

    average_time = total_time / len(QUESTIONS)

    speed_points = max(
        0,
        30 - (average_time / 15) * 30,
    )

    score = round(
        max(
            0,
            min(
                100,
                accuracy_points + speed_points,
            ),
        )
    )

    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (
                telegram_id,
                username,
                first_name
            )
            VALUES ($1, $2, $3)
            ON CONFLICT (telegram_id)
            DO UPDATE SET
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                updated_at = NOW()
        """,
            telegram_id,
            user.get("username"),
            user.get("first_name", ""),
        )

        await conn.execute("""
            INSERT INTO test_results (
                telegram_id,
                test_type,
                score,
                correct_answers,
                total_questions,
                total_time_seconds
            )
            VALUES ($1, 'iq', $2, $3, $4, $5)
        """,
            telegram_id,
            score,
            correct_answers,
            len(QUESTIONS),
            round(total_time, 2),
        )

        await conn.execute("""
            UPDATE users
            SET
                best_score = GREATEST(best_score, $2),
                tests_taken = tests_taken + 1,
                updated_at = NOW()
            WHERE telegram_id = $1
        """,
            telegram_id,
            score,
        )

    return {
        "ok": True,
        "score": score,
        "correctAnswers": correct_answers,
        "totalQuestions": len(QUESTIONS),
    }


@app.get("/api/me")
async def get_me(request: Request):
    user = telegram_user_from_request(request)

    if not user:
        return {
            "ok": False,
            "error": "Telegram userni tasdiqlab bo'lmadi.",
        }

    telegram_id = await upsert_user(user)

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                telegram_id,
                username,
                first_name,
                best_score,
                tests_taken
            FROM users
            WHERE telegram_id = $1
        """, telegram_id)

    return {
        "ok": True,
        "user": {
            "id": row["telegram_id"] if row else telegram_id,
            "username": row["username"] if row else user.get("username"),
            "first_name": row["first_name"] if row else user.get("first_name", ""),
        },
        "best_score": row["best_score"] if row else 0,
        "tests_taken": row["tests_taken"] if row else 0,
    }


@app.get("/api/ranking")
async def ranking():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                username,
                first_name,
                best_score,
                tests_taken
            FROM users
            WHERE tests_taken > 0
            ORDER BY best_score DESC, tests_taken ASC, updated_at ASC
            LIMIT 100
        """)

    return {
        "ok": True,
        "users": [
            {
                "username": row["username"],
                "first_name": row["first_name"],
                "best_score": row["best_score"],
                "tests_taken": row["tests_taken"],
            }
            for row in rows
        ],
    }


# ============================================================
# LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    await init_db()

    await bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True,
    )

    try:
        yield
    finally:
        try:
            await bot.delete_webhook()
        finally:
            await bot.session.close()
            await close_db()


app.router.lifespan_context = lifespan
