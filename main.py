import os
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")

PUBLIC_URL = (
    os.getenv("PUBLIC_URL")
    or os.getenv("RENDER_EXTERNAL_URL")
)

if not PUBLIC_URL:
    raise RuntimeError("PUBLIC_URL / RENDER_EXTERNAL_URL is missing")

PUBLIC_URL = PUBLIC_URL.rstrip("/")

WEBHOOK_PATH = "/telegram/webhook"
WEBHOOK_URL = PUBLIC_URL + WEBHOOK_PATH


# =========================================================
# BOT
# =========================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =========================================================
# MINI APP HTML
# =========================================================

HTML = """
<!DOCTYPE html>
<html lang="uz">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
    initial-scale=1,
    maximum-scale=1,
    user-scalable=no"
>

<meta name="theme-color" content="#0b0d10">

<title>ZAKO</title>

<style>

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    padding: 0;
    background: #0b0d10;
    color: #ffffff;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

body {
    min-height: 100vh;
}

.app {
    width: 100%;
    max-width: 620px;
    margin: 0 auto;

    padding:
        20px
        18px
        100px;
}


/* HEADER */

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 26px;
    font-weight: 900;
    letter-spacing: 3px;
}

.avatar {
    width: 38px;
    height: 38px;

    border-radius: 50%;

    background: #ffffff;
    color: #0b0d10;

    display: flex;
    align-items: center;
    justify-content: center;

    font-weight: 900;
}


/* HERO */

.hero {
    padding:
        70px
        3px
        28px;
}

.eyebrow {
    margin: 0 0 12px;

    color: #858e9b;

    font-size: 11px;
    font-weight: 800;

    letter-spacing: 2px;
}

.hero h1 {
    margin: 0;

    font-size: 52px;
    line-height: .96;

    letter-spacing: -2.5px;
}

.hero p {
    margin:
        18px
        0
        26px;

    max-width: 400px;

    color: #9da6b3;

    font-size: 15px;
    line-height: 1.5;
}


/* MAIN BUTTON */

.start-button {
    width: 100%;

    border: 0;
    border-radius: 17px;

    padding: 18px;

    background: #ffffff;
    color: #0b0d10;

    font-size: 14px;
    font-weight: 900;

    cursor: pointer;

    transition: transform .12s;
}

.start-button:active {
    transform: scale(.98);
}


/* SCORE */

.score-card {
    padding: 20px;

    border-radius: 19px;

    background: #12161b;
    border: 1px solid #252b33;
}

.score-label {
    display: block;

    color: #7f8997;

    font-size: 10px;
    font-weight: 800;

    letter-spacing: 1.2px;
}

.score {
    display: block;

    margin-top: 7px;

    font-size: 43px;
    font-weight: 900;
}

.score-info {
    margin-top: 7px;

    color: #687280;

    font-size: 11px;
}


/* SECTION */

.section {
    margin-top: 30px;
}

.section-title {
    margin-bottom: 13px;

    color: #7f8997;

    font-size: 11px;
    font-weight: 800;

    letter-spacing: 1.5px;
}


/* TESTS */

.tests {
    display: grid;

    grid-template-columns:
        1fr
        1fr;

    gap: 10px;
}

.test-card {
    min-height: 115px;

    padding: 17px;

    border-radius: 18px;

    background: #12161b;
    border: 1px solid #252b33;

    text-align: left;
}

.test-icon {
    font-size: 25px;
}

.test-name {
    display: block;

    margin-top: 8px;

    font-size: 16px;
    font-weight: 800;
}

.test-status {
    display: block;

    margin-top: 5px;

    color: #697382;

    font-size: 11px;
}


/* DUEL */

.duel {
    margin-top: 14px;

    padding: 18px;

    display: flex;
    gap: 13px;
    align-items: center;

    border-radius: 19px;

    background: #151a20;
    border: 1px solid #252c35;
}

.duel-icon {
    font-size: 28px;
}

.duel-title {
    font-size: 14px;
    font-weight: 900;
}

.duel-text {
    margin-top: 5px;

    color: #7f8997;

    font-size: 11px;
    line-height: 1.4;
}


/* BOTTOM */

.bottom {
    position: fixed;

    left: 0;
    right: 0;
    bottom: 0;

    padding:
        11px
        15px
        calc(11px + env(safe-area-inset-bottom));

    display: flex;
    justify-content: space-around;

    background: rgba(11, 13, 16, .95);

    border-top: 1px solid #20252c;

    backdrop-filter: blur(18px);
}

.nav {
    border: 0;

    background: none;

    color: #697382;

    display: flex;
    flex-direction: column;
    align-items: center;

    gap: 3px;

    font-size: 19px;
}

.nav small {
    font-size: 9px;
}

.nav.active {
    color: #ffffff;
}

</style>

</head>


<body>

<div class="app">

    <header class="header">

        <div class="logo">
            ZAKO
        </div>

        <div class="avatar">
            Z
        </div>

    </header>


    <section class="hero">

        <div class="eyebrow">
            O‘ZINGNI SINAB KO‘R
        </div>

        <h1>
            Qanchalik<br>
            ZAKOsan?
        </h1>

        <p>
            Aqlingni sinab ko‘r.
            Natijangni do‘stlaring bilan solishtir.
        </p>

        <button
            class="start-button"
            onclick="startTest()"
        >
            🧠 AQL TESTINI BOSHLASH
        </button>

    </section>


    <section class="score-card">

        <span class="score-label">
            SENING ZAKO SCORE'ING
        </span>

        <strong class="score">
            —
        </strong>

        <div class="score-info">
            Birinchi testdan keyin ochiladi
        </div>

    </section>


    <section class="section">

        <div class="section-title">
            SINAB KO‘R
        </div>


        <div class="tests">

            <div class="test-card">

                <div class="test-icon">
                    🧠
                </div>

                <span class="test-name">
                    Aql
                </span>

                <span class="test-status">
                    Asosiy test
                </span>

            </div>


            <div class="test-card">

                <div class="test-icon">
                    ⚡
                </div>

                <span class="test-name">
                    Tezlik
                </span>

                <span class="test-status">
                    Tez orada
                </span>

            </div>


            <div class="test-card">

                <div class="test-icon">
                    🧩
                </div>

                <span class="test-name">
                    Xotira
                </span>

                <span class="test-status">
                    Tez orada
                </span>

            </div>


            <div class="test-card">

                <div class="test-icon">
                    👑
                </div>

                <span class="test-name">
                    Liderlik
                </span>

                <span class="test-status">
                    Tez orada
                </span>

            </div>

        </div>

    </section>


    <section class="duel">

        <div class="duel-icon">
            ⚔️
        </div>

        <div>

            <div class="duel-title">
                DO‘STINGNI YENG
            </div>

            <div class="duel-text">
                Avval testdan o‘t.
                Keyin uni duelga chaqirasan.
            </div>

        </div>

    </section>

</div>


<nav class="bottom">

    <button class="nav active">
        🏠
        <small>Bosh sahifa</small>
    </button>

    <button class="nav">
        🏆
        <small>Reyting</small>
    </button>

    <button class="nav">
        👤
        <small>Profil</small>
    </button>

</nav>


<script src="https://telegram.org/js/telegram-web-app.js"></script>


<script>

const tg = window.Telegram?.WebApp;

if (tg) {

    tg.ready();

    tg.expand();

    tg.setHeaderColor?.("#0b0d10");

    tg.setBackgroundColor?.("#0b0d10");
}


function startTest() {

    if (tg) {

        tg.HapticFeedback?.impactOccurred("medium");

    }

    alert(
        "🧠 AQL TESTI\\n\\n" +
        "Keyingi buildda haqiqiy test boshlanadi."
    );
}

</script>

</body>

</html>
"""


# =========================================================
# BOT HANDLER
# =========================================================

@dp.message(CommandStart())
async def start_handler(message: types.Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 ZAKO'NI OCHISH",
                    web_app=WebAppInfo(url=PUBLIC_URL)
                )
            ]
        ]
    )

    await message.answer(
        "🧠 <b>ZAKO</b>\n\n"
        "O'zingni sinab ko'r.\n"
        "Boshqalar bilan solishtir.\n\n"
        "👇 Boshlash uchun tugmani bosing.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(title="ZAKO")


@app.get("/", response_class=HTMLResponse)
async def mini_app():

    return HTML


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "zako"
    }


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):

    data = await request.json()

    update = types.Update.model_validate(data)

    await dp.feed_update(
        bot,
        update
    )

    return {
        "ok": True
    }


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
async def startup():

    await bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )

    print("================================")
    print("ZAKO STARTED")
    print("Mini App:", PUBLIC_URL)
    print("Webhook:", WEBHOOK_URL)
    print("================================")


@app.on_event("shutdown")
async def shutdown():

    await bot.delete_webhook()

    await bot.session.close()
