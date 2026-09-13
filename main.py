import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart

BOT_TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_URL = os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

if not PUBLIC_URL:
    raise RuntimeError("PUBLIC_URL is not set")

WEBHOOK_PATH = "/telegram/webhook"
WEBHOOK_URL = PUBLIC_URL + WEBHOOK_PATH

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()


# =========================
# TELEGRAM BOT
# =========================

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
        "🧠 <b>ZAKO</b>\n\nO'zingni sinab ko'r.\n"
        "Qanchalik ZAKOsan?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# =========================
# MINI APP
# =========================

HTML = r"""
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

<title>ZAKO</title>

<script src="https://telegram.org/js/telegram-web-app.js"></script>

<style>
* {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

body {
    margin: 0;
    background: #090b0f;
    color: #f5f7fa;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                 "Segoe UI", sans-serif;
}

button {
    font-family: inherit;
}

.app {
    min-height: 100vh;
    padding: 26px 20px 105px;
}

.logo {
    font-size: 40px;
    font-weight: 900;
    letter-spacing: 6px;
    margin-bottom: 95px;
}

.eyebrow {
    color: #8d98a8;
    font-size: 16px;
    font-weight: 800;
    letter-spacing: 4px;
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
    margin-bottom: 28px;
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

.score-card {
    margin-top: 28px;
    padding: 27px;
    border: 1px solid #252b34;
    background: #11151a;
    border-radius: 25px;
}

.small-title {
    color: #8994a5;
    font-weight: 800;
    letter-spacing: 3px;
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
    color: #8994a5;
    font-size: 17px;
    font-weight: 900;
    letter-spacing: 4px;
    margin-bottom: 16px;
}

.test-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.test-card {
    background: #11151a;
    border: 1px solid #252b34;
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
    background: #11151a;
    border: 1px solid #252b34;
    border-radius: 25px;
}

.duel h2 {
    margin: 0 0 9px;
}

.duel p {
    color: #7d8796;
    margin-bottom: 20px;
}

.secondary {
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
    background: rgba(9,11,15,.96);
    border-top: 1px solid #20252d;
    display: flex;
    justify-content: space-around;
    align-items: center;
    z-index: 20;
}

.nav {
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


/* TEST SCREEN */

.test-screen {
    display: none;
    min-height: 100vh;
    padding: 26px 20px 40px;
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
    min-height: 100vh;
    padding: 40px 20px 50px;
    text-align: center;
}

.result-label {
    color: #8994a5;
    letter-spacing: 4px;
    font-weight: 900;
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

.home {
    width: 100%;
    background: transparent;
    color: white;
    border: 1px solid #303741;
    border-radius: 18px;
    padding: 17px;
    font-size: 17px;
    font-weight: 800;
}
</style>
</head>

<body>

<!-- HOME -->

<div class="app" id="home">

    <div class="logo">ZAKO</div>

    <div class="hero">

        <div class="eyebrow">O'ZINGNI SINAB KO'R</div>

        <h1>
            Qanchalik<br>
            ZAKOsan?
        </h1>

        <p>
            Aqlingni sinab ko'r.
            Natijangni do'stlaring bilan solishtir.
        </p>

        <button class="primary" onclick="startTest()">
            🧠 AQL TESTINI BOSHLASH
        </button>

    </div>


    <div class="score-card">

        <div class="small-title">
            SENING ZAKO SCORE'ING
        </div>

        <div class="score" id="homeScore">—</div>

        <div class="muted">
            Birinchi testdan keyin ochiladi
        </div>

    </div>


    <div class="section">

        <div class="section-title">
            SINAB KO'R
        </div>

        <div class="test-grid">

            <div class="test-card">
                <div class="test-icon">🧠</div>
                <div class="test-name">Aql</div>
                <div class="test-desc">
                    Mantiq va fikrlash
                </div>
            </div>

            <div class="test-card">
                <div class="test-icon">⚡</div>
                <div class="test-name">Tezlik</div>
                <div class="test-desc">
                    Qanchalik tez fikrlaysan?
                </div>
            </div>

            <div class="test-card">
                <div class="test-icon">🧩</div>
                <div class="test-name">Xotira</div>
                <div class="test-desc">
                    Eslab qolish kuchi
                </div>
            </div>

            <div class="test-card">
                <div class="test-icon">👑</div>
                <div class="test-name">Liderlik</div>
                <div class="test-desc">
                    Qaror qabul qilish
                </div>
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


<!-- TEST -->

<div class="test-screen" id="test">

    <div class="test-top">

        <button class="back" onclick="goHome()">
            ← Chiqish
        </button>

        <div class="timer" id="timer">
            15
        </div>

    </div>

    <div class="progress">
        <div class="progress-bar" id="progressBar"></div>
    </div>

    <div class="question-number" id="questionNumber">
        SAVOL 1 / 10
    </div>

    <div class="question" id="question">
        Savol
    </div>

    <div class="answers" id="answers"></div>

</div>


<!-- RESULT -->

<div class="result-screen" id="result">

    <div class="result-label">
        SENING NATIJANG
    </div>

    <div class="result-score" id="resultScore">
        0
    </div>

    <div class="result-level" id="resultLevel">
        ZAKO
    </div>

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


<!-- NAV -->

<div class="bottom">

    <div class="nav active" onclick="goHome()">
        <span class="nav-icon">🏠</span>
        Bosh sahifa
    </div>

    <div class="nav">
        <span class="nav-icon">🏆</span>
        Reyting
    </div>

    <div class="nav">
        <span class="nav-icon">👤</span>
        Profil
    </div>

</div>


<script>

const tg = window.Telegram.WebApp;

tg.ready();
tg.expand();


/* =========================
   QUESTIONS
========================= */

const questions = [

    {
        q: "Ketma-ketlikni davom ettir: 2, 4, 8, 16, ?",
        a: ["24", "30", "32", "36"],
        correct: 2
    },

    {
        q: "Agar barcha ZAKOlar aqlli bo'lsa, Ali ZAKO bo'lsa, Ali qanday?",
        a: ["Tez", "Aqlli", "Kuchli", "Bilmaymiz"],
        correct: 1
    },

    {
        q: "3 ta mashina 3 daqiqada 3 ta detal ishlab chiqaradi. 1 mashina 3 daqiqada nechta detal ishlab chiqaradi?",
        a: ["1", "2", "3", "9"],
        correct: 0
    },

    {
        q: "Ketma-ketlik: 1, 1, 2, 3, 5, 8, ?",
        a: ["11", "12", "13", "15"],
        correct: 2
    },

    {
        q: "5 ta sham yonib turibdi. 2 tasi o'chirildi. Nechta sham qoldi?",
        a: ["2", "3", "5", "0"],
        correct: 2
    },

    {
        q: "Agar kecha yakshanba bo'lgan bo'lsa, ertadan keyingi kun qaysi kun?",
        a: ["Seshanba", "Chorshanba", "Payshanba", "Juma"],
        correct: 1
    },

    {
        q: "10 ning yarmi + 10 ning yarmi nechaga teng?",
        a: ["5", "10", "15", "20"],
        correct: 1
    },

    {
        q: "Qaysi biri boshqalardan farq qiladi?",
        a: ["Olma", "Nok", "Sabzi", "Shaftoli"],
        correct: 2
    },

    {
        q: "Bir odam 5-qavatdan lift bilan tushdi. Keyin 3-qavatga piyoda chiqdi. Nega?",
        a: [
            "Lift buzilgan",
            "Sport qilmoqchi",
            "Bo'yi lift tugmasiga yetmaydi",
            "Bilmaymiz"
        ],
        correct: 2
    },

    {
        q: "Agar 2 + 3 = 10, 3 + 4 = 21 bo'lsa, 4 + 5 = ?",
        a: ["30", "36", "40", "45"],
        correct: 1
    }

];


let current = 0;
let correctAnswers = 0;
let totalTime = 0;
let questionStarted = 0;
let timerInterval = null;
let timeLeft = 15;


/* =========================
   START TEST
========================= */

function startTest() {

    current = 0;
    correctAnswers = 0;
    totalTime = 0;

    document.getElementById("home").style.display = "none";
    document.getElementById("result").style.display = "none";
    document.getElementById("test").style.display = "block";

    showQuestion();
}


/* =========================
   SHOW QUESTION
========================= */

function showQuestion() {

    clearInterval(timerInterval);

    const q = questions[current];

    document.getElementById("questionNumber").innerText =
        `SAVOL ${current + 1} / ${questions.length}`;

    document.getElementById("question").innerText = q.q;

    document.getElementById("progressBar").style.width =
        `${((current) / questions.length) * 100}%`;

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


/* =========================
   ANSWER
========================= */

function chooseAnswer(index, clickedButton) {

    clearInterval(timerInterval);

    const q = questions[current];

    const buttons =
        document.querySelectorAll(".answer");

    buttons.forEach(b => b.disabled = true);

    const elapsed =
        Math.min(15, (Date.now() - questionStarted) / 1000);

    totalTime += elapsed;

    if (index === q.correct) {

        correctAnswers++;

        if (clickedButton) {
            clickedButton.classList.add("correct");
        }

    } else {

        if (clickedButton) {
            clickedButton.classList.add("wrong");
        }

        if (buttons[q.correct]) {
            buttons[q.correct].classList.add("correct");
        }

    }

    setTimeout(() => {

        current++;

        if (current >= questions.length) {
            finishTest();
        } else {
            showQuestion();
        }

    }, 550);
}


/* =========================
   FINISH
========================= */

function finishTest() {

    clearInterval(timerInterval);

    /*
      70% natija — to'g'ri javoblar
      30% natija — tezlik
    */

    const accuracy =
        (correctAnswers / questions.length) * 70;

    const averageTime =
        totalTime / questions.length;

    const speed =
        Math.max(0, 30 - (averageTime / 15) * 30);

    let score =
        Math.round(accuracy + speed);

    score = Math.max(0, Math.min(100, score));

    localStorage.setItem("zako_score", score);

    document.getElementById("test").style.display = "none";
    document.getElementById("result").style.display = "block";

    document.getElementById("resultScore").innerText = score;

    let level;
    let text;

    if (score >= 90) {

        level = "🧠 ZAKO DARAJASI";
        text = "Juda kuchli natija. Ko'pchilik bu darajaga chiqolmaydi.";

    } else if (score >= 75) {

        level = "🥇 KUCHLI";
        text = "Mantiqiy fikrlashing yaxshi. Lekin bundan ham yuqoriga chiqishing mumkin.";

    } else if (score >= 55) {

        level = "🥈 YAXSHI";
        text = "Yomon emas. Bir oz mashq bilan natijang ancha oshadi.";

    } else {

        level = "🥉 BOSHLANG'ICH";
        text = "Bu hali boshlanishi. Qayta urinib ko'r.";

    }

    document.getElementById("resultLevel").innerText = level;
    document.getElementById("resultText").innerText =
        text + ` ${correctAnswers}/10 ta savolni to'g'ri topding.`;

    document.getElementById("progressBar").style.width = "100%";
}


/* =========================
   HOME
========================= */

function goHome() {

    clearInterval(timerInterval);

    document.getElementById("test").style.display = "none";
    document.getElementById("result").style.display = "none";
    document.getElementById("home").style.display = "block";

    loadScore();
}


function loadScore() {

    const score =
        localStorage.getItem("zako_score");

    if (score) {
        document.getElementById("homeScore").innerText = score;
    }

}

loadScore();


/* =========================
   SHARE RESULT
========================= */

function shareResult() {

    const score =
        localStorage.getItem("zako_score") || 0;

    const text =
        `🧠 Men ZAKO testidan ${score}/100 oldim!\n\nQani, senchi? O'zingni sinab ko'r.`;

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


/* =========================
   SHARE CHALLENGE
========================= */

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

</script>

</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(HTML)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "zako-bot"}


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = types.Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.on_event("startup")
async def startup():
    await bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )


@app.on_event("shutdown")
async def shutdown():
    await bot.delete_webhook()
    await bot.session.close()
