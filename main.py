import os,json,hmac,hashlib,urllib.parse,secrets,random,asyncio,base64,re
from datetime import datetime,timezone,timedelta,date
from contextlib import asynccontextmanager
from fastapi import FastAPI,Request,UploadFile,File
from fastapi.responses import HTMLResponse,JSONResponse,FileResponse
import asyncpg
from pathlib import Path
from aiogram import Bot,Dispatcher,types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton,WebAppInfo

BOT_TOKEN=os.getenv('BOT_TOKEN')
PUBLIC_URL=(os.getenv('PUBLIC_URL') or os.getenv('RENDER_EXTERNAL_URL') or '').rstrip('/')
DATABASE_URL=os.getenv('DATABASE_URL')
OPENAI_API_KEY=os.getenv('OPENAI_API_KEY','')
OPENAI_MODEL=os.getenv('OPENAI_MODEL','gpt-5.6-luna')
if not BOT_TOKEN: raise RuntimeError('BOT_TOKEN is not set')
if not PUBLIC_URL: raise RuntimeError('PUBLIC_URL / RENDER_EXTERNAL_URL is not set')
if not DATABASE_URL: raise RuntimeError('DATABASE_URL is not set')

QUESTION_BANKS={
  "iq": [
    {
      "q": "Qatorni davom ettir: 2, 6, 12, 20, ?",
      "a": [
        "28",
        "30",
        "32",
        "34"
      ],
      "correct": 1,
      "kind": "sequence",
      "id": "iq_1"
    },
    {
      "q": "Qatorni davom ettir: 5, 9, 17, 33, ?",
      "a": [
        "57",
        "49",
        "67",
        "65"
      ],
      "correct": 3,
      "kind": "sequence",
      "id": "iq_2"
    },
    {
      "q": "Qatorni davom ettir: 64, 32, 16, 8, ?",
      "a": [
        "6",
        "4",
        "1",
        "2"
      ],
      "correct": 1,
      "kind": "sequence",
      "id": "iq_3"
    },
    {
      "q": "Qatorni davom ettir: 3, 8, 15, 24, ?",
      "a": [
        "31",
        "39",
        "36",
        "35"
      ],
      "correct": 2,
      "kind": "sequence",
      "id": "iq_4"
    },
    {
      "q": "Qatorni davom ettir: 1, 4, 10, 22, ?",
      "a": [
        "46",
        "48",
        "42",
        "34"
      ],
      "correct": 0,
      "kind": "sequence",
      "id": "iq_5"
    },
    {
      "q": "Qatorni davom ettir: 7, 10, 16, 28, ?",
      "a": [
        "46",
        "58",
        "40",
        "52"
      ],
      "correct": 3,
      "kind": "sequence",
      "id": "iq_6"
    },
    {
      "q": "Qatorni davom ettir: 90, 81, 63, 36, ?",
      "a": [
        "12",
        "6",
        "9",
        "0"
      ],
      "correct": 3,
      "kind": "sequence",
      "id": "iq_7"
    },
    {
      "q": "Qatorni davom ettir: 2, 3, 5, 8, 13, ?",
      "a": [
        "18",
        "22",
        "20",
        "21"
      ],
      "correct": 3,
      "kind": "sequence",
      "id": "iq_8"
    },
    {
      "q": "Qatorni davom ettir: 100, 50, 25, 12.5, ?",
      "a": [
        "7.5",
        "8.25",
        "6.25",
        "5"
      ],
      "correct": 2,
      "kind": "sequence",
      "id": "iq_9"
    },
    {
      "q": "Qatorni davom ettir: 4, 12, 36, 108, ?",
      "a": [
        "216",
        "432",
        "324",
        "288"
      ],
      "correct": 2,
      "kind": "sequence",
      "id": "iq_10"
    },
    {
      "q": "Qatorni davom ettir: 1, 2, 6, 24, ?",
      "a": [
        "72",
        "144",
        "120",
        "96"
      ],
      "correct": 2,
      "kind": "sequence",
      "id": "iq_11"
    },
    {
      "q": "Qatorni davom ettir: 11, 14, 20, 29, ?",
      "a": [
        "44",
        "38",
        "42",
        "41"
      ],
      "correct": 3,
      "kind": "sequence",
      "id": "iq_12"
    },
    {
      "q": "Qatorni davom ettir: 81, 72, 54, 27, ?",
      "a": [
        "18",
        "9",
        "0",
        "12"
      ],
      "correct": 2,
      "kind": "sequence",
      "id": "iq_13"
    },
    {
      "q": "Qatorni davom ettir: 2, 5, 11, 23, ?",
      "a": [
        "35",
        "47",
        "49",
        "41"
      ],
      "correct": 1,
      "kind": "sequence",
      "id": "iq_14"
    },
    {
      "q": "Qatorni davom ettir: 6, 7, 9, 12, 16, ?",
      "a": [
        "21",
        "20",
        "22",
        "19"
      ],
      "correct": 0,
      "kind": "sequence",
      "id": "iq_15"
    },
    {
      "q": "Qatorni davom ettir: 48, 24, 27, 13.5, 16.5, ?",
      "a": [
        "8.25",
        "11.5",
        "9.5",
        "10.5"
      ],
      "correct": 0,
      "kind": "sequence",
      "id": "iq_16"
    },
    {
      "q": "Qatorni davom ettir: 3, 9, 8, 24, 23, ?",
      "a": [
        "72",
        "68",
        "46",
        "69"
      ],
      "correct": 3,
      "kind": "sequence",
      "id": "iq_17"
    },
    {
      "q": "Qatorni davom ettir: 14, 17, 23, 32, 44, ?",
      "a": [
        "59",
        "57",
        "60",
        "62"
      ],
      "correct": 0,
      "kind": "sequence",
      "id": "iq_18"
    },
    {
      "q": "Qatorni davom ettir: 1, 5, 14, 30, 55, ?",
      "a": [
        "91",
        "84",
        "92",
        "81"
      ],
      "correct": 1,
      "kind": "sequence",
      "id": "iq_19"
    },
    {
      "q": "Qatorni davom ettir: 40, 35, 25, 10, ?",
      "a": [
        "-5",
        "5",
        "0",
        "-10"
      ],
      "correct": 3,
      "kind": "sequence",
      "id": "iq_20"
    },
    {
      "q": "Ali Bekdan baland. Bek Sardordan baland. Uchalasidan eng pasti kim?",
      "a": [
        "Ali",
        "Aniqlab bo‘lmaydi",
        "Bek",
        "Sardor"
      ],
      "correct": 3,
      "kind": "deduction",
      "id": "iq_21"
    },
    {
      "q": "Hech bir metall yog‘och emas. Mis metall. Qaysi xulosa majburiy?",
      "a": [
        "Mis yog‘och emas",
        "Mis faqat qizil",
        "Mis yog‘och bo‘lishi mumkin",
        "Mis suzadi"
      ],
      "correct": 0,
      "kind": "deduction",
      "id": "iq_22"
    },
    {
      "q": "Barcha L lar M. Hech bir M N emas. L haqida nima aniq?",
      "a": [
        "L lar N",
        "Hech narsa",
        "N lar L",
        "L lar N emas"
      ],
      "correct": 3,
      "kind": "deduction",
      "id": "iq_23"
    },
    {
      "q": "Faqat seshanba yoki payshanba kuni klub ochiq. Klub bugun ochiq. Qaysi xulosa to‘g‘ri?",
      "a": [
        "Bugun yakshanba",
        "Bugun dushanba",
        "Bugun juma",
        "Bugun seshanba yoki payshanba"
      ],
      "correct": 3,
      "kind": "deduction",
      "id": "iq_24"
    },
    {
      "q": "A, B dan oldin keladi. C, A dan keyin, B dan oldin keladi. Tartib qaysi?",
      "a": [
        "A-B-C",
        "B-C-A",
        "A-C-B",
        "C-A-B"
      ],
      "correct": 2,
      "kind": "deduction",
      "id": "iq_25"
    },
    {
      "q": "To‘rtta qutidan bittasida sovrin bor. 1, 2, 4 bo‘shligi ma’lum. Sovrin qayerda?",
      "a": [
        "1",
        "3",
        "2",
        "4"
      ],
      "correct": 1,
      "kind": "deduction",
      "id": "iq_26"
    },
    {
      "q": "Agar P > Q va Q = R bo‘lsa, qaysi biri aniq?",
      "a": [
        "P<R",
        "P>R",
        "R>P",
        "P=Q"
      ],
      "correct": 1,
      "kind": "deduction",
      "id": "iq_27"
    },
    {
      "q": "“Agar signal yashil bo‘lsa, eshik ochiladi.” Eshik ochilmadi. Nima aniq?",
      "a": [
        "Signal yashil bo‘lgan",
        "Signal qizil bo‘lgan",
        "Signal yashil bo‘lmagan",
        "Eshik buzilgan"
      ],
      "correct": 2,
      "kind": "deduction",
      "id": "iq_28"
    },
    {
      "q": "Uchta kitobdan qizil kitob ko‘kdan qalin, ko‘k esa yashildan qalin. Eng yupqasi qaysi?",
      "a": [
        "Aniqlab bo‘lmaydi",
        "Yashil",
        "Qizil",
        "Ko‘k"
      ],
      "correct": 1,
      "kind": "deduction",
      "id": "iq_29"
    },
    {
      "q": "Bir guruhdagi barcha talabalar ID olgan. Madina shu guruhda. Nima aniq?",
      "a": [
        "Madina o‘qituvchi",
        "Madina ID olgan",
        "Madina sardor",
        "Madina imtihondan o‘tgan"
      ],
      "correct": 1,
      "kind": "deduction",
      "id": "iq_30"
    },
    {
      "q": "Faqat bittasi rost: “A quti bo‘sh”, “B quti bo‘sh”, “C quti bo‘sh”. A va B bo‘sh emas. Qaysi gap rost?",
      "a": [
        "Uchoviyam yolg‘on",
        "B bo‘sh",
        "C bo‘sh",
        "A bo‘sh"
      ],
      "correct": 2,
      "kind": "deduction",
      "id": "iq_31"
    },
    {
      "q": "Diyor Kamoldan chapda. Kamol Javohirdan chapda. O‘rtada kim?",
      "a": [
        "Kamol",
        "Aniqlab bo‘lmaydi",
        "Javohir",
        "Diyor"
      ],
      "correct": 0,
      "kind": "deduction",
      "id": "iq_32"
    },
    {
      "q": "Barcha tez yuguruvchilar mashq qiladi. Sardor mashq qilmaydi. Nima aniq?",
      "a": [
        "Sardor sportchi emas",
        "Sardor yuguruvchi",
        "Sardor sekin",
        "Sardor tez yuguruvchi emas"
      ],
      "correct": 3,
      "kind": "deduction",
      "id": "iq_33"
    },
    {
      "q": "Agar karta qizil bo‘lsa, uning orqasida 7 bor. Karta orqasida 7 yo‘q. Qaysi xulosa to‘g‘ri?",
      "a": [
        "Karta ko‘k",
        "Karta qizil emas",
        "Karta qizil",
        "Raqam yo‘q"
      ],
      "correct": 1,
      "kind": "deduction",
      "id": "iq_34"
    },
    {
      "q": "To‘rtta uchrashuv: A B dan oldin, D C dan keyin, B D dan oldin. Qaysi tartib mumkin?",
      "a": [
        "A-C-D-B",
        "A-B-C-D",
        "C-A-B-D",
        "B-A-D-C"
      ],
      "correct": 1,
      "kind": "deduction",
      "id": "iq_35"
    },
    {
      "q": "Hech bir shirin taom achchiq emas. Ba’zi desertlar shirin. Qaysi xulosa aniq?",
      "a": [
        "Ba’zi desertlar achchiq emas",
        "Ba’zi desertlar achchiq",
        "Hech bir desert achchiq emas",
        "Barcha desertlar shirin"
      ],
      "correct": 0,
      "kind": "deduction",
      "id": "iq_36"
    },
    {
      "q": "Faqat bitta kalit eshikni ochadi. A ishlamadi, C ishlamadi. Qaysi kalit ochadi?",
      "a": [
        "Aniqlab bo‘lmaydi",
        "A",
        "C",
        "B"
      ],
      "correct": 3,
      "kind": "deduction",
      "id": "iq_37"
    },
    {
      "q": "X soni Y dan katta, Z esa X dan kichik. Y va Z haqida nima aniq?",
      "a": [
        "Y>Z",
        "Z>Y",
        "Aniqlab bo‘lmaydi",
        "Y=Z"
      ],
      "correct": 2,
      "kind": "deduction",
      "id": "iq_38"
    },
    {
      "q": "Biror odam “men kecha emas, bugun ham emas, ertaga ham emas ketaman” dedi. U qaysi kuni ketishi mumkin?",
      "a": [
        "Ertaga",
        "Bu ma’lumot yetarli emas",
        "Bugun",
        "Dushanba"
      ],
      "correct": 1,
      "kind": "deduction",
      "id": "iq_39"
    },
    {
      "q": "Agar barcha A lar B va barcha B lar C bo‘lsa, qaysi xulosa majburiy?",
      "a": [
        "C lar A",
        "B lar A",
        "A lar B emas",
        "A lar C"
      ],
      "correct": 3,
      "kind": "deduction",
      "id": "iq_40"
    },
    {
      "q": "Bir sonning 30% i 24. Sonning o‘zi nechaga teng?",
      "a": [
        "60",
        "96",
        "80",
        "72"
      ],
      "correct": 2,
      "kind": "quant",
      "id": "iq_41"
    },
    {
      "q": "3 ta daftar 18 000 so‘m. 7 ta daftar shu narxda qancha?",
      "a": [
        "36 000",
        "42 000",
        "54 000",
        "48 000"
      ],
      "correct": 1,
      "kind": "quant",
      "id": "iq_42"
    },
    {
      "q": "120 km yo‘lning 35% i bosib o‘tildi. Necha km qoldi?",
      "a": [
        "85",
        "78",
        "42",
        "65"
      ],
      "correct": 1,
      "kind": "quant",
      "id": "iq_43"
    },
    {
      "q": "Bir mahsulot 250 000 so‘m. 20% chegirmadan keyin narxi?",
      "a": [
        "210 000",
        "180 000",
        "190 000",
        "200 000"
      ],
      "correct": 3,
      "kind": "quant",
      "id": "iq_44"
    },
    {
      "q": "4 ishchi ishni 15 kunda tugatsa, ishchilar soni 6 bo‘lsa, tezlik bir xil deb necha kun?",
      "a": [
        "14",
        "12",
        "10",
        "8"
      ],
      "correct": 2,
      "kind": "quant",
      "id": "iq_45"
    },
    {
      "q": "2:3 nisbatdagi ikki son yig‘indisi 55. Katta son?",
      "a": [
        "35",
        "22",
        "30",
        "33"
      ],
      "correct": 3,
      "kind": "quant",
      "id": "iq_46"
    },
    {
      "q": "Ketma-ket uchta juft son yig‘indisi 42. Eng kattasi?",
      "a": [
        "14",
        "18",
        "20",
        "16"
      ],
      "correct": 3,
      "kind": "quant",
      "id": "iq_47"
    },
    {
      "q": "Bir idishning 3/4 qismi 18 litr. To‘liq sig‘im?",
      "a": [
        "24",
        "27",
        "20",
        "22"
      ],
      "correct": 0,
      "kind": "quant",
      "id": "iq_48"
    },
    {
      "q": "Soat 09:45 dan 2 soat 35 daqiqa keyin vaqt?",
      "a": [
        "12:10",
        "12:20",
        "11:20",
        "12:30"
      ],
      "correct": 1,
      "kind": "quant",
      "id": "iq_49"
    },
    {
      "q": "5 ta mashina 5 daqiqada 25 detal tayyorlaydi. Shu tezlikda 1 mashina 5 daqiqada nechta?",
      "a": [
        "10",
        "25",
        "5",
        "4"
      ],
      "correct": 2,
      "kind": "quant",
      "id": "iq_50"
    },
    {
      "q": "Bir sinfda 28 o‘quvchi bor. 3/7 qismi qizlar. O‘g‘il bolalar nechta?",
      "a": [
        "16",
        "12",
        "18",
        "14"
      ],
      "correct": 0,
      "kind": "quant",
      "id": "iq_51"
    },
    {
      "q": "80 ning 15% i bilan 60 ning 20% i yig‘indisi?",
      "a": [
        "28",
        "20",
        "24",
        "32"
      ],
      "correct": 2,
      "kind": "quant",
      "id": "iq_52"
    },
    {
      "q": "Bir yo‘lning 2/5 qismi 16 km. To‘liq yo‘l?",
      "a": [
        "45",
        "36",
        "32",
        "40"
      ],
      "correct": 3,
      "kind": "quant",
      "id": "iq_53"
    },
    {
      "q": "A soni B dan 12 ga katta. A+B=58. A nechaga teng?",
      "a": [
        "23",
        "29",
        "35",
        "41"
      ],
      "correct": 2,
      "kind": "quant",
      "id": "iq_54"
    },
    {
      "q": "Bir kitob 240 bet. Kuniga 30 bet o‘qilsa necha kunda tugaydi?",
      "a": [
        "7",
        "6",
        "8",
        "9"
      ],
      "correct": 2,
      "kind": "quant",
      "id": "iq_55"
    },
    {
      "q": "Avtomobil 72 km/soat tezlikda 25 daqiqa yurdi. Masofa?",
      "a": [
        "36",
        "24",
        "30",
        "42"
      ],
      "correct": 2,
      "kind": "quant",
      "id": "iq_56"
    },
    {
      "q": "Bir son 4 ga bo‘linib, natijaga 7 qo‘shilsa 19 chiqadi. Son?",
      "a": [
        "36",
        "42",
        "48",
        "52"
      ],
      "correct": 1,
      "kind": "quant",
      "id": "iq_57"
    },
    {
      "q": "45 daqiqaning 2/3 qismi necha daqiqa?",
      "a": [
        "25",
        "35",
        "20",
        "30"
      ],
      "correct": 3,
      "kind": "quant",
      "id": "iq_58"
    },
    {
      "q": "Bir mahsulot 160 000 so‘mdan 184 000 so‘mga oshdi. Necha foiz oshdi?",
      "a": [
        "15%",
        "10%",
        "20%",
        "12%"
      ],
      "correct": 0,
      "kind": "quant",
      "id": "iq_59"
    },
    {
      "q": "8 kishilik stolga 3 ta shunday stol qo‘yilsa, jami nechta o‘rin?",
      "a": [
        "27",
        "18",
        "24",
        "21"
      ],
      "correct": 2,
      "kind": "quant",
      "id": "iq_60"
    },
    {
      "q": "KITOB : O‘QISH = QAYCHI : ?",
      "a": [
        "Kesish",
        "O‘lchash",
        "Chizish",
        "Yopish"
      ],
      "correct": 0,
      "kind": "analogy",
      "id": "iq_61"
    },
    {
      "q": "KALIT : QULF = PAROL : ?",
      "a": [
        "Akkount",
        "Ruchka",
        "Stol",
        "Deraza"
      ],
      "correct": 0,
      "kind": "analogy",
      "id": "iq_62"
    },
    {
      "q": "TERMOMETR : HARORAT = TAROZI : ?",
      "a": [
        "Vaqt",
        "Masofa",
        "Tezlik",
        "Og‘irlik"
      ],
      "correct": 3,
      "kind": "analogy",
      "id": "iq_63"
    },
    {
      "q": "YURAK : QON = NASOS : ?",
      "a": [
        "Tuproq",
        "Havo",
        "Suv",
        "Yorug‘lik"
      ],
      "correct": 2,
      "kind": "analogy",
      "id": "iq_64"
    },
    {
      "q": "XARITA : YO‘L = LUG‘AT : ?",
      "a": [
        "So‘z",
        "Ovqat",
        "Rasm",
        "Musiqa"
      ],
      "correct": 0,
      "kind": "analogy",
      "id": "iq_65"
    },
    {
      "q": "QALAM : YOZISH = KAMERA : ?",
      "a": [
        "Kesish",
        "O‘lchash",
        "Tinglash",
        "Suratga olish"
      ],
      "correct": 3,
      "kind": "analogy",
      "id": "iq_66"
    },
    {
      "q": "SHIFOKOR : BEMOR = USTA : ?",
      "a": [
        "Asbob",
        "Devor",
        "Mijoz",
        "Pul"
      ],
      "correct": 2,
      "kind": "analogy",
      "id": "iq_67"
    },
    {
      "q": "URUG‘ : O‘SIMLIK = TUXUM : ?",
      "a": [
        "Tosh",
        "Suv",
        "Metall",
        "Hayvon"
      ],
      "correct": 3,
      "kind": "analogy",
      "id": "iq_68"
    },
    {
      "q": "DARAxt : O‘RMON = YULDUZ : ?",
      "a": [
        "Daryo",
        "Tosh",
        "Osmon",
        "Uy"
      ],
      "correct": 2,
      "kind": "analogy",
      "id": "iq_69"
    },
    {
      "q": "SOAT : VAQT = KOMPAS : ?",
      "a": [
        "Harorat",
        "Hajm",
        "Og‘irlik",
        "Yo‘nalish"
      ],
      "correct": 3,
      "kind": "analogy",
      "id": "iq_70"
    },
    {
      "q": "SAVOL : JAVOB = MUAMMO : ?",
      "a": [
        "Ye chim",
        "Qoida",
        "Sabab",
        "Vaqt"
      ],
      "correct": 0,
      "kind": "analogy",
      "id": "iq_71"
    },
    {
      "q": "BOSH : SHAPKA = OYOQ : ?",
      "a": [
        "Ko‘ylak",
        "Poyabzal",
        "Qo‘lqop",
        "Kamar"
      ],
      "correct": 1,
      "kind": "analogy",
      "id": "iq_72"
    },
    {
      "q": "ASALARI : UYA = QUSH : ?",
      "a": [
        "Qum",
        "Suv",
        "Daraxt",
        "Uya"
      ],
      "correct": 3,
      "kind": "analogy",
      "id": "iq_73"
    },
    {
      "q": "MOTOR : MASHINA = YURAK : ?",
      "a": [
        "Kitob",
        "Uy",
        "Organizm",
        "Ko‘cha"
      ],
      "correct": 2,
      "kind": "analogy",
      "id": "iq_74"
    },
    {
      "q": "DAqiqa : SOAT = SANTIMETR : ?",
      "a": [
        "Metr",
        "Kilogramm",
        "Litr",
        "Sekund"
      ],
      "correct": 0,
      "kind": "analogy",
      "id": "iq_75"
    },
    {
      "q": "YORUG‘LIK : KO‘RISH = OVOZ : ?",
      "a": [
        "Ta’m bilish",
        "Hid bilish",
        "Eshitish",
        "Ushlash"
      ],
      "correct": 2,
      "kind": "analogy",
      "id": "iq_76"
    },
    {
      "q": "QOIDA : O‘YIN = QONUN : ?",
      "a": [
        "Rasm",
        "Jamoa",
        "Jamiyat",
        "Kitob"
      ],
      "correct": 2,
      "kind": "analogy",
      "id": "iq_77"
    },
    {
      "q": "MASHQ : KUCH = O‘QISH : ?",
      "a": [
        "Shovqin",
        "Charchoq",
        "Bilim",
        "Uyqu"
      ],
      "correct": 2,
      "kind": "analogy",
      "id": "iq_78"
    },
    {
      "q": "QULF : XAVFSIZLIK = SOYABON : ?",
      "a": [
        "Yomg‘ir",
        "Tezlik",
        "Ovoz",
        "Issiqlik"
      ],
      "correct": 0,
      "kind": "analogy",
      "id": "iq_79"
    },
    {
      "q": "RETSEPT : OSHPAZ = REJA : ?",
      "a": [
        "Arxitektor",
        "Sportchi",
        "Haydovchi",
        "Musiqachi"
      ],
      "correct": 0,
      "kind": "analogy",
      "id": "iq_80"
    },
    {
      "q": "Bir xonada 4 burchak bor. Har burchakda bittadan mushuk. Jami mushuk nechta?",
      "a": [
        "8",
        "16",
        "4",
        "12"
      ],
      "correct": 2,
      "kind": "trick",
      "id": "iq_81"
    },
    {
      "q": "5 ta sham yonib turibdi. 2 tasi o‘chirildi. Xonada nechta sham qoladi?",
      "a": [
        "5",
        "3",
        "2",
        "0"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_82"
    },
    {
      "q": "Bir odam 10-qavatdan lift bilan tushdi, lekin qaytishda 7-qavatda tushib piyoda chiqdi. Nega?",
      "a": [
        "U 7-qavatda yashaydi",
        "Lift buzildi",
        "Zinani yaxshi ko‘radi",
        "Bo‘yi yetmadi"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_83"
    },
    {
      "q": "Ikki ota va ikki o‘g‘il uchta olmani teng bo‘lib oldi. Har biri bittadan oldi. Necha kishi edi?",
      "a": [
        "3",
        "4"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_84"
    },
    {
      "q": "Bir oilada 3 qiz bor, har qizning bitta akasi bor. Oilada nechta farzand?",
      "a": [
        "7",
        "3",
        "4",
        "6"
      ],
      "correct": 2,
      "kind": "trick",
      "id": "iq_85"
    },
    {
      "q": "Soat 12 da yomg‘ir yog‘moqda. 72 soatdan keyin quyosh chiqishi mumkinmi?",
      "a": [
        "Ma’lumot yetarli emas",
        "Faqat yozda",
        "Ha",
        "Yo‘q"
      ],
      "correct": 2,
      "kind": "trick",
      "id": "iq_86"
    },
    {
      "q": "Bir poygada sen ikkinchi o‘rindagi odamni quvib o‘tding. Hozir nechanchi o‘rindasan?",
      "a": [
        "3",
        "4",
        "2",
        "1"
      ],
      "correct": 2,
      "kind": "trick",
      "id": "iq_87"
    },
    {
      "q": "Bir daraxtda 10 qush bor edi. Ovchi bitta o‘q uzdi. Daraxtda nechta qush qolishi mumkin?",
      "a": [
        "0",
        "10",
        "9",
        "1"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_88"
    },
    {
      "q": "1 kg temir va 1 kg paxta qaysi biri og‘ir?",
      "a": [
        "Paxta",
        "Ikkalasi teng",
        "Temir"
      ],
      "correct": 1,
      "kind": "trick",
      "id": "iq_89"
    },
    {
      "q": "Bir haftada nechta kunning nomida “a” harfi bor?",
      "a": [
        "5",
        "6",
        "7",
        "3"
      ],
      "correct": 2,
      "kind": "trick",
      "id": "iq_90"
    },
    {
      "q": "3 ta xona bor, har birida 2 ta chiroq. Jami nechta chiroq?",
      "a": [
        "6",
        "7",
        "5",
        "8"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_91"
    },
    {
      "q": "Bir sonni o‘ziga qo‘shsang 18 chiqadi. Son?",
      "a": [
        "9",
        "8",
        "10"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_92"
    },
    {
      "q": "Ketma-ket 5 ta raqam yig‘indisi 25. Ular 3,4,5,6,7 bo‘lishi mumkinmi?",
      "a": [
        "Ha",
        "Faqat juft bo‘lsa",
        "Yo‘q",
        "Faqat toq bo‘lsa"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_93"
    },
    {
      "q": "Bir quti 6 tomonga ega. Har tomoni kvadrat. Bu nima?",
      "a": [
        "Silindr",
        "Shar",
        "Kub",
        "Konus"
      ],
      "correct": 2,
      "kind": "trick",
      "id": "iq_94"
    },
    {
      "q": "Bir oilada 2 aka-uka va ularning 2 singlisi bor. Jami farzand nechta?",
      "a": [
        "3",
        "6",
        "2",
        "4"
      ],
      "correct": 3,
      "kind": "trick",
      "id": "iq_95"
    },
    {
      "q": "Agar bugun chorshanba bo‘lsa, 10 kundan keyin qaysi kun?",
      "a": [
        "Dushanba",
        "Shanba",
        "Yakshanba",
        "Juma"
      ],
      "correct": 1,
      "kind": "trick",
      "id": "iq_96"
    },
    {
      "q": "Bir son 0 ga ko‘paytirildi. Natija 15 bo‘lishi mumkinmi?",
      "a": [
        "Yo‘q",
        "Ha"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_97"
    },
    {
      "q": "Qaysi biri boshqalardan farq qiladi?",
      "a": [
        "Nok",
        "Olma",
        "Shaftoli",
        "Sabzi"
      ],
      "correct": 3,
      "kind": "trick",
      "id": "iq_98"
    },
    {
      "q": "Qaysi so‘z mantiqan boshqalardan farq qiladi?",
      "a": [
        "Yanvar",
        "Chorshanba",
        "Dushanba",
        "Seshanba"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_99"
    },
    {
      "q": "Agar 4 ta odam bir-biri bilan bir martadan qo‘l berib ko‘rishsa, jami nechta qo‘l siqish?",
      "a": [
        "6",
        "5",
        "4",
        "8"
      ],
      "correct": 0,
      "kind": "trick",
      "id": "iq_100"
    }
  ],
  "speed": [
    {
      "q": "27 + 38",
      "a": [
        "63",
        "66",
        "64",
        "65"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_1"
    },
    {
      "q": "94 − 57",
      "a": [
        "36",
        "37",
        "38",
        "47"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_2"
    },
    {
      "q": "16 × 7",
      "a": [
        "112",
        "124",
        "102",
        "96"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_3"
    },
    {
      "q": "144 ÷ 12",
      "a": [
        "12",
        "14",
        "16",
        "10"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_4"
    },
    {
      "q": "25% of 80",
      "a": [
        "15",
        "30",
        "20",
        "25"
      ],
      "correct": 2,
      "kind": "rapid_math",
      "id": "speed_5"
    },
    {
      "q": "19 + 26",
      "a": [
        "45",
        "47",
        "44",
        "46"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_6"
    },
    {
      "q": "72 − 38",
      "a": [
        "34",
        "32",
        "36",
        "30"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_7"
    },
    {
      "q": "13 × 8",
      "a": [
        "104",
        "112",
        "96",
        "108"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_8"
    },
    {
      "q": "225 ÷ 15",
      "a": [
        "20",
        "15",
        "18",
        "12"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_9"
    },
    {
      "q": "15% of 200",
      "a": [
        "35",
        "30",
        "40",
        "25"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_10"
    },
    {
      "q": "48 + 57",
      "a": [
        "100",
        "95",
        "115",
        "105"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_11"
    },
    {
      "q": "91 − 46",
      "a": [
        "44",
        "45",
        "46",
        "55"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_12"
    },
    {
      "q": "17 × 6",
      "a": [
        "108",
        "96",
        "112",
        "102"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_13"
    },
    {
      "q": "168 ÷ 14",
      "a": [
        "11",
        "14",
        "16",
        "12"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_14"
    },
    {
      "q": "35% of 60",
      "a": [
        "20",
        "24",
        "21",
        "18"
      ],
      "correct": 2,
      "kind": "rapid_math",
      "id": "speed_15"
    },
    {
      "q": "64 + 29",
      "a": [
        "94",
        "92",
        "93",
        "95"
      ],
      "correct": 2,
      "kind": "rapid_math",
      "id": "speed_16"
    },
    {
      "q": "83 − 29",
      "a": [
        "52",
        "56",
        "64",
        "54"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_17"
    },
    {
      "q": "14 × 9",
      "a": [
        "126",
        "136",
        "116",
        "124"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_18"
    },
    {
      "q": "196 ÷ 14",
      "a": [
        "16",
        "12",
        "18",
        "14"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_19"
    },
    {
      "q": "12.5% of 80",
      "a": [
        "10",
        "8",
        "15",
        "12"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_20"
    },
    {
      "q": "Qaysi katta?",
      "a": [
        "0.67",
        "0.7",
        "0.607",
        "0.69"
      ],
      "correct": 1,
      "kind": "rapid_compare",
      "id": "speed_21"
    },
    {
      "q": "Qaysi kichik?",
      "a": [
        "0.72",
        "3/4",
        "0.8",
        "0.76"
      ],
      "correct": 0,
      "kind": "rapid_compare",
      "id": "speed_22"
    },
    {
      "q": "Qaysi son 9 ga bo‘linadi?",
      "a": [
        "151",
        "142",
        "135",
        "124"
      ],
      "correct": 2,
      "kind": "rapid_compare",
      "id": "speed_23"
    },
    {
      "q": "Qaysi son juft?",
      "a": [
        "701",
        "582",
        "317"
      ],
      "correct": 1,
      "kind": "rapid_compare",
      "id": "speed_24"
    },
    {
      "q": "Qaysi kasr eng katta?",
      "a": [
        "7/12",
        "5/9",
        "1/2",
        "3/5"
      ],
      "correct": 3,
      "kind": "rapid_compare",
      "id": "speed_25"
    },
    {
      "q": "Qaysi qiymat 0.25 ga teng?",
      "a": [
        "3/8",
        "1/2",
        "1/4",
        "2/5"
      ],
      "correct": 2,
      "kind": "rapid_compare",
      "id": "speed_26"
    },
    {
      "q": "Qaysi son 3 va 5 ga ham bo‘linadi?",
      "a": [
        "42",
        "25",
        "35",
        "30"
      ],
      "correct": 3,
      "kind": "rapid_compare",
      "id": "speed_27"
    },
    {
      "q": "Qaysi biri eng kichik?",
      "a": [
        "0.9",
        "0.09",
        "0.109",
        "0.19"
      ],
      "correct": 1,
      "kind": "rapid_compare",
      "id": "speed_28"
    },
    {
      "q": "Qaysi juftlik yig‘indisi 100?",
      "a": [
        "44+57",
        "39+62",
        "47+52",
        "42+58"
      ],
      "correct": 3,
      "kind": "rapid_compare",
      "id": "speed_29"
    },
    {
      "q": "Qaysi ko‘paytma 72?",
      "a": [
        "9×7",
        "6×11",
        "8×9",
        "7×10"
      ],
      "correct": 2,
      "kind": "rapid_compare",
      "id": "speed_30"
    },
    {
      "q": "Qaysi vaqt oldin?",
      "a": [
        "08:15",
        "08:05",
        "08:50",
        "08:40"
      ],
      "correct": 1,
      "kind": "rapid_time",
      "id": "speed_31"
    },
    {
      "q": "Qaysi vaqt kechroq?",
      "a": [
        "17:15",
        "17:30",
        "17:45",
        "17:05"
      ],
      "correct": 2,
      "kind": "rapid_time",
      "id": "speed_32"
    },
    {
      "q": "45 daqiqadan keyin 10:20 bo‘lsa, hozir?",
      "a": [
        "09:35",
        "09:45",
        "10:05",
        "09:25"
      ],
      "correct": 0,
      "kind": "rapid_time",
      "id": "speed_33"
    },
    {
      "q": "20 daqiqa oldin 14:10 bo‘lgan vaqt?",
      "a": [
        "14:30",
        "14:00",
        "13:50",
        "13:40"
      ],
      "correct": 2,
      "kind": "rapid_time",
      "id": "speed_34"
    },
    {
      "q": "Bir soat 20 daqiqa = ?",
      "a": [
        "100 min",
        "90 min",
        "80 min",
        "70 min"
      ],
      "correct": 2,
      "kind": "rapid_time",
      "id": "speed_35"
    },
    {
      "q": "150 soniya = ?",
      "a": [
        "2 min",
        "2 min 30 s",
        "3 min",
        "2 min 10 s"
      ],
      "correct": 1,
      "kind": "rapid_time",
      "id": "speed_36"
    },
    {
      "q": "Qaysi qatorda faqat undoshlar bor?",
      "a": [
        "a,b,k",
        "b,d,k",
        "s,e,n",
        "m,o,t"
      ],
      "correct": 1,
      "kind": "attention",
      "id": "speed_37"
    },
    {
      "q": "Qaysi so‘zda 2 ta “a” bor?",
      "a": [
        "qalam",
        "daraxt",
        "samarali",
        "kitob"
      ],
      "correct": 2,
      "kind": "attention",
      "id": "speed_38"
    },
    {
      "q": "“ZAKO” so‘zida nechta harf bor?",
      "a": [
        "4",
        "3",
        "6",
        "5"
      ],
      "correct": 0,
      "kind": "attention",
      "id": "speed_39"
    },
    {
      "q": "“Maktab” so‘zida nechta unli bor?",
      "a": [
        "4",
        "1",
        "2",
        "3"
      ],
      "correct": 2,
      "kind": "attention",
      "id": "speed_40"
    },
    {
      "q": "Qaysi belgi boshqalardan farq qiladi?",
      "a": [
        "△",
        "△",
        "△",
        "▲"
      ],
      "correct": 3,
      "kind": "attention",
      "id": "speed_41"
    },
    {
      "q": "Qaysi son ketma-ketlikni buzadi: 2,4,6,9,10?",
      "a": [
        "2",
        "6",
        "10",
        "9"
      ],
      "correct": 3,
      "kind": "attention",
      "id": "speed_42"
    },
    {
      "q": "Qaysi so‘z alifbo bo‘yicha birinchi?",
      "a": [
        "shaftoli",
        "uzum",
        "olma",
        "anor"
      ],
      "correct": 3,
      "kind": "attention",
      "id": "speed_43"
    },
    {
      "q": "Qaysi son 50 dan katta va 60 dan kichik?",
      "a": [
        "70",
        "51",
        "61",
        "49"
      ],
      "correct": 1,
      "kind": "attention",
      "id": "speed_44"
    },
    {
      "q": "Qaysi juftlik bir xil qiymatga ega?",
      "a": [
        "9×6 va 56",
        "7×8 va 54",
        "6×7 va 42",
        "8×5 va 45"
      ],
      "correct": 2,
      "kind": "attention",
      "id": "speed_45"
    },
    {
      "q": "Qaysi javobda barcha sonlar toq?",
      "a": [
        "2,5,7",
        "7,8,11",
        "3,5,9",
        "1,4,9"
      ],
      "correct": 2,
      "kind": "attention",
      "id": "speed_46"
    },
    {
      "q": "Bir qo‘lda 5 barmoq. Ikki qo‘lda?",
      "a": [
        "12",
        "9",
        "10",
        "8"
      ],
      "correct": 2,
      "kind": "rapid_logic",
      "id": "speed_47"
    },
    {
      "q": "3 ta uchburchakning jami burchaklari?",
      "a": [
        "15",
        "6",
        "9",
        "12"
      ],
      "correct": 2,
      "kind": "rapid_logic",
      "id": "speed_48"
    },
    {
      "q": "2 ta soat 120 daqiqami?",
      "a": [
        "Ha",
        "Yo‘q"
      ],
      "correct": 0,
      "kind": "rapid_logic",
      "id": "speed_49"
    },
    {
      "q": "Bir o‘nlikda nechta birlik bor?",
      "a": [
        "10",
        "12",
        "5",
        "8"
      ],
      "correct": 0,
      "kind": "rapid_logic",
      "id": "speed_50"
    },
    {
      "q": "4 ning kvadrati?",
      "a": [
        "8",
        "12",
        "20",
        "16"
      ],
      "correct": 3,
      "kind": "rapid_logic",
      "id": "speed_51"
    },
    {
      "q": "81 ning ildizi?",
      "a": [
        "10",
        "7",
        "8",
        "9"
      ],
      "correct": 3,
      "kind": "rapid_logic",
      "id": "speed_52"
    },
    {
      "q": "7×7 − 10 = ?",
      "a": [
        "29",
        "39",
        "49",
        "41"
      ],
      "correct": 1,
      "kind": "rapid_logic",
      "id": "speed_53"
    },
    {
      "q": "1000 − 1 = ?",
      "a": [
        "990",
        "1001",
        "909",
        "999"
      ],
      "correct": 3,
      "kind": "rapid_logic",
      "id": "speed_54"
    },
    {
      "q": "Bir yarim soat necha daqiqa?",
      "a": [
        "75",
        "120",
        "90"
      ],
      "correct": 2,
      "kind": "rapid_logic",
      "id": "speed_55"
    },
    {
      "q": "2.5 + 1.5 = ?",
      "a": [
        "3",
        "4.5",
        "4",
        "5"
      ],
      "correct": 2,
      "kind": "rapid_logic",
      "id": "speed_56"
    },
    {
      "q": "18+47",
      "a": [
        "66",
        "67",
        "64",
        "65"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_57"
    },
    {
      "q": "76−28",
      "a": [
        "46",
        "48",
        "58",
        "50"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_58"
    },
    {
      "q": "11×9",
      "a": [
        "89",
        "109",
        "99",
        "101"
      ],
      "correct": 2,
      "kind": "rapid_math",
      "id": "speed_59"
    },
    {
      "q": "132÷11",
      "a": [
        "11",
        "12",
        "13",
        "14"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_60"
    },
    {
      "q": "40% of 90",
      "a": [
        "40",
        "45",
        "30",
        "36"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_61"
    },
    {
      "q": "23+19",
      "a": [
        "41",
        "42",
        "44",
        "43"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_62"
    },
    {
      "q": "100−63",
      "a": [
        "37",
        "38",
        "47",
        "36"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_63"
    },
    {
      "q": "12×12",
      "a": [
        "154",
        "134",
        "144",
        "124"
      ],
      "correct": 2,
      "kind": "rapid_math",
      "id": "speed_64"
    },
    {
      "q": "175÷25",
      "a": [
        "7",
        "9",
        "6",
        "8"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_65"
    },
    {
      "q": "5% of 300",
      "a": [
        "25",
        "15",
        "20",
        "10"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_66"
    },
    {
      "q": "54+39",
      "a": [
        "93",
        "94",
        "92",
        "95"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_67"
    },
    {
      "q": "88−49",
      "a": [
        "39",
        "38",
        "40",
        "41"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_68"
    },
    {
      "q": "15×8",
      "a": [
        "130",
        "125",
        "120",
        "110"
      ],
      "correct": 2,
      "kind": "rapid_math",
      "id": "speed_69"
    },
    {
      "q": "210÷15",
      "a": [
        "16",
        "14",
        "12",
        "15"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_70"
    },
    {
      "q": "60% of 50",
      "a": [
        "30",
        "40",
        "25",
        "35"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_71"
    },
    {
      "q": "47+28",
      "a": [
        "74",
        "77",
        "76",
        "75"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_72"
    },
    {
      "q": "73−38",
      "a": [
        "45",
        "35",
        "36",
        "34"
      ],
      "correct": 1,
      "kind": "rapid_math",
      "id": "speed_73"
    },
    {
      "q": "18×5",
      "a": [
        "100",
        "80",
        "95",
        "90"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_74"
    },
    {
      "q": "240÷16",
      "a": [
        "15",
        "18",
        "14",
        "16"
      ],
      "correct": 0,
      "kind": "rapid_math",
      "id": "speed_75"
    },
    {
      "q": "75% of 40",
      "a": [
        "20",
        "35",
        "25",
        "30"
      ],
      "correct": 3,
      "kind": "rapid_math",
      "id": "speed_76"
    },
    {
      "q": "Qaysi biri 1 ga eng yaqin?",
      "a": [
        "1.09",
        "1.2",
        "0.91",
        "0.99"
      ],
      "correct": 3,
      "kind": "rapid_compare",
      "id": "speed_77"
    },
    {
      "q": "Qaysi son 100 dan 25% kichik?",
      "a": [
        "85",
        "75",
        "80",
        "70"
      ],
      "correct": 1,
      "kind": "rapid_compare",
      "id": "speed_78"
    },
    {
      "q": "Qaysi juftlikda ikkinchi son birinchidan 10 katta?",
      "a": [
        "14,24",
        "21,32",
        "30,39",
        "17,26"
      ],
      "correct": 0,
      "kind": "rapid_compare",
      "id": "speed_79"
    },
    {
      "q": "Qaysi so‘z 5 harfdan iborat?",
      "a": [
        "kitob",
        "qalam",
        "olma",
        "daraxt"
      ],
      "correct": 0,
      "kind": "attention",
      "id": "speed_80"
    },
    {
      "q": "“tezlik” so‘zida nechta undosh bor?",
      "a": [
        "5",
        "6",
        "4",
        "3"
      ],
      "correct": 2,
      "kind": "attention",
      "id": "speed_81"
    },
    {
      "q": "Qaysi sonning raqamlari yig‘indisi 9?",
      "a": [
        "522",
        "421",
        "234",
        "315"
      ],
      "correct": 2,
      "kind": "attention",
      "id": "speed_82"
    },
    {
      "q": "Qaysi qiymat 2.4 dan kichik?",
      "a": [
        "2.04",
        "2.44",
        "3.1",
        "2.8"
      ],
      "correct": 0,
      "kind": "rapid_compare",
      "id": "speed_83"
    },
    {
      "q": "7+8×2 = ?",
      "a": [
        "22",
        "30",
        "16",
        "23"
      ],
      "correct": 3,
      "kind": "rapid_logic",
      "id": "speed_84"
    },
    {
      "q": "(18−6)÷3 = ?",
      "a": [
        "4",
        "8",
        "6",
        "2"
      ],
      "correct": 0,
      "kind": "rapid_logic",
      "id": "speed_85"
    },
    {
      "q": "5² − 4 = ?",
      "a": [
        "21",
        "31",
        "29",
        "25"
      ],
      "correct": 0,
      "kind": "rapid_logic",
      "id": "speed_86"
    },
    {
      "q": "56+17−9 = ?",
      "a": [
        "64",
        "63",
        "66",
        "65"
      ],
      "correct": 0,
      "kind": "rapid_logic",
      "id": "speed_87"
    },
    {
      "q": "9×8+4 = ?",
      "a": [
        "80",
        "68",
        "72",
        "76"
      ],
      "correct": 3,
      "kind": "rapid_logic",
      "id": "speed_88"
    },
    {
      "q": "144−48÷6 = ?",
      "a": [
        "136",
        "120",
        "16",
        "96"
      ],
      "correct": 0,
      "kind": "rapid_logic",
      "id": "speed_89"
    },
    {
      "q": "Qaysi biri 3.5 dan katta?",
      "a": [
        "3.49",
        "3.51",
        "3.15",
        "3.05"
      ],
      "correct": 1,
      "kind": "rapid_compare",
      "id": "speed_90"
    },
    {
      "q": "Qaysi son 4 ga bo‘linadi?",
      "a": [
        "124",
        "118",
        "126",
        "130"
      ],
      "correct": 0,
      "kind": "rapid_compare",
      "id": "speed_91"
    },
    {
      "q": "Qaysi qiymat 75% ga teng?",
      "a": [
        "0.85",
        "0.75",
        "0.65",
        "0.57"
      ],
      "correct": 1,
      "kind": "rapid_compare",
      "id": "speed_92"
    },
    {
      "q": "Qaysi juftlikda ayirma 12?",
      "a": [
        "35,23",
        "51,40",
        "42,29",
        "60,49"
      ],
      "correct": 0,
      "kind": "rapid_compare",
      "id": "speed_93"
    },
    {
      "q": "“maktab” so‘zining oxirgi harfi?",
      "a": [
        "b",
        "t",
        "a",
        "m"
      ],
      "correct": 0,
      "kind": "attention",
      "id": "speed_94"
    },
    {
      "q": "Qaysi qatorda sonlar kamayib boradi?",
      "a": [
        "3,4,2",
        "5,2,4",
        "9,7,5",
        "8,6,7"
      ],
      "correct": 2,
      "kind": "attention",
      "id": "speed_95"
    },
    {
      "q": "Qaysi son 2 ga ham, 3 ga ham bo‘linadi?",
      "a": [
        "25",
        "18",
        "31",
        "14"
      ],
      "correct": 1,
      "kind": "rapid_compare",
      "id": "speed_96"
    },
    {
      "q": "2×(7+3) = ?",
      "a": [
        "21",
        "20",
        "17",
        "24"
      ],
      "correct": 1,
      "kind": "rapid_logic",
      "id": "speed_97"
    },
    {
      "q": "36÷6+8 = ?",
      "a": [
        "14",
        "18",
        "12",
        "16"
      ],
      "correct": 0,
      "kind": "rapid_logic",
      "id": "speed_98"
    },
    {
      "q": "0.4 + 0.35 = ?",
      "a": [
        "0.65",
        "0.75",
        "0.85",
        "0.95"
      ],
      "correct": 1,
      "kind": "rapid_logic",
      "id": "speed_99"
    },
    {
      "q": "Bir chorak soat necha daqiqa?",
      "a": [
        "15",
        "10",
        "20"
      ],
      "correct": 0,
      "kind": "rapid_time",
      "id": "speed_100"
    }
  ],
  "memory": [
    {
      "q": "Yodlab oling: anor, ko‘prik, qalam, oyna, soat, daryo. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "ko‘prik",
        "daryo",
        "anor",
        "oyna"
      ],
      "correct": 2,
      "kind": "word_position",
      "memory_prompt": "anor, ko‘prik, qalam, oyna, soat, daryo",
      "id": "memory_1"
    },
    {
      "q": "Yodlab oling: ko‘prik, qalam, oyna, soat, daryo, bulut. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "soat",
        "oyna",
        "daryo",
        "ko‘prik"
      ],
      "correct": 0,
      "kind": "word_position",
      "memory_prompt": "ko‘prik, qalam, oyna, soat, daryo, bulut",
      "id": "memory_2"
    },
    {
      "q": "Yodlab oling: qalam, oyna, soat, daryo, bulut, kalit. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "oyna",
        "daryo",
        "kalit",
        "qalam"
      ],
      "correct": 3,
      "kind": "word_position",
      "memory_prompt": "qalam, oyna, soat, daryo, bulut, kalit",
      "id": "memory_3"
    },
    {
      "q": "Yodlab oling: oyna, soat, daryo, bulut, kalit, non. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "kalit",
        "bulut",
        "oyna",
        "daryo"
      ],
      "correct": 1,
      "kind": "word_position",
      "memory_prompt": "oyna, soat, daryo, bulut, kalit, non",
      "id": "memory_4"
    },
    {
      "q": "Yodlab oling: soat, daryo, bulut, kalit, non, kitob. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "daryo",
        "soat",
        "kitob",
        "kalit"
      ],
      "correct": 1,
      "kind": "word_position",
      "memory_prompt": "soat, daryo, bulut, kalit, non, kitob",
      "id": "memory_5"
    },
    {
      "q": "Yodlab oling: daryo, bulut, kalit, non, kitob, olma. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "kalit",
        "daryo",
        "kitob",
        "non"
      ],
      "correct": 3,
      "kind": "word_position",
      "memory_prompt": "daryo, bulut, kalit, non, kitob, olma",
      "id": "memory_6"
    },
    {
      "q": "Yodlab oling: bulut, kalit, non, kitob, olma, sham. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "kitob",
        "bulut",
        "sham",
        "kalit"
      ],
      "correct": 1,
      "kind": "word_position",
      "memory_prompt": "bulut, kalit, non, kitob, olma, sham",
      "id": "memory_7"
    },
    {
      "q": "Yodlab oling: kalit, non, kitob, olma, sham, tog‘. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "olma",
        "kitob",
        "sham",
        "kalit"
      ],
      "correct": 0,
      "kind": "word_position",
      "memory_prompt": "kalit, non, kitob, olma, sham, tog‘",
      "id": "memory_8"
    },
    {
      "q": "Yodlab oling: non, kitob, olma, sham, tog‘, telefon. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "telefon",
        "non",
        "sham",
        "kitob"
      ],
      "correct": 1,
      "kind": "word_position",
      "memory_prompt": "non, kitob, olma, sham, tog‘, telefon",
      "id": "memory_9"
    },
    {
      "q": "Yodlab oling: kitob, olma, sham, tog‘, telefon, gilos. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "kitob",
        "tog‘",
        "sham",
        "telefon"
      ],
      "correct": 1,
      "kind": "word_position",
      "memory_prompt": "kitob, olma, sham, tog‘, telefon, gilos",
      "id": "memory_10"
    },
    {
      "q": "Yodlab oling: olma, sham, tog‘, telefon, gilos, stul. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "stul",
        "olma",
        "telefon",
        "sham"
      ],
      "correct": 1,
      "kind": "word_position",
      "memory_prompt": "olma, sham, tog‘, telefon, gilos, stul",
      "id": "memory_11"
    },
    {
      "q": "Yodlab oling: sham, tog‘, telefon, gilos, stul, daftar. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "gilos",
        "telefon",
        "sham",
        "stul"
      ],
      "correct": 0,
      "kind": "word_position",
      "memory_prompt": "sham, tog‘, telefon, gilos, stul, daftar",
      "id": "memory_12"
    },
    {
      "q": "Yodlab oling: tog‘, telefon, gilos, stul, daftar, qush. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "telefon",
        "stul",
        "qush",
        "tog‘"
      ],
      "correct": 3,
      "kind": "word_position",
      "memory_prompt": "tog‘, telefon, gilos, stul, daftar, qush",
      "id": "memory_13"
    },
    {
      "q": "Yodlab oling: telefon, gilos, stul, daftar, qush, mashina. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "qush",
        "telefon",
        "stul",
        "daftar"
      ],
      "correct": 3,
      "kind": "word_position",
      "memory_prompt": "telefon, gilos, stul, daftar, qush, mashina",
      "id": "memory_14"
    },
    {
      "q": "Yodlab oling: gilos, stul, daftar, qush, mashina, gul. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "stul",
        "qush",
        "gilos",
        "gul"
      ],
      "correct": 2,
      "kind": "word_position",
      "memory_prompt": "gilos, stul, daftar, qush, mashina, gul",
      "id": "memory_15"
    },
    {
      "q": "Yodlab oling: stul, daftar, qush, mashina, gul, choy. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "qush",
        "mashina",
        "stul",
        "gul"
      ],
      "correct": 1,
      "kind": "word_position",
      "memory_prompt": "stul, daftar, qush, mashina, gul, choy",
      "id": "memory_16"
    },
    {
      "q": "Yodlab oling: daftar, qush, mashina, gul, choy, oy. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "qush",
        "oy",
        "gul",
        "daftar"
      ],
      "correct": 3,
      "kind": "word_position",
      "memory_prompt": "daftar, qush, mashina, gul, choy, oy",
      "id": "memory_17"
    },
    {
      "q": "Yodlab oling: qush, mashina, gul, choy, oy, daraxt. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "choy",
        "qush",
        "oy",
        "gul"
      ],
      "correct": 0,
      "kind": "word_position",
      "memory_prompt": "qush, mashina, gul, choy, oy, daraxt",
      "id": "memory_18"
    },
    {
      "q": "Yodlab oling: mashina, gul, choy, oy, daraxt, kema. Savol: 1-o‘rindagi so‘z qaysi?",
      "a": [
        "oy",
        "kema",
        "mashina",
        "gul"
      ],
      "correct": 2,
      "kind": "word_position",
      "memory_prompt": "mashina, gul, choy, oy, daraxt, kema",
      "id": "memory_19"
    },
    {
      "q": "Yodlab oling: gul, choy, oy, daraxt, kema, sumka. Savol: 4-o‘rindagi so‘z qaysi?",
      "a": [
        "oy",
        "gul",
        "daraxt",
        "kema"
      ],
      "correct": 2,
      "kind": "word_position",
      "memory_prompt": "gul, choy, oy, daraxt, kema, sumka",
      "id": "memory_20"
    },
    {
      "q": "Yodlab oling: 7 – 2 – 9 – 4 – 1 – 8. Keyin qarang. 2-o‘rindagi raqam qaysi?",
      "a": [
        "1",
        "7",
        "2",
        "9"
      ],
      "correct": 2,
      "kind": "number_position",
      "memory_prompt": "7 – 2 – 9 – 4 – 1 – 8",
      "id": "memory_21"
    },
    {
      "q": "Yodlab oling: 3 – 8 – 1 – 6 – 5 – 2. Keyin qarang. 4-o‘rindagi raqam qaysi?",
      "a": [
        "6",
        "1",
        "5",
        "3"
      ],
      "correct": 0,
      "kind": "number_position",
      "memory_prompt": "3 – 8 – 1 – 6 – 5 – 2",
      "id": "memory_22"
    },
    {
      "q": "Yodlab oling: 9 – 4 – 7 – 2 – 6 – 1. Keyin qarang. 6-o‘rindagi raqam qaysi?",
      "a": [
        "9",
        "7",
        "1",
        "6"
      ],
      "correct": 2,
      "kind": "number_position",
      "memory_prompt": "9 – 4 – 7 – 2 – 6 – 1",
      "id": "memory_23"
    },
    {
      "q": "Yodlab oling: 5 – 0 – 8 – 3 – 9 – 4. Keyin qarang. 2-o‘rindagi raqam qaysi?",
      "a": [
        "8",
        "9",
        "5",
        "0"
      ],
      "correct": 3,
      "kind": "number_position",
      "memory_prompt": "5 – 0 – 8 – 3 – 9 – 4",
      "id": "memory_24"
    },
    {
      "q": "Yodlab oling: 2 – 6 – 1 – 8 – 4 – 7. Keyin qarang. 4-o‘rindagi raqam qaysi?",
      "a": [
        "4",
        "1",
        "8",
        "2"
      ],
      "correct": 2,
      "kind": "number_position",
      "memory_prompt": "2 – 6 – 1 – 8 – 4 – 7",
      "id": "memory_25"
    },
    {
      "q": "Yodlab oling: 8 – 3 – 5 – 1 – 9 – 6 – 2. Keyin qarang. 5-o‘rindagi raqam qaysi?",
      "a": [
        "9",
        "5",
        "8",
        "6"
      ],
      "correct": 0,
      "kind": "number_position",
      "memory_prompt": "8 – 3 – 5 – 1 – 9 – 6 – 2",
      "id": "memory_26"
    },
    {
      "q": "Yodlab oling: 4 – 9 – 2 – 7 – 1 – 6 – 8. Keyin qarang. 7-o‘rindagi raqam qaysi?",
      "a": [
        "1",
        "8",
        "4",
        "2"
      ],
      "correct": 1,
      "kind": "number_position",
      "memory_prompt": "4 – 9 – 2 – 7 – 1 – 6 – 8",
      "id": "memory_27"
    },
    {
      "q": "Yodlab oling: 6 – 1 – 8 – 4 – 0 – 5 – 3. Keyin qarang. 2-o‘rindagi raqam qaysi?",
      "a": [
        "1",
        "0",
        "8",
        "3"
      ],
      "correct": 0,
      "kind": "number_position",
      "memory_prompt": "6 – 1 – 8 – 4 – 0 – 5 – 3",
      "id": "memory_28"
    },
    {
      "q": "Yodlab oling: 7 – 5 – 2 – 9 – 3 – 1 – 6. Keyin qarang. 4-o‘rindagi raqam qaysi?",
      "a": [
        "6",
        "3",
        "9",
        "5"
      ],
      "correct": 2,
      "kind": "number_position",
      "memory_prompt": "7 – 5 – 2 – 9 – 3 – 1 – 6",
      "id": "memory_29"
    },
    {
      "q": "Yodlab oling: 1 – 8 – 4 – 6 – 2 – 9 – 5. Keyin qarang. 6-o‘rindagi raqam qaysi?",
      "a": [
        "9",
        "5",
        "8",
        "6"
      ],
      "correct": 0,
      "kind": "number_position",
      "memory_prompt": "1 – 8 – 4 – 6 – 2 – 9 – 5",
      "id": "memory_30"
    },
    {
      "q": "Yodlab oling: 9 – 1 – 3 – 8 – 6 – 2 – 7. Keyin qarang. 1-o‘rindagi raqam qaysi?",
      "a": [
        "2",
        "1",
        "9",
        "8"
      ],
      "correct": 2,
      "kind": "number_position",
      "memory_prompt": "9 – 1 – 3 – 8 – 6 – 2 – 7",
      "id": "memory_31"
    },
    {
      "q": "Yodlab oling: 2 – 7 – 5 – 0 – 4 – 9 – 1. Keyin qarang. 3-o‘rindagi raqam qaysi?",
      "a": [
        "9",
        "5",
        "0",
        "2"
      ],
      "correct": 1,
      "kind": "number_position",
      "memory_prompt": "2 – 7 – 5 – 0 – 4 – 9 – 1",
      "id": "memory_32"
    },
    {
      "q": "Yodlab oling: 8 – 6 – 1 – 3 – 7 – 2 – 5. Keyin qarang. 5-o‘rindagi raqam qaysi?",
      "a": [
        "2",
        "7",
        "1",
        "8"
      ],
      "correct": 1,
      "kind": "number_position",
      "memory_prompt": "8 – 6 – 1 – 3 – 7 – 2 – 5",
      "id": "memory_33"
    },
    {
      "q": "Yodlab oling: 4 – 2 – 9 – 5 – 1 – 8 – 6. Keyin qarang. 7-o‘rindagi raqam qaysi?",
      "a": [
        "1",
        "4",
        "9",
        "6"
      ],
      "correct": 3,
      "kind": "number_position",
      "memory_prompt": "4 – 2 – 9 – 5 – 1 – 8 – 6",
      "id": "memory_34"
    },
    {
      "q": "Yodlab oling: 3 – 9 – 0 – 6 – 2 – 7 – 4. Keyin qarang. 2-o‘rindagi raqam qaysi?",
      "a": [
        "9",
        "0",
        "4",
        "2"
      ],
      "correct": 0,
      "kind": "number_position",
      "memory_prompt": "3 – 9 – 0 – 6 – 2 – 7 – 4",
      "id": "memory_35"
    },
    {
      "q": "Yodlab oling: 5 – 1 – 7 – 4 – 8 – 0 – 2. Keyin qarang. 4-o‘rindagi raqam qaysi?",
      "a": [
        "4",
        "2",
        "8",
        "1"
      ],
      "correct": 0,
      "kind": "number_position",
      "memory_prompt": "5 – 1 – 7 – 4 – 8 – 0 – 2",
      "id": "memory_36"
    },
    {
      "q": "Yodlab oling: 6 – 3 – 9 – 2 – 5 – 1 – 8. Keyin qarang. 6-o‘rindagi raqam qaysi?",
      "a": [
        "1",
        "2",
        "8",
        "3"
      ],
      "correct": 0,
      "kind": "number_position",
      "memory_prompt": "6 – 3 – 9 – 2 – 5 – 1 – 8",
      "id": "memory_37"
    },
    {
      "q": "Yodlab oling: 0 – 4 – 7 – 1 – 6 – 9 – 3. Keyin qarang. 1-o‘rindagi raqam qaysi?",
      "a": [
        "9",
        "1",
        "4",
        "0"
      ],
      "correct": 3,
      "kind": "number_position",
      "memory_prompt": "0 – 4 – 7 – 1 – 6 – 9 – 3",
      "id": "memory_38"
    },
    {
      "q": "Yodlab oling: 8 – 2 – 5 – 9 – 0 – 6 – 4. Keyin qarang. 3-o‘rindagi raqam qaysi?",
      "a": [
        "6",
        "8",
        "9",
        "5"
      ],
      "correct": 3,
      "kind": "number_position",
      "memory_prompt": "8 – 2 – 5 – 9 – 0 – 6 – 4",
      "id": "memory_39"
    },
    {
      "q": "Yodlab oling: 1 – 7 – 3 – 8 – 4 – 2 – 9. Keyin qarang. 5-o‘rindagi raqam qaysi?",
      "a": [
        "2",
        "1",
        "4",
        "3"
      ],
      "correct": 2,
      "kind": "number_position",
      "memory_prompt": "1 – 7 – 3 – 8 – 4 – 2 – 9",
      "id": "memory_40"
    },
    {
      "q": "Yodlab oling: Aziza — ko‘k; Bek — yashil; Dilnoza — sariq; Kamol — qizil; Sardor — oq. Savol: Aziza qaysi rang bilan bog‘langan?",
      "a": [
        "sariq",
        "yashil",
        "ko‘k",
        "qizil"
      ],
      "correct": 2,
      "kind": "pair_recall",
      "memory_prompt": "Aziza — ko‘k; Bek — yashil; Dilnoza — sariq; Kamol — qizil; Sardor — oq",
      "id": "memory_41"
    },
    {
      "q": "Yodlab oling: Kamol — qizil; Sardor — oq; Malika — binafsha; Jasur — kulrang; Nodira — pushti. Savol: Bek qaysi rang bilan bog‘langan?",
      "a": [
        "oq",
        "binafsha",
        "qizil",
        "yashil"
      ],
      "correct": 3,
      "kind": "pair_recall",
      "memory_prompt": "Kamol — qizil; Sardor — oq; Malika — binafsha; Jasur — kulrang; Nodira — pushti",
      "id": "memory_42"
    },
    {
      "q": "Yodlab oling: Jasur — kulrang; Nodira — pushti; Rustam — jigarrang; Madina — to‘q ko‘k; Akmal — to‘q sariq. Savol: Dilnoza qaysi rang bilan bog‘langan?",
      "a": [
        "kulrang",
        "pushti",
        "sariq",
        "jigarrang"
      ],
      "correct": 2,
      "kind": "pair_recall",
      "memory_prompt": "Jasur — kulrang; Nodira — pushti; Rustam — jigarrang; Madina — to‘q ko‘k; Akmal — to‘q sariq",
      "id": "memory_43"
    },
    {
      "q": "Yodlab oling: Madina — to‘q ko‘k; Akmal — to‘q sariq; Sevara — kumush; Otabek — oltin; Zarina — havorang. Savol: Kamol qaysi rang bilan bog‘langan?",
      "a": [
        "kumush",
        "to‘q sariq",
        "qizil",
        "to‘q ko‘k"
      ],
      "correct": 2,
      "kind": "pair_recall",
      "memory_prompt": "Madina — to‘q ko‘k; Akmal — to‘q sariq; Sevara — kumush; Otabek — oltin; Zarina — havorang",
      "id": "memory_44"
    },
    {
      "q": "Yodlab oling: Otabek — oltin; Zarina — havorang; Diyor — qora; Lola — yashil; Umid — qizil. Savol: Sardor qaysi rang bilan bog‘langan?",
      "a": [
        "qora",
        "oq",
        "oltin",
        "havorang"
      ],
      "correct": 1,
      "kind": "pair_recall",
      "memory_prompt": "Otabek — oltin; Zarina — havorang; Diyor — qora; Lola — yashil; Umid — qizil",
      "id": "memory_45"
    },
    {
      "q": "Yodlab oling: Lola — yashil; Umid — qizil; Shahnoza — oq; Farruh — sariq; Mohira — ko‘k. Savol: Malika qaysi rang bilan bog‘langan?",
      "a": [
        "yashil",
        "binafsha",
        "oq",
        "qizil"
      ],
      "correct": 1,
      "kind": "pair_recall",
      "memory_prompt": "Lola — yashil; Umid — qizil; Shahnoza — oq; Farruh — sariq; Mohira — ko‘k",
      "id": "memory_46"
    },
    {
      "q": "Yodlab oling: Farruh — sariq; Mohira — ko‘k; Aziza — ko‘k; Bek — yashil; Dilnoza — sariq. Savol: Jasur qaysi rang bilan bog‘langan?",
      "a": [
        "kulrang",
        "sariq",
        "ko‘k",
        "ko‘k"
      ],
      "correct": 0,
      "kind": "pair_recall",
      "memory_prompt": "Farruh — sariq; Mohira — ko‘k; Aziza — ko‘k; Bek — yashil; Dilnoza — sariq",
      "id": "memory_47"
    },
    {
      "q": "Yodlab oling: Bek — yashil; Dilnoza — sariq; Kamol — qizil; Sardor — oq; Malika — binafsha. Savol: Nodira qaysi rang bilan bog‘langan?",
      "a": [
        "qizil",
        "pushti",
        "sariq",
        "yashil"
      ],
      "correct": 1,
      "kind": "pair_recall",
      "memory_prompt": "Bek — yashil; Dilnoza — sariq; Kamol — qizil; Sardor — oq; Malika — binafsha",
      "id": "memory_48"
    },
    {
      "q": "Yodlab oling: Sardor — oq; Malika — binafsha; Jasur — kulrang; Nodira — pushti; Rustam — jigarrang. Savol: Rustam qaysi rang bilan bog‘langan?",
      "a": [
        "kulrang",
        "jigarrang",
        "binafsha",
        "oq"
      ],
      "correct": 1,
      "kind": "pair_recall",
      "memory_prompt": "Sardor — oq; Malika — binafsha; Jasur — kulrang; Nodira — pushti; Rustam — jigarrang",
      "id": "memory_49"
    },
    {
      "q": "Yodlab oling: Nodira — pushti; Rustam — jigarrang; Madina — to‘q ko‘k; Akmal — to‘q sariq; Sevara — kumush. Savol: Madina qaysi rang bilan bog‘langan?",
      "a": [
        "to‘q ko‘k",
        "pushti",
        "to‘q sariq",
        "jigarrang"
      ],
      "correct": 0,
      "kind": "pair_recall",
      "memory_prompt": "Nodira — pushti; Rustam — jigarrang; Madina — to‘q ko‘k; Akmal — to‘q sariq; Sevara — kumush",
      "id": "memory_50"
    },
    {
      "q": "Yodlab oling: Akmal — to‘q sariq; Sevara — kumush; Otabek — oltin; Zarina — havorang; Diyor — qora. Savol: Akmal qaysi rang bilan bog‘langan?",
      "a": [
        "havorang",
        "kumush",
        "to‘q sariq",
        "oltin"
      ],
      "correct": 2,
      "kind": "pair_recall",
      "memory_prompt": "Akmal — to‘q sariq; Sevara — kumush; Otabek — oltin; Zarina — havorang; Diyor — qora",
      "id": "memory_51"
    },
    {
      "q": "Yodlab oling: Zarina — havorang; Diyor — qora; Lola — yashil; Umid — qizil; Shahnoza — oq. Savol: Sevara qaysi rang bilan bog‘langan?",
      "a": [
        "kumush",
        "havorang",
        "qora",
        "yashil"
      ],
      "correct": 0,
      "kind": "pair_recall",
      "memory_prompt": "Zarina — havorang; Diyor — qora; Lola — yashil; Umid — qizil; Shahnoza — oq",
      "id": "memory_52"
    },
    {
      "q": "Yodlab oling: Umid — qizil; Shahnoza — oq; Farruh — sariq; Mohira — ko‘k; Aziza — ko‘k. Savol: Otabek qaysi rang bilan bog‘langan?",
      "a": [
        "oltin",
        "qizil",
        "oq",
        "sariq"
      ],
      "correct": 0,
      "kind": "pair_recall",
      "memory_prompt": "Umid — qizil; Shahnoza — oq; Farruh — sariq; Mohira — ko‘k; Aziza — ko‘k",
      "id": "memory_53"
    },
    {
      "q": "Yodlab oling: Mohira — ko‘k; Aziza — ko‘k; Bek — yashil; Dilnoza — sariq; Kamol — qizil. Savol: Zarina qaysi rang bilan bog‘langan?",
      "a": [
        "yashil",
        "ko‘k",
        "ko‘k",
        "havorang"
      ],
      "correct": 3,
      "kind": "pair_recall",
      "memory_prompt": "Mohira — ko‘k; Aziza — ko‘k; Bek — yashil; Dilnoza — sariq; Kamol — qizil",
      "id": "memory_54"
    },
    {
      "q": "Yodlab oling: Dilnoza — sariq; Kamol — qizil; Sardor — oq; Malika — binafsha; Jasur — kulrang. Savol: Diyor qaysi rang bilan bog‘langan?",
      "a": [
        "oq",
        "sariq",
        "qora",
        "qizil"
      ],
      "correct": 2,
      "kind": "pair_recall",
      "memory_prompt": "Dilnoza — sariq; Kamol — qizil; Sardor — oq; Malika — binafsha; Jasur — kulrang",
      "id": "memory_55"
    },
    {
      "q": "Yodlab oling: Malika — binafsha; Jasur — kulrang; Nodira — pushti; Rustam — jigarrang; Madina — to‘q ko‘k. Savol: Lola qaysi rang bilan bog‘langan?",
      "a": [
        "pushti",
        "binafsha",
        "kulrang",
        "yashil"
      ],
      "correct": 3,
      "kind": "pair_recall",
      "memory_prompt": "Malika — binafsha; Jasur — kulrang; Nodira — pushti; Rustam — jigarrang; Madina — to‘q ko‘k",
      "id": "memory_56"
    },
    {
      "q": "Yodlab oling: Rustam — jigarrang; Madina — to‘q ko‘k; Akmal — to‘q sariq; Sevara — kumush; Otabek — oltin. Savol: Umid qaysi rang bilan bog‘langan?",
      "a": [
        "to‘q sariq",
        "jigarrang",
        "qizil",
        "to‘q ko‘k"
      ],
      "correct": 2,
      "kind": "pair_recall",
      "memory_prompt": "Rustam — jigarrang; Madina — to‘q ko‘k; Akmal — to‘q sariq; Sevara — kumush; Otabek — oltin",
      "id": "memory_57"
    },
    {
      "q": "Yodlab oling: Sevara — kumush; Otabek — oltin; Zarina — havorang; Diyor — qora; Lola — yashil. Savol: Shahnoza qaysi rang bilan bog‘langan?",
      "a": [
        "havorang",
        "kumush",
        "oltin",
        "oq"
      ],
      "correct": 3,
      "kind": "pair_recall",
      "memory_prompt": "Sevara — kumush; Otabek — oltin; Zarina — havorang; Diyor — qora; Lola — yashil",
      "id": "memory_58"
    },
    {
      "q": "Yodlab oling: Diyor — qora; Lola — yashil; Umid — qizil; Shahnoza — oq; Farruh — sariq. Savol: Farruh qaysi rang bilan bog‘langan?",
      "a": [
        "sariq",
        "yashil",
        "qora",
        "qizil"
      ],
      "correct": 0,
      "kind": "pair_recall",
      "memory_prompt": "Diyor — qora; Lola — yashil; Umid — qizil; Shahnoza — oq; Farruh — sariq",
      "id": "memory_59"
    },
    {
      "q": "Yodlab oling: Shahnoza — oq; Farruh — sariq; Mohira — ko‘k; Aziza — ko‘k; Bek — yashil. Savol: Mohira qaysi rang bilan bog‘langan?",
      "a": [
        "oq",
        "sariq",
        "yashil",
        "ko‘k"
      ],
      "correct": 3,
      "kind": "pair_recall",
      "memory_prompt": "Shahnoza — oq; Farruh — sariq; Mohira — ko‘k; Aziza — ko‘k; Bek — yashil",
      "id": "memory_60"
    },
    {
      "q": "Yodlab oling: Shaharlar: Toshkent—O‘zbekiston; Ankara—Turkiya; Madrid—Ispaniya; Rim—Italiya. Madrid qaysi davlat?",
      "a": [
        "Turkiya",
        "O‘zbekiston",
        "Italiya",
        "Ispaniya"
      ],
      "correct": 3,
      "kind": "fact_recall",
      "memory_prompt": "Shaharlar: Toshkent—O‘zbekiston; Ankara—Turkiya; Madrid—Ispaniya; Rim—Italiya",
      "id": "memory_61"
    },
    {
      "q": "Yodlab oling: Mevalar: olma—qizil; banan—sariq; uzum—binafsha; limon—sariq. Uzumning rangi?",
      "a": [
        "binafsha",
        "yashil",
        "sariq",
        "qizil"
      ],
      "correct": 0,
      "kind": "fact_recall",
      "memory_prompt": "Mevalar: olma—qizil; banan—sariq; uzum—binafsha; limon—sariq",
      "id": "memory_62"
    },
    {
      "q": "Yodlab oling: Kunlar: Dushanba—1; Seshanba—2; Chorshanba—3; Payshanba—4. Payshanba nechanchi?",
      "a": [
        "3",
        "5",
        "4",
        "2"
      ],
      "correct": 2,
      "kind": "fact_recall",
      "memory_prompt": "Kunlar: Dushanba—1; Seshanba—2; Chorshanba—3; Payshanba—4",
      "id": "memory_63"
    },
    {
      "q": "Yodlab oling: Hayvonlar: mushuk—Mimi; it—Rex; qush—Kiki; ot—Dono. Qushning nomi?",
      "a": [
        "Mimi",
        "Dono",
        "Kiki"
      ],
      "correct": 2,
      "kind": "fact_recall",
      "memory_prompt": "Hayvonlar: mushuk—Mimi; it—Rex; qush—Kiki; ot—Dono",
      "id": "memory_64"
    },
    {
      "q": "Yodlab oling: Stollar: A—2 oyoq; B—4 oyoq; C—3 oyoq; D—1 oyoq. B stolining oyoqlari?",
      "a": [
        "1",
        "2",
        "3",
        "4"
      ],
      "correct": 3,
      "kind": "fact_recall",
      "memory_prompt": "Stollar: A—2 oyoq; B—4 oyoq; C—3 oyoq; D—1 oyoq",
      "id": "memory_65"
    },
    {
      "q": "Yodlab oling: Kitoblar: A—120 bet; B—180; C—95; D—240. C kitob necha bet?",
      "a": [
        "240",
        "95",
        "180",
        "120"
      ],
      "correct": 1,
      "kind": "fact_recall",
      "memory_prompt": "Kitoblar: A—120 bet; B—180; C—95; D—240",
      "id": "memory_66"
    },
    {
      "q": "Yodlab oling: Ichimliklar: choy—issiq; sharbat—sovuq; qahva—issiq; suv—sovuq. Qahva qanday?",
      "a": [
        "iliq",
        "issiq",
        "muzli",
        "sovuq"
      ],
      "correct": 1,
      "kind": "fact_recall",
      "memory_prompt": "Ichimliklar: choy—issiq; sharbat—sovuq; qahva—issiq; suv—sovuq",
      "id": "memory_67"
    },
    {
      "q": "Yodlab oling: Ranglar: qizil—1; ko‘k—2; yashil—3; oq—4. Yashilning raqami?",
      "a": [
        "1",
        "4",
        "3",
        "2"
      ],
      "correct": 2,
      "kind": "fact_recall",
      "memory_prompt": "Ranglar: qizil—1; ko‘k—2; yashil—3; oq—4",
      "id": "memory_68"
    },
    {
      "q": "Yodlab oling: Sportlar: futbol—11; basketbol—5; voleybol—6; tennis—2. Voleybolda maydondagi o‘yinchi soni?",
      "a": [
        "2",
        "5",
        "6",
        "11"
      ],
      "correct": 2,
      "kind": "fact_recall",
      "memory_prompt": "Sportlar: futbol—11; basketbol—5; voleybol—6; tennis—2",
      "id": "memory_69"
    },
    {
      "q": "Yodlab oling: Sayyoralar: Merkuriy—1; Venera—2; Yer—3; Mars—4. Yer nechanchi?",
      "a": [
        "2",
        "1",
        "3",
        "4"
      ],
      "correct": 2,
      "kind": "fact_recall",
      "memory_prompt": "Sayyoralar: Merkuriy—1; Venera—2; Yer—3; Mars—4",
      "id": "memory_70"
    },
    {
      "q": "Eslab qoling: Kodlar: Ali—27; Bek—41; Diyor—63; Lola—18. Diyorning kodi?",
      "a": [
        "41",
        "63",
        "18"
      ],
      "correct": 1,
      "kind": "fact_recall",
      "memory_prompt": "Kodlar: Ali—27; Bek—41; Diyor—63; Lola—18",
      "id": "memory_71"
    },
    {
      "q": "Eslab qoling: Jadval: qizil—olma; sariq—banan; yashil—nok; to‘q sariq—apelsin. Yashilga qaysi meva tegishli?",
      "a": [
        "banan",
        "nok",
        "olma",
        "apelsin"
      ],
      "correct": 1,
      "kind": "fact_recall",
      "memory_prompt": "Jadval: qizil—olma; sariq—banan; yashil—nok; to‘q sariq—apelsin",
      "id": "memory_72"
    },
    {
      "q": "Eslab qoling: Jamoa: A—himoya; B—hujum; C—darvozabon; D—zaxira. Darvozabon qaysi harf?",
      "a": [
        "A",
        "C",
        "B",
        "D"
      ],
      "correct": 1,
      "kind": "fact_recall",
      "memory_prompt": "Jamoa: A—himoya; B—hujum; C—darvozabon; D—zaxira",
      "id": "memory_73"
    },
    {
      "q": "Eslab qoling: Xonalar: 1—kutubxona; 2—oshxona; 3—laboratoriya; 4—zal. Laboratoriya raqami?",
      "a": [
        "1",
        "4",
        "3"
      ],
      "correct": 2,
      "kind": "fact_recall",
      "memory_prompt": "Xonalar: 1—kutubxona; 2—oshxona; 3—laboratoriya; 4—zal",
      "id": "memory_74"
    },
    {
      "q": "Eslab qoling: Musiqalar: A—3 min; B—5 min; C—2 min; D—4 min. Eng uzun trek qaysi?",
      "a": [
        "C",
        "A",
        "B",
        "D"
      ],
      "correct": 2,
      "kind": "fact_recall",
      "memory_prompt": "Musiqalar: A—3 min; B—5 min; C—2 min; D—4 min",
      "id": "memory_75"
    },
    {
      "q": "Eslab qoling: Do‘konlar: A—12; B—7; C—19; D—15 mahsulot. Eng ko‘p mahsulot qaysida?",
      "a": [
        "A",
        "B",
        "D",
        "C"
      ],
      "correct": 3,
      "kind": "fact_recall",
      "memory_prompt": "Do‘konlar: A—12; B—7; C—19; D—15 mahsulot",
      "id": "memory_76"
    },
    {
      "q": "Eslab qoling: Yo‘nalishlar: avtobus—shimol; poyezd—g‘arb; samolyot—janub; kema—sharq. Poyezd qaysi tomonga?",
      "a": [
        "shimol",
        "g‘arb",
        "sharq"
      ],
      "correct": 1,
      "kind": "fact_recall",
      "memory_prompt": "Yo‘nalishlar: avtobus—shimol; poyezd—g‘arb; samolyot—janub; kema—sharq",
      "id": "memory_77"
    },
    {
      "q": "Eslab qoling: Vazifalar: Ali—email; Bek—hisobot; Lola—qo‘ng‘iroq; Diyor—jadval. Hisobotni kim qiladi?",
      "a": [
        "Ali",
        "Diyor",
        "Bek"
      ],
      "correct": 2,
      "kind": "fact_recall",
      "memory_prompt": "Vazifalar: Ali—email; Bek—hisobot; Lola—qo‘ng‘iroq; Diyor—jadval",
      "id": "memory_78"
    },
    {
      "q": "Eslab qoling: Mehmonxonalar: A—2 qavat; B—5; C—3; D—4. B nechta qavat?",
      "a": [
        "3",
        "5",
        "4",
        "2"
      ],
      "correct": 1,
      "kind": "fact_recall",
      "memory_prompt": "Mehmonxonalar: A—2 qavat; B—5; C—3; D—4",
      "id": "memory_79"
    },
    {
      "q": "Eslab qoling: Raqamlar: A—17; B—29; C—11; D—35. Eng kichigi qaysi?",
      "a": [
        "A",
        "C",
        "B"
      ],
      "correct": 1,
      "kind": "fact_recall",
      "memory_prompt": "Raqamlar: A—17; B—29; C—11; D—35",
      "id": "memory_80"
    },
    {
      "q": "6 soniya kuzating: olma | sham | tog‘ | telefon | gilos | stul | daftar. Endi: 3-o‘rinda nima bor edi?",
      "a": [
        "sham",
        "tog‘",
        "daftar",
        "telefon"
      ],
      "correct": 1,
      "kind": "rapid_recall",
      "memory_prompt": "olma | sham | tog‘ | telefon | gilos | stul | daftar",
      "id": "memory_81"
    },
    {
      "q": "6 soniya kuzating: sham | tog‘ | telefon | gilos | stul | daftar | qush. Endi: 7-o‘rinda nima bor edi?",
      "a": [
        "qush",
        "daftar",
        "sham",
        "gilos"
      ],
      "correct": 0,
      "kind": "rapid_recall",
      "memory_prompt": "sham | tog‘ | telefon | gilos | stul | daftar | qush",
      "id": "memory_82"
    },
    {
      "q": "6 soniya kuzating: tog‘ | telefon | gilos | stul | daftar | qush | mashina. Endi: 4-o‘rinda nima bor edi?",
      "a": [
        "gilos",
        "daftar",
        "stul",
        "tog‘"
      ],
      "correct": 2,
      "kind": "rapid_recall",
      "memory_prompt": "tog‘ | telefon | gilos | stul | daftar | qush | mashina",
      "id": "memory_83"
    },
    {
      "q": "6 soniya kuzating: telefon | gilos | stul | daftar | qush | mashina | gul. Endi: 1-o‘rinda nima bor edi?",
      "a": [
        "gul",
        "telefon",
        "gilos",
        "qush"
      ],
      "correct": 1,
      "kind": "rapid_recall",
      "memory_prompt": "telefon | gilos | stul | daftar | qush | mashina | gul",
      "id": "memory_84"
    },
    {
      "q": "6 soniya kuzating: gilos | stul | daftar | qush | mashina | gul | choy. Endi: 5-o‘rinda nima bor edi?",
      "a": [
        "qush",
        "stul",
        "mashina",
        "gul"
      ],
      "correct": 2,
      "kind": "rapid_recall",
      "memory_prompt": "gilos | stul | daftar | qush | mashina | gul | choy",
      "id": "memory_85"
    },
    {
      "q": "6 soniya kuzating: stul | daftar | qush | mashina | gul | choy | oy. Endi: 2-o‘rinda nima bor edi?",
      "a": [
        "stul",
        "daftar",
        "qush",
        "choy"
      ],
      "correct": 1,
      "kind": "rapid_recall",
      "memory_prompt": "stul | daftar | qush | mashina | gul | choy | oy",
      "id": "memory_86"
    },
    {
      "q": "6 soniya kuzating: daftar | qush | mashina | gul | choy | oy | daraxt. Endi: 6-o‘rinda nima bor edi?",
      "a": [
        "mashina",
        "daraxt",
        "oy",
        "choy"
      ],
      "correct": 2,
      "kind": "rapid_recall",
      "memory_prompt": "daftar | qush | mashina | gul | choy | oy | daraxt",
      "id": "memory_87"
    },
    {
      "q": "6 soniya kuzating: qush | mashina | gul | choy | oy | daraxt | kema. Endi: 3-o‘rinda nima bor edi?",
      "a": [
        "choy",
        "gul",
        "mashina",
        "kema"
      ],
      "correct": 1,
      "kind": "rapid_recall",
      "memory_prompt": "qush | mashina | gul | choy | oy | daraxt | kema",
      "id": "memory_88"
    },
    {
      "q": "6 soniya kuzating: mashina | gul | choy | oy | daraxt | kema | sumka. Endi: 7-o‘rinda nima bor edi?",
      "a": [
        "sumka",
        "mashina",
        "oy",
        "kema"
      ],
      "correct": 0,
      "kind": "rapid_recall",
      "memory_prompt": "mashina | gul | choy | oy | daraxt | kema | sumka",
      "id": "memory_89"
    },
    {
      "q": "6 soniya kuzating: gul | choy | oy | daraxt | kema | sumka | qaychi. Endi: 4-o‘rinda nima bor edi?",
      "a": [
        "oy",
        "daraxt",
        "gul",
        "kema"
      ],
      "correct": 1,
      "kind": "rapid_recall",
      "memory_prompt": "gul | choy | oy | daraxt | kema | sumka | qaychi",
      "id": "memory_90"
    },
    {
      "q": "6 soniya kuzating: choy | oy | daraxt | kema | sumka | qaychi | ko‘ylak. Endi: 1-o‘rinda nima bor edi?",
      "a": [
        "choy",
        "sumka",
        "oy",
        "ko‘ylak"
      ],
      "correct": 0,
      "kind": "rapid_recall",
      "memory_prompt": "choy | oy | daraxt | kema | sumka | qaychi | ko‘ylak",
      "id": "memory_91"
    },
    {
      "q": "6 soniya kuzating: oy | daraxt | kema | sumka | qaychi | ko‘ylak | qoshiq. Endi: 5-o‘rinda nima bor edi?",
      "a": [
        "daraxt",
        "sumka",
        "qaychi",
        "ko‘ylak"
      ],
      "correct": 2,
      "kind": "rapid_recall",
      "memory_prompt": "oy | daraxt | kema | sumka | qaychi | ko‘ylak | qoshiq",
      "id": "memory_92"
    },
    {
      "q": "6 soniya kuzating: daraxt | kema | sumka | qaychi | ko‘ylak | qoshiq | yulduz. Endi: 2-o‘rinda nima bor edi?",
      "a": [
        "daraxt",
        "kema",
        "sumka",
        "qoshiq"
      ],
      "correct": 1,
      "kind": "rapid_recall",
      "memory_prompt": "daraxt | kema | sumka | qaychi | ko‘ylak | qoshiq | yulduz",
      "id": "memory_93"
    },
    {
      "q": "6 soniya kuzating: kema | sumka | qaychi | ko‘ylak | qoshiq | yulduz | eshik. Endi: 6-o‘rinda nima bor edi?",
      "a": [
        "qoshiq",
        "yulduz",
        "eshik",
        "qaychi"
      ],
      "correct": 1,
      "kind": "rapid_recall",
      "memory_prompt": "kema | sumka | qaychi | ko‘ylak | qoshiq | yulduz | eshik",
      "id": "memory_94"
    },
    {
      "q": "6 soniya kuzating: sumka | qaychi | ko‘ylak | qoshiq | yulduz | eshik | sandiq. Endi: 3-o‘rinda nima bor edi?",
      "a": [
        "qaychi",
        "sandiq",
        "qoshiq",
        "ko‘ylak"
      ],
      "correct": 3,
      "kind": "rapid_recall",
      "memory_prompt": "sumka | qaychi | ko‘ylak | qoshiq | yulduz | eshik | sandiq",
      "id": "memory_95"
    },
    {
      "q": "6 soniya kuzating: qaychi | ko‘ylak | qoshiq | yulduz | eshik | sandiq | ruchka. Endi: 7-o‘rinda nima bor edi?",
      "a": [
        "qaychi",
        "yulduz",
        "ruchka",
        "sandiq"
      ],
      "correct": 2,
      "kind": "rapid_recall",
      "memory_prompt": "qaychi | ko‘ylak | qoshiq | yulduz | eshik | sandiq | ruchka",
      "id": "memory_96"
    },
    {
      "q": "6 soniya kuzating: ko‘ylak | qoshiq | yulduz | eshik | sandiq | ruchka | suv. Endi: 4-o‘rinda nima bor edi?",
      "a": [
        "eshik",
        "ko‘ylak",
        "sandiq",
        "yulduz"
      ],
      "correct": 0,
      "kind": "rapid_recall",
      "memory_prompt": "ko‘ylak | qoshiq | yulduz | eshik | sandiq | ruchka | suv",
      "id": "memory_97"
    },
    {
      "q": "6 soniya kuzating: qoshiq | yulduz | eshik | sandiq | ruchka | suv | qum. Endi: 1-o‘rinda nima bor edi?",
      "a": [
        "ruchka",
        "yulduz",
        "qoshiq",
        "qum"
      ],
      "correct": 2,
      "kind": "rapid_recall",
      "memory_prompt": "qoshiq | yulduz | eshik | sandiq | ruchka | suv | qum",
      "id": "memory_98"
    },
    {
      "q": "6 soniya kuzating: yulduz | eshik | sandiq | ruchka | suv | qum | maktab. Endi: 5-o‘rinda nima bor edi?",
      "a": [
        "eshik",
        "ruchka",
        "qum",
        "suv"
      ],
      "correct": 3,
      "kind": "rapid_recall",
      "memory_prompt": "yulduz | eshik | sandiq | ruchka | suv | qum | maktab",
      "id": "memory_99"
    },
    {
      "q": "6 soniya kuzating: eshik | sandiq | ruchka | suv | qum | maktab | ko‘cha. Endi: 2-o‘rinda nima bor edi?",
      "a": [
        "ruchka",
        "sandiq",
        "eshik",
        "maktab"
      ],
      "correct": 1,
      "kind": "rapid_recall",
      "memory_prompt": "eshik | sandiq | ruchka | suv | qum | maktab | ko‘cha",
      "id": "memory_100"
    }
  ],
  "leadership": [
    {
      "q": "Jamoa loyihasida deadline yaqin, eng muhim vazifa ortda qolgan. Birinchi qadam?",
      "a": [
        "Deadline haqida jim qolish",
        "Aybdorni izlash",
        "Vazifani qismlarga ajratib, mas’ullar va muddatni aniqlash",
        "Hammasini o‘zing qilish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_1"
    },
    {
      "q": "Ikki kuchli xodim bir masalada tortishmoqda, qolganlar ishlamay qoldi. Nima qilasan?",
      "a": [
        "Jamoani tarqatish",
        "Muammoni faktlarga ajratib, qisqa qaror mezonini belgilash",
        "Bittasini darhol chetlatish",
        "Bahsni shaxsiylashtirish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_2"
    },
    {
      "q": "Yangi a’zo xato qildi, lekin xatosini yashirmay darhol aytdi. Rahbar sifatida?",
      "a": [
        "Sababni tahlil qilib, tuzatish va qayta takrorlanmasligi uchun jarayon yaratish",
        "Uni omma oldida koyish",
        "Xatoni yopish",
        "Uni barcha vazifadan olish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_3"
    },
    {
      "q": "Mijoz oxirgi daqiqada talabni o‘zgartirdi. Muddat o‘zgarmadi. Nima qilasan?",
      "a": [
        "Mijozni bloklash",
        "Hammasini va’da qilish",
        "Jamoani ayblash",
        "Talabning ta’sirini baholab, ustuvorlik va yangi scope bo‘yicha kelishish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_4"
    },
    {
      "q": "Jamoada hech kim yangi vazifani olishni xohlamayapti, lekin vazifa muhim. Eng yaxshi yondashuv?",
      "a": [
        "Vazifani yashirish",
        "Birinchi ko‘ringan odamga berish",
        "Vazifaning maqsadini va yuklamani ochiq ko‘rsatib, mas’uliyatni adolatli taqsimlash",
        "O‘zing qilish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_5"
    },
    {
      "q": "Yaxshi xodim natija bermay qoldi. Darhol ishdan bo‘shatishdan oldin?",
      "a": [
        "Boshqalarga shikoyat qilish",
        "Uni e’tiborsiz qoldirish",
        "Muammoni aniqlash uchun ochiq suhbat va aniq kutishlarni belgilash",
        "Maoshini yashirin kamaytirish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_6"
    },
    {
      "q": "Yig‘ilish 60 daqiqa davom etyapti, lekin qaror chiqmayapti. Nima qilasan?",
      "a": [
        "Yig‘ilishni sababsiz tugatish",
        "Yig‘ilishni yana cho‘zish",
        "Hamma bilan alohida bahslashish",
        "Muammo, variantlar va qaror muddatini aniq qilib, yakuniy mas’ulni belgilash"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_7"
    },
    {
      "q": "Jamoa yaxshi natija berdi, lekin sening emas, ikki a’zoning hissasi katta. Rahbar sifatida?",
      "a": [
        "Barchasini o‘zingniki qilish",
        "Hech kimni maqtamaslik",
        "Ularni ochiq e’tirof etish va natijani jamoaga bog‘lash",
        "Faqat rahbariyatga aytish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_8"
    },
    {
      "q": "Muhim qaror uchun ma’lumot yetarli emas, ammo vaqt juda kam. Nima qilasan?",
      "a": [
        "Qarorni cheksiz kechiktirish",
        "Boshqaga yuklash",
        "Mavjud eng muhim faktlarni ajratib, riskni baholab, qaytariladigan qarorni tanlash",
        "Tasodifiy tanlash"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_9"
    },
    {
      "q": "Jamoada bir kishi doim gapiradi, boshqalar jim. Yig‘ilishda?",
      "a": [
        "Faqat jimlarni tanqid qilish",
        "Yig‘ilishni bekor qilish",
        "Har bir muhim nuqtaga navbat bilan fikr so‘rash va vaqt chegarasi qo‘yish",
        "Uni to‘xtatmaslik"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_10"
    },
    {
      "q": "Ikki variantdan biri tez, biri sifatliroq. Deadline qat’iy. Nima qilasan?",
      "a": [
        "Qarorni jamoaga tashlash",
        "Har doim eng tezini tanlash",
        "Qaysi talablar majburiy ekanini aniqlab, sifat va muddat o‘rtasidagi trade-offni ochiq tanlash",
        "Har doim eng sifatlisini tanlash"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_11"
    },
    {
      "q": "Xodim sening qaroringga ochiqchasiga rozi emas. Eng foydali javob?",
      "a": [
        "Nega qarshi ekanini dalil bilan tushuntirishini so‘rash",
        "Bahsni yopish",
        "Boshqalarga qarshi qo‘yish",
        "Uni darhol jazolash"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_12"
    },
    {
      "q": "Muvaffaqiyatsiz loyiha tugadi. Keyingi yig‘ilishda birinchi mavzu?",
      "a": [
        "Natijani yashiramiz",
        "Kim aybdor?",
        "Nima o‘rgandik va keyingi safar qaysi jarayonni o‘zgartiramiz?",
        "Kimni almashtiramiz?"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_13"
    },
    {
      "q": "Yangi strategiya jamoaga yoqmayapti, lekin maqsad o‘zgarmagan. Nima qilasan?",
      "a": [
        "Faqat buyruq berish",
        "Hech kimga izoh bermaslik",
        "E’tirozlarni sabablariga ajratib, asosiy maqsad va cheklovlarni tushuntirish",
        "Strategiyani darhol bekor qilish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_14"
    },
    {
      "q": "Bir xodim juda tez ishlaydi, ammo xatolari ko‘p. Nima qilasan?",
      "a": [
        "Faqat tanqid qilish",
        "Faqat tezligini maqtash",
        "Sifat mezonini aniqlab, tezlikni saqlagan holda tekshiruv bosqichini qo‘shish",
        "Uni boshqa bo‘limga yuborish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_15"
    },
    {
      "q": "Jamoada kichik konflikt bor, ish hali to‘xtamagan. Qanday yo‘l?",
      "a": [
        "Konfliktni inkor qilish",
        "Bir tomonni tanlash",
        "Barchani jazolash",
        "Muammoni shaxs emas, xatti-harakat va natija nuqtasida muhokama qilish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_16"
    },
    {
      "q": "Rahbar sifatida sen xato qaror qilganingni tushunding. Nima qilasan?",
      "a": [
        "Bahona topish",
        "Boshqani ayblash",
        "Yashirish",
        "Xatoni tan olib, ta’sirini kamaytirish va keyingi qadamni aytish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_17"
    },
    {
      "q": "Jamoa haddan tashqari ko‘p vazifani bir vaqtda boshladi. Nima qilasan?",
      "a": [
        "Eng osonini tanlash",
        "Hamma ishni to‘xtatish",
        "Ustuvorlikni belgilab, tugatishga yaqin ishlarni yakunlashga fokuslash",
        "Yana vazifa qo‘shish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_18"
    },
    {
      "q": "Mijoz noto‘g‘ri ma’lumot yubordi va loyiha xavf ostida. Nima qilasan?",
      "a": [
        "Muammoni aniq hujjatlashtirib, kerakli ma’lumotni so‘rash va ta’sirini baholash",
        "Darhol mijozni ayblash",
        "Jamoani ayblash",
        "Xatoni yashirish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_19"
    },
    {
      "q": "Jamoada yangi odam o‘z fikrini aytishga uyaladi. Rahbar sifatida?",
      "a": [
        "Kichik, xavfsiz formatda fikrini so‘rab, foydali fikrini e’tirof etish",
        "Uni doim boshqaga qo‘shish",
        "Uni majburlash",
        "Yig‘ilishdan chiqarish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_20"
    },
    {
      "q": "Bir mijoz shartnomadagi bitta bandni boshqacha tushunganini aytdi. Birinchi qadam?",
      "a": [
        "Bandni aniq talqin qilib, yozma kelishuvga qaytish",
        "Ishni davom ettirib, keyin tushuntirish",
        "Mijozni noto‘g‘ri deb e’lon qilish",
        "Shartnomani bekor qilish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_21"
    },
    {
      "q": "Jamoada ikki odamning maqsadi bir-biriga zid bo‘lib qoldi. Nima qilasan?",
      "a": [
        "Umumiy loyiha maqsadini ustuvor qo‘yib, ziddiyatni mezonlar orqali hal qilish",
        "Kattaroq lavozimdagini tanlash",
        "Muammoni e’tiborsiz qoldirish",
        "Ikkalasiga ham alohida maqsad berish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_22"
    },
    {
      "q": "Yangi loyiha boshida hamma juda ko‘p funksiyani taklif qildi. Rahbar sifatida?",
      "a": [
        "Asosiy foydalanuvchi muammosini hal qiladigan minimum funksiyalarni ajratish",
        "Hammasini birinchi versiyaga qo‘shish",
        "Fikrlarning barchasini rad etish",
        "Eng chiroyli funksiyani tanlash"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_23"
    },
    {
      "q": "Jamoa bir haftada uch marta bir xil savolni berdi. Bu nimani ko‘rsatadi?",
      "a": [
        "Savol berishni taqiqlash kerakligini",
        "Jamoa dangasa ekanini",
        "Jarayonda tushunarsiz joy borligini va uni hujjatlashtirish kerakligini",
        "Ko‘proq yig‘ilish kerakligini"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_24"
    },
    {
      "q": "Tajribali xodim yangi xodimni doim tuzatadi, lekin o‘zi ishni topshirib qo‘ymaydi. Nima qilasan?",
      "a": [
        "Yangi xodimni chetlatish",
        "Vazifani topshirish va fikr bildirish chegaralarini aniq belgilash",
        "Ularning o‘zlari hal qilishini kutish",
        "Tajribali xodimni hamma ishga qo‘yish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_25"
    },
    {
      "q": "Jamoa yaxshi g‘oyani topdi, ammo uni tekshirish uchun bir kun yetadi. Eng to‘g‘ri qaror?",
      "a": [
        "Kichik test o‘tkazib, dalilga qarab keyingi qadamni tanlash",
        "Darhol katta loyiha qilish",
        "Faqat rahbarning sezgisiga tayanish",
        "G‘oyani bir oy kutish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_26"
    },
    {
      "q": "Sening jamoang boshqa bo‘limga bog‘liq, ular javob bermayapti. Nima qilasan?",
      "a": [
        "Ishni to‘xtatish",
        "Kerakli natija va muddatni aniq yozib, muqobil yo‘lni ham tayyorlash",
        "Ularni omma oldida tanqid qilish",
        "Hech narsa demay kutish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_27"
    },
    {
      "q": "Jamoada yangi qoida kiritmoqchisan, lekin nima muammoni hal qilishi aniq emas.",
      "a": [
        "Qoidani baribir joriy qilish",
        "Boshqa jamoalarning qoidasini ko‘chirish",
        "Avval muammoni va qoida kerakligini isbotlash",
        "Hech qanday qoida qilmaslik"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_28"
    },
    {
      "q": "Bir xodim natijani tez beradi, lekin ma’lumot manbasini tekshirmaydi.",
      "a": [
        "Barcha vazifasini olib qo‘yish",
        "Tezligini mukofotlash",
        "Natijani tekshirmaslik",
        "Tezlikni saqlab, manbani tekshirishni jarayonga qo‘shish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_29"
    },
    {
      "q": "Jamoa a’zosi muhim ishni bajardi, lekin natijani hech kimga ko‘rsatmagan.",
      "a": [
        "Keyingi ishni ham shunday qoldirish",
        "Natijani ko‘rsatish mezonini jarayonning bir qismiga aylantirish",
        "Uni darhol jazolash",
        "Natijani o‘zing topish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_30"
    },
    {
      "q": "Bir loyiha bo‘yicha ikki xil raqam yuribdi.",
      "a": [
        "Manbalarni solishtirib, bitta ishonchli manbani belgilash",
        "Ko‘proq uchinchi raqamni topish",
        "Eng kattasini tanlash",
        "O‘rtachasini olish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_31"
    },
    {
      "q": "Jamoa “deadline bor” deb sifat tekshiruvini butunlay tashlamoqchi.",
      "a": [
        "Minimal majburiy sifat nazoratini saqlash",
        "Tekshiruvni abadiy davom ettirish",
        "Faqat dizaynni tekshirish",
        "Hamma tekshiruvni bekor qilish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_32"
    },
    {
      "q": "Xodim topshiriqni noto‘g‘ri tushungan, ammo topshiriqning o‘zi ham noaniq edi.",
      "a": [
        "Noaniqlikni tan olib, topshiriqni aniqroq qayta yozish",
        "Vazifani bekor qilish",
        "Faqat xodimni ayblash",
        "Xatoni yashirish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_33"
    },
    {
      "q": "Jamoada “kim nima qilishi” haqidagi bahs vaqtni yeb qo‘ymoqda.",
      "a": [
        "Bahsni davom ettirish",
        "Barchasini rahbar qilish",
        "Mas’uliyatni yozma ravishda taqsimlab, ishni boshlash",
        "Vazifani bekor qilish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_34"
    },
    {
      "q": "Mijoz juda ko‘p kichik o‘zgarish so‘rayapti, asosiy maqsad esa o‘zgarmagan.",
      "a": [
        "Mijozni almashtirish",
        "Barcha o‘zgarishni rad etish",
        "Har birini darhol qilish",
        "O‘zgarishlarni umumiy maqsadga ta’siri bo‘yicha saralash"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_35"
    },
    {
      "q": "Bir xodim jamoa oldida boshqa xodimning xatosini keskin tanqid qildi.",
      "a": [
        "Mavzuni butunlay yopish",
        "Tanqidni xatti-harakat va yechimga qaytarish",
        "Tanqidchini qo‘llab-quvvatlash",
        "Xato qilganni omma oldida koyish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_36"
    },
    {
      "q": "Jamoada odamlar faqat topshiriq kelganda harakat qilmoqda.",
      "a": [
        "Barchani almashtirish",
        "Maqsad va natija egaligini oshirish, tashabbus uchun joy berish",
        "Har soatda topshiriq berish",
        "Nazoratni ikki baravar oshirish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_37"
    },
    {
      "q": "Muhim mijoz bilan uchrashuvda sening xodiming xato javob berdi.",
      "a": [
        "Uchrashuvni darhol tugatish",
        "Uni mijoz oldida tanqid qilish",
        "Uchrashuvdan keyin aniqlik kiritib, xodim bilan alohida ishlash",
        "Xatoni yashirish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_38"
    },
    {
      "q": "Bir xodim yaxshi ishlaydi, ammo barcha bilimini o‘zida saqlaydi.",
      "a": [
        "Uni yanada ko‘proq ish bilan band qilish",
        "Boshqa xodimlarni chetlatish",
        "Bilimni hujjatlashtirish va jamoa ichida ulashishni rag‘batlantirish",
        "Bilimiga tegmaslik"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_39"
    },
    {
      "q": "Loyiha natijasi yomon, lekin sabablar ko‘p. Tahlilni nimadan boshlaysan?",
      "a": [
        "Eng oxirgi xatoni ayblash",
        "Hamma sababni teng deb olish",
        "Eng katta ta’sir qilgan sabablarni dalil bilan ajratish",
        "Birinchi topilgan sababni tanlash"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_40"
    },
    {
      "q": "Jamoada yaxshi fikr bor, lekin hech kim uning egasi emas.",
      "a": [
        "Uni rahbarning ishi qilish",
        "Yana fikr yig‘ish",
        "Fikrni yopish",
        "Fikr uchun mas’ul va keyingi qadamni aniq belgilash"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_41"
    },
    {
      "q": "Xodimning natijasi tushdi, lekin uning shaxsiy sharoitida o‘zgarish bo‘lganini bilasan.",
      "a": [
        "Avval insoniy suhbat, keyin aniq ish kutishlarini kelishish",
        "Darhol jazolash",
        "Muammoni e’tiborsiz qoldirish",
        "Boshqalarga aytish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_42"
    },
    {
      "q": "Biror vazifa juda katta bo‘lib, odamlar uni boshlamayapti.",
      "a": [
        "Uni tekshiriladigan kichik bosqichlarga bo‘lish",
        "Deadline ni olib tashlash",
        "Barcha vazifani bitta odamga berish",
        "Vazifani bekor qilish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_43"
    },
    {
      "q": "Jamoa qaror qildi, lekin hech kim nima uchunligini yozmagan.",
      "a": [
        "Qaror sababi va mezonini qisqa hujjatlashtirish",
        "Yana ovoz berish",
        "Qarorni bekor qilish",
        "Faqat rahbar eslab qolishi"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_44"
    },
    {
      "q": "Tashqi pudratchi sifatli ishladi, lekin keyingi safar narxi oshishini aytdi.",
      "a": [
        "Darhol rad etish",
        "Darhol rozi bo‘lish",
        "Narx, sifat va muqobillarni taqqoslab kelishish",
        "Narx haqida gaplashmaslik"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_45"
    },
    {
      "q": "Jamoada bir vazifa uchun besh kishi fikr bildiradi, lekin qaror egasi yo‘q.",
      "a": [
        "Hamma teng rahbar bo‘lishi",
        "Fikrlarni e’tiborsiz qoldirish",
        "Faqat eng baland ovozni tinglash",
        "Qaror egasini belgilash va maslahat beruvchilarni ajratish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_46"
    },
    {
      "q": "Loyiha foydali ko‘rinadi, ammo uning foydalanuvchisi aniq emas.",
      "a": [
        "Ko‘proq funksiya qo‘shish",
        "Budjetni oshirish",
        "Kimga va qanday muammo yechilishini aniqlash",
        "Darhol reklama qilish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_47"
    },
    {
      "q": "Jamoa a’zosi doim “bu imkonsiz” deydi, lekin dalil keltirmaydi.",
      "a": [
        "Fikrini e’tiborsiz qoldirish",
        "Uni jim qilish",
        "Qaysi cheklovga tayanganini so‘rab, taxminni faktga ajratish",
        "Darhol ishdan olish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_48"
    },
    {
      "q": "Yaxshi xodim boshqa kompaniyadan taklif oldi.",
      "a": [
        "Darhol almashtirish",
        "Uning sabablarini tinglab, real imkoniyatlarni ochiq muhokama qilish",
        "Ma’lumotni yashirish",
        "Uni qo‘rqitish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_49"
    },
    {
      "q": "Jamoa juda ko‘p KPI kuzatyapti, lekin hech biri qaror qabul qilishga yordam bermaydi.",
      "a": [
        "KPI sonini ko‘paytirish",
        "Faqat eng osonini tanlash",
        "KPI ni butunlay olib tashlash",
        "Eng muhim natijalarni o‘lchaydigan oz sonli KPI qoldirish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_50"
    },
    {
      "q": "Bir xodim doim yordam beradi, natijada o‘z vazifalari kechikadi.",
      "a": [
        "Buni muammo deb hisoblamaslik",
        "Yordam berish chegarasini belgilab, uning asosiy mas’uliyatini himoya qilish",
        "Uni yordam berishdan to‘liq to‘xtatish",
        "Boshqalarga barcha ishni berish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_51"
    },
    {
      "q": "Jamoada yangi jarayon bor, lekin hech kim undan foydalanmayapti.",
      "a": [
        "Jarima joriy qilish",
        "Jarayonni kuzatib, nima uchun ishlamayotganini topish",
        "Jarayonni majburlab o‘zgartirmaslik",
        "Yana hujjat yozish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_52"
    },
    {
      "q": "Rahbar sifatida sening fikringga hamma avtomatik “ha” deyapti.",
      "a": [
        "Qarorlarni yolg‘iz qilish",
        "Bundan xursand bo‘lib davom etish",
        "Hech kimni yig‘ilishga chaqirmaslik",
        "Qarshi fikr bildirishni ataylab so‘rash"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_53"
    },
    {
      "q": "Bir xodim xatosini tuzatdi, lekin sabab yana paydo bo‘lishi mumkin.",
      "a": [
        "Xatoni yopish",
        "Jarayonni o‘zgartirib, sababni yo‘qotish",
        "Faqat xodimni ogohlantirish",
        "Keyingi safar kutish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_54"
    },
    {
      "q": "Mijozga berilgan va’da jamoa imkoniyatidan katta chiqdi.",
      "a": [
        "Mijozni ayblash",
        "Jamoani majburlash",
        "Hech narsa demaslik",
        "Va’dani qayta kelishib, real variantlarni ko‘rsatish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_55"
    },
    {
      "q": "Ikki jamoa bir-birini ayblayapti, lekin muammo jarayonda.",
      "a": [
        "Jarayonning qaysi joyida uzilish bo‘lganini birga topish",
        "Muammoni yopish",
        "Bir jamoani jazolash",
        "Aybdorni ovoz bilan tanlash"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_56"
    },
    {
      "q": "Bir loyiha uchun juda ko‘p pul sarflandi, lekin foyda hali ko‘rinmadi.",
      "a": [
        "Sarflangan pulni hisoblamaslik",
        "Keyingi xarajatni natija mezoniga bog‘lash",
        "Darhol yopish",
        "Yana pul sarflash"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_57"
    },
    {
      "q": "Jamoa yangi a’zoni yaxshi qabul qilmadi.",
      "a": [
        "Moslashuv va rollarni ochiq tushuntirib, hamkorlik uchun kichik vazifa berish",
        "Yangi odamni darhol almashtirish",
        "Muammoni inkor qilish",
        "Jamoani jazolash"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_58"
    },
    {
      "q": "Yig‘ilishda hamma muammoni aytdi, lekin hech kim yechim taklif qilmadi.",
      "a": [
        "Yig‘ilishni yana bir soat cho‘zish",
        "Faqat rahbar yechim topishi",
        "Muammolarni o‘chirish",
        "Muammolarni ustuvor qilib, keyingi qadam egalarini belgilash"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_59"
    },
    {
      "q": "Jamoa bir qarorni tez qabul qilishi kerak, lekin qaror qaytarib bo‘lmaydi.",
      "a": [
        "Eng muhim xavflarni tekshirib, qaror mezonlarini qisqartirish",
        "Qarorni umuman qabul qilmaslik",
        "Har kimdan alohida fikr kutish",
        "Tasodifiy tanlash"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_60"
    },
    {
      "q": "Yangi xodim xato qilishdan qo‘rqib, hech qanday tashabbus ko‘rsatmayapti.",
      "a": [
        "Barcha ishni o‘zing qilish",
        "Uni tanqid qilish",
        "Xavfi kichik mustaqil vazifalar berib, feedback berish",
        "Uni faqat kuzatish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_61"
    },
    {
      "q": "Bir jamoa a’zosi boshqalardan ko‘proq ish olmoqda va norozi.",
      "a": [
        "Muammoni yashirish",
        "Unga yana ish berish",
        "Yuklamani ko‘rinadigan qilib, vazifalarni qayta muvozanatlash",
        "Norozi bo‘lganini tanqid qilish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_62"
    },
    {
      "q": "Muhim hujjatda ikki versiya bor va qaysi biri oxirgisi noma’lum.",
      "a": [
        "Yangi uchinchi versiya yaratish",
        "Eng kattasini tanlash",
        "Ikkalasini ham yuborish",
        "Bitta rasmiy versiyani belgilab, qolganini arxivlash"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_63"
    },
    {
      "q": "Jamoa juda tez qaror qilyapti va keyin ko‘p marta fikrini o‘zgartiryapti.",
      "a": [
        "Tezlikni yanada oshirish",
        "Qaror oldidan qisqa tekshiruv va mezon kiritish",
        "Barcha qarorni rahbarga berish",
        "Hech qanday qaror qilmaslik"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_64"
    },
    {
      "q": "Bir xodimning g‘oyasi yaxshi, lekin jamoa uni shaxsiy sabab bilan rad etmoqda.",
      "a": [
        "Jamoani darhol tarqatish",
        "G‘oyani avtomatik qabul qilish",
        "G‘oyani odamdan ajratib, mezon asosida baholash",
        "Xodimni himoya qilish uchun bahsni yopish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_65"
    },
    {
      "q": "Jamoa yaxshi ishlayapti, lekin hech kim keyingi oy uchun reja qilmagan.",
      "a": [
        "Keyingi muhim maqsadlarni jamoa bilan kelishish",
        "Barcha ishni to‘xtatish",
        "Hozirgi natija yetarli deyish",
        "Darhol yangi odam olish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_66"
    },
    {
      "q": "Xodimga berilgan feedback juda umumiy bo‘lib chiqdi.",
      "a": [
        "Faqat “yaxshi ishlagin” deyish",
        "Aniq misol, ta’sir va keyingi xatti-harakatni aytish",
        "Boshqa xodimdan aytishni so‘rash",
        "Feedbackni butunlay to‘xtatish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_67"
    },
    {
      "q": "Jamoa o‘zaro yordam so‘rashni zaiflik deb ko‘rmoqda.",
      "a": [
        "Muammolarni yashirish",
        "Faqat kuchlilarni maqtash",
        "Yordamni taqiqlash",
        "Yordam so‘rashni normal jarayon qilib, muammolarni erta ko‘rsatishni rag‘batlantirish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_68"
    },
    {
      "q": "Bir qaror bo‘yicha ma’lumotlar qarama-qarshi chiqdi.",
      "a": [
        "Qarorni tasodifiy qilish",
        "Manba ishonchliligini tekshirib, qaysi ma’lumotga tayanishni aniqlash",
        "Eng qulay ma’lumotni tanlash",
        "O‘rtacha qiymatni olish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_69"
    },
    {
      "q": "Jamoa a’zosi juda yaxshi natija berdi, lekin boshqalarga qo‘pol munosabatda bo‘ladi.",
      "a": [
        "Faqat xulqini jazolash",
        "Natijani ham, jamoaviy xulqni ham alohida feedback qilish",
        "Muammoni yashirish",
        "Natija uchun hammasini kechirish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_70"
    },
    {
      "q": "Loyiha maqsadi o‘zgardi, ammo eski vazifalar davom etmoqda.",
      "a": [
        "Yangi maqsadni e’tiborsiz qoldirish",
        "Eski reja bilan davom etish",
        "Barcha vazifani tugatish",
        "Eski vazifalarni yangi maqsadga moslab qayta saralash"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_71"
    },
    {
      "q": "Jamoada qarorlar tez, ammo bajarilishi sekin.",
      "a": [
        "Qarordan keyingi mas’ul va muddatni aniq belgilash",
        "Qarorlarni kamaytirish",
        "Ko‘proq yig‘ilish qilish",
        "Yana tezroq qaror qilish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_72"
    },
    {
      "q": "Bir loyiha boshqa loyihaga zarar yetkazmoqda.",
      "a": [
        "Har ikkalasiga ham bir xil resurs berish",
        "Hech narsa qilmaslik",
        "Resurslar va umumiy ustuvorlikni qayta ko‘rib chiqish",
        "Birini yashirish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_73"
    },
    {
      "q": "Xodim yaxshi ishlayapti, lekin undan doim bir xil ish talab qilinmoqda.",
      "a": [
        "Rivojlanish uchun murakkabroq mas’uliyat berish",
        "Ishini kamaytirish",
        "Uni boshqa joyga yuborish",
        "Faqat shu ishni davom ettirish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_74"
    },
    {
      "q": "Jamoa muhim vazifani tugatdi, lekin natija foydalanuvchida sinab ko‘rilmagan.",
      "a": [
        "Yana ichki yig‘ilish qilish",
        "Real foydalanuvchida tekshirib, feedback olish",
        "Natijani tayyor deb e’lon qilish",
        "Darhol bayram qilish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_75"
    },
    {
      "q": "Jamoa a’zosi “men bilaman” deb, tekshiruvni rad etdi.",
      "a": [
        "Unga ishonib ketish",
        "Uni chetlatish",
        "Muhim qarorda tekshiruvni standart sifatida saqlash",
        "Tekshiruvni hamma uchun bekor qilish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_76"
    },
    {
      "q": "Biror muammo faqat jamoa rahbari aralashganda hal bo‘ladi.",
      "a": [
        "Jamoaning o‘zi hal qila oladigan vakolatni oshirish",
        "Barcha vakolatni olib qo‘yish",
        "Har safar rahbarni chaqirish",
        "Muammoni rahbarga topshirish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_77"
    },
    {
      "q": "Jamoada kuchli odamlar ko‘p, lekin umumiy yo‘nalish yo‘q.",
      "a": [
        "Maqsadni bekor qilish",
        "Yagona maqsad va ustuvorliklarni qayta aniqlash",
        "Faqat eng kuchli odamni tinglash",
        "Har kimga alohida yo‘l berish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_78"
    },
    {
      "q": "Mijoz birinchi variantni rad etdi, lekin muammoni hal qilishga hali ham qiziqadi.",
      "a": [
        "Birinchi variantni majburlash",
        "Rad sababini o‘rganib, yangi variantni muammoga moslash",
        "Narxni avtomatik tushirish",
        "Mijozni yo‘qotilgan deb hisoblash"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_79"
    },
    {
      "q": "Jamoa xatosini tez tuzatadi, lekin xatolar soni kamaymayapti.",
      "a": [
        "Ko‘proq jazolash",
        "Tuzatishni tezlashtirish",
        "Takroriy sababni topish uchun naqshlarni tahlil qilish",
        "Xatolarni hisoblamaslik"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_80"
    },
    {
      "q": "Bir xodim juda ko‘p tashabbus ko‘rsatadi, lekin ustuvorlikni buzadi.",
      "a": [
        "Uning ishini butunlay olib qo‘yish",
        "Tashabbusni saqlab, ustuvorlik va kelishuv chegarasini belgilash",
        "Uni maqtash va davom ettirish",
        "Barcha tashabbusni taqiqlash"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_81"
    },
    {
      "q": "Jamoa bir qarorga kelolmayapti, chunki har kim boshqa mezondan foydalanmoqda.",
      "a": [
        "Avval baholash mezonlarini kelishish",
        "Yana fikr yig‘ish",
        "Rahbarning shaxsiy fikrini aytish",
        "Eng ko‘p ovoz olgan fikrni olish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_82"
    },
    {
      "q": "Yangi loyiha uchun ikki haftalik vaqt bor, lekin jamoa birinchi haftani rejasiz o‘tkazmoqda.",
      "a": [
        "Deadline ni olib tashlash",
        "Jamoani almashtirish",
        "Ikkinchi haftani uzaytirish",
        "Birinchi haftaning aniq natijasini belgilash"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_83"
    },
    {
      "q": "Jamoa a’zosi mijoz bilan kelishuvni og‘zaki qildi, yozma iz qoldirmadi.",
      "a": [
        "Mijozni ayblash",
        "Og‘zaki kelishuvni yetarli deb hisoblash",
        "Xodimni darhol ishdan olish",
        "Kelishuvni yozma tasdiqlash va kelajakda standart yaratish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_84"
    },
    {
      "q": "Jamoa ichida yaxshi savol berildi, lekin vaqt sabab javobsiz qoldi.",
      "a": [
        "Yig‘ilishni tugatish",
        "Savol berganni to‘xtatish",
        "Savolni unutish",
        "Savolni yozib, keyingi qaror nuqtasini belgilash"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_85"
    },
    {
      "q": "Bir xodimning ishini boshqa xodim doim qayta tekshiradi va ikkalasi ham sekinlashadi.",
      "a": [
        "Tekshiruvni ko‘paytirish",
        "Qaysi tekshiruv haqiqatan kerakligini aniqlab, ortiqcha bosqichni olib tashlash",
        "Bittasini ishdan olish",
        "Xatolarni e’tiborsiz qoldirish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_86"
    },
    {
      "q": "Jamoa ichida “bu mening ishim emas” degan gap ko‘paydi.",
      "a": [
        "Rol chegarasi va umumiy natija mas’uliyatini birga aniqlash",
        "Shikoyat qilganlarni jazolash",
        "Hamma ishni hamma qilishini talab qilish",
        "Faqat rahbar ishlashi"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_87"
    },
    {
      "q": "Bir xodim juda yaxshi fikr topdi, ammo uni amalga oshirish uchun boshqa bo‘lim kerak.",
      "a": [
        "Boshqa bo‘limni ayblash",
        "Hamkor bo‘lim bilan manfaat va keyingi qadamni aniq kelishish",
        "Fikrni tashlab yuborish",
        "Fikrni yashirish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_88"
    },
    {
      "q": "Jamoa juda ko‘p ma’lumot yig‘moqda, lekin qaror chiqarmayapti.",
      "a": [
        "Barcha ma’lumotni o‘chirish",
        "Qarorni tasodifiy qilish",
        "Qarorga ta’sir qiladigan minimal ma’lumotni ajratish",
        "Yana ma’lumot yig‘ish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_89"
    },
    {
      "q": "Mijozga xush keladigan, lekin bajarib bo‘lmaydigan va’da berish bosimi bor.",
      "a": [
        "Mijozga javob bermaslik",
        "Real imkoniyatni aytib, bajariladigan muqobil taklif qilish",
        "Jamoani majburlash",
        "Baribir va’da berish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_90"
    },
    {
      "q": "Jamoa a’zolari natijadan faxrlanmoqda, ammo bitta katta xavf qolgan.",
      "a": [
        "Faqat xavf haqida gapirish",
        "Yutuqni bekor qilish",
        "Xavfni yashirish",
        "Yutuqni tan olib, xavfni ham ochiq ko‘rsatish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_91"
    },
    {
      "q": "Rahbar sifatida sen juda ko‘p mayda qarorlarni o‘zing qilyapsan.",
      "a": [
        "Qayta takrorlanadigan qarorlar uchun qoidalar va vakolat berish",
        "Barcha qarorni o‘zingda qoldirish",
        "Mayda qarorlarni butunlay bekor qilish",
        "Jamoani qisqartirish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_92"
    },
    {
      "q": "Jamoa yangi usulni sinadi va natija yomon chiqdi.",
      "a": [
        "Hech qanday xulosa qilmaslik",
        "Aybdor qidirish",
        "Usulni darhol taqiqlash",
        "Nima ishlamaganini tahlil qilib, keyingi tajribani kichraytirish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_93"
    },
    {
      "q": "Xodim kuchli natija berdi, lekin uni qanday qilganini tushuntira olmaydi.",
      "a": [
        "Usulni yashirish",
        "Natijani yetarli deb hisoblash",
        "Jarayonni hujjatlashtirib, takrorlash mumkinligini tekshirish",
        "Uni boshqa ishga o‘tkazish"
      ],
      "correct": 2,
      "kind": "leadership",
      "id": "leadership_94"
    },
    {
      "q": "Jamoada bir qaror tez-tez qayta ochiladi.",
      "a": [
        "Qaysi yangi ma’lumot qarorni o‘zgartirishi mumkinligini oldindan belgilash",
        "Qarorni hech qachon o‘zgartirmaslik",
        "Barcha qarorni rahbarga berish",
        "Har safar qayta ovoz berish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_95"
    },
    {
      "q": "Bir jamoa a’zosi boshqalardan doim ko‘proq ma’lumot oladi.",
      "a": [
        "Ma’lumotga kirishni teng va rolga mos qilish",
        "Boshqalardan yashirish",
        "Ma’lumotni umuman yopish",
        "Unga yanada ko‘proq berish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_96"
    },
    {
      "q": "Jamoa a’zosi muammoni ko‘rsatdi, lekin yechimni bilmadi.",
      "a": [
        "Muammoni ko‘rsatgani uchun rag‘batlantirib, yechimni birga izlash",
        "Muammo ko‘rsatishni taqiqlash",
        "Uni ayblash",
        "Muammoni yopish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_97"
    },
    {
      "q": "Yangi loyiha juda hayajonli, lekin foydalanuvchi ehtiyoji hali tekshirilmagan.",
      "a": [
        "Avval foydalanuvchi ehtiyojini tekshirish",
        "Darhol katta jamoa yig‘ish",
        "Reklama boshlash",
        "Budjetni oshirish"
      ],
      "correct": 0,
      "kind": "leadership",
      "id": "leadership_98"
    },
    {
      "q": "Jamoa bir xodimga haddan tashqari bog‘langan.",
      "a": [
        "Shu odamni yanada muhim qilish",
        "Vazifalarni juftlik va hujjat orqali bo‘lish",
        "Muammoni kutish",
        "Boshqa xodimlarni chetlatish"
      ],
      "correct": 1,
      "kind": "leadership",
      "id": "leadership_99"
    },
    {
      "q": "Muhim qaror qabul qilindi, lekin jamoa nima uchunligini tushunmayapti.",
      "a": [
        "Qarorni yashirish",
        "Faqat buyruq berish",
        "Qarorni bekor qilish",
        "Qaror sababi, mezoni va kutilgan natijani tushuntirish"
      ],
      "correct": 3,
      "kind": "leadership",
      "id": "leadership_100"
    }
  ]
}
FUN_TESTS={'love': {'name': '❤️ Sevgi uslubing', 'paid': False, 'intro': 'Munosabatlarda qanday yo‘l tutishingni ko‘r. Bu ko‘ngilochar self-reflection testi.', 'questions': [{'q': 'Yaqin insoning kayfiyati tushganini sezsang, odatda?', 'a': ['Gaplashishga joy beraman', 'Darhol yechim izlayman', 'Hazil bilan kayfiyatini ko‘taraman', 'Nima bo‘lganini kutaman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 2, 2, 1]}, {'q': 'Senga ko‘ra yaxshi munosabatning eng muhim belgisi?', 'a': ['Ishonch', 'Doimiy yozishish', 'Qimmat sovg‘alar', 'Hamma narsada bir xil fikr'], 'correct': 0, 'kind': 'profile', 'weights': [3, 2, 1, 1]}, {'q': 'Bahs paytida sen ko‘proq...', 'a': ['Tushunishga urinaman', 'G‘alaba qilishni xohlayman', 'Jim bo‘lib qolaman', 'Mavzuni o‘zgartiraman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 2, 1]}, {'q': 'Yaqin insoning kichik yutug‘iga munosabating?', 'a': ['Chin dildan xursand bo‘laman', 'Oddiy qabul qilaman', 'O‘zim bilan solishtiraman', 'Keyin tabriklayman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 2, 1, 1]}, {'q': 'Sovg‘ada nimani ko‘proq qadrlaysan?', 'a': ['Ma’nosini', 'Narxini', 'Kattaligini', 'Kutilmaganligini'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 1, 2]}, {'q': 'Senga yoqmaydigan gapni eshitsang...', 'a': ['Tinch paytda aytaman', 'Darhol javob qaytaraman', 'Ichimda saqlayman', 'Hazilga buraman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 2, 1]}, {'q': 'Birga vaqt o‘tkazishda...', 'a': ['Sifatli suhbat', 'Ko‘proq tashqariga chiqish', 'Telefon ko‘rish', 'Har kim o‘z ishida'], 'correct': 0, 'kind': 'profile', 'weights': [3, 2, 1, 1]}, {'q': 'Ishonch buzilsa...', 'a': ['Sabab va chegaralarni ochiq gaplashaman', 'Darhol tugataman', 'Hech narsa bo‘lmagandek yuraman', 'Do‘stlardan maslahat olaman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 1, 2]}]}, 'effort': {'name': '🔥 Tirishqoqlik testi', 'paid': False, 'intro': 'Maqsadga yaqinlashganda odatda qanday yo‘l tutishingni ko‘r.', 'questions': [{'q': 'Rejangdagi ish kutilganidan qiyin chiqdi.', 'a': ['Usulni o‘zgartirib davom etaman', 'Tashlayman', 'Boshqa odamni kutaman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 0, 1]}, {'q': 'Natija chiqmayotgan bo‘lsa, birinchi qiladigan ishing?', 'a': ['Xatoni tahlil qilaman', 'Ko‘proq vaqt sarflayman', 'Mavzuni almashtiraman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 2, 0]}, {'q': 'Katta maqsad oldida...', 'a': ['Uni kichik bosqichlarga bo‘laman', 'Faqat motivatsiya kutaman', 'Oxirida boshlayman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 0]}, {'q': 'Bir kun rejang buzildi.', 'a': ['Ertasi yana davom etaman', 'Hammasini bekor qilaman', 'Yangi oy boshlanishini kutaman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 0, 1]}, {'q': 'Qiyin topshiriqda yordam so‘rash haqida?', 'a': ['Kerak bo‘lsa so‘rayman', 'Hech qachon so‘ramayman', 'Darhol boshqaga beraman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 2, 1]}, {'q': 'Natijang past chiqdi.', 'a': ['Nimani yaxshilashni izlayman', 'Bu meniki emas deyman', 'Keyinroq ko‘raman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 0, 1]}, {'q': 'Bir ish zerikarli, ammo muhim.', 'a': ['Uni vaqtga bo‘lib bajaraman', 'Doim kechiktiraman', 'Faqat kayfiyat bo‘lsa qilaman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 0, 1]}, {'q': 'Maqsadingga yaqinlashding, lekin charchading.', 'a': ['Sur’atni moslab davom etaman', 'Butunlay to‘xtayman', 'Maqsadni o‘zgartiraman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 0, 1]}]}, 'stress': {'name': '🧠 Bosim ostidagi uslubing', 'paid': True, 'cost': 50, 'intro': 'Bosim va noaniqlikda qanday qaror qilishga moyilligingni ko‘rsatadigan ko‘ngilochar test.', 'questions': [{'q': 'Bir vaqtning o‘zida uchta ish shoshilinch bo‘lib qoldi.', 'a': ['Ustuvorlikni ajrataman', 'Hammasini birdan boshlayman', 'Eng osonini qilaman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 1]}, {'q': 'Kutilmagan muammo chiqdi.', 'a': ['Avval faktlarni yig‘aman', 'Darhol qaror qilaman', 'Muammoni keyinga qoldiraman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 0]}, {'q': 'Bosim kuchayganda...', 'a': ['Ritmni sekinlashtirib, muhim ishni ajrataman', 'Tezroq ishlashga urinaman', 'Boshqa odamga beraman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 2, 1]}, {'q': 'Rejang birdan ishlamay qoldi.', 'a': ['Yangi yo‘lni sinab ko‘raman', 'Rejani majburan davom ettiraman', 'Hammasini to‘xtataman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 2, 0]}, {'q': 'Jamoa vahimaga tushdi.', 'a': ['Vaziyatni qisqa va aniq tushuntiraman', 'Men ham vahimaga tushaman', 'Hech narsa demayman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 1]}, {'q': 'Muhim qarorda ma’lumotning bir qismi yetishmayapti.', 'a': ['Qaysi ma’lumot eng zarurini aniqlayman', 'Taxmin bilan ketaman', 'Qarorni cheksiz kechiktiraman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 1]}, {'q': 'Xato qilding va vaqt kam.', 'a': ['Ta’sirini kamaytirib, tuzatishga o‘taman', 'Xatoni yashiraman', 'Kim aybdorligini izlayman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 0, 1]}, {'q': 'Biror ish ketma-ket ikki marta muvaffaqiyatsiz bo‘ldi.', 'a': ['Usulni tahlil qilib o‘zgartiraman', 'Uchinchi marta aynan takrorlayman', 'Butunlay tashlayman'], 'correct': 0, 'kind': 'profile', 'weights': [3, 1, 0]}]}}
QUESTION_SETS={'iq':'Aql','speed':'Tezlik','memory':'Xotira','leadership':'Liderlik'}
TIME_LIMITS={'iq':90,'speed':20,'memory':60,'leadership':90}
MAX_TEST_AGE=60*60
bot=Bot(token=BOT_TOKEN);dp=Dispatcher();app=FastAPI();db_pool=None

# ---------- Telegram auth ----------
def validate_init_data(init_data:str):
    if not init_data: return None
    try:
        p=dict(urllib.parse.parse_qsl(init_data,keep_blank_values=True))
        received=p.pop('hash',None)
        if not received: return None
        check='\n'.join(f'{k}={p[k]}' for k in sorted(p))
        secret=hmac.new(b'WebAppData',BOT_TOKEN.encode(),hashlib.sha256).digest()
        calc=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc,received): return None
        if p.get('auth_date') and datetime.now(timezone.utc).timestamp()-int(p['auth_date'])>86400: return None
        return json.loads(p['user']) if p.get('user') else None
    except Exception:return None

def telegram_user_from_request(request,body=None):
    raw=request.headers.get('X-Telegram-Init-Data','')
    if body and body.get('initData'): raw=body['initData']
    return validate_init_data(raw)

def sign_token(payload):
    raw=json.dumps(payload,separators=(',',':'),ensure_ascii=False).encode();sig=hmac.new(BOT_TOKEN.encode(),raw,hashlib.sha256).hexdigest()[:32]
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')+'.'+sig

def verify_token(token):
    try:
        b,s=token.split('.',1);raw=base64.urlsafe_b64decode(b+'='*((4-len(b)%4)%4));calc=hmac.new(BOT_TOKEN.encode(),raw,hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(calc,s): return None
        p=json.loads(raw);return p if datetime.now(timezone.utc).timestamp()-p['ts']<=MAX_TEST_AGE else None
    except Exception:return None

# ---------- Database ----------
async def init_db():
    global db_pool
    db_pool=await asyncpg.create_pool(DATABASE_URL,min_size=1,max_size=5,command_timeout=15)
    async with db_pool.acquire() as c:
        await c.execute('''CREATE TABLE IF NOT EXISTS users(
          telegram_id BIGINT PRIMARY KEY,username TEXT,first_name TEXT,
          best_score INTEGER NOT NULL DEFAULT 0,global_score INTEGER NOT NULL DEFAULT 0,
          coins INTEGER NOT NULL DEFAULT 0,tests_taken INTEGER NOT NULL DEFAULT 0,
          streak INTEGER NOT NULL DEFAULT 0,last_daily_reward DATE,
          recent_questions JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
        for sql in [
          'ALTER TABLE users ADD COLUMN IF NOT EXISTS global_score INTEGER NOT NULL DEFAULT 0',
          'ALTER TABLE users ADD COLUMN IF NOT EXISTS coins INTEGER NOT NULL DEFAULT 0',
          'ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER NOT NULL DEFAULT 0',
          'ALTER TABLE users ADD COLUMN IF NOT EXISTS last_daily_reward DATE',
          'ALTER TABLE users ADD COLUMN IF NOT EXISTS recent_questions JSONB NOT NULL DEFAULT \'{}\'::jsonb',
          'CREATE INDEX IF NOT EXISTS idx_users_global_score ON users(global_score DESC,updated_at ASC)']:
            await c.execute(sql)
        await c.execute('''CREATE TABLE IF NOT EXISTS test_results(
          id BIGSERIAL PRIMARY KEY,telegram_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
          test_type TEXT NOT NULL,score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
          correct_answers INTEGER NOT NULL,total_questions INTEGER NOT NULL,
          total_time_seconds REAL NOT NULL DEFAULT 0,coins_earned INTEGER NOT NULL DEFAULT 0,
          idempotency_key TEXT UNIQUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
        await c.execute('ALTER TABLE test_results ADD COLUMN IF NOT EXISTS idempotency_key TEXT')
        await c.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_test_results_idem ON test_results(idempotency_key) WHERE idempotency_key IS NOT NULL')
        await c.execute('CREATE INDEX IF NOT EXISTS idx_test_results_user ON test_results(telegram_id,created_at DESC)')
        # Repair legacy global scores from actual history; never use best score as global score.
        await c.execute('''UPDATE users u SET global_score=COALESCE((SELECT SUM(score) FROM test_results t WHERE t.telegram_id=u.telegram_id),0)
                           WHERE EXISTS(SELECT 1 FROM test_results t2 WHERE t2.telegram_id=u.telegram_id)''')

async def upsert_user(user):
    tid=int(user['id'])
    async with db_pool.acquire() as c:
        await c.execute('''INSERT INTO users(telegram_id,username,first_name) VALUES($1,$2,$3)
          ON CONFLICT(telegram_id) DO UPDATE SET username=EXCLUDED.username,first_name=EXCLUDED.first_name,updated_at=NOW()''',tid,user.get('username'),user.get('first_name',''))
    return tid

@dp.message(CommandStart())
async def start_handler(message:types.Message):
    kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🚀 ZAKO\'NI OCHISH',web_app=WebAppInfo(url=PUBLIC_URL))]])
    await message.answer('🧠 <b>ZAKO</b>\n\nO\'zingni sinab ko\'r.\nQanchalik ZAKOsan?',reply_markup=kb,parse_mode='HTML')

# ---------- routes ----------
@app.get('/',response_class=HTMLResponse)
async def home(): return HTMLResponse(HTML,headers={'Cache-Control':'no-store,no-cache,must-revalidate,max-age=0','Pragma':'no-cache','Expires':'0'})
@app.head('/')
async def head_home(): return HTMLResponse('',headers={'Cache-Control':'no-store'})
@app.get('/health')
async def health(): return {'status':'ok','question_counts':{k:len(v) for k,v in QUESTION_BANKS.items()},'ai_enabled':bool(OPENAI_API_KEY),'database':db_pool is not None}
@app.post('/telegram/webhook')
async def webhook(request:Request):
    data=await request.json();upd=types.Update.model_validate(data,context={'bot':bot});await dp.feed_update(bot,upd);return {'ok':True}

@app.post('/api/test/start')
async def test_start(request:Request):
    body=await request.json(); user=telegram_user_from_request(request,body)
    if not user:return {'ok':False,'error':'Telegram sessiyasi tasdiqlanmadi.'}
    typ=body.get('testType','iq')
    if typ not in QUESTION_BANKS:return {'ok':False,'error':'Test turi noto‘g‘ri.'}
    tid=await upsert_user(user)
    async with db_pool.acquire() as c: row=await c.fetchrow('SELECT recent_questions FROM users WHERE telegram_id=$1',tid)
    recent=row['recent_questions'] if row and isinstance(row['recent_questions'],dict) else {}
    used=set(recent.get(typ,[])); pool=QUESTION_BANKS[typ]
    available=[x for x in pool if x['id'] not in used]
    if len(available)<10: available=pool
    selected=random.sample(available,10)
    # Never expose correct answer or scoring metadata to client.
    qs=[{'id':x['id'],'q':x['q'],'a':x['a'],'memoryPrompt':x.get('memory_prompt')} for x in selected]
    token=sign_token({'uid':tid,'type':typ,'q':[x['id'] for x in selected],'ts':datetime.now(timezone.utc).timestamp(),'nonce':secrets.token_hex(8)})
    return {'ok':True,'testToken':token,'testType':typ,'testName':QUESTION_SETS[typ],'timeLimit':TIME_LIMITS[typ],'questions':qs}

@app.post('/api/test/submit')
async def test_submit(request:Request):
    body=await request.json();user=telegram_user_from_request(request,body)
    if not user:return {'ok':False,'error':'Telegram sessiyasi tasdiqlanmadi.'}
    tid=int(user['id']);tok=verify_token(body.get('testToken',''))
    if not tok or int(tok['uid'])!=tid:return {'ok':False,'error':'Test sessiyasi eskirgan. Testni qayta boshlang.'}
    answers=body.get('answers');expected=tok['q'];typ=tok['type']
    if not isinstance(answers,list) or len(answers)!=10:return {'ok':False,'error':'Test to‘liq yakunlanmagan.'}
    lookup={x['id']:x for x in QUESTION_BANKS[typ]};seen=set();correct=0;total_time=0.0
    for item in answers:
        try:qid=str(item['questionId']);ai=int(item['answerIndex']);ts=float(item.get('timeSeconds',0))
        except Exception:return {'ok':False,'error':'Javob ma’lumotlari noto‘g‘ri.'}
        if qid not in expected or qid in seen or qid not in lookup:return {'ok':False,'error':'Javoblar tartibi noto‘g‘ri.'}
        if not -1<=ai<len(lookup[qid]['a']):return {'ok':False,'error':'Javob varianti noto‘g‘ri.'}
        if ts<0 or ts>TIME_LIMITS[typ]+120:return {'ok':False,'error':'Javob vaqti noto‘g‘ri.'}
        seen.add(qid);total_time+=ts
        if ai==lookup[qid]['correct']:correct+=1
    if seen!=set(expected):return {'ok':False,'error':'Barcha savollar javoblanmagan.'}
    score=correct*10
    if typ=='speed':
        avg=total_time/10;bonus=max(0,min(30,round((1-avg/TIME_LIMITS['speed'])*30)))
        score=max(0,min(100,round(correct*7+bonus)))
    coins=10+correct*2+(10 if score>=90 else 0)
    idem=hashlib.sha256((str(tid)+'|'+tok.get('nonce','')).encode()).hexdigest()
    async with db_pool.acquire() as c:
        async with c.transaction():
            old=await c.fetchrow('SELECT score,correct_answers,total_questions,coins_earned FROM test_results WHERE idempotency_key=$1',idem)
            if old:
                u=await c.fetchrow('SELECT global_score,best_score,tests_taken,coins FROM users WHERE telegram_id=$1',tid)
                return {'ok':True,'score':old['score'],'correctAnswers':old['correct_answers'],'totalQuestions':old['total_questions'],'coinsEarned':old['coins_earned'],'globalScore':u['global_score'],'duplicate':True}
            row=await c.fetchrow('SELECT global_score,best_score,tests_taken,recent_questions FROM users WHERE telegram_id=$1 FOR UPDATE',tid)
            if not row:return {'ok':False,'error':'Foydalanuvchi topilmadi.'}
            recent=dict(row['recent_questions'] or {});arr=list(recent.get(typ,[]));arr.extend(expected);recent[typ]=arr[-90:]
            global_score=int(row['global_score'])+score;best=max(int(row['best_score']),score);tests=int(row['tests_taken'])+1
            await c.execute('''INSERT INTO test_results(telegram_id,test_type,score,correct_answers,total_questions,total_time_seconds,coins_earned,idempotency_key)
              VALUES($1,$2,$3,$4,10,$5,$6,$7)''',tid,typ,score,correct,round(total_time,2),coins,idem)
            await c.execute('''UPDATE users SET global_score=$2,best_score=$3,coins=coins+$4,tests_taken=$5,recent_questions=$6::jsonb,updated_at=NOW() WHERE telegram_id=$1''',tid,global_score,best,coins,tests,json.dumps(recent,separators=(',',':')))
    return {'ok':True,'score':score,'correctAnswers':correct,'totalQuestions':10,'testType':typ,'coinsEarned':coins,'globalScore':global_score,'insight':insight_for(typ,score,correct)}

def insight_for(typ,score,correct):
    texts={
      'iq':['Mantiqiy bog‘lanishlarni izlashga yaxshi moyilsan.','Murakkab savollarda shoshilmasang, kuching yanada ko‘rinadi.','Qiyin savollarda birinchi taxminni tekshirish foydali.'],
      'speed':['Tez qaror va aniqlikni birga ushlay olasan.','Tezlik yaxshi, endi aniqlikni yanada barqaror qil.','Shoshilishdan ko‘ra ritmni topish senga ko‘proq foyda beradi.'],
      'memory':['Ma’lumotni tartib bilan ushlash kuchli tomoning bo‘lishi mumkin.','Diqqatni bir nuqtaga jamlaganingda xotirang yaxshiroq ishlaydi.','Xotirada tafsilotlarni mustahkamlash uchun guruhlash foydali.'],
      'leadership':['Qaror paytida vaziyatni tizimlashtirishga moyilsan.','Odamlar va natija o‘rtasidagi muvozanat muhim kuching bo‘lishi mumkin.','Yaxshi rahbar qarorni ham, uning sababini ham tushuntiradi.']}
    arr=texts[typ];return arr[0 if score>=80 else 1 if score>=60 else 2]

@app.get('/api/me')
async def me(request:Request):
    user=telegram_user_from_request(request)
    if not user:return {'ok':False,'error':'Telegram sessiyasi tasdiqlanmadi.'}
    tid=await upsert_user(user)
    async with db_pool.acquire() as c:
        u=await c.fetchrow('SELECT telegram_id,username,first_name,best_score,global_score,coins,tests_taken,streak,last_daily_reward FROM users WHERE telegram_id=$1',tid)
        rows=await c.fetch('SELECT test_type,AVG(score)::float AS avg FROM test_results WHERE telegram_id=$1 GROUP BY test_type',tid)
    cats={r['test_type']:round(float(r['avg'])) for r in rows};vals=list(cats.values());overall=round(sum(vals)/len(vals)) if vals else 0
    level=max(1,1+int(u['global_score'])//250)
    return {'ok':True,'user':{'id':u['telegram_id'],'username':u['username'],'first_name':u['first_name']},'global_score':u['global_score'],'coins':u['coins'],'tests_taken':u['tests_taken'],'best_score':u['best_score'],'level':level,'category_scores':cats,'overall_percent':overall,'streak':u['streak']}

@app.get('/api/ranking')
async def ranking():
    async with db_pool.acquire() as c: rows=await c.fetch('SELECT first_name,username,global_score,tests_taken FROM users WHERE tests_taken>0 ORDER BY global_score DESC,updated_at ASC LIMIT 100')
    return {'ok':True,'users':[dict(r) for r in rows]}

@app.post('/api/reward/daily')
async def daily(request:Request):
    body=await request.json();user=telegram_user_from_request(request,body)
    if not user:return {'ok':False,'error':'Telegram sessiyasi tasdiqlanmadi.'}
    tid=await upsert_user(user);today=date.today()
    async with db_pool.acquire() as c:
        async with c.transaction():
            row=await c.fetchrow('SELECT streak,last_daily_reward FROM users WHERE telegram_id=$1 FOR UPDATE',tid)
            if row['last_daily_reward']==today:return {'ok':False,'error':'Bugungi bonus allaqachon olingan.'}
            streak=(int(row['streak'])+1) if row['last_daily_reward'] and (today-row['last_daily_reward']).days==1 else 1
            coins=10+min(streak,7)*2
            await c.execute('UPDATE users SET coins=coins+$2,streak=$3,last_daily_reward=$4,updated_at=NOW() WHERE telegram_id=$1',tid,coins,streak,today)
    return {'ok':True,'coins':coins,'streak':streak}

# ---------- fun tests ----------
@app.get('/api/fun-tests')
async def fun_tests():
    return {'ok':True,'tests':[{'id':k,'name':v['name'],'paid':v['paid'],'intro':v['intro'],'questionCount':len(v['questions'])} for k,v in FUN_TESTS.items()]}
@app.post('/api/fun/start')
async def fun_start(request:Request):
    body=await request.json();user=telegram_user_from_request(request,body)
    if not user:return {'ok':False,'error':'Telegram sessiyasi tasdiqlanmadi.'}
    tid=await upsert_user(user);typ=body.get('type');test=FUN_TESTS.get(typ)
    if not test:return {'ok':False,'error':'Bunday test yo‘q.'}
    cost=int(test.get('cost',0)) if test.get('paid') else 0
    if cost:
        async with db_pool.acquire() as c:
            async with c.transaction():
                row=await c.fetchrow('SELECT coins FROM users WHERE telegram_id=$1 FOR UPDATE',tid)
                if not row or int(row['coins'])<cost:return {'ok':False,'error':f'Bu test {cost} coin turadi. Coin yetarli emas.'}
                await c.execute('UPDATE users SET coins=coins-$2,updated_at=NOW() WHERE telegram_id=$1',tid,cost)
    qs=[{'id':f'{typ}_{i}','q':x['q'],'a':x['a']} for i,x in enumerate(test['questions'])]
    return {'ok':True,'token':sign_token({'uid':tid,'fun':typ,'ts':datetime.now(timezone.utc).timestamp(),'nonce':secrets.token_hex(8)}),'name':test['name'],'questions':qs,'cost':cost}
@app.post('/api/fun/submit')
async def fun_submit(request:Request):
    body=await request.json();user=telegram_user_from_request(request,body);tok=verify_token(body.get('token','')) if user else None
    if not user or not tok or int(tok['uid'])!=int(user['id']) or 'fun' not in tok:return {'ok':False,'error':'Test sessiyasi eskirgan.'}
    test=FUN_TESTS[tok['fun']];answers=body.get('answers',[])
    if len(answers)!=len(test['questions']):return {'ok':False,'error':'Test to‘liq tugatilmagan.'}
    total=0
    for i,item in enumerate(answers):
        try: total+=int(test['questions'][i]['weights'][int(item['answerIndex'])])
        except Exception:return {'ok':False,'error':'Javoblar noto‘g‘ri.'}
    max_total=len(test['questions'])*3;score=round(total/max_total*100)
    labels=['Juda kuchli','Yaxshi shakllangan','Muvozanatli','Yana bir tomoningni sinab ko‘r']
    label=labels[0 if score>=85 else 1 if score>=70 else 2 if score>=50 else 3]
    return {'ok':True,'score':score,'label':label,'text':fun_result(tok['fun'],score),'coinsEarned':0}

def fun_result(typ,score):
    if typ=='love':
        return 'Sen munosabatlarda e’tibor va samimiyatni qadrlaydigan, yaqin insonni tushunishga intiladigan odamsan.' if score>=70 else 'Sen uchun munosabatda erkinlik va o‘zaro hurmat muhim ko‘rinadi.'
    return 'Maqsadga kelganda taslim bo‘lishdan ko‘ra yo‘lni o‘zgartirishga moyilsan. Bu yaxshi ustunlik.' if score>=70 else 'Senga kichik, aniq bosqichlar bilan ishlash ayniqsa mos kelishi mumkin.'

# ---------- Optional AI tools ----------
async def ai_text(prompt):
    if not OPENAI_API_KEY:return None
    try:
        from openai import AsyncOpenAI
        client=AsyncOpenAI(api_key=OPENAI_API_KEY)
        r=await client.responses.create(model=OPENAI_MODEL,input=prompt)
        return r.output_text
    except Exception as e:
        return None

@app.post('/api/ai/text-to-test')
async def ai_text_to_test(request:Request):
    body=await request.json();user=telegram_user_from_request(request,body)
    if not user:return {'ok':False,'error':'Telegram sessiyasi tasdiqlanmadi.'}
    if not OPENAI_API_KEY:return {'ok':False,'error':'AI hozir ulanmagan. OPENAI_API_KEY kerak.'}
    text=str(body.get('text',''))[:30000]
    if len(text)<30:return {'ok':False,'error':'Kamida 30 ta belgidan iborat matn yuboring.'}
    out=await ai_text('''Quyidagi o‘quv matnidan o‘zbek tilida 10 ta mazmunan turlicha test tuz. Har birida 3 yoki 4 variant bo‘lsin. Faqat matndan tekshiriladigan savollar. JSON array qaytar: q, a, correct.\n\n'''+text)
    if not out:return {'ok':False,'error':'AI javob bermadi. Keyinroq urinib ko‘ring.'}
    try:data=json.loads(out[out.find('['):out.rfind(']')+1]);return {'ok':True,'questions':data}
    except Exception:return {'ok':False,'error':'AI natijasini o‘qib bo‘lmadi.'}

@app.post('/api/ai/pdf-to-summary')
async def ai_pdf_summary(request:Request,file:UploadFile=File(...)):
    user=telegram_user_from_request(request)
    if not user:return {'ok':False,'error':'Telegram sessiyasi tasdiqlanmadi.'}
    if not OPENAI_API_KEY:return {'ok':False,'error':'AI hozir ulanmagan. OPENAI_API_KEY kerak.'}
    text=extract_pdf_text(await file.read())
    if len(text)<30:return {'ok':False,'error':'PDFdan yetarli matn topilmadi.'}
    out=await ai_text('Quyidagi PDF matnini o‘zbek tilida aniq, qisqa konspektga aylantir. Sarlavhalar, asosiy fikrlar va yakuniy xulosadan foydalan.\n\n'+text)
    return {'ok':bool(out),'summary':out or 'AI javob bermadi.'}

@app.post('/api/ai/pdf-to-test')
async def ai_pdf_to_test(request:Request,file:UploadFile=File(...)):
    user=telegram_user_from_request(request)
    if not user:return {'ok':False,'error':'Telegram sessiyasi tasdiqlanmadi.'}
    if not OPENAI_API_KEY:return {'ok':False,'error':'AI hozir ulanmagan. OPENAI_API_KEY kerak.'}
    text=extract_pdf_text(await file.read())
    if len(text)<50:return {'ok':False,'error':'PDFdan yetarli matn topilmadi.'}
    prompt='Quyidagi o‘quv materialidan o‘zbek tilida 10 ta mazmunan turlicha test tuz. Savollar faktni ko‘chirib qo‘yish emas, tushunishni tekshirsin. 2 ta savol ha/yo‘q, 3 ta savol 3 variantli, qolganlari 4 variantli bo‘lsin. Har bir savolda faqat bitta aniq to‘g‘ri javob bo‘lsin. Faqat JSON array qaytar: [{"q":"...","a":[...],"correct":0}].\n\n'+text
    out=await ai_text(prompt)
    if not out:return {'ok':False,'error':'AI javob bermadi.'}
    try:return {'ok':True,'questions':json.loads(out[out.find('['):out.rfind(']')+1])}
    except Exception:return {'ok':False,'error':'AI test natijasini o‘qib bo‘lmadi.'}

@app.post('/api/ai/pdf-to-slides')
async def ai_pdf_to_slides(request:Request,file:UploadFile=File(...)):
    user=telegram_user_from_request(request)
    if not user:return {'ok':False,'error':'Telegram sessiyasi tasdiqlanmadi.'}
    if not OPENAI_API_KEY:return {'ok':False,'error':'AI hozir ulanmagan. OPENAI_API_KEY kerak.'}
    text=extract_pdf_text(await file.read())
    if len(text)<80:return {'ok':False,'error':'PDFdan yetarli matn topilmadi.'}
    prompt='Quyidagi materialdan 8 slaydlik o‘zbekcha prezentatsiya rejasi tuz. Har slaydda title va 3-5 ta qisqa bullet bo‘lsin. JSON array qaytar: [{"title":"...","bullets":["...","..."]}]. Matnni keraksiz cho‘zma.\n\n'+text
    out=await ai_text(prompt)
    if not out:return {'ok':False,'error':'AI javob bermadi.'}
    try:slides=json.loads(out[out.find('['):out.rfind(']')+1])
    except Exception:return {'ok':False,'error':'AI slayd rejasini o‘qib bo‘lmadi.'}
    try:
        from pptx import Presentation
        from pptx.util import Pt
        root=Path('/tmp/zako_files');root.mkdir(exist_ok=True)
        name=secrets.token_hex(18)+'.pptx';path=root/name
        prs=Presentation()
        for i,sl in enumerate(slides[:12]):
            layout=prs.slide_layouts[1 if i else 0];slide=prs.slides.add_slide(layout)
            slide.shapes.title.text=str(sl.get('title','ZAKO'))
            if i and len(slide.placeholders)>1:
                tf=slide.placeholders[1].text_frame;tf.clear()
                for j,b in enumerate(sl.get('bullets',[])[:5]):
                    para=tf.paragraphs[0] if j==0 else tf.add_paragraph();para.text=str(b);para.level=0;para.font.size=Pt(22)
        prs.save(path)
        return {'ok':True,'fileUrl':f'/api/ai/download/{name}','slides':len(prs.slides)}
    except Exception:return {'ok':False,'error':'PPTX yaratishda xato.'}

@app.get('/api/ai/download/{name}')
async def ai_download(name:str):
    if not re.fullmatch(r'[0-9a-f]{36}\.pptx',name):return JSONResponse({'ok':False,'error':'Fayl topilmadi.'},status_code=404)
    path=Path('/tmp/zako_files')/name
    if not path.exists():return JSONResponse({'ok':False,'error':'Fayl muddati tugagan.'},status_code=404)
    return FileResponse(path,media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',filename='ZAKO_slides.pptx')

def extract_pdf_text(data:bytes):
    try:
        import fitz
        doc=fitz.open(stream=data,filetype='pdf')
        return '\n'.join(p.get_text() for p in doc)[:60000]
    except Exception:return ''

@asynccontextmanager
async def lifespan(app_instance:FastAPI):
    await init_db()
    try:
        await bot.set_webhook(url=PUBLIC_URL+'/telegram/webhook',drop_pending_updates=True)
    except Exception: pass
    yield
    try: await bot.delete_webhook(drop_pending_updates=False)
    except Exception: pass
    await db_pool.close()
app.router.lifespan_context=lifespan

HTML='<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no"><meta name="theme-color" content="#090b0f"><title>ZAKO</title><script src="https://telegram.org/js/telegram-web-app.js"></script><style>\n*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}html,body{margin:0;background:#090b0f;color:#f5f7fa;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",sans-serif}button{font:inherit;cursor:pointer}.screen{min-height:100vh;padding:28px 20px 110px}.home h1{font-size:52px;line-height:.96;margin:10px 0 18px;letter-spacing:-3px}.muted{color:#8d98a8;line-height:1.5}.eyebrow,.label{color:#8d98a8;font-weight:850;letter-spacing:3px}.primary,.share{width:100%;border:0;border-radius:22px;background:#fff;color:#090b0f;padding:19px;font-weight:900}.card{background:#11151a;border:1px solid #252b34;border-radius:22px;padding:20px;margin-top:14px}.score{font-size:56px;font-weight:950;margin:12px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.test-card{background:#11151a;border:1px solid #252b34;border-radius:22px;padding:20px;text-align:left;color:#fff}.icon{font-size:30px}.name{font-size:19px;font-weight:900;margin-top:10px}.desc{font-size:13px;color:#778294;margin-top:5px}.coin{display:flex;justify-content:space-between;align-items:center}.coin b{font-size:24px}.bottom{position:fixed;z-index:30;left:0;right:0;bottom:0;height:88px;background:rgba(9,11,15,.98);border-top:1px solid #20252d;display:flex}.nav{flex:1;background:none;border:0;color:#687486;font-size:12px}.nav.active{color:#fff}.nav span{display:block;font-size:26px;margin-bottom:5px}.test{display:none}.top{display:flex;justify-content:space-between;align-items:center}.timer{padding:9px 13px;border-radius:14px;background:#171c23;border:1px solid #2a313b;font-weight:900}.progress{height:5px;background:#1c2129;border-radius:5px;margin:25px 0}.bar{height:100%;width:0;background:#fff}.question{font-size:29px;line-height:1.17;font-weight:900;margin:18px 0 25px}.answer{width:100%;background:#11151a;border:1px solid #2a313b;color:#fff;border-radius:18px;padding:18px;text-align:left;margin-bottom:10px;font-weight:750}.answer.selected{border-color:#fff}.result,.profile,.ranking,.tools{display:none}.big{font-size:92px;font-weight:950;text-align:center;margin:25px 0}.center{text-align:center}.result p{color:#8d98a8;line-height:1.5}.mini{background:#0d1014;border-radius:17px;padding:16px}.mini b{display:block;font-size:13px}.mini strong{font-size:28px;display:block;margin-top:8px}.overall{margin-top:12px;background:#fff;color:#090b0f;padding:17px;border-radius:18px;display:flex;justify-content:space-between;font-weight:900}.row{display:flex;align-items:center;gap:12px;padding:16px;background:#11151a;border:1px solid #252b34;border-radius:17px;margin:8px 0}.rank{width:30px;color:#8994a5;font-weight:900}.grow{flex:1}.right{font-weight:900}.tool{background:#11151a;border:1px solid #252b34;border-radius:20px;padding:20px;margin:10px 0}.tool button{margin-top:12px}.textarea{width:100%;min-height:150px;background:#0b0e12;border:1px solid #2a313b;border-radius:15px;color:#fff;padding:14px;resize:none}.fun-result{font-size:18px;line-height:1.5;color:#aeb7c4}.back{background:none;border:0;color:#9aa4b2;padding:0 0 15px}\n</style></head><body>\n<div id="home" class="screen home"><div class="eyebrow">O‘ZINGNI SINAB KO‘R</div><h1>Qanchalik<br>ZAKOsan?</h1><p class="muted">Aqlingni, tezligingni, xotirangni va qarorlaringni sinab ko‘r. Natijangni do‘stlaring bilan solishtir.</p><button class="primary" id="mainTest">🧠 AQL TESTINI BOSHLASH</button><div class="card"><div class="label">GLOBAL ZAKO SCORE</div><div class="score" id="homeScore">—</div><div class="muted" id="homeMeta">Birinchi testdan keyin ochiladi</div></div><div class="card coin"><div><div class="label">ZAKO COIN</div><div class="muted">Test, streak va challenge orqali yig‘.</div></div><b>🪙 <span id="homeCoins">0</span></b></div><div class="card"><div class="label">SINAB KO‘R</div><div class="grid" style="margin-top:14px"><button class="test-card" data-test="iq"><div class="icon">🧠</div><div class="name">Aql</div><div class="desc">Mantiq va fikrlash</div></button><button class="test-card" data-test="speed"><div class="icon">⚡</div><div class="name">Tezlik</div><div class="desc">Tez va aniq</div></button><button class="test-card" data-test="memory"><div class="icon">🧩</div><div class="name">Xotira</div><div class="desc">Eslab qolish</div></button><button class="test-card" data-test="leadership"><div class="icon">👑</div><div class="name">Liderlik</div><div class="desc">Qaror va jamoa</div></button></div></div><div class="card"><div class="label">❤️ QO‘SHIMCHA TESTLAR</div><div class="grid" style="margin-top:14px"><button class="test-card" data-fun="love"><div class="icon">❤️</div><div class="name">Sevgi</div><div class="desc">Munosabat uslubing</div></button><button class="test-card" data-fun="effort"><div class="icon">🔥</div><div class="name">Tirishqoqlik</div><div class="desc">Maqsadga munosabating</div></button><button class="test-card" data-fun="stress"><div class="icon">🧠</div><div class="name">Bosim</div><div class="desc">🪙 50 coin</div></button></div></div><div class="card"><div class="label">🤖 AI TOOLS</div><p class="muted">PDF yoki matnni test/konspektga aylantirish. AI kaliti ulanganidan keyin ishlaydi.</p><button class="primary" id="toolsBtn">AI XIZMATLAR</button></div><button class="primary" style="margin-top:14px" id="dailyBtn">🎁 KUNLIK COINNI OLISH</button></div>\n<div id="test" class="screen test"><div class="top"><button class="back" id="backBtn">← Chiqish</button><div class="timer" id="timer">90</div></div><div class="progress"><div class="bar" id="bar"></div></div><div class="label" id="qnum">SAVOL 1 / 10</div><div class="muted" id="timeText">Vaqt: 90 soniya</div><div id="memoryBox" class="card" style="display:none"><div class="label">ESLAB QOL</div><div id="memoryPrompt" style="font-size:19px;line-height:1.5;font-weight:800;margin-top:10px"></div></div><div class="question" id="question">Savol</div><div id="answers"></div></div>\n<div id="result" class="screen result center"><div class="label">SENING NATIJANG</div><div class="big" id="resultScore">—</div><h2 id="resultTitle">HISOBLANMOQDA</h2><p id="resultText">Natijang serverda tekshirilmoqda.</p><p id="resultCoins"></p><button class="share" id="shareBtn">🚀 NATIJAMNI ULASHISH</button><button class="test-card" style="width:100%;margin-top:10px;text-align:center" id="homeBtn">BOSH SAHIFAGA</button></div>\n<div id="profile" class="screen profile"><button class="back" id="profileBack">← Bosh sahifa</button><h1>👤 Profil</h1><div class="card"><div class="label">ZAKO LEVEL</div><div class="score" id="level">1</div><div id="profileName" style="font-size:24px;font-weight:900"></div><div class="muted" id="profileUsername"></div><div class="grid" style="margin-top:18px"><div class="mini"><b>GLOBAL SCORE</b><strong id="pScore">0</strong></div><div class="mini"><b>COIN</b><strong id="pCoins">0</strong></div><div class="mini"><b>TESTLAR</b><strong id="pTests">0</strong></div><div class="mini"><b>REKORD</b><strong id="pBest">0</strong></div></div></div><div class="card"><div class="label">NATIJALARING</div><div class="grid" style="margin-top:14px"><div class="mini"><b>🧠 Aql</b><strong id="iqP">—</strong></div><div class="mini"><b>⚡ Tezlik</b><strong id="speedP">—</strong></div><div class="mini"><b>🧩 Xotira</b><strong id="memoryP">—</strong></div><div class="mini"><b>👑 Liderlik</b><strong id="leadP">—</strong></div></div><div class="overall"><span>UMUMIY</span><strong id="overall">0%</strong></div></div></div>\n<div id="ranking" class="screen ranking"><button class="back" id="rankBack">← Bosh sahifa</button><h1>🏆 Global reyting</h1><p class="muted">Barcha topshirgan testlaring yig‘indisi.</p><div id="rankingList"></div></div>\n<div id="tools" class="screen tools"><button class="back" id="toolsBack">← Bosh sahifa</button><h1>🤖 AI Tools</h1><div class="tool"><h3>🧠 Matn → Test</h3><textarea id="aiText" class="textarea" placeholder="Mavzu yoki matnni shu yerga yoz..."></textarea><button class="primary" id="aiTestBtn">TEST YARATISH</button><pre id="aiOut" class="muted" style="white-space:pre-wrap"></pre></div><div class="tool"><h3>📄 PDF → Konspekt</h3><input id="pdfInput" type="file" accept="application/pdf"><button class="primary" id="pdfBtn">KONSPEKT QILISH</button><button class="primary" id="pdfTestBtn">PDF → TEST</button><button class="primary" id="pdfSlideBtn">PDF → SLAYD</button><pre id="pdfOut" class="muted" style="white-space:pre-wrap"></pre></div></div>\n<div class="bottom"><button class="nav active" id="navHome"><span>🏠</span>Bosh sahifa</button><button class="nav" id="navRank"><span>🏆</span>Reyting</button><button class="nav" id="navProfile"><span>👤</span>Profil</button></div>\n<script>\n(()=>{const tg=window.Telegram?.WebApp;if(tg){tg.ready();tg.expand()}const $=id=>document.getElementById(id);const init=()=>tg?.initData||\'\';let page=\'home\',questions=[],idx=0,answers=[],started=0,timer=null,limit=90,token=\'\',type=\'iq\',funType=null;const limits={iq:90,speed:20,memory:60,leadership:90};\nfunction show(id){[\'home\',\'test\',\'result\',\'profile\',\'ranking\',\'tools\'].forEach(x=>$(x).style.display=\'none\');$(id).style.display=\'block\';page=id;document.querySelectorAll(\'.nav\').forEach(x=>x.classList.remove(\'active\'));if(id===\'home\')$(\'navHome\').classList.add(\'active\');if(id===\'profile\')$(\'navProfile\').classList.add(\'active\');if(id===\'ranking\')$(\'navRank\').classList.add(\'active\')}\nasync function start(t){type=t;try{const r=await fetch(\'/api/test/start\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\',\'X-Telegram-Init-Data\':init()},body:JSON.stringify({initData:init(),testType:t})});const d=await r.json();if(!d.ok)throw Error(d.error);questions=d.questions;token=d.testToken;idx=0;answers=[];limit=limits[t];show(\'test\');render()}catch(e){alert(e.message||\'Testni boshlashda xato\')}}\nfunction render(){clearInterval(timer);const q=questions[idx];$(\'qnum\').textContent=`SAVOL ${idx+1} / ${questions.length}`;$(\'timeText\').textContent=`Vaqt: ${limit} soniya`;$(\'bar\').style.width=(idx/questions.length*100)+\'%\';const mem=$(\'memoryBox\');const box=$(\'answers\');box.innerHTML=\'\';if(q.memoryPrompt){mem.style.display=\'block\';$(\'memoryPrompt\').textContent=q.memoryPrompt;$(\'question\').textContent=\'Ma’lumotni yodlab oling...\';$(\'timer\').textContent=\'5\';let m=5;const mt=setInterval(()=>{m--;$(\'timer\').textContent=m;if(m<=0){clearInterval(mt);mem.style.display=\'none\';showMemoryQuestion(q)}},1000)}else{mem.style.display=\'none\';showMemoryQuestion(q)}}\nfunction showMemoryQuestion(q){clearInterval(timer);$(\'question\').textContent=q.q;const box=$(\'answers\');box.innerHTML=\'\';q.a.forEach((a,i)=>{const b=document.createElement(\'button\');b.className=\'answer\';b.textContent=a;b.addEventListener(\'click\',()=>answer(i,b),{once:true});box.appendChild(b)});limit=limits[type];$(\'timeText\').textContent=`Vaqt: ${limit} soniya`;$(\'timer\').textContent=limit;started=Date.now();let left=limit;timer=setInterval(()=>{left--;$(\'timer\').textContent=left;if(left<=0){clearInterval(timer);answer(-1,null)}},1000)}\nfunction answer(ai,btn){clearInterval(timer);document.querySelectorAll(\'.answer\').forEach(x=>x.disabled=true);if(btn)btn.classList.add(\'selected\');const seconds=Math.max(0,(Date.now()-started)/1000);answers.push({questionId:questions[idx].id,answerIndex:ai,timeSeconds:Number(seconds.toFixed(2))});setTimeout(()=>{idx++;if(idx<questions.length)render();else submit()},180)}\nasync function submit(){show(\'result\');$(\'resultScore\').textContent=\'…\';$(\'resultTitle\').textContent=\'HISOBLANMOQDA\';$(\'resultText\').textContent=\'Natijang serverda saqlanmoqda...\';try{const r=await fetch(\'/api/test/submit\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\',\'X-Telegram-Init-Data\':init()},body:JSON.stringify({initData:init(),testToken:token,answers})});const d=await r.json();if(!d.ok)throw Error(d.error);$(\'resultScore\').textContent=d.score+\'%\';$(\'resultTitle\').textContent=d.score>=90?\'🔥 ZAKO DARAJA\':d.score>=75?\'🥇 KUCHLI\':d.score>=55?\'🥈 YAXSHI\':\'🌱 BOSHLANG‘ICH\';$(\'resultText\').textContent=d.insight;$(\'resultCoins\').textContent=`🪙 +${d.coinsEarned} coin • GLOBAL SCORE: ${d.globalScore}`;localStorage.removeItem(\'zako_pending_test\')}catch(e){localStorage.setItem(\'zako_pending_test\',JSON.stringify({token,answers,type}));$(\'resultScore\').textContent=\'—\';$(\'resultTitle\').textContent=\'ALOQA UZILDI\';$(\'resultText\').textContent=\'Natijang o‘chmadi. Internetni tekshirib, quyidagi tugma bilan qayta yubor.\';const b=document.createElement(\'button\');b.className=\'share\';b.textContent=\'🔄 NATIJANI QAYTA YUBORISH\';b.onclick=retryPending;$(\'result\').insertBefore(b,$(\'shareBtn\'))}}\nasync function retryPending(){const p=JSON.parse(localStorage.getItem(\'zako_pending_test\')||\'null\');if(!p)return;try{const r=await fetch(\'/api/test/submit\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\',\'X-Telegram-Init-Data\':init()},body:JSON.stringify({initData:init(),testToken:p.token,answers:p.answers})});const d=await r.json();if(!d.ok)throw Error(d.error);localStorage.removeItem(\'zako_pending_test\');$(\'resultScore\').textContent=d.score+\'%\';$(\'resultTitle\').textContent=\'SAQLANDI\';$(\'resultText\').textContent=d.insight;$(\'resultCoins\').textContent=`🪙 +${d.coinsEarned} coin • GLOBAL SCORE: ${d.globalScore}`}catch(e){alert(e.message||\'Hali aloqa yo‘q\')}}\nasync function profile(){show(\'profile\');try{const r=await fetch(\'/api/me\',{headers:{\'X-Telegram-Init-Data\':init()}}),d=await r.json();if(!d.ok)return;const u=d.user;$(\'profileName\').textContent=u.first_name||\'ZAKO\';$(\'profileUsername\').textContent=u.username?\'@\'+u.username:\'\';$(\'pScore\').textContent=d.global_score;$(\'pCoins\').textContent=d.coins;$(\'pTests\').textContent=d.tests_taken;$(\'pBest\').textContent=d.best_score;$(\'level\').textContent=d.level;const c=d.category_scores||{};$(\'iqP\').textContent=c.iq==null?\'—\':c.iq+\'%\';$(\'speedP\').textContent=c.speed==null?\'—\':c.speed+\'%\';$(\'memoryP\').textContent=c.memory==null?\'—\':c.memory+\'%\';$(\'leadP\').textContent=c.leadership==null?\'—\':c.leadership+\'%\';$(\'overall\').textContent=(d.overall_percent||0)+\'%\';$(\'homeScore\').textContent=d.global_score;$(\'homeCoins\').textContent=d.coins;$(\'homeMeta\').textContent=d.tests_taken?`${d.tests_taken} ta test • Rekord ${d.best_score}`:\'Birinchi testdan keyin ochiladi\'}catch(e){}}\nasync function ranking(){show(\'ranking\');$(\'rankingList\').innerHTML=\'<p class="muted">Yuklanmoqda...</p>\';try{const d=await (await fetch(\'/api/ranking\')).json();$(\'rankingList\').innerHTML=\'\';d.users.forEach((u,i)=>{const row=document.createElement(\'div\');row.className=\'row\';row.innerHTML=`<div class="rank">${i+1}</div><div class="grow"><b>${escape(u.first_name||u.username||\'ZAKO\')}</b><div class="muted">${u.tests_taken} ta test</div></div><div class="right">${u.global_score}</div>`;$(\'rankingList\').appendChild(row)})}catch(e){$(\'rankingList\').textContent=\'Reyting yuklanmadi\'}}\nfunction escape(s){return String(s).replace(/[&<>"\']/g,m=>({\'&\':\'&amp;\',\'<\':\'&lt;\',\'>\':\'&gt;\',\'"\':\'&quot;\',"\'":\'&#039;\'}[m]))}\nasync function daily(){try{const d=await (await fetch(\'/api/reward/daily\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\',\'X-Telegram-Init-Data\':init()},body:JSON.stringify({initData:init()})})).json();alert(d.ok?`🪙 +${d.coins} coin!\\nStreak: ${d.streak} kun`:d.error);if(d.ok)profile()}catch(e){alert(\'Coin olishda xato\')}}\nfunction share(){const s=$(\'resultScore\').textContent;const url=\'https://t.me/share/url?url=\'+encodeURIComponent(\'https://t.me/zako_tbot\')+\'&text=\'+encodeURIComponent(`🧠 Men ZAKO testidan ${s} oldim. Qani, senchi?`);tg?.openTelegramLink?.(url)}\nasync function fun(t){try{const d=await (await fetch(\'/api/fun/start\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\',\'X-Telegram-Init-Data\':init()},body:JSON.stringify({initData:init(),type:t})})).json();if(!d.ok)throw Error(d.error);funType=t;const qs=d.questions;let i=0,ans=[];show(\'test\');$(\'memoryBox\').style.display=\'none\';$(\'timeText\').textContent=d.name;$(\'timer\').textContent=\'\';function next(){if(i>=qs.length){show(\'result\');$(\'resultScore\').textContent=\'…\';fetch(\'/api/fun/submit\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\',\'X-Telegram-Init-Data\':init()},body:JSON.stringify({initData:init(),token:d.token,answers:ans})}).then(x=>x.json()).then(x=>{$(\'resultScore\').textContent=x.score+\'%\';$(\'resultTitle\').textContent=x.label;$(\'resultText\').textContent=x.text;$(\'resultCoins\').textContent=\'❤️ ZAKO self-reflection\'});return}const q=qs[i];$(\'qnum\').textContent=`${i+1} / ${qs.length}`;$(\'question\').textContent=q.q;const box=$(\'answers\');box.innerHTML=\'\';q.a.forEach((a,j)=>{const b=document.createElement(\'button\');b.className=\'answer\';b.textContent=a;b.onclick=()=>{ans.push({answerIndex:j});i++;setTimeout(next,120)};box.appendChild(b)})}next()}catch(e){alert(e.message)}}\nasync function aiTest(){const text=$(\'aiText\').value;const d=await (await fetch(\'/api/ai/text-to-test\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\',\'X-Telegram-Init-Data\':init()},body:JSON.stringify({initData:init(),text})})).json();$(\'aiOut\').textContent=d.ok?JSON.stringify(d.questions,null,2):d.error}\nasync function pdf(){const f=$(\'pdfInput\').files[0];if(!f)return alert(\'PDF tanlang\');const fd=new FormData();fd.append(\'file\',f);const r=await fetch(\'/api/ai/pdf-to-summary\',{method:\'POST\',headers:{\'X-Telegram-Init-Data\':init()},body:fd});const d=await r.json();$(\'pdfOut\').textContent=d.summary||d.error}\nasync function pdfTest(){const f=$(\'pdfInput\').files[0];if(!f)return alert(\'PDF tanlang\');const fd=new FormData();fd.append(\'file\',f);const d=await (await fetch(\'/api/ai/pdf-to-test\',{method:\'POST\',headers:{\'X-Telegram-Init-Data\':init()},body:fd})).json();$(\'pdfOut\').textContent=d.ok?JSON.stringify(d.questions,null,2):d.error}\nasync function pdfSlides(){const f=$(\'pdfInput\').files[0];if(!f)return alert(\'PDF tanlang\');const fd=new FormData();fd.append(\'file\',f);const d=await (await fetch(\'/api/ai/pdf-to-slides\',{method:\'POST\',headers:{\'X-Telegram-Init-Data\':init()},body:fd})).json();$(\'pdfOut\').textContent=d.ok?(\'Tayyor: \'+location.origin+d.fileUrl):d.error}\n$(\'mainTest\').onclick=()=>start(\'iq\');document.querySelectorAll(\'[data-test]\').forEach(b=>b.onclick=()=>start(b.dataset.test));document.querySelectorAll(\'[data-fun]\').forEach(b=>b.onclick=()=>fun(b.dataset.fun));$(\'navHome\').onclick=()=>show(\'home\');$(\'navRank\').onclick=ranking;$(\'navProfile\').onclick=profile;$(\'backBtn\').onclick=()=>show(\'home\');$(\'homeBtn\').onclick=()=>show(\'home\');$(\'profileBack\').onclick=()=>show(\'home\');$(\'rankBack\').onclick=()=>show(\'home\');$(\'toolsBack\').onclick=()=>show(\'home\');$(\'shareBtn\').onclick=share;$(\'dailyBtn\').onclick=daily;$(\'toolsBtn\').onclick=()=>show(\'tools\');$(\'aiTestBtn\').onclick=aiTest;$(\'pdfBtn\').onclick=pdf;$(\'pdfTestBtn\').onclick=pdfTest;$(\'pdfSlideBtn\').onclick=pdfSlides;profile();\n})()</script></body></html>'
