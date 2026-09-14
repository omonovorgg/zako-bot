import os, asyncio, json, secrets, time, hashlib, hmac, html as htmlmod, datetime
from pathlib import Path
from urllib.parse import parse_qsl, quote
from urllib.request import Request, urlopen

import asyncpg
from fastapi import FastAPI, Request as FRequest, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# ================= ZAKO CONFIG =================
ADMIN_IDS = {2109569429}  # @omono_v
BOT_USERNAME = "zako_tbot"
# Kanal sozlamasi /admin orqali saqlanadi.
# ===============================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
PUBLIC_URL = (os.getenv("RENDER_EXTERNAL_URL", "") or os.getenv("PUBLIC_URL", "")).rstrip("/")
if not BOT_TOKEN or not DATABASE_URL:
    raise RuntimeError("BOT_TOKEN va DATABASE_URL Render Environment Variables'da bo‘lishi kerak.")
if not PUBLIC_URL:
    raise RuntimeError("Render URL topilmadi.")

WEBHOOK_SECRET = hashlib.sha256((BOT_TOKEN + "|zako-webhook").encode()).hexdigest()[:48]
pool = None
admin_state = {}
WELCOME = Path(__file__).with_name("welcome.png")
HTML = '<!doctype html>\n<html lang="uz">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">\n<meta name="theme-color" content="#090b12">\n<title>ZAKO</title>\n<script src="https://telegram.org/js/telegram-web-app.js"></script>\n<style>\n*{box-sizing:border-box}html,body{margin:0;background:#090b12;color:#f7f8fb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}\nbody{min-height:100vh}.wrap{max-width:620px;margin:auto;padding:18px 16px 42px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}\n.logo{font-weight:900;letter-spacing:2px;font-size:25px}.pill{background:#171b26;border:1px solid #252b3a;padding:8px 11px;border-radius:999px;font-size:13px}\nh1{font-size:29px;line-height:1.08;margin:8px 0 10px}.sub{color:#9da6b8;line-height:1.5;margin-bottom:20px}\n.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.card{background:#121620;border:1px solid #252c3b;border-radius:20px;padding:18px;min-height:145px;cursor:pointer;transition:.15s}.card:active{transform:scale(.98)}.emoji{font-size:30px}.ct{font-weight:800;font-size:18px;margin-top:12px}.cs{color:#9099ab;font-size:12px;margin-top:5px}\n.btn{width:100%;border:0;border-radius:16px;padding:15px 16px;font-size:16px;font-weight:800;background:#fff;color:#080a0f;cursor:pointer}.btn.secondary{background:#171b26;color:#fff;border:1px solid #2a3140}.btn:disabled{opacity:.45}\n.stack{display:flex;flex-direction:column;gap:10px}.qbox{background:#121620;border:1px solid #252c3b;border-radius:22px;padding:18px}.progress{height:6px;background:#202532;border-radius:8px;overflow:hidden;margin:8px 0 16px}.bar{height:100%;width:100%;background:#39d98a;transition:width .18s linear,background .18s linear}.bar.warn{animation:barpulse .65s ease-in-out infinite alternate}@keyframes barpulse{from{opacity:.55}to{opacity:1}}.qnum{color:#8791a4;font-size:13px}.question{font-size:22px;line-height:1.25;font-weight:850;margin:8px 0 18px}.opts{display:grid;gap:10px}.opt{border:1px solid #2a3140;background:#171c27;color:#fff;padding:15px;border-radius:15px;text-align:left;font-size:15px;font-weight:700;cursor:pointer}.opt.sel{border-color:#fff;background:#252b38}.opt.correct{border-color:#fff}.small{font-size:12px;color:#8f98aa}.center{text-align:center}.resultScore{font-size:66px;font-weight:950;line-height:1;margin:10px 0}.insight{background:#121620;border:1px solid #252c3b;padding:16px;border-radius:18px;color:#cbd2df;line-height:1.5}.stat{display:flex;justify-content:space-between;padding:13px 0;border-bottom:1px solid #222936}.stat:last-child{border-bottom:0}.muted{color:#9099ab}.danger{color:#ff9b9b}.picker{height:210px;overflow:hidden;position:relative;border-radius:18px;background:#10141d}.wheel{height:100%;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;overflow-y:auto;scroll-snap-type:y mandatory;padding:72px 0}.wheel div{height:44px;min-height:44px;display:flex;align-items:center;justify-content:center;width:100%;font-size:18px;color:#70798a;scroll-snap-align:center}.wheel div.active{color:#fff;font-size:22px;font-weight:900}.picker:before,.picker:after{content:"";position:absolute;left:12%;right:12%;height:44px;border-top:1px solid #fff4;border-bottom:1px solid #fff4;top:83px;pointer-events:none}.colors{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.color{height:62px;border-radius:18px;border:2px solid transparent;font-size:28px;background:#181d28;cursor:pointer}.color.sel{border-color:#fff}.slider{width:100%;margin:28px 0}.sliderlabels{display:flex;justify-content:space-between;color:#9aa3b4;font-size:12px}.memorybox{font-size:30px;letter-spacing:7px;text-align:center;padding:26px 10px;background:#0d1119;border-radius:16px;margin-bottom:14px}.sharebox{word-break:break-all;background:#0d1119;padding:12px;border-radius:12px;font-size:12px;color:#9da6b8}.back{margin-bottom:14px;color:#9da6b8;cursor:pointer}.notice{padding:12px 14px;border-radius:14px;background:#151a25;color:#aeb7c7;font-size:13px;line-height:1.4;margin-bottom:12px}.shopcard{background:#121620;border:1px solid #252c3b;border-radius:20px;padding:16px}.hero{background:#121620;border:1px solid #252c3b;border-radius:22px;padding:18px}.coin{color:#fff}\n.profile-stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}\n.pstat{position:relative;min-height:112px;border-radius:20px;padding:16px;border:1px solid;overflow:hidden;box-shadow:0 10px 28px rgba(0,0,0,.18);transition:transform .16s,box-shadow .16s}\n.pstat:active{transform:scale(.98)}.pstat:after{content:"";position:absolute;width:90px;height:90px;border-radius:50%;right:-28px;top:-28px;opacity:.16;filter:blur(2px)}\n.pstat .pe{font-size:28px}.pstat .pl{font-size:12px;margin-top:8px;opacity:.78}.pstat .pv{font-size:25px;font-weight:950;margin-top:3px}\n.pstat.iq{background:linear-gradient(145deg,#171a2c,#10131d);border-color:#7776ff}.pstat.iq:after{background:#7776ff}\n.pstat.speed{background:linear-gradient(145deg,#251d12,#12151b);border-color:#ffad32}.pstat.speed:after{background:#ffad32}\n.pstat.memory{background:linear-gradient(145deg,#10251e,#11151a);border-color:#43d17a}.pstat.memory:after{background:#43d17a}\n.pstat.leadership{background:linear-gradient(145deg,#271b2d,#12151c);border-color:#d36cff}.pstat.leadership:after{background:#d36cff}\n.rankhead,.rankrow{display:grid;grid-template-columns:42px minmax(0,1fr) 62px minmax(78px,1.05fr);gap:7px;align-items:center}\n.rankhead{padding:0 8px 8px;color:#7f899c;font-size:10px;font-weight:850;text-transform:uppercase}\n.rankrow{background:#121620;border:1px solid #252c3b;border-radius:15px;padding:11px 8px;margin-bottom:7px;min-height:54px}\n.rankrow .rn{font-weight:900}.rankrow .rname{font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rankrow .rscore{text-align:right;font-weight:950}.rankrow .rprize{font-size:13px;font-weight:800;color:#cfd5e0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:right}\n.rankrow.gold{border-color:#d9ad3c;background:linear-gradient(90deg,#211c10,#121620)}.rankrow.silver{border-color:#8793a5;background:linear-gradient(90deg,#1a1d22,#121620)}.rankrow.bronze{border-color:#a96b45;background:linear-gradient(90deg,#211812,#121620)}\n@media(max-width:430px){.rankhead,.rankrow{grid-template-columns:34px minmax(0,1fr) 52px minmax(70px,.9fr);gap:5px}.rankrow{padding:10px 6px}.rankrow .rprize{font-size:12px}.rankhead{font-size:9px}}\n@media(max-width:430px){.grid{grid-template-columns:1fr 1fr}.question{font-size:20px}.wrap{padding-left:13px;padding-right:13px}}\n.bottomnav{position:fixed;left:50%;bottom:10px;transform:translateX(-50%);width:min(590px,calc(100% - 24px));display:grid;grid-template-columns:repeat(4,1fr);gap:6px;background:#121620ee;border:1px solid #2a3140;border-radius:20px;padding:7px;backdrop-filter:blur(14px);z-index:50;backdrop-filter:blur(14px)}.bottomnav button{border:0;background:transparent;color:#8f98aa;padding:8px 4px;border-radius:14px;font-size:19px;cursor:pointer}.bottomnav button span{display:block;font-size:10px;margin-top:3px}.bottomnav button.on{background:#252b38;color:#fff}.wrap{padding-bottom:95px}</style>\n</head>\n<body>\n<div id="app"></div>\n<script>\nconst DATA = {"core":{"iq":[{"id":"iq1","q":"Bir loyihada 4 vazifa bor: A, B, C, D. A B dan oldin, C A dan keyin, D esa B dan keyin bajariladi. Qaysi tartib mumkin?","type":"mcq","opts":["A → B → C → D","B → A → D → C","A → C → B → D","C → A → B → D"],"ans":0},{"id":"iq2","q":"3 ta quti bor: birida faqat qizil, birida faqat ko‘k, birida aralash sharlar. Yorliqlarning barchasi noto‘g‘ri. Faqat bitta shar olib, qutilarni aniqlash uchun qaysi qutidan olasiz?","type":"mcq","opts":["“Qizil”","“Ko‘k”","“Aralash”","Istalgan"],"ans":2},{"id":"iq3","q":"Barcha X lar Y. Ba’zi Y lar Z. Qaysi xulosa majburiy?","type":"mcq","opts":["Barcha X lar Z","Ba’zi X lar Z","Hech bir X Z emas","X lar Y ga kiradi"],"ans":3},{"id":"iq4","q":"Bir mahsulot 20% arzonlashtirilib 240 000 so‘m bo‘ldi. Chegirmadan oldingi narx qancha edi?","type":"mcq","opts":["280 000","288 000","300 000","320 000"],"ans":2},{"id":"iq5","q":"4 kishi bir-biri bilan bir martadan uchrashib qo‘l berishdi. Jami nechta qo‘l siqish bo‘ladi?","type":"mcq","opts":["4","6","8","12"],"ans":1},{"id":"iq6","q":"Bir sonning 30% i 24 ga teng. Shu sonning 75% i nechaga teng?","type":"mcq","opts":["48","54","60","72"],"ans":2},{"id":"iq7","q":"Ketma-ketlikdagi keyingi sonni toping: 2, 6, 12, 20, 30, ?","type":"mcq","opts":["36","40","42","44"],"ans":2},{"id":"iq8","q":"Agar barcha rahbarlar qaror qabul qiladi va ayrim qaror qabul qiluvchilar tajribasiz bo‘lsa, qaysi gapni aniq aytish mumkin?","type":"mcq","opts":["Barcha rahbarlar tajribali","Ayrim rahbarlar tajribasiz","Rahbarlar qaror qabul qiladi","Hech bir tajribasiz rahbar yo‘q"],"ans":2},{"id":"iq9","q":"Bir yo‘lda A shahardan B shaharga 60 km/soat, qaytishda 40 km/soat tezlikda yurildi. Bir xil masofa uchun o‘rtacha tezlik qancha?","type":"mcq","opts":["48 km/soat","50 km/soat","52 km/soat","55 km/soat"],"ans":0},{"id":"iq10","q":"5 ta ishchi ishni 12 kunda tugatadi. Bir xil unumdorlikda 10 ta ishchi shu ishni necha kunda tugatadi?","type":"mcq","opts":["3","5","6","8"],"ans":2}],"speed":[{"id":"sp1","q":"Qaysi kod aynan bir xil?","type":"mcq","opts":["K7M2P / K7M2P","K7M2P / K7N2P","K7M2P / K7MZP","K7M2P / K72MP"],"ans":0},{"id":"sp2","q":"Eng katta qiymatni tanlang.","type":"mcq","opts":["0.809","0.89","0.8099","0.899"],"ans":3},{"id":"sp3","q":"Qaysi belgi ketma-ketlikni buzadi?  ▲ ▲ ▲ △ ▲","type":"mcq","opts":["1-belgi","2-belgi","4-belgi","5-belgi"],"ans":2},{"id":"sp4","q":"Qaysi juftlik teng?","type":"mcq","opts":["17×3 / 51","18×3 / 52","72÷8 / 8","45+7 / 53"],"ans":0},{"id":"sp5","q":"Chap va o‘ng kod bir xilmi?  Q9R7K  /  Q9R7K","type":"yesno","opts":["HA","YO‘Q"],"ans":0},{"id":"sp6","q":"Qaysi raqam boshqalardan farq qiladi?  18, 24, 30, 35","type":"mcq","opts":["18","24","30","35"],"ans":3},{"id":"sp7","q":"Qaysi so‘zda “z” harfi bor?","type":"mcq","opts":["BULUT","ZAMON","KITOB","DARAXT"],"ans":1},{"id":"sp8","q":"Qaysi qiymat 1 ga eng yaqin?","type":"mcq","opts":["0.91","0.99","0.89","0.79"],"ans":1},{"id":"sp9","q":"Qaysi juftlik aynan bir xil?","type":"mcq","opts":["B8Q1 / B8Q1","M4T7 / M4T1","P2L9 / P2I9","X7R3 / X7R8"],"ans":0},{"id":"sp10","q":"Qaysi natija eng katta?","type":"mcq","opts":["14+9","31-7","6×4","50÷2"],"ans":3}],"memory":[{"id":"mem1","q":"Eslab qoling: 7 — K — 2 — M — 9. Qaysi belgi 2 dan keyin kelgan?","type":"memory","memory":"7  K  2  M  9","opts":["7","K","M","9"],"ans":2},{"id":"mem2","q":"Eslab qoling: ▲ — 4 — B — 8 — Q. Qaysi belgi ikkinchi o‘rinda edi?","type":"memory","memory":"▲  4  B  8  Q","opts":["▲","4","B","8"],"ans":1},{"id":"mem3","q":"Eslab qoling: 3 — L — 8 — R — 1 — T. Qaysi belgi R dan oldin kelgan?","type":"memory","memory":"3  L  8  R  1  T","opts":["L","8","1","T"],"ans":1},{"id":"mem4","q":"Eslab qoling: 5 — A — 9 — C — 4. Qaysi raqam A dan keyin kelgan?","type":"memory","memory":"5  A  9  C  4","opts":["5","9","4","C"],"ans":1},{"id":"mem5","q":"Eslab qoling: N — 6 — P — 2 — V — 8. Qaysi belgi uchinchi o‘rinda edi?","type":"memory","memory":"N  6  P  2  V  8","opts":["6","P","2","V"],"ans":1},{"id":"mem6","q":"Eslab qoling: 4 — Z — 7 — K — 3 — M. Qaysi raqam K dan keyin kelgan?","type":"memory","memory":"4  Z  7  K  3  M","opts":["4","7","3","M"],"ans":2},{"id":"mem7","q":"Eslab qoling: R — 2 — H — 9 — D. Birinchi va oxirgi belgilar qaysi?","type":"memory","memory":"R  2  H  9  D","opts":["R va D","2 va 9","H va D","R va 9"],"ans":0},{"id":"mem8","q":"Eslab qoling: 8 — C — 1 — F — 6 — Q. F dan oldingi ikki belgi qaysi?","type":"memory","memory":"8  C  1  F  6  Q","opts":["8, C","C, 1","1, F","F, 6"],"ans":1},{"id":"mem9","q":"Eslab qoling: B — 7 — T — 3 — L. T dan keyingi belgi qaysi?","type":"memory","memory":"B  7  T  3  L","opts":["7","3","L","B"],"ans":1},{"id":"mem10","q":"Eslab qoling: 2 — G — 5 — X — 8. Qaysi belgi 5 dan oldin kelgan?","type":"memory","memory":"2  G  5  X  8","opts":["2","G","X","8"],"ans":1}],"leadership":[{"id":"lead1","q":"Jamoangizda muddat yaqin. Bir xodim juda tez, ikkinchisi esa ancha sifatli ishlaydi. Eng to‘g‘ri qaror?","type":"mcq","opts":["Hammasini tez ishlaydigan xodimga berish","Sifatli ishni muhim qismga, tezkor xodimni tez bajariladigan qismga biriktirish","Ikkalasiga ham bir xil vazifa berish","Eng tajribalisini tanlab, qolganini kutish"],"ans":1},{"id":"lead2","q":"Ikki xodim bir masalada kelisha olmayapti. Vazifa esa kechikmoqda. Avval nima qilasiz?","type":"mcq","opts":["Darhol bir tomonning fikrini tanlaysiz","Ikkalasini ham jazolaysiz","Muammoni, faktlarni va qaror uchun kerakli mezonni aniqlaysiz","Vazifani boshqa odamga berasiz"],"ans":2},{"id":"lead3","q":"Muhim loyiha 1 kun kechikmoqda. Sabab aniq emas. Eng yaxshi birinchi qadam?","type":"mcq","opts":["Aybdorni topish","Jamoani ko‘proq ishlashga majburlash","Qaysi bosqich to‘xtaganini va sababini aniqlash","Loyihani bekor qilish"],"ans":2},{"id":"lead4","q":"Jamoada kuchli xodim bor, lekin barcha qarorni o‘zi qilishga urinadi. Nima qilasiz?","type":"mcq","opts":["Uni chetlashtirasiz","Hammasini o‘zingiz nazorat qilasiz","Mas’uliyat chegarasini belgilab, qaror vakolatini aniq taqsimlaysiz","Hech narsa demaysiz"],"ans":2},{"id":"lead5","q":"Yangi xodim xato qildi, lekin xatosini yashirmay darhol aytdi. Rahbar sifatida eng foydali javob?","type":"mcq","opts":["Uni hammaga tanbeh berish","Xatoni tuzatish va qayta takrorlanmasligi uchun sababini tahlil qilish","Xatoni e’tiborsiz qoldirish","Keyingi vazifalarni undan olish"],"ans":1},{"id":"lead6","q":"Resurs yetmayapti: uchta vazifa bor, faqat bittasini bugun tugatish mumkin. Qanday tanlaysiz?","type":"mcq","opts":["Eng oson vazifani","Eng ko‘p gapirilgan vazifani","Eng katta ta’sir va eng yaqin oqibatga ega vazifani","Tasodifiy tanlaysiz"],"ans":2},{"id":"lead7","q":"Jamoa natijasi yaxshi, ammo ikki xodim hissasi teng emas. Qanday yo‘l tutasiz?","type":"mcq","opts":["Hamma uchun bir xil mukofot","Hissani va natijani alohida baholab, keyingi rollarni shunga moslashtirish","Faqat eng faol xodimni maqtash","Hech kimga fikr bildirmaslik"],"ans":1},{"id":"lead8","q":"Qabul qilgan qaroringiz kutilgan natijani bermadi. Kuchli rahbarning birinchi reaksiyasi?","type":"mcq","opts":["Aybdorni qidirish","Qaror ortidagi taxminlar va ma’lumotlarni qayta tekshirish","Qarorni yashirish","Jamoani ayblash"],"ans":1},{"id":"lead9","q":"Jamoada muammo bor, lekin hech kim gapirmayapti. Eng yaxshi usul?","type":"mcq","opts":["Darhol jazolash","Ochiq savol berib, xavfsiz muhitda muammoni aniqlash","Muammoni o‘zingiz taxmin qilish","Yig‘ilishni bekor qilish"],"ans":1},{"id":"lead10","q":"Sizga muhim ish topshirildi, lekin maqsad noaniq. Eng to‘g‘ri qadam?","type":"mcq","opts":["Darhol boshlash","Natija mezoni va ustuvorlikni aniqlashtirish","Boshqaga topshirish","Muddatni kutish"],"ans":1}]},"social":{"love":[{"id":"a1","q":"Menga qaysi ichimlik ko‘proq yoqadi?","type":"mcq","opts":["🥤 Cola","🥤 Pepsi","🧃 Sharbat","☕ Choy"]},{"id":"a2","q":"Tug‘ilgan oyim qaysi?","type":"month","opts":[]},{"id":"a3","q":"Men qaysi rangni ko‘proq tanlayman?","type":"color","opts":["🔴","🔵","🟢","🟡","🟣","⚫","⚪","🟠"]},{"id":"a4","q":"Ideal dam olish kunim qaysi?","type":"mcq","opts":["🏠 Uyda film","🌆 Do‘stlar bilan tashqarida","✈️ Sayohat","🎮 O‘yin"]},{"id":"a5","q":"Men qaysi taomni tanlashim ehtimoli yuqori?","type":"mcq","opts":["🍕 Pizza","🍔 Burger","🍜 Lag‘mon","🍣 Sushi"]},{"id":"a6","q":"Men ko‘proq qaysi paytni yoqtiraman?","type":"slider","opts":[]},{"id":"a7","q":"Kutilmagan sovg‘adan qaysi birini tanlayman?","type":"mcq","opts":["🎧 Texnika","🌹 Romantik sovg‘a","👟 Kiyim","🎁 Sirli sovg‘a"]},{"id":"a8","q":"Men sayohatda nimani ko‘proq xohlayman?","type":"mcq","opts":["🏖 Dengiz","🏔 Tog‘","🏙 Katta shahar","🌲 Tabiat"]},{"id":"a9","q":"Menga xabar yozishmi yoki qo‘ng‘iroq qilishmi yoqadi?","type":"mcq","opts":["💬 Xabar","📞 Qo‘ng‘iroq","🤷 Vaziyatga qarab","🎥 Videoqo‘ng‘iroq"]},{"id":"a10","q":"Men bo‘sh vaqtimda birini tanlasam...","type":"mcq","opts":["🎬 Kino","🎮 O‘yin","📚 Kitob","🚶 Sayr"]},{"id":"a11","q":"Menga qaysi ob-havo yoqadi?","type":"mcq","opts":["☀️ Issiq","🌧 Yomg‘ir","❄️ Qor","🌥 Salqin"]},{"id":"a12","q":"Men ertalab uyg‘onganda birinchi nima qilishim ehtimoli yuqori?","type":"mcq","opts":["📱 Telefonni tekshirish","💧 Suv ichish","☕ Choy/kofe","😴 Yana uxlash"]},{"id":"a13","q":"Men tanlashim kerak bo‘lsa, qaysi rangli kiyimni olaman?","type":"color","opts":["⚫","⚪","🔵","🟢","🔴","🟡"]},{"id":"a14","q":"Menga qaysi musiqa kayfiyati yaqinroq?","type":"mcq","opts":["🔥 Energetik","🌙 Sokin","💔 Melanxolik","🎉 Raqsbop"]},{"id":"a15","q":"Men uchun ideal kecha...","type":"mcq","opts":["🍿 Film","🌃 Sayr","🎮 O‘yin","👥 Do‘stlar bilan suhbat"]},{"id":"a16","q":"Agar 1 kun bo‘sh vaqtim bo‘lsa, nimani tanlashim mumkin?","type":"mcq","opts":["😴 Dam olish","🚗 Shahar tashqarisi","🎮 O‘yin","🎬 Kino"]},{"id":"a17","q":"Men ko‘proq qaysi sovg‘ani qadrlayman?","type":"mcq","opts":["💌 Ma’noli xat","💰 Qimmat narsa","🍫 Shirinlik","📸 Birga tushgan foto"]},{"id":"a18","q":"Men restoran tanlasam, nimaga ko‘proq qarayman?","type":"mcq","opts":["🍽 Taom","💰 Narx","✨ Muhit","⭐ Sharhlar"]},{"id":"a19","q":"Men qaysi hayvonni yoqimli deb bilishim ehtimoli yuqori?","type":"mcq","opts":["🐱 Mushuk","🐶 It","🐼 Panda","🦊 Tulki"]},{"id":"a20","q":"Menga qaysi fasl ko‘proq yoqadi?","type":"mcq","opts":["🌸 Bahor","☀️ Yoz","🍂 Kuz","❄️ Qish"]},{"id":"a21","q":"Men tanlashim kerak bo‘lsa, qaysi transport?","type":"mcq","opts":["🚗 Mashina","✈️ Samolyot","🚆 Poyezd","🚲 Velosiped"]},{"id":"a22","q":"Menga qaysi biri ko‘proq yoqadi?","type":"mcq","opts":["🌊 Dengiz","🏙 Shahar","🏔 Tog‘","🏡 Qishloq"]},{"id":"a23","q":"Men vaqtida kelish masalasida qandayman?","type":"mcq","opts":["⏰ Juda punktual","🙂 Odatda vaqtida","🏃 Ko‘pincha shoshilaman","😅 Kechikishim mumkin"]},{"id":"a24","q":"Men kayfiyatim tushsa, ko‘proq nima qilaman?","type":"mcq","opts":["🎵 Musiqa","😴 Uxlayman","👥 Kim bilandir gaplashaman","🎮 Chalg‘itaman"]}],"friend":[{"id":"f1","q":"Do‘sting qaysi ichimlikni tanlaydi?","type":"mcq","opts":["🥤 Cola","🥤 Pepsi","🧃 Sharbat","☕ Choy"]},{"id":"f2","q":"Do‘stingning tug‘ilgan oyi qaysi?","type":"month","opts":[]},{"id":"f3","q":"Do‘sting qaysi rangni tanlaydi?","type":"color","opts":["🔴","🔵","🟢","🟡","🟣","⚫","⚪","🟠"]},{"id":"f4","q":"Do‘sting ideal dam olish kunini qanday o‘tkazadi?","type":"mcq","opts":["🏠 Uyda","🌆 Tashqarida","✈️ Sayohatda","🎮 O‘yin bilan"]},{"id":"f5","q":"Do‘sting qaysi ovqatni tanlashi ehtimoli yuqori?","type":"mcq","opts":["🍕 Pizza","🍔 Burger","🍜 Lag‘mon","🍣 Sushi"]},{"id":"f6","q":"Do‘sting ko‘proq qaysi paytni yoqtiradi?","type":"slider","opts":[]},{"id":"f7","q":"Do‘stingga 1 mln so‘m tushsa, birinchi nima qiladi?","type":"mcq","opts":["🛍 Sarflaydi","💰 Saqlaydi","🎁 Sovg‘a qiladi","✈️ Sayohatga ishlatadi"]},{"id":"f8","q":"Do‘sting sayohatda nimani tanlaydi?","type":"mcq","opts":["🏖 Dengiz","🏔 Tog‘","🏙 Shahar","🌲 Tabiat"]},{"id":"f9","q":"Do‘sting bilan bog‘lanishning qaysi usuli unga yoqadi?","type":"mcq","opts":["💬 Xabar","📞 Qo‘ng‘iroq","🤷 Vaziyatga qarab","🎥 Video"]},{"id":"f10","q":"Do‘sting bo‘sh vaqtida nimani tanlaydi?","type":"mcq","opts":["🎬 Kino","🎮 O‘yin","📚 Kitob","🚶 Sayr"]},{"id":"f11","q":"Do‘stingga qaysi ob-havo yoqadi?","type":"mcq","opts":["☀️ Issiq","🌧 Yomg‘ir","❄️ Qor","🌥 Salqin"]},{"id":"f12","q":"Do‘sting ertalab uyg‘onganda nima qiladi?","type":"mcq","opts":["📱 Telefon","💧 Suv","☕ Choy/kofe","😴 Yana uxlaydi"]},{"id":"f13","q":"Do‘sting qaysi kiyim rangini tanlaydi?","type":"color","opts":["⚫","⚪","🔵","🟢","🔴","🟡"]},{"id":"f14","q":"Do‘sting qaysi musiqa kayfiyatini tanlaydi?","type":"mcq","opts":["🔥 Energetik","🌙 Sokin","💔 Melanxolik","🎉 Raqsbop"]},{"id":"f15","q":"Do‘stingning ideal kechasi?","type":"mcq","opts":["🍿 Film","🌃 Sayr","🎮 O‘yin","👥 Suhbat"]},{"id":"f16","q":"Do‘stingga bir kun bo‘sh vaqt berilsa...","type":"mcq","opts":["😴 Dam","🚗 Sayohat","🎮 O‘yin","🎬 Kino"]},{"id":"f17","q":"Do‘sting qaysi sovg‘ani ko‘proq qadrlaydi?","type":"mcq","opts":["💌 Xat","💰 Qimmat narsa","🍫 Shirinlik","📸 Foto"]},{"id":"f18","q":"Do‘sting restoran tanlaganda nimaga qaraydi?","type":"mcq","opts":["🍽 Taom","💰 Narx","✨ Muhit","⭐ Sharhlar"]},{"id":"f19","q":"Do‘stingga qaysi hayvon yoqishi ehtimoli yuqori?","type":"mcq","opts":["🐱 Mushuk","🐶 It","🐼 Panda","🦊 Tulki"]},{"id":"f20","q":"Do‘stingning sevimli fasli qaysi bo‘lishi mumkin?","type":"mcq","opts":["🌸 Bahor","☀️ Yoz","🍂 Kuz","❄️ Qish"]},{"id":"f21","q":"Do‘sting sayohatda qaysi transportni tanlaydi?","type":"mcq","opts":["🚗 Mashina","✈️ Samolyot","🚆 Poyezd","🚲 Velosiped"]},{"id":"f22","q":"Do‘sting qaysi joyni tanlaydi?","type":"mcq","opts":["🌊 Dengiz","🏙 Shahar","🏔 Tog‘","🏡 Qishloq"]},{"id":"f23","q":"Do‘sting vaqtida kelish masalasida qanday?","type":"mcq","opts":["⏰ Juda punktual","🙂 Odatda vaqtida","🏃 Shoshilib keladi","😅 Kechikadi"]},{"id":"f24","q":"Do‘sting kayfiyati tushsa, nima qiladi?","type":"mcq","opts":["🎵 Musiqa","😴 Uxlaydi","👥 Gaplashadi","🎮 Chalg‘iydi"]}]},"months":["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentabr","Oktabr","Noyabr","Dekabr"]};\nconst app = document.getElementById("app");\nlet tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;\nif(tg){ try{tg.ready(); tg.expand();}catch(e){} }\n\nconst state = {screen:"home", cat:null, qs:[], idx:0, answers:[], started:0, timer:null, left:0, social:null, socialAnswers:[], socialIdx:0, challenge:null, xp:0, coins:0, streak:0, week:0,month:0,done:{},premium_until:null,premium_claimed:false,frame_id:null,referralLink:"",rank:0};\nconst NAMES={iq:"Aql",speed:"Tezlik",memory:"Xotira",leadership:"Liderlik"};\nfunction apiHeaders(){return {"Content-Type":"application/json","X-Telegram-Init-Data":tg?.initData||""};}\nfunction alertUser(msg){try{if(tg?.showAlert)tg.showAlert(String(msg));else alert(String(msg));}catch(e){console.error(msg);}}\nfunction confirmExit(){if(confirm("Testni tark etsangiz, joriy natija saqlanmaydi. Chiqasizmi?")){home();}}\n\n\nfunction esc(s){return String(s).replace(/[&<>"\\\']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;","\'":"&#39;"}[c]));}\nfunction getName(){return (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && (tg.initDataUnsafe.user.first_name||tg.initDataUnsafe.user.username)) || "ZAKO foydalanuvchisi";}\nfunction save(key,val){try{localStorage.setItem(key,JSON.stringify(val));}catch(e){}}\nfunction load(key,def){try{let x=JSON.parse(localStorage.getItem(key));return x??def;}catch(e){return def;}}\nfunction renderTop(){return `<div class="top"><div class="logo">🧠 ZAKO</div><div class="pill">⭐ ${state.xp||0} XP &nbsp; 🪙 ${state.coins||0}</div></div>`;}\nfunction todayKey(){return new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Tashkent",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());}\nfunction refreshWallet(){return fetch("/api/wallet",{headers:apiHeaders(),cache:"no-store"}).then(async r=>{const d=await r.json();if(!r.ok)throw new Error(d.detail||"Wallet xatosi");if(d.xp!==undefined){state.xp=d.xp;state.coins=d.coins;state.streak=d.streak;state.week=d.week||0;state.month=d.month||0;state.rank=d.rank||0;state.done=d.done||{};state.premium_until=d.premium_until;state.premium_claimed=!!d.premium_claimed;state.frame_id=d.frame_id;}return d;}).catch(()=>null);}\nfunction nav(active){return `<div class="bottomnav">\n<button class="${active===\'home\'?\'on\':\'\'}" onclick="home()">🏠<span>Bosh</span></button>\n<button class="${active===\'friends\'?\'on\':\'\'}" onclick="friends()">👥<span>Do‘stlar</span></button>\n<button class="${active===\'tasks\'?\'on\':\'\'}" onclick="tasks()">🎯<span>Topshiriq</span></button>\n<button class="${active===\'profile\'?\'on\':\'\'}" onclick="profile()">👤<span>Profil</span></button></div>`;}\nfunction testCard(e,t,s,c,done){\n const body=done?`<div class="small">✅ BAJARILDI · ${state.done[c]}%</div>`:`<div class="small">Bugungi testda</div>`;\n return `<div class="card ${done?\'done\':\'\'}"><div class="emoji">${e}</div><div class="ct">${t}</div><div class="cs">${s}</div>${body}</div>`;\n}\nasync function syncPendingScore(){\n const p=load("zako_pending_bundle",null);if(!p||!p.results||!p.attempt_id)return;if(p.date!==todayKey()){localStorage.removeItem("zako_pending_bundle");return;}\n let ok=true;for(const [cat,x] of Object.entries(p.results)){if(!(await submitScore(p.attempt_id+"_"+cat,cat,x.pct))){ok=false;break;}}if(ok)localStorage.removeItem("zako_pending_bundle");\n}\nasync function home(){\n state.screen="home";state.social=null;await syncPendingScore();await refreshWallet();\n const name=esc(getName()),d=state.done||{};const allDone=["iq","leadership","memory","speed"].every(x=>d[x]!==undefined);\n app.innerHTML=`<div class="wrap">${renderTop()}<div class="sub">Salom, <b>${name}</b> 👋</div>\n <div class="hero"><div class="small">🏆 ZAKO SCORE</div><div class="resultScore">${state.week||0}</div><div class="small">🔥 ${state.streak||0} kunlik streak</div></div>\n <div style="height:12px"></div>\n <div class="hero"><div class="ct">🏆 REYTING</div><div style="font-size:22px;font-weight:950;margin-top:8px">${state.week||0} BALL</div><div class="small" style="margin-top:4px">${state.rank?"#"+state.rank:"—"} O‘RIN</div><div style="height:10px"></div><button class="btn" onclick="ranking()">🏆 REYTINGNI KO‘RISH</button></div>\n <div style="height:14px"></div><div class="hero"><div class="ct">🎯 BUGUNGI SINOV</div><div class="sub">8 ta savol · 4 bo‘lim</div><button class="btn" ${allDone?"disabled":""} onclick="startCore()">${allDone?"✅ BAJARILDI":"BOSHLASH"}</button></div>\n <div style="height:18px"></div><div class="small">🧠 MIYA</div><div class="grid">\n ${testCard("🧠","Aql","20 soniya","iq",d.iq!==undefined)}${testCard("⚡","Tezlik","5 soniya","speed",d.speed!==undefined)}${testCard("🧩","Xotira","10 soniya","memory",d.memory!==undefined)}${testCard("👑","Liderlik","20 soniya","leadership",d.leadership!==undefined)}\n </div><div style="height:80px"></div>${nav("home")}</div>`;\n}\nfunction friends(){\n app.innerHTML=`<div class="wrap">${renderTop()}<h1>👥 Do‘stlar</h1>\n <div class="hero"><div class="ct">❤️ Meni qanchalik bilasan?</div><div class="sub">Do‘stlaringiz sizni qanchalik bilishini tekshiring.</div><button class="btn" onclick="socialMenu(\'love\')">❤️ Taklif qilish</button></div>\n <div style="height:10px"></div><div class="hero"><div class="ct">🤝 Do‘stingni qanchalik bilasan?</div><div class="sub">Do‘stingni qanchalik bilishingni sinab ko‘r.</div><button class="btn" onclick="socialMenu(\'friend\')">🤝 Do‘stni sinash</button></div>\n <div style="height:18px"></div><div class="hero"><div class="ct">🔗 Do‘stlarni taklif qilish</div><div id="refbox" class="sub">Yuklanmoqda…</div><button class="btn secondary" onclick="copyReferral()">📋 Taklif havolasini nusxalash</button></div>\n <div style="height:18px"></div><div class="small">📋 SIZNI QANCHALIK BILISHADI</div><div id="friendsbox" class="stack"><div class="notice">Yuklanmoqda…</div></div>\n <div style="height:80px"></div>${nav(\'friends\')}</div>`;\n loadFriends();loadReferral();\n}\nasync function loadFriends(){\n try{const r=await fetch(\'/api/friends\',{headers:apiHeaders(),cache:\'no-store\'});const d=await r.json();const b=document.getElementById(\'friendsbox\');if(!b)return;\n b.innerHTML=(d.items||[]).map(x=>`<div class="shopcard"><div class="ct">${x.kind===\'love\'?\'❤️\':\'🤝\'} ${esc(x.name)}</div><div class="small">Sizni <b>${x.pct}%</b> biladi</div></div>`).join(\'\')||`<div class="notice">Hali hech kim sizni sinamagan.</div>`;\n }catch(e){const b=document.getElementById(\'friendsbox\');if(b)b.innerHTML=`<div class="notice">Natijalarni yuklab bo‘lmadi.</div>`;}}\nasync function loadReferral(){\n try{const r=await fetch(\'/api/referrals\',{headers:apiHeaders(),cache:\'no-store\'});const d=await r.json();state.referralLink=d.link||\'\';const b=document.getElementById(\'refbox\');if(!b)return;\n b.innerHTML=`Har bir haqiqiy yangi taklif uchun <b>🪙 +5 Coin</b>.<br>Taklif qilinganlar: <b>${d.count}</b><div class="sharebox" style="margin-top:10px">${esc(d.link||\'\')}</div>`;\n }catch(e){const b=document.getElementById(\'refbox\');if(b)b.textContent=\'Taklif havolasini yuklab bo‘lmadi.\';}}\nasync function copyReferral(){if(!state.referralLink)await loadReferral();if(state.referralLink)copyText(encodeURIComponent(state.referralLink));}\n\nasync function tasks(){\n app.innerHTML=`<div class="wrap">${renderTop()}<h1>🎯 Topshiriqlar</h1>\n <div class="hero"><div class="ct">📋 Mukofotli topshiriqlar</div><div class="sub">Kanalga obuna bo‘ling, tekshiring va XP/Coin oling.</div></div>\n <div style="height:12px"></div><div id="taskbox" class="stack"><div class="notice">Yuklanmoqda…</div></div>\n <div style="height:80px"></div>${nav(\'tasks\')}</div>`;\n try{const r=await fetch(\'/api/tasks\',{headers:apiHeaders(),cache:\'no-store\'});const d=await r.json();const b=document.getElementById(\'taskbox\');if(!b)return;\n b.innerHTML=(d.items||[]).map(x=>`<div class="shopcard"><div class="ct">📢 ${esc(x.title)}</div><div class="small">Mukofot: ${x.reward_xp?`⭐ +${x.reward_xp} XP`:\'\'}${x.reward_xp&&x.reward_coins?\' · \':\'\'}${x.reward_coins?`🪙 +${x.reward_coins} Coin`:\'\'}</div><div style="height:10px"></div>${x.claimed?`<button class="btn secondary" disabled>✅ BAJARILDI</button>`:`<div class="grid"><button class="btn secondary" onclick="openTaskLink(\'${encodeURIComponent(x.url||\'\')}\')">📢 Kanalga o‘tish</button><button class="btn" onclick="claimTask(${x.id})">✅ BAJARISH</button></div>`}</div>`).join(\'\')||`<div class="notice">Hozircha topshiriqlar yo‘q.</div>`;\n }catch(e){document.getElementById(\'taskbox\').innerHTML=`<div class="notice">Topshiriqlarni yuklab bo‘lmadi.</div>`;}}\nfunction openTaskLink(enc){const u=decodeURIComponent(enc);if(!u){alertUser(\'Kanal havolasi topilmadi.\');return;}if(tg?.openTelegramLink)tg.openTelegramLink(u);else location.href=u;}\nasync function claimTask(id){\n try{const r=await fetch(\'/api/tasks/claim\',{method:\'POST\',headers:apiHeaders(),body:JSON.stringify({task_id:id}),cache:\'no-store\'});const d=await r.json();if(!r.ok)throw new Error(d.detail||\'Tekshirib bo‘lmadi.\');await refreshWallet();alertUser(`✅ Topshiriq bajarildi!\\n${d.xp?`⭐ +${d.xp} XP\\n`:\'\'}${d.coins?`🪙 +${d.coins} Coin`:\'\'}`);tasks();\n }catch(e){alertUser(e.message||\'Topshiriqni tekshirishda xatolik.\');}}\nfunction card(e,t,s,c){return `<div class="card" onclick="startCore(\'${c}\')"><div class="emoji">${e}</div><div class="ct">${t}</div><div class="cs">${s} · 6 savol</div></div>`;}\nasync function startCore(){\n clearInterval(state.timer);await refreshWallet();\n const d=state.done||{};\n if(["iq","leadership","memory","speed"].some(c=>d[c]!==undefined)){\n  alertUser("Bugungi test allaqachon bajarilgan. Ertaga qayta urinib ko‘ring.");home();return;\n }\n state.cat="all";state.idx=0;state.answers=[];state.started=Date.now();\n state.attemptId=(window.crypto&&crypto.randomUUID)?crypto.randomUUID():Date.now()+"-"+Math.random().toString(36).slice(2);\n const order=["iq","leadership","memory","speed"], qs=[];\n order.forEach(cat=>{\n  const all=DATA.core[cat],recent=load("recent_"+cat,[]),available=all.filter(q=>!recent.includes(q.id));\n  const pool=available.length>=2?available:all;\n  shuffle(pool).slice(0,2).forEach(q=>qs.push({...q,cat}));\n });\n state.qs=qs;state.screen="core";renderCore();\n}\nfunction shuffle(a){a=[...a];for(let i=a.length-1;i>0;i--){let j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}\nfunction timeFor(cat){return ({iq:20,leadership:20,memory:10,speed:5})[cat]||20;}\nfunction timerColor(p){return p>0.6?"#39d98a":p>0.35?"#f2c94c":p>0.15?"#f2994a":"#ff5b5b";}\nfunction renderCore(){\n clearInterval(state.timer);const q=state.qs[state.idx];const cat=q.cat;state.left=timeFor(cat);state.qStarted=Date.now();\n const pct=state.left?100:0;let content="";\n if(q.type==="memory"){\n  content=`<div id="memoryShow" class="memorybox">${esc(q.memory)}</div><div id="memoryQuestion" style="display:none"><div class="question">${esc(q.q)}</div><div class="opts">${q.opts.map((x,i)=>`<button class="opt" onclick="answerCore(${i})">${esc(x)}</button>`).join("")}</div></div>`;\n }else{\n  content=`<div class="question">${esc(q.q)}</div><div class="opts">${q.opts.map((x,i)=>`<button class="opt" onclick="answerCore(${i})">${esc(x)}</button>`).join("")}</div>`;\n }\n app.innerHTML=`<div class="wrap">${renderTop()}<div class="back" onclick="confirmExit()">← Bosh sahifa</div>\n <div class="qbox"><div class="qnum"><b>${({iq:"🧠 AQL",leadership:"👑 LIDERLIK",memory:"🧩 XOTIRA",speed:"⚡ TEZLIK"})[cat]}</b><span style="float:right">${state.idx+1} / 8 · ⏱ <span id="timer">${state.left}</span>s</span></div>\n <div class="progress"><div id="timebar" class="bar" style="width:${pct}%;background:${timerColor(1)}"></div></div>${content}</div></div>`;\n if(q.type==="memory"){\n  setTimeout(()=>{const m=document.getElementById("memoryShow"),qq=document.getElementById("memoryQuestion");if(m)m.style.display="none";if(qq)qq.style.display="block";},1800);\n }\n state.timer=setInterval(()=>{state.left--;const el=document.getElementById("timer"),bar=document.getElementById("timebar");const p=Math.max(0,state.left/timeFor(cat));if(el)el.textContent=Math.max(0,state.left);if(bar){bar.style.width=(p*100)+"%";bar.style.background=timerColor(p);bar.classList.toggle("warn",p<=0.15);}if(state.left<=0){clearInterval(state.timer);answerCore(null);}},1000);\n}\nfunction answerCore(i){\n clearInterval(state.timer);if(state.qs[state.idx])state.answers[state.idx]=i;\n if(state.idx<7){state.idx++;renderCore();}else finishCore();\n}\nasync function finishCore(){\n clearInterval(state.timer);\n const byCat={};["iq","leadership","memory","speed"].forEach(cat=>{const items=state.qs.map((q,i)=>({q,i})).filter(x=>x.q.cat===cat);let correct=0;items.forEach(x=>{if(state.answers[x.i]===x.q.ans)correct++;});byCat[cat]={correct,total:items.length,pct:Math.round(correct/items.length*100)};});\n const attempt=state.attemptId;save("zako_pending_bundle",{attempt_id:attempt,results:byCat,date:todayKey()});\n app.innerHTML=`<div class="wrap">${renderTop()}<div class="center"><div class="small">TEST YAKUNLANDI</div><div class="resultScore">${Math.round(Object.values(byCat).reduce((a,x)=>a+x.pct,0)/4)}%</div><div class="small">8 ta savol · 4 bo‘lim</div></div><div style="height:16px"></div><div class="stack">${Object.entries(byCat).map(([c,x])=>`<div class="notice"><b>${({iq:"🧠 Aql",leadership:"👑 Liderlik",memory:"🧩 Xotira",speed:"⚡ Tezlik"})[c]}</b> — ${x.pct}% · ${x.correct}/${x.total}</div>`).join("")}</div><div style="height:12px"></div><div class="notice" id="scoreStatus">⏳ Natija serverga yozilmoqda…</div><button class="btn secondary" onclick="home()">Bosh sahifa</button></div>`;\n let allOk=true;\n for(const [cat,x] of Object.entries(byCat)){const ok=await submitScore(attempt+"_"+cat,cat,x.pct);if(!ok){allOk=false;break;}}\n if(allOk){localStorage.removeItem("zako_pending_bundle");await refreshWallet();home();}\n}\nasync function submitScore(attempt,cat,pct){\n const status=document.getElementById("scoreStatus");let last="Serverga ulanib bo‘lmadi.";\n for(let n=0;n<4;n++){\n  try{const controller=new AbortController();const t=setTimeout(()=>controller.abort(),35000);const r=await fetch("/api/score",{method:"POST",headers:apiHeaders(),body:JSON.stringify({category:cat,pct,attempt_id:attempt}),cache:"no-store",signal:controller.signal});clearTimeout(t);const text=await r.text();let d={};try{d=JSON.parse(text)}catch(_){}if(!r.ok)throw new Error(d.detail||`Server xatosi (${r.status})`);if(status)status.innerHTML=`🏆 Natija saqlandi: <b>${cat}</b>`;return true;}catch(e){last=e.name==="AbortError"?"Server uzoq javob berdi.":(e.message||"Aloqa xatosi.");if(status)status.innerHTML=`⚠️ ${esc(last)}<br><span class="small">Qayta urinilmoqda…</span>`;if(n<3)await new Promise(res=>setTimeout(res,1500*(n+1)));}\n }\n if(status)status.innerHTML=`⚠️ <b>Natija hali serverga yozilmadi.</b><br><span class="small">${esc(last)}</span>`;return false;\n}\nasync function ranking(period="week"){\n app.innerHTML=`<div class="wrap">${renderTop()}<div class="back" onclick="home()">← Bosh sahifa</div><h1>🏆 Reyting</h1>\n <div class="grid"><button class="btn ${period===\'week\'?\'\':\'secondary\'}" onclick="ranking(\'week\')">Haftalik</button><button class="btn ${period===\'month\'?\'\':\'secondary\'}" onclick="ranking(\'month\')">Oylik</button></div>\n <div style="height:14px"></div><div class="rankhead"><span>O‘RIN</span><span>ISM</span><span style="text-align:right">BALL</span><span style="text-align:right">YUTUQ</span></div>\n <div id="rankbox" class="stack"><div class="notice">Yuklanmoqda…</div></div></div>`;\n try{\n  const r=await fetch("/api/ranking?period="+period,{headers:apiHeaders(),cache:"no-store"});\n  const j=await r.json();if(!r.ok)throw new Error(j.detail||"Reytingni yuklab bo‘lmadi.");\n  const prizeMap={};(j.prizes||[]).forEach(x=>prizeMap[x.place]=x.prize||"—");\n  const b=document.getElementById("rankbox");\n  b.innerHTML=j.rows.length?j.rows.map((x,i)=>{\n    const cls=i===0?"gold":i===1?"silver":i===2?"bronze":"";\n    const medal=i<3?["🥇","🥈","🥉"][i]:"#"+(i+1);\n    return `<div class="rankrow ${cls}"><span class="rn">${medal}</span><span class="rname">${esc(x.name)}</span><span class="rscore">${x.score}</span><span class="rprize">${esc(prizeMap[i+1]||"—")} ${prizeMap[i+1]?"🎁":""}</span></div>`;\n  }).join(""):"<div class=\'notice\'>Hali natijalar yo‘q.</div>";\n }catch(e){\n  const b=document.getElementById("rankbox");if(b)b.innerHTML=`<div class="notice">❌ ${esc(e.message||"Reytingni yuklab bo‘lmadi.")}</div>`;\n }\n}\nasync function shop(){\n app.innerHTML=`<div class="wrap">${renderTop()}<div class="back" onclick="profile()">← Profil</div><h1>🛍 Coin Shop</h1>\n <div class="notice">⭐ <b>1000 XP = 10 Coin</b>. Coin kamyob valyuta.</div><button class="btn secondary" onclick="convertXP()">⭐ XP → 🪙 Coin</button><div style="height:12px"></div><div id="shopbox" class="stack">Yuklanmoqda…</div></div>`;\n try{const r=await fetch("/api/shop",{headers:apiHeaders(),cache:"no-store"});const j=await r.json();document.getElementById("shopbox").innerHTML=(j.items||[]).map(x=>{\n  if(x.kind===\'frame\')return `<div class="shopcard"><div class="ct">🖼️ ${esc(x.title)}</div><div class="small">${esc(x.description||\'\')}</div><div style="height:8px"></div><button class="btn" onclick="redeemGift(${x.id})">${x.xp_price?`⭐ ${x.xp_price} XP`: `🪙 ${x.coins_price} Coin`} → Taqish</button></div>`;\n  if(x.kind===\'gift\')return `<div class="shopcard"><div class="ct">🎁 ${esc(x.title)}</div><div class="small">${esc(x.description||\'\')}</div><div style="height:8px"></div><button class="btn" onclick="redeemGift(${x.id})">🪙 ${x.coins_price} Coin</button></div>`;\n  return `<div class="shopcard"><div class="ct">🪙 ${esc(x.title)}</div><div class="small">${esc(x.description||\'\')}</div><div style="height:8px"></div><button class="btn" onclick="buyCoins(${x.id})">⭐ ${x.stars_price} Stars → ${x.coins_price} Coin</button></div>`;\n }).join("")||"<div class=\'notice\'>Shop hozircha bo‘sh.</div>";\n }catch(e){document.getElementById("shopbox").textContent="Shopni yuklab bo‘lmadi.";}\n}\nasync function convertXP(){try{const r=await fetch("/api/xp/convert",{method:"POST",headers:apiHeaders(),body:"{}"});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Almashtirishda xatolik.");if(!d.converted){alertUser("1000 XP kerak.");return;}await refreshWallet();alertUser(`✅ ${d.converted} Coin olindi.`);shop();}catch(e){alertUser(e.message);}}\nasync function redeemGift(id){try{const r=await fetch("/api/shop/redeem",{method:"POST",headers:apiHeaders(),body:JSON.stringify({item_id:id})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Xatolik.");await refreshWallet();alertUser(d.message||"✅ Bajarildi.");profile();}catch(e){alertUser(e.message);}}\nasync function buyCoins(id){try{const r=await fetch("/api/coin/invoice",{method:"POST",headers:apiHeaders(),body:JSON.stringify({item_id:id})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"To‘lov oynasi ochilmadi.");if(tg?.openInvoice)tg.openInvoice(d.invoice,()=>{setTimeout(()=>{refreshWallet();shop();},1500);});else location.href=d.invoice;}catch(e){alertUser(e.message);}}\nasync function claimPremium(){try{const r=await fetch("/api/streak/premium",{method:"POST",headers:apiHeaders(),body:"{}"});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Premiumni olishda xatolik.");alertUser(d.already?"Bu mukofot avval olingan.":"🎉 1 oylik Premium olindi!");await refreshWallet();profile();}catch(e){alertUser(e.message);}}\nasync function profile(){\n await refreshWallet();\n const frame=state.frame_id?`🖼️ Ramka #${state.frame_id}`:"🖼️ Oddiy ramka";\n const prem=state.premium_until?`👑 Premium: ${new Date(state.premium_until).toLocaleDateString(\'uz-UZ\')}`:"👑 Premium yo‘q";\n const d=state.done||{};\n app.innerHTML=`<div class="wrap">${renderTop()}<h1>👤 Profil</h1>\n <div class="hero profilehero">\n   <div class="profileframe">\n     <div class="logo">🧠 ZAKO</div>\n     <div style="font-size:25px;font-weight:900;margin-top:8px">${esc(getName())}</div>\n     <div class="small" style="margin-top:5px">${frame}</div>\n     <div class="small" style="margin-top:5px">${prem}</div>\n   </div>\n   <div class="stat"><span>🏆 ZAKO Score</span><b>${state.week||0}</b></div>\n   <div class="stat"><span>⭐ XP</span><b>${state.xp}</b></div>\n   <div class="stat"><span>🪙 Coin</span><b>${state.coins}</b></div>\n   <div class="stat"><span>🔥 Streak</span><b>${state.streak} kun</b></div>\n </div>\n <div class="profile-stats">\n   <div class="pstat iq"><div class="pe">🧠</div><div class="pl">AQL</div><div class="pv">${d.iq??\'—\'}${d.iq!=null?\'%\':\'\'}</div></div>\n   <div class="pstat speed"><div class="pe">⚡</div><div class="pl">TEZLIK</div><div class="pv">${d.speed??\'—\'}${d.speed!=null?\'%\':\'\'}</div></div>\n   <div class="pstat memory"><div class="pe">🧩</div><div class="pl">XOTIRA</div><div class="pv">${d.memory??\'—\'}${d.memory!=null?\'%\':\'\'}</div></div>\n   <div class="pstat leadership"><div class="pe">👑</div><div class="pl">LIDERLIK</div><div class="pv">${d.leadership??\'—\'}${d.leadership!=null?\'%\':\'\'}</div></div>\n </div>\n <div style="height:12px"></div>\n <button class="btn" onclick="shop()">🛍 Coin Shop</button>\n ${state.streak>=30&&!state.premium_claimed?`<div style="height:8px"></div><button class="btn secondary" onclick="claimPremium()">🔥 30 streak → 1 oylik Premium</button>`:\'\'}\n \n <div style="height:80px"></div>${nav(\'profile\')}</div>`;\n}\nfunction socialMenu(kind="love"){\n state.social=kind; state.socialIdx=0; state.socialAnswers=[];\n const title=kind==="love"?"❤️ Meni qanchalik bilasan?":"🤝 Do‘stingni qanchalik bilasan?";\n app.innerHTML=`<div class="wrap">${renderTop()}<div class="back" onclick="home()">← Bosh sahifa</div>\n <div class="hero"><span class="badge">${title}</span><h1>6 ta savol. Rostini belgila.</h1>\n <div class="sub">${kind==="love"?"O‘zing haqingdagi javoblarni tanla. Keyin tayyor xabarni do‘stingga yubor.":"Do‘sting haqidagi to‘g‘ri javoblarni tanla. Keyin uning seni qanchalik bilishini tekshir."}</div></div>\n <button class="btn" onclick="createSocial()">🚀 Boshlash</button></div>`;\n}\nfunction createSocial(){state.qs=shuffle(DATA.social[state.social]).slice(0,6);state.idx=0;state.answers=[];renderSocialCreator();}\nfunction renderSocialCreator(){\n const q=state.qs[state.idx];\n app.innerHTML=`<div class="wrap">${renderTop()}<div class="qnum">${state.idx+1} / 6</div><div class="progress"><div class="bar" style="width:${(state.idx/6)*100}%"></div></div>\n <div class="qbox"><div class="question">${esc(q.q)}</div>${socialInput(q,"creator")}</div></div>`;\n}\nfunction socialInput(q,mode){\n const fn=mode==="creator"?"socialCreatorChoose":"challengerChoose";\n if(q.type==="month")return `<div class="picker"><div class="wheel" id="monthWheel">${DATA.months.map((m,i)=>`<div data-i="${i}">${esc(m)}</div>`).join("")}</div></div><button class="btn" style="margin-top:12px" onclick="chooseMonth(\'${mode}\')">Tanlash</button>`;\n if(q.type==="color")return `<div class="colors">${q.opts.map((x,i)=>`<button class="color" onclick="${fn}(${i})">${esc(x)}</button>`).join("")}</div>`;\n if(q.type==="slider")return `<input class="slider" id="slider" type="range" min="0" max="100" value="50" oninput="document.getElementById(\'sv\').textContent=this.value+\'%\'"/><div class="sliderlabels"><span>🌅 Ertalab</span><span id="sv">50%</span><span>🌙 Kechasi</span></div><div style="height:15px"></div><button class="btn" onclick="${fn}(Number(document.getElementById(\'slider\').value))">Tanlash</button>`;\n return `<div class="opts">${q.opts.map((x,i)=>`<button class="opt" onclick="${fn}(${i})">${esc(x)}</button>`).join("")}</div>`;\n}\nfunction chooseMonth(mode){\n const w=document.getElementById("monthWheel"); if(!w)return;\n const els=[...w.children],center=w.scrollTop+w.clientHeight/2;let best=0,dist=Infinity;\n els.forEach((el,i)=>{const d=Math.abs(el.offsetTop+el.offsetHeight/2-center);if(d<dist){dist=d;best=i;}});\n mode==="creator"?socialCreatorChoose(best):challengerChoose(best);\n}\nfunction socialCreatorChoose(v){\n state.answers[state.idx]=v;\n if(state.idx<5){state.idx++;renderSocialCreator();}else finishSocialCreator();\n}\nasync function finishSocialCreator(){\n if(!tg?.initData){alertUser("Telegram ichida oching.");return;}\n try{\n  const r=await fetch("/api/social/create",{method:"POST",headers:apiHeaders(),body:JSON.stringify({kind:state.social,q_ids:state.qs.map(q=>q.id),answers:state.answers}),cache:"no-store"});\n  const d=await r.json(); if(!r.ok)throw new Error(d.detail||"Test yaratilmadi.");\n  const text=state.social==="love"?"❤️ Meni qanchalik bilasan?\\n\\nQani, meni qanchalik bilishingni tekshir 😏":"🤝 Do‘stingni qanchalik bilasan?\\n\\nQani, meni qanchalik bilishingni tekshir 😏";\n  const shareUrl="https://t.me/share/url?url="+encodeURIComponent(d.url)+"&text="+encodeURIComponent(text);\n  app.innerHTML=`<div class="wrap">${renderTop()}<div class="center"><div style="font-size:55px">🔗</div><h1>Test tayyor!</h1><div class="sub">Tayyor xabarni do‘stingga yubor. U linkni bosadi → ZAKO BOT → kanal obunasi → ZAKO → 6 ta savol. Tugatgach natija senga botdan keladi.</div></div>\n  <div class="sharebox">${esc(text).replace(/\\n/g,"<br>")}<br><br>🔗 Test linki xabarga biriktiriladi.</div><div style="height:12px"></div>\n  <div class="stack"><button class="btn" onclick="openShare(\'${encodeURIComponent(shareUrl)}\')">📤 Do‘stga yuborish</button><button class="btn secondary" onclick="copyText(\'${encodeURIComponent(d.url)}\')">📋 Linkni nusxalash</button><button class="btn secondary" onclick="home()">Bosh sahifa</button></div></div>`;\n }catch(e){alertUser(e.message||"Aloqa xatosi. Internetni tekshirib qayta urinib ko‘ring.");}\n}\nfunction openShare(enc){const u=decodeURIComponent(enc);if(tg?.openTelegramLink)tg.openTelegramLink(u);else location.href=u;}\nasync function copyText(enc){const u=decodeURIComponent(enc);try{await navigator.clipboard.writeText(u);alertUser("Link nusxalandi.");}catch(e){prompt("Linkni nusxalang:",u);}}\nasync function loadChallenge(token){\n try{\n  const r=await fetch("/api/social/get?token="+encodeURIComponent(token),{headers:{"X-Telegram-Init-Data":tg?.initData||""},cache:"no-store"});\n  const d=await r.json();if(!r.ok)throw new Error(d.detail||"Testni ochib bo‘lmadi.");\n  state.challengeToken=token;state.challenge=d;state.social=d.kind;state.qs=d.questions;state.idx=0;state.answers=[];renderChallenger();\n }catch(e){app.innerHTML=`<div class="wrap">${renderTop()}<div class="hero"><h1>🔒 Test ochilmadi</h1><div class="sub">${esc(e.message||"Test topilmadi.")}</div></div><button class="btn secondary" onclick="home()">Bosh sahifa</button></div>`;}\n}\nfunction renderChallenger(){\n const q=state.qs[state.idx];\n app.innerHTML=`<div class="wrap">${renderTop()}<div class="qnum">${state.idx+1} / 6</div><div class="progress"><div class="bar" style="width:${(state.idx/6)*100}%"></div></div><div class="qbox"><div class="question">${esc(q.q)}</div>${socialInput(q,"challenger")}</div></div>`;\n}\nfunction challengerChoose(v){\n state.answers[state.idx]=v;\n if(state.idx<5){state.idx++;renderChallenger();}else finishChallenge();\n}\nasync function finishChallenge(){\n try{\n  const r=await fetch("/api/social/finish",{method:"POST",headers:apiHeaders(),body:JSON.stringify({token:state.challengeToken,answers:state.answers}),cache:"no-store"});\n  const d=await r.json();if(!r.ok)throw new Error(d.detail||"Natijani yuborib bo‘lmadi.");\n  const title=state.social==="love"?"❤️ Meni qanchalik bilasan?":"🤝 Do‘stingni qanchalik bilasan?";\n  app.innerHTML=`<div class="wrap">${renderTop()}<div class="center"><div class="small">${title}</div><div class="resultScore">${d.pct}%</div><div class="insight">${esc(d.reaction)}</div></div><div style="height:12px"></div><div class="notice">📩 Natija test egasiga ZAKO BOTIDAN yuborildi.</div><button class="btn secondary" onclick="home()">🚀 Men ham test yarataman</button></div>`;\n }catch(e){alertUser(e.message||"Natijani yuborib bo‘lmadi. Internetni tekshirib qayta urin.");}\n}\nwindow.home=home;window.startCore=startCore;window.answerCore=answerCore;window.confirmExit=confirmExit;window.socialMenu=socialMenu;window.createSocial=createSocial;window.socialCreatorChoose=socialCreatorChoose;window.challengerChoose=challengerChoose;window.chooseMonth=chooseMonth;window.openShare=openShare;window.copyText=copyText;window.loadChallenge=loadChallenge;window.finishChallenge=finishChallenge;window.ranking=ranking;window.profile=profile;window.shop=shop;window.friends=friends;window.tasks=tasks;window.loadFriends=loadFriends;window.convertXP=convertXP;window.redeemGift=redeemGift;window.buyCoins=buyCoins;\nconst challenge=new URLSearchParams(location.search).get("challenge");if(challenge)loadChallenge(challenge);else home();\n</script>\n</body>\n</html>'

DATA = {'core': {'iq': [{'id': 'iq1', 'q': 'Bir loyihada 4 vazifa bor: A, B, C, D. A B dan oldin, C A dan keyin, D esa B dan keyin bajariladi. Qaysi tartib mumkin?', 'type': 'mcq', 'opts': ['A → B → C → D', 'B → A → D → C', 'A → C → B → D', 'C → A → B → D'], 'ans': 0}, {'id': 'iq2', 'q': '3 ta quti bor: birida faqat qizil, birida faqat ko‘k, birida aralash sharlar. Yorliqlarning barchasi noto‘g‘ri. Faqat bitta shar olib, qutilarni aniqlash uchun qaysi qutidan olasiz?', 'type': 'mcq', 'opts': ['“Qizil”', '“Ko‘k”', '“Aralash”', 'Istalgan'], 'ans': 2}, {'id': 'iq3', 'q': 'Barcha X lar Y. Ba’zi Y lar Z. Qaysi xulosa majburiy?', 'type': 'mcq', 'opts': ['Barcha X lar Z', 'Ba’zi X lar Z', 'Hech bir X Z emas', 'X lar Y ga kiradi'], 'ans': 3}, {'id': 'iq4', 'q': 'Bir mahsulot 20% arzonlashtirilib 240 000 so‘m bo‘ldi. Chegirmadan oldingi narx qancha edi?', 'type': 'mcq', 'opts': ['280 000', '288 000', '300 000', '320 000'], 'ans': 2}, {'id': 'iq5', 'q': '4 kishi bir-biri bilan bir martadan uchrashib qo‘l berishdi. Jami nechta qo‘l siqish bo‘ladi?', 'type': 'mcq', 'opts': ['4', '6', '8', '12'], 'ans': 1}, {'id': 'iq6', 'q': 'Bir sonning 30% i 24 ga teng. Shu sonning 75% i nechaga teng?', 'type': 'mcq', 'opts': ['48', '54', '60', '72'], 'ans': 2}, {'id': 'iq7', 'q': 'Ketma-ketlikdagi keyingi sonni toping: 2, 6, 12, 20, 30, ?', 'type': 'mcq', 'opts': ['36', '40', '42', '44'], 'ans': 2}, {'id': 'iq8', 'q': 'Agar barcha rahbarlar qaror qabul qiladi va ayrim qaror qabul qiluvchilar tajribasiz bo‘lsa, qaysi gapni aniq aytish mumkin?', 'type': 'mcq', 'opts': ['Barcha rahbarlar tajribali', 'Ayrim rahbarlar tajribasiz', 'Rahbarlar qaror qabul qiladi', 'Hech bir tajribasiz rahbar yo‘q'], 'ans': 2}, {'id': 'iq9', 'q': 'Bir yo‘lda A shahardan B shaharga 60 km/soat, qaytishda 40 km/soat tezlikda yurildi. Bir xil masofa uchun o‘rtacha tezlik qancha?', 'type': 'mcq', 'opts': ['48 km/soat', '50 km/soat', '52 km/soat', '55 km/soat'], 'ans': 0}, {'id': 'iq10', 'q': '5 ta ishchi ishni 12 kunda tugatadi. Bir xil unumdorlikda 10 ta ishchi shu ishni necha kunda tugatadi?', 'type': 'mcq', 'opts': ['3', '5', '6', '8'], 'ans': 2}], 'speed': [{'id': 'sp1', 'q': 'Qaysi kod aynan bir xil?', 'type': 'mcq', 'opts': ['K7M2P / K7M2P', 'K7M2P / K7N2P', 'K7M2P / K7MZP', 'K7M2P / K72MP'], 'ans': 0}, {'id': 'sp2', 'q': 'Eng katta qiymatni tanlang.', 'type': 'mcq', 'opts': ['0.809', '0.89', '0.8099', '0.899'], 'ans': 3}, {'id': 'sp3', 'q': 'Qaysi belgi ketma-ketlikni buzadi?  ▲ ▲ ▲ △ ▲', 'type': 'mcq', 'opts': ['1-belgi', '2-belgi', '4-belgi', '5-belgi'], 'ans': 2}, {'id': 'sp4', 'q': 'Qaysi juftlik teng?', 'type': 'mcq', 'opts': ['17×3 / 51', '18×3 / 52', '72÷8 / 8', '45+7 / 53'], 'ans': 0}, {'id': 'sp5', 'q': 'Chap va o‘ng kod bir xilmi?  Q9R7K  /  Q9R7K', 'type': 'yesno', 'opts': ['HA', 'YO‘Q'], 'ans': 0}, {'id': 'sp6', 'q': 'Qaysi raqam boshqalardan farq qiladi?  18, 24, 30, 35', 'type': 'mcq', 'opts': ['18', '24', '30', '35'], 'ans': 3}, {'id': 'sp7', 'q': 'Qaysi so‘zda “z” harfi bor?', 'type': 'mcq', 'opts': ['BULUT', 'ZAMON', 'KITOB', 'DARAXT'], 'ans': 1}, {'id': 'sp8', 'q': 'Qaysi qiymat 1 ga eng yaqin?', 'type': 'mcq', 'opts': ['0.91', '0.99', '0.89', '0.79'], 'ans': 1}, {'id': 'sp9', 'q': 'Qaysi juftlik aynan bir xil?', 'type': 'mcq', 'opts': ['B8Q1 / B8Q1', 'M4T7 / M4T1', 'P2L9 / P2I9', 'X7R3 / X7R8'], 'ans': 0}, {'id': 'sp10', 'q': 'Qaysi natija eng katta?', 'type': 'mcq', 'opts': ['14+9', '31-7', '6×4', '50÷2'], 'ans': 3}], 'memory': [{'id': 'mem1', 'q': 'Eslab qoling: 7 — K — 2 — M — 9. Qaysi belgi 2 dan keyin kelgan?', 'type': 'memory', 'memory': '7  K  2  M  9', 'opts': ['7', 'K', 'M', '9'], 'ans': 2}, {'id': 'mem2', 'q': 'Eslab qoling: ▲ — 4 — B — 8 — Q. Qaysi belgi ikkinchi o‘rinda edi?', 'type': 'memory', 'memory': '▲  4  B  8  Q', 'opts': ['▲', '4', 'B', '8'], 'ans': 1}, {'id': 'mem3', 'q': 'Eslab qoling: 3 — L — 8 — R — 1 — T. Qaysi belgi R dan oldin kelgan?', 'type': 'memory', 'memory': '3  L  8  R  1  T', 'opts': ['L', '8', '1', 'T'], 'ans': 1}, {'id': 'mem4', 'q': 'Eslab qoling: 5 — A — 9 — C — 4. Qaysi raqam A dan keyin kelgan?', 'type': 'memory', 'memory': '5  A  9  C  4', 'opts': ['5', '9', '4', 'C'], 'ans': 1}, {'id': 'mem5', 'q': 'Eslab qoling: N — 6 — P — 2 — V — 8. Qaysi belgi uchinchi o‘rinda edi?', 'type': 'memory', 'memory': 'N  6  P  2  V  8', 'opts': ['6', 'P', '2', 'V'], 'ans': 1}, {'id': 'mem6', 'q': 'Eslab qoling: 4 — Z — 7 — K — 3 — M. Qaysi raqam K dan keyin kelgan?', 'type': 'memory', 'memory': '4  Z  7  K  3  M', 'opts': ['4', '7', '3', 'M'], 'ans': 2}, {'id': 'mem7', 'q': 'Eslab qoling: R — 2 — H — 9 — D. Birinchi va oxirgi belgilar qaysi?', 'type': 'memory', 'memory': 'R  2  H  9  D', 'opts': ['R va D', '2 va 9', 'H va D', 'R va 9'], 'ans': 0}, {'id': 'mem8', 'q': 'Eslab qoling: 8 — C — 1 — F — 6 — Q. F dan oldingi ikki belgi qaysi?', 'type': 'memory', 'memory': '8  C  1  F  6  Q', 'opts': ['8, C', 'C, 1', '1, F', 'F, 6'], 'ans': 1}, {'id': 'mem9', 'q': 'Eslab qoling: B — 7 — T — 3 — L. T dan keyingi belgi qaysi?', 'type': 'memory', 'memory': 'B  7  T  3  L', 'opts': ['7', '3', 'L', 'B'], 'ans': 1}, {'id': 'mem10', 'q': 'Eslab qoling: 2 — G — 5 — X — 8. Qaysi belgi 5 dan oldin kelgan?', 'type': 'memory', 'memory': '2  G  5  X  8', 'opts': ['2', 'G', 'X', '8'], 'ans': 1}], 'leadership': [{'id': 'lead1', 'q': 'Jamoangizda muddat yaqin. Bir xodim juda tez, ikkinchisi esa ancha sifatli ishlaydi. Eng to‘g‘ri qaror?', 'type': 'mcq', 'opts': ['Hammasini tez ishlaydigan xodimga berish', 'Sifatli ishni muhim qismga, tezkor xodimni tez bajariladigan qismga biriktirish', 'Ikkalasiga ham bir xil vazifa berish', 'Eng tajribalisini tanlab, qolganini kutish'], 'ans': 1}, {'id': 'lead2', 'q': 'Ikki xodim bir masalada kelisha olmayapti. Vazifa esa kechikmoqda. Avval nima qilasiz?', 'type': 'mcq', 'opts': ['Darhol bir tomonning fikrini tanlaysiz', 'Ikkalasini ham jazolaysiz', 'Muammoni, faktlarni va qaror uchun kerakli mezonni aniqlaysiz', 'Vazifani boshqa odamga berasiz'], 'ans': 2}, {'id': 'lead3', 'q': 'Muhim loyiha 1 kun kechikmoqda. Sabab aniq emas. Eng yaxshi birinchi qadam?', 'type': 'mcq', 'opts': ['Aybdorni topish', 'Jamoani ko‘proq ishlashga majburlash', 'Qaysi bosqich to‘xtaganini va sababini aniqlash', 'Loyihani bekor qilish'], 'ans': 2}, {'id': 'lead4', 'q': 'Jamoada kuchli xodim bor, lekin barcha qarorni o‘zi qilishga urinadi. Nima qilasiz?', 'type': 'mcq', 'opts': ['Uni chetlashtirasiz', 'Hammasini o‘zingiz nazorat qilasiz', 'Mas’uliyat chegarasini belgilab, qaror vakolatini aniq taqsimlaysiz', 'Hech narsa demaysiz'], 'ans': 2}, {'id': 'lead5', 'q': 'Yangi xodim xato qildi, lekin xatosini yashirmay darhol aytdi. Rahbar sifatida eng foydali javob?', 'type': 'mcq', 'opts': ['Uni hammaga tanbeh berish', 'Xatoni tuzatish va qayta takrorlanmasligi uchun sababini tahlil qilish', 'Xatoni e’tiborsiz qoldirish', 'Keyingi vazifalarni undan olish'], 'ans': 1}, {'id': 'lead6', 'q': 'Resurs yetmayapti: uchta vazifa bor, faqat bittasini bugun tugatish mumkin. Qanday tanlaysiz?', 'type': 'mcq', 'opts': ['Eng oson vazifani', 'Eng ko‘p gapirilgan vazifani', 'Eng katta ta’sir va eng yaqin oqibatga ega vazifani', 'Tasodifiy tanlaysiz'], 'ans': 2}, {'id': 'lead7', 'q': 'Jamoa natijasi yaxshi, ammo ikki xodim hissasi teng emas. Qanday yo‘l tutasiz?', 'type': 'mcq', 'opts': ['Hamma uchun bir xil mukofot', 'Hissani va natijani alohida baholab, keyingi rollarni shunga moslashtirish', 'Faqat eng faol xodimni maqtash', 'Hech kimga fikr bildirmaslik'], 'ans': 1}, {'id': 'lead8', 'q': 'Qabul qilgan qaroringiz kutilgan natijani bermadi. Kuchli rahbarning birinchi reaksiyasi?', 'type': 'mcq', 'opts': ['Aybdorni qidirish', 'Qaror ortidagi taxminlar va ma’lumotlarni qayta tekshirish', 'Qarorni yashirish', 'Jamoani ayblash'], 'ans': 1}, {'id': 'lead9', 'q': 'Jamoada muammo bor, lekin hech kim gapirmayapti. Eng yaxshi usul?', 'type': 'mcq', 'opts': ['Darhol jazolash', 'Ochiq savol berib, xavfsiz muhitda muammoni aniqlash', 'Muammoni o‘zingiz taxmin qilish', 'Yig‘ilishni bekor qilish'], 'ans': 1}, {'id': 'lead10', 'q': 'Sizga muhim ish topshirildi, lekin maqsad noaniq. Eng to‘g‘ri qadam?', 'type': 'mcq', 'opts': ['Darhol boshlash', 'Natija mezoni va ustuvorlikni aniqlashtirish', 'Boshqaga topshirish', 'Muddatni kutish'], 'ans': 1}]}, 'social': {'love': [{'id': 'a1', 'q': 'Menga qaysi ichimlik ko‘proq yoqadi?', 'type': 'mcq', 'opts': ['🥤 Cola', '🥤 Pepsi', '🧃 Sharbat', '☕ Choy']}, {'id': 'a2', 'q': 'Tug‘ilgan oyim qaysi?', 'type': 'month', 'opts': []}, {'id': 'a3', 'q': 'Men qaysi rangni ko‘proq tanlayman?', 'type': 'color', 'opts': ['🔴', '🔵', '🟢', '🟡', '🟣', '⚫', '⚪', '🟠']}, {'id': 'a4', 'q': 'Ideal dam olish kunim qaysi?', 'type': 'mcq', 'opts': ['🏠 Uyda film', '🌆 Do‘stlar bilan tashqarida', '✈️ Sayohat', '🎮 O‘yin']}, {'id': 'a5', 'q': 'Men qaysi taomni tanlashim ehtimoli yuqori?', 'type': 'mcq', 'opts': ['🍕 Pizza', '🍔 Burger', '🍜 Lag‘mon', '🍣 Sushi']}, {'id': 'a6', 'q': 'Men ko‘proq qaysi paytni yoqtiraman?', 'type': 'slider', 'opts': []}, {'id': 'a7', 'q': 'Kutilmagan sovg‘adan qaysi birini tanlayman?', 'type': 'mcq', 'opts': ['🎧 Texnika', '🌹 Romantik sovg‘a', '👟 Kiyim', '🎁 Sirli sovg‘a']}, {'id': 'a8', 'q': 'Men sayohatda nimani ko‘proq xohlayman?', 'type': 'mcq', 'opts': ['🏖 Dengiz', '🏔 Tog‘', '🏙 Katta shahar', '🌲 Tabiat']}, {'id': 'a9', 'q': 'Menga xabar yozishmi yoki qo‘ng‘iroq qilishmi yoqadi?', 'type': 'mcq', 'opts': ['💬 Xabar', '📞 Qo‘ng‘iroq', '🤷 Vaziyatga qarab', '🎥 Videoqo‘ng‘iroq']}, {'id': 'a10', 'q': 'Men bo‘sh vaqtimda birini tanlasam...', 'type': 'mcq', 'opts': ['🎬 Kino', '🎮 O‘yin', '📚 Kitob', '🚶 Sayr']}, {'id': 'a11', 'q': 'Menga qaysi ob-havo yoqadi?', 'type': 'mcq', 'opts': ['☀️ Issiq', '🌧 Yomg‘ir', '❄️ Qor', '🌥 Salqin']}, {'id': 'a12', 'q': 'Men ertalab uyg‘onganda birinchi nima qilishim ehtimoli yuqori?', 'type': 'mcq', 'opts': ['📱 Telefonni tekshirish', '💧 Suv ichish', '☕ Choy/kofe', '😴 Yana uxlash']}, {'id': 'a13', 'q': 'Men tanlashim kerak bo‘lsa, qaysi rangli kiyimni olaman?', 'type': 'color', 'opts': ['⚫', '⚪', '🔵', '🟢', '🔴', '🟡']}, {'id': 'a14', 'q': 'Menga qaysi musiqa kayfiyati yaqinroq?', 'type': 'mcq', 'opts': ['🔥 Energetik', '🌙 Sokin', '💔 Melanxolik', '🎉 Raqsbop']}, {'id': 'a15', 'q': 'Men uchun ideal kecha...', 'type': 'mcq', 'opts': ['🍿 Film', '🌃 Sayr', '🎮 O‘yin', '👥 Do‘stlar bilan suhbat']}, {'id': 'a16', 'q': 'Agar 1 kun bo‘sh vaqtim bo‘lsa, nimani tanlashim mumkin?', 'type': 'mcq', 'opts': ['😴 Dam olish', '🚗 Shahar tashqarisi', '🎮 O‘yin', '🎬 Kino']}, {'id': 'a17', 'q': 'Men ko‘proq qaysi sovg‘ani qadrlayman?', 'type': 'mcq', 'opts': ['💌 Ma’noli xat', '💰 Qimmat narsa', '🍫 Shirinlik', '📸 Birga tushgan foto']}, {'id': 'a18', 'q': 'Men restoran tanlasam, nimaga ko‘proq qarayman?', 'type': 'mcq', 'opts': ['🍽 Taom', '💰 Narx', '✨ Muhit', '⭐ Sharhlar']}, {'id': 'a19', 'q': 'Men qaysi hayvonni yoqimli deb bilishim ehtimoli yuqori?', 'type': 'mcq', 'opts': ['🐱 Mushuk', '🐶 It', '🐼 Panda', '🦊 Tulki']}, {'id': 'a20', 'q': 'Menga qaysi fasl ko‘proq yoqadi?', 'type': 'mcq', 'opts': ['🌸 Bahor', '☀️ Yoz', '🍂 Kuz', '❄️ Qish']}, {'id': 'a21', 'q': 'Men tanlashim kerak bo‘lsa, qaysi transport?', 'type': 'mcq', 'opts': ['🚗 Mashina', '✈️ Samolyot', '🚆 Poyezd', '🚲 Velosiped']}, {'id': 'a22', 'q': 'Menga qaysi biri ko‘proq yoqadi?', 'type': 'mcq', 'opts': ['🌊 Dengiz', '🏙 Shahar', '🏔 Tog‘', '🏡 Qishloq']}, {'id': 'a23', 'q': 'Men vaqtida kelish masalasida qandayman?', 'type': 'mcq', 'opts': ['⏰ Juda punktual', '🙂 Odatda vaqtida', '🏃 Ko‘pincha shoshilaman', '😅 Kechikishim mumkin']}, {'id': 'a24', 'q': 'Men kayfiyatim tushsa, ko‘proq nima qilaman?', 'type': 'mcq', 'opts': ['🎵 Musiqa', '😴 Uxlayman', '👥 Kim bilandir gaplashaman', '🎮 Chalg‘itaman']}], 'friend': [{'id': 'f1', 'q': 'Do‘sting qaysi ichimlikni tanlaydi?', 'type': 'mcq', 'opts': ['🥤 Cola', '🥤 Pepsi', '🧃 Sharbat', '☕ Choy']}, {'id': 'f2', 'q': 'Do‘stingning tug‘ilgan oyi qaysi?', 'type': 'month', 'opts': []}, {'id': 'f3', 'q': 'Do‘sting qaysi rangni tanlaydi?', 'type': 'color', 'opts': ['🔴', '🔵', '🟢', '🟡', '🟣', '⚫', '⚪', '🟠']}, {'id': 'f4', 'q': 'Do‘sting ideal dam olish kunini qanday o‘tkazadi?', 'type': 'mcq', 'opts': ['🏠 Uyda', '🌆 Tashqarida', '✈️ Sayohatda', '🎮 O‘yin bilan']}, {'id': 'f5', 'q': 'Do‘sting qaysi ovqatni tanlashi ehtimoli yuqori?', 'type': 'mcq', 'opts': ['🍕 Pizza', '🍔 Burger', '🍜 Lag‘mon', '🍣 Sushi']}, {'id': 'f6', 'q': 'Do‘sting ko‘proq qaysi paytni yoqtiradi?', 'type': 'slider', 'opts': []}, {'id': 'f7', 'q': 'Do‘stingga 1 mln so‘m tushsa, birinchi nima qiladi?', 'type': 'mcq', 'opts': ['🛍 Sarflaydi', '💰 Saqlaydi', '🎁 Sovg‘a qiladi', '✈️ Sayohatga ishlatadi']}, {'id': 'f8', 'q': 'Do‘sting sayohatda nimani tanlaydi?', 'type': 'mcq', 'opts': ['🏖 Dengiz', '🏔 Tog‘', '🏙 Shahar', '🌲 Tabiat']}, {'id': 'f9', 'q': 'Do‘sting bilan bog‘lanishning qaysi usuli unga yoqadi?', 'type': 'mcq', 'opts': ['💬 Xabar', '📞 Qo‘ng‘iroq', '🤷 Vaziyatga qarab', '🎥 Video']}, {'id': 'f10', 'q': 'Do‘sting bo‘sh vaqtida nimani tanlaydi?', 'type': 'mcq', 'opts': ['🎬 Kino', '🎮 O‘yin', '📚 Kitob', '🚶 Sayr']}, {'id': 'f11', 'q': 'Do‘stingga qaysi ob-havo yoqadi?', 'type': 'mcq', 'opts': ['☀️ Issiq', '🌧 Yomg‘ir', '❄️ Qor', '🌥 Salqin']}, {'id': 'f12', 'q': 'Do‘sting ertalab uyg‘onganda nima qiladi?', 'type': 'mcq', 'opts': ['📱 Telefon', '💧 Suv', '☕ Choy/kofe', '😴 Yana uxlaydi']}, {'id': 'f13', 'q': 'Do‘sting qaysi kiyim rangini tanlaydi?', 'type': 'color', 'opts': ['⚫', '⚪', '🔵', '🟢', '🔴', '🟡']}, {'id': 'f14', 'q': 'Do‘sting qaysi musiqa kayfiyatini tanlaydi?', 'type': 'mcq', 'opts': ['🔥 Energetik', '🌙 Sokin', '💔 Melanxolik', '🎉 Raqsbop']}, {'id': 'f15', 'q': 'Do‘stingning ideal kechasi?', 'type': 'mcq', 'opts': ['🍿 Film', '🌃 Sayr', '🎮 O‘yin', '👥 Suhbat']}, {'id': 'f16', 'q': 'Do‘stingga bir kun bo‘sh vaqt berilsa...', 'type': 'mcq', 'opts': ['😴 Dam', '🚗 Sayohat', '🎮 O‘yin', '🎬 Kino']}, {'id': 'f17', 'q': 'Do‘sting qaysi sovg‘ani ko‘proq qadrlaydi?', 'type': 'mcq', 'opts': ['💌 Xat', '💰 Qimmat narsa', '🍫 Shirinlik', '📸 Foto']}, {'id': 'f18', 'q': 'Do‘sting restoran tanlaganda nimaga qaraydi?', 'type': 'mcq', 'opts': ['🍽 Taom', '💰 Narx', '✨ Muhit', '⭐ Sharhlar']}, {'id': 'f19', 'q': 'Do‘stingga qaysi hayvon yoqishi ehtimoli yuqori?', 'type': 'mcq', 'opts': ['🐱 Mushuk', '🐶 It', '🐼 Panda', '🦊 Tulki']}, {'id': 'f20', 'q': 'Do‘stingning sevimli fasli qaysi bo‘lishi mumkin?', 'type': 'mcq', 'opts': ['🌸 Bahor', '☀️ Yoz', '🍂 Kuz', '❄️ Qish']}, {'id': 'f21', 'q': 'Do‘sting sayohatda qaysi transportni tanlaydi?', 'type': 'mcq', 'opts': ['🚗 Mashina', '✈️ Samolyot', '🚆 Poyezd', '🚲 Velosiped']}, {'id': 'f22', 'q': 'Do‘sting qaysi joyni tanlaydi?', 'type': 'mcq', 'opts': ['🌊 Dengiz', '🏙 Shahar', '🏔 Tog‘', '🏡 Qishloq']}, {'id': 'f23', 'q': 'Do‘sting vaqtida kelish masalasida qanday?', 'type': 'mcq', 'opts': ['⏰ Juda punktual', '🙂 Odatda vaqtida', '🏃 Shoshilib keladi', '😅 Kechikadi']}, {'id': 'f24', 'q': 'Do‘sting kayfiyati tushsa, nima qiladi?', 'type': 'mcq', 'opts': ['🎵 Musiqa', '😴 Uxlaydi', '👥 Gaplashadi', '🎮 Chalg‘iydi']}]}, 'months': ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr']}
async def db():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5, command_timeout=20)
    return pool

async def init_db():
    p = await db()
    async with p.acquire() as c:
        await c.execute("""
        CREATE TABLE IF NOT EXISTS zako_users(
            telegram_id BIGINT PRIMARY KEY, username TEXT, first_name TEXT,
            joined_at TIMESTAMPTZ NOT NULL DEFAULT now(), last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
            xp BIGINT NOT NULL DEFAULT 0, coins BIGINT NOT NULL DEFAULT 0, streak INTEGER NOT NULL DEFAULT 0, streak_day DATE
        );
        ALTER TABLE zako_users ADD COLUMN IF NOT EXISTS xp BIGINT NOT NULL DEFAULT 0;
        ALTER TABLE zako_users ADD COLUMN IF NOT EXISTS coins BIGINT NOT NULL DEFAULT 0;
        ALTER TABLE zako_users ADD COLUMN IF NOT EXISTS streak INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE zako_users ADD COLUMN IF NOT EXISTS streak_day DATE;
        ALTER TABLE zako_users ADD COLUMN IF NOT EXISTS referred_by BIGINT;
        ALTER TABLE zako_users ADD COLUMN IF NOT EXISTS referral_rewarded BOOLEAN NOT NULL DEFAULT false;
        ALTER TABLE zako_users ADD COLUMN IF NOT EXISTS premium_until TIMESTAMPTZ;
        ALTER TABLE zako_users ADD COLUMN IF NOT EXISTS streak_premium_claimed BOOLEAN NOT NULL DEFAULT false;
        ALTER TABLE zako_users ADD COLUMN IF NOT EXISTS frame_id BIGINT;
        CREATE TABLE IF NOT EXISTS zako_scores(
            id BIGSERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL REFERENCES zako_users(telegram_id) ON DELETE CASCADE,
            category TEXT NOT NULL, pct SMALLINT NOT NULL CHECK (pct BETWEEN 0 AND 100), attempt_id TEXT NOT NULL UNIQUE, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE IF NOT EXISTS zako_daily_scores(
            id BIGSERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL REFERENCES zako_users(telegram_id) ON DELETE CASCADE, category TEXT NOT NULL,
            pct SMALLINT NOT NULL CHECK (pct BETWEEN 0 AND 100), attempt_id TEXT NOT NULL UNIQUE, score_day DATE NOT NULL DEFAULT CURRENT_DATE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(telegram_id,category,score_day)
        );
        CREATE TABLE IF NOT EXISTS zako_settings(k TEXT PRIMARY KEY,v TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS zako_challenges(
            token TEXT PRIMARY KEY, creator_id BIGINT NOT NULL REFERENCES zako_users(telegram_id) ON DELETE CASCADE, kind TEXT NOT NULL CHECK(kind IN ('love','friend')),
            q_ids JSONB NOT NULL, answers JSONB NOT NULL, used BOOLEAN NOT NULL DEFAULT false, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE IF NOT EXISTS zako_social_results(
            id BIGSERIAL PRIMARY KEY, challenge_token TEXT NOT NULL, creator_id BIGINT NOT NULL, challenger_id BIGINT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('love','friend')), pct SMALLINT NOT NULL CHECK(pct BETWEEN 0 AND 100), created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS zako_social_results_creator_idx ON zako_social_results(creator_id,created_at DESC);
        CREATE TABLE IF NOT EXISTS zako_shop_items(
            id BIGSERIAL PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
            coins_price BIGINT NOT NULL DEFAULT 0, xp_price BIGINT NOT NULL DEFAULT 0, stars_price INTEGER NOT NULL DEFAULT 0, active BOOLEAN NOT NULL DEFAULT true, sort_order INTEGER NOT NULL DEFAULT 0
        );
        ALTER TABLE zako_shop_items ADD COLUMN IF NOT EXISTS xp_price BIGINT NOT NULL DEFAULT 0;
        ALTER TABLE zako_shop_items DROP CONSTRAINT IF EXISTS zako_shop_items_kind_check;
        ALTER TABLE zako_shop_items ADD CONSTRAINT zako_shop_items_kind_check CHECK(kind IN ('gift','coin_pack','frame'));
        CREATE TABLE IF NOT EXISTS zako_redemptions(
            id BIGSERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL, item_id BIGINT NOT NULL, item_title TEXT NOT NULL, coins_spent BIGINT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE IF NOT EXISTS zako_payments(
            id BIGSERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL, payload TEXT UNIQUE NOT NULL, coins BIGINT NOT NULL, stars INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', created_at TIMESTAMPTZ NOT NULL DEFAULT now(), paid_at TIMESTAMPTZ
        );
        CREATE TABLE IF NOT EXISTS zako_rank_prizes(
            period TEXT NOT NULL CHECK(period IN ('week','month')), place INTEGER NOT NULL CHECK(place BETWEEN 1 AND 10), prize TEXT NOT NULL DEFAULT '', PRIMARY KEY(period,place)
        );
        CREATE TABLE IF NOT EXISTS zako_tasks(
            id BIGSERIAL PRIMARY KEY, kind TEXT NOT NULL CHECK(kind='channel'), title TEXT NOT NULL, chat_id TEXT NOT NULL, url TEXT NOT NULL DEFAULT '',
            reward_xp BIGINT NOT NULL DEFAULT 0, reward_coins BIGINT NOT NULL DEFAULT 0, active BOOLEAN NOT NULL DEFAULT true, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE IF NOT EXISTS zako_task_claims(
            task_id BIGINT NOT NULL REFERENCES zako_tasks(id) ON DELETE CASCADE, telegram_id BIGINT NOT NULL REFERENCES zako_users(telegram_id) ON DELETE CASCADE,
            claimed_at TIMESTAMPTZ NOT NULL DEFAULT now(), PRIMARY KEY(task_id,telegram_id)
        );
        CREATE INDEX IF NOT EXISTS zako_scores_user_idx ON zako_scores(telegram_id);
        CREATE INDEX IF NOT EXISTS zako_daily_scores_day_idx ON zako_daily_scores(score_day);
        CREATE INDEX IF NOT EXISTS zako_challenges_created_idx ON zako_challenges(created_at);
        INSERT INTO zako_daily_scores(telegram_id,category,pct,attempt_id,score_day,created_at)
        SELECT s.telegram_id,s.category,s.pct,s.attempt_id,(s.created_at AT TIME ZONE 'Asia/Tashkent')::date,s.created_at
        FROM zako_scores s WHERE NOT EXISTS(SELECT 1 FROM zako_daily_scores d WHERE d.attempt_id=s.attempt_id) ON CONFLICT DO NOTHING;
        """)
        await c.execute("INSERT INTO zako_rank_prizes(period,place,prize) SELECT 'week',g,CASE WHEN g=1 THEN '100 000 so‘m' WHEN g=2 THEN '70 000 so‘m' WHEN g=3 THEN '50 000 so‘m' ELSE '—' END FROM generate_series(1,10) g ON CONFLICT DO NOTHING")
        await c.execute("INSERT INTO zako_shop_items(kind,title,description,coins_price,stars_price,sort_order) SELECT 'coin_pack','100 Coin','Telegram Stars orqali 100 Coin',100,10,1 WHERE NOT EXISTS(SELECT 1 FROM zako_shop_items WHERE kind='coin_pack')")
        await c.execute("INSERT INTO zako_shop_items(kind,title,description,coins_price,xp_price,stars_price,sort_order) SELECT 'frame','⚡ Energy Frame','Profil uchun 5000 XP ramka',0,5000,0,2 WHERE NOT EXISTS(SELECT 1 FROM zako_shop_items WHERE kind='frame')")
    return p

async def save_user(u):
    p=await db()
    async with p.acquire() as c:
        await c.execute("""
        INSERT INTO zako_users(telegram_id,username,first_name,last_seen)
        VALUES($1,$2,$3,now())
        ON CONFLICT(telegram_id) DO UPDATE SET
          username=EXCLUDED.username, first_name=EXCLUDED.first_name, last_seen=now()
        """, int(u["id"]), u.get("username"), u.get("first_name"))

async def register_referral(new_uid, referred_by):
    try:
        new_uid=int(new_uid); referred_by=int(referred_by)
    except Exception:
        return False
    if new_uid==referred_by:
        return False
    p=await db()
    async with p.acquire() as c:
        async with c.transaction():
            row=await c.fetchrow("SELECT referred_by FROM zako_users WHERE telegram_id=$1 FOR UPDATE",new_uid)
            if not row or row["referred_by"] is not None:
                return False
            ref=await c.fetchrow("SELECT telegram_id FROM zako_users WHERE telegram_id=$1",referred_by)
            if not ref:
                return False
            await c.execute("UPDATE zako_users SET referred_by=$2 WHERE telegram_id=$1",new_uid,referred_by)
            return True

async def get_setting(k, default=""):
    p=await db()
    async with p.acquire() as c:
        v=await c.fetchval("SELECT v FROM zako_settings WHERE k=$1",k)
        return default if v is None else v

async def set_setting(k,v):
    p=await db()
    async with p.acquire() as c:
        await c.execute("""
        INSERT INTO zako_settings(k,v) VALUES($1,$2)
        ON CONFLICT(k) DO UPDATE SET v=EXCLUDED.v
        """,k,v)

async def tg(method,payload):
    data=json.dumps(payload,ensure_ascii=False).encode()
    req=Request(f"https://api.telegram.org/bot{BOT_TOKEN}/{method}",data=data,headers={"Content-Type":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"[TG ERROR] {method}: {type(e).__name__}: {e}",flush=True)
        return {"ok":False,"description":str(e)}

async def is_subscribed(uid):
    ch=await get_setting("channel","")
    if not ch: return True
    r=await tg("getChatMember",{"chat_id":ch,"user_id":int(uid)})
    if not r.get("ok"):
        print(f"[SUB CHECK ERROR] channel={ch} uid={uid} response={r}",flush=True)
        return False
    x=r.get("result",{})
    st=x.get("status")
    return st in ("creator","administrator","member") or (st=="restricted" and bool(x.get("is_member")))

async def channel_url():
    return await get_setting("channel_url","")

def normalize_channel(value):
    value=(value or "").strip()
    if value.startswith("https://t.me/"):
        tail=value.split("https://t.me/",1)[1].split("?",1)[0].strip("/")
        if tail and not tail.startswith("+") and "/" not in tail:
            return "@"+tail.lstrip("@"), "https://t.me/"+tail.lstrip("@")
        return value, value
    if value.startswith("https://telegram.me/"):
        tail=value.split("https://telegram.me/",1)[1].split("?",1)[0].strip("/")
        if tail and not tail.startswith("+") and "/" not in tail:
            return "@"+tail.lstrip("@"), "https://t.me/"+tail.lstrip("@")
        return value, value
    if value.startswith("@"):
        return value, "https://t.me/"+value[1:]
    if value.startswith("-100") and value[4:].isdigit():
        return value, ""
    if value.isdigit():
        return value, ""
    return "", ""

async def verify_channel(channel):
    chat=await tg("getChat",{"chat_id":channel})
    if not chat.get("ok"):
        return False, "Kanal topilmadi. @username yoki -100... ID ni tekshiring."
    bot=await tg("getMe",{})
    if not bot.get("ok"):
        return False, "Bot ma’lumotini tekshirib bo‘lmadi."
    member=await tg("getChatMember",{"chat_id":channel,"user_id":int(bot["result"]["id"])})
    if not member.get("ok"):
        return False, "Bot kanalni ko‘ra olmayapti. Botni kanalga administrator qilib qo‘ying."
    status=(member.get("result") or {}).get("status")
    if status not in ("creator","administrator"):
        return False, "Bot kanalga administrator bo‘lishi kerak. Avval botni kanalga admin qiling."
    return True, chat.get("result",{}).get("title") or "Kanal"

async def make_sub_keyboard(challenge=None):
    rows=[]
    url=await channel_url()
    if url:
        rows.append([{"text":"📢 Kanalga obuna bo‘lish","url":url}])
    cb="subcheck"+(":"+challenge if challenge else "")
    rows.append([{"text":"✅ Obunani tekshirish","callback_data":cb}])
    return {"inline_keyboard":rows}

def open_keyboard(challenge=None):
    u=PUBLIC_URL+"/"
    if challenge:
        u += "?challenge="+quote(challenge,safe="")
    return {"inline_keyboard":[[{"text":"🚀 ZAKO'NI OCHISH","web_app":{"url":u}}]]}

async def send_welcome_content(uid,text,markup):
    if WELCOME.exists():
        r=await tg("sendPhoto",{"chat_id":int(uid),"photo":PUBLIC_URL+"/welcome.png","caption":text,"parse_mode":"HTML","reply_markup":markup})
        if r.get("ok"): return r
        print(f"[WELCOME PHOTO FALLBACK] {r}",flush=True)
    return await tg("sendMessage",{"chat_id":int(uid),"text":text,"parse_mode":"HTML","reply_markup":markup})

async def welcome_message(uid,challenge=None):
    if uid in ADMIN_IDS and not challenge:
        markup={"inline_keyboard":[
            [{"text":"🚀 ZAKO'NI OCHISH","web_app":{"url":PUBLIC_URL+"/"}}],
            [{"text":"⚙️ ADMIN PANEL","callback_data":"admin"}]
        ]}
        text="🧠 <b>ZAKO</b>\n\nO‘zingni sinab ko‘r. Qanchalik ZAKOsan?"
        return await send_welcome_content(uid,text,markup)
    ok=await is_subscribed(uid)
    if not ok:
        text=("❤️ <b>Meni qanchalik bilasan?</b>\n\nTestni boshlash uchun avval kanalga obuna bo‘l.") if challenge else ("🧠 <b>ZAKO</b>\n\nO‘zingni sinab ko‘r. Qanchalik ZAKOsan?")
        return await send_welcome_content(uid,text,await make_sub_keyboard(challenge))
    text=("❤️ <b>Meni qanchalik bilasan?</b>\n\nTest tayyor. Pastdagi tugma orqali ZAKO'ni oching.") if challenge else ("🧠 <b>ZAKO</b>\n\nO‘zingni sinab ko‘r. Qanchalik ZAKOsan?")
    markup=open_keyboard(challenge)
    return await send_welcome_content(uid,text,markup)

def validate_init(data):
    if not data: raise HTTPException(401,"Telegram sessiyasi yo‘q.")
    try:
        pairs=dict(parse_qsl(data,keep_blank_values=True))
        received=pairs.pop("hash")
        auth_date=int(pairs["auth_date"])
        if int(time.time())-auth_date>3600: raise ValueError("expired")
        check="\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
        secret=hmac.new(b"WebAppData",BOT_TOKEN.encode(),hashlib.sha256).digest()
        calc=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc,received): raise ValueError("hash")
        user=json.loads(pairs["user"])
        if not user.get("id"): raise ValueError("user")
        return user
    except Exception:
        raise HTTPException(401,"Telegram sessiyasi yaroqsiz yoki eskirgan.")

async def send_admin(uid):
    kb={"inline_keyboard":[
        [{"text":"📊 Statistika","callback_data":"ad:stats"}],
        [{"text":"📢 Majburiy obuna","callback_data":"ad:channel"}],
        [{"text":"🗑 Obunani o‘chirish","callback_data":"ad:delch"}],
        [{"text":"👤 Userga xabar","callback_data":"ad:user"}],
        [{"text":"📣 Hammaga xabar","callback_data":"ad:all"}],
        [{"text":"🏆 Top reyting","callback_data":"ad:top"}],
        [{"text":"🎁 Haftalik sovrinlar","callback_data":"ad:prizesw"}],
        [{"text":"🎁 Oylik sovrinlar","callback_data":"ad:prizesm"}],
        [{"text":"🛍 Coin Shop","callback_data":"ad:shop"}],
        [{"text":"🎯 Topshiriqlar","callback_data":"ad:tasks"}],
        [{"text":"🧹 Eski challenge'larni tozalash","callback_data":"ad:cleanup"}]
    ]}
    await tg("sendMessage",{"chat_id":uid,"text":"⚙️ <b>ZAKO ADMIN</b>\n\nBoshqaruv bo‘limini tanlang.","parse_mode":"HTML","reply_markup":kb})

async def admin_callback(uid,mode):
    if mode=="stats":
        p=await db()
        async with p.acquire() as c:
            vals=[
                await c.fetchval("SELECT count(*) FROM zako_users"),
                await c.fetchval("SELECT count(*) FROM zako_users WHERE joined_at>=now()-interval '1 day'"),
                await c.fetchval("SELECT count(*) FROM zako_users WHERE joined_at>=now()-interval '7 days'"),
                await c.fetchval("SELECT count(*) FROM zako_users WHERE last_seen>=now()-interval '1 day'"),
                await c.fetchval("SELECT count(*) FROM zako_scores"),
                await c.fetchval("SELECT count(*) FROM zako_challenges")]
        return await tg("sendMessage",{"chat_id":uid,"text":f"📊 <b>Statistika</b>\n\n👤 Jami: <b>{vals[0]}</b>\n🆕 24 soat: <b>{vals[1]}</b>\n📅 7 kun: <b>{vals[2]}</b>\n🟢 Faol 24 soat: <b>{vals[3]}</b>\n🧠 Testlar: <b>{vals[4]}</b>\n❤️/🤝 Challenge: <b>{vals[5]}</b>","parse_mode":"HTML"})

    if mode=="shop_add":
        parts=[x.strip() for x in text.split("|",4)]
        if len(parts)==4:
            title,desc,coins_s,stars_s=parts;xp_s="0"
        elif len(parts)==5:
            title,desc,xp_s,coins_s,stars_s=parts
        else:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Format: Nomi|Tavsif|XP|Coin|Stars"})
        try: xp=int(xp_s); coins=int(coins_s); stars=int(stars_s)
        except:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ XP, Coin va Stars raqam bo‘lsin."})
        kind=st["kind"]
        if kind=="gift" and coins<=0:return await tg("sendMessage",{"chat_id":uid,"text":"❌ Gift Coin narxi 0 dan katta bo‘lsin."})
        if kind=="coin_pack" and (coins<=0 or stars<=0):return await tg("sendMessage",{"chat_id":uid,"text":"❌ Coin va Stars 0 dan katta bo‘lsin."})
        if kind=="frame" and xp<=0 and coins<=0:return await tg("sendMessage",{"chat_id":uid,"text":"❌ Ramka uchun XP yoki Coin narxi bo‘lsin."})
        p=await db()
        async with p.acquire() as c:
            await c.execute("INSERT INTO zako_shop_items(kind,title,description,xp_price,coins_price,stars_price) VALUES($1,$2,$3,$4,$5,$6)",kind,title,desc,xp,coins,stars)
        return await tg("sendMessage",{"chat_id":uid,"text":"✅ Shop elementi qo‘shildi."})
    if mode=="shop_edit":
        parts=[x.strip() for x in text.split("|",5)]
        if len(parts)!=6:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Format: Nomi|Tavsif|XP|Coin|Stars|ON/OFF"})
        try:xp=int(parts[2]);coins=int(parts[3]);stars=int(parts[4])
        except:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ XP, Coin va Stars raqam bo‘lsin."})
        active=parts[5].upper() in {"ON","1","TRUE","HA"};p=await db()
        async with p.acquire() as c:
            res=await c.execute("UPDATE zako_shop_items SET title=$2,description=$3,xp_price=$4,coins_price=$5,stars_price=$6,active=$7 WHERE id=$1",st["item_id"],parts[0],parts[1],xp,coins,stars,active)
        return await tg("sendMessage",{"chat_id":uid,"text":"✅ O‘zgartirildi." if res=="UPDATE 1" else "❌ ID topilmadi."})
    if mode=="channel":
        admin_state[uid]={"mode":"channel"}
        current=await get_setting("channel","")
        extra=f"\n\nHozirgi kanal: <code>{htmlmod.escape(current)}</code>" if current else ""
        return await tg("sendMessage",{"chat_id":uid,"text":"📢 <b>Majburiy obuna kanalini ulash</b>"+extra+"\n\nBitta xabarda kanal <b>@username</b> yoki <b>-100...</b> ID'sini yuboring.\n\nPublic kanal bo‘lsa havolani alohida so‘ramayman — avtomatik olaman.\nPrivate kanal bo‘lsa ID bilan birga keyingi xabarda invite link so‘raladi.","parse_mode":"HTML"})
    if mode=="delch":
        await set_setting("channel","");await set_setting("channel_url","")
        return await tg("sendMessage",{"chat_id":uid,"text":"🗑 Majburiy obuna o‘chirildi."})
    if mode=="user":
        admin_state[uid]={"mode":"user_id"}
        return await tg("sendMessage",{"chat_id":uid,"text":"👤 Userning Telegram ID'sini yuboring."})
    if mode=="all":
        admin_state[uid]={"mode":"broadcast_prepare"}
        return await tg("sendMessage",{"chat_id":uid,"text":"📣 Hammaga yuboriladigan xabarni yuboring. Avval tasdiqlataman."})
    if mode=="top":
        p=await db()
        async with p.acquire() as c:
            rows=await c.fetch("""SELECT u.first_name,u.username,COALESCE(SUM(s.pct),0)::int score
                FROM zako_users u LEFT JOIN zako_daily_scores s ON s.telegram_id=u.telegram_id
                GROUP BY u.telegram_id ORDER BY score DESC,u.telegram_id LIMIT 10""")
        lines=["🏆 <b>TOP 10</b>",""]
        for i,r in enumerate(rows,1): lines.append(f"{i}. {htmlmod.escape(r['first_name'] or r['username'] or 'ZAKO')} — <b>{r['score']}</b>")
        return await tg("sendMessage",{"chat_id":uid,"text":"\n".join(lines),"parse_mode":"HTML"})
    if mode in {"prizesw","prizesm"}:
        period="week" if mode=="prizesw" else "month"
        title="Haftalik" if period=="week" else "Oylik"
        p=await db()
        async with p.acquire() as c:rows=await c.fetch("SELECT place,prize FROM zako_rank_prizes WHERE period=$1 ORDER BY place",period)
        by={int(x["place"]):x["prize"] for x in rows}
        kb={"inline_keyboard":[
            [{"text":f"#{i} — {by.get(i) or '—'}","callback_data":f"ad:prizeedit:{period}:{i}"},
             {"text":"✏️","callback_data":f"ad:prizeedit:{period}:{i}"},
             {"text":"🗑","callback_data":f"ad:prizedel:{period}:{i}"}] for i in range(1,11)
        ]+[[{"text":"➕ Bo‘sh o‘rinni qo‘shish","callback_data":f"ad:prizeadd:{period}"}],
           [{"text":"🗑 Barchasini o‘chirish","callback_data":f"ad:prizeclear:{period}"}],
           [{"text":"⬅️ Admin panel","callback_data":"admin"}]]}
        return await tg("sendMessage",{"chat_id":uid,"text":f"🎁 <b>{title} sovrinlari</b>\n\nHar bir o‘rinni alohida tahrirlash yoki o‘chirish mumkin.","parse_mode":"HTML","reply_markup":kb})
    if mode.startswith("prizeedit:"):
        _,period,place_s=mode.split(":",2);place=int(place_s);title="Haftalik" if period=="week" else "Oylik"
        admin_state[uid]={"mode":"prize_edit","period":period,"place":place}
        p=await db()
        async with p.acquire() as c:old=await c.fetchval("SELECT prize FROM zako_rank_prizes WHERE period=$1 AND place=$2",period,place)
        return await tg("sendMessage",{"chat_id":uid,"text":f"🎁 <b>{title} #{place}</b>\n\nHozirgi: <b>{htmlmod.escape(old or '—')}</b>\n\nYangi sovrin nomini yuboring.\n🗑 O‘chirish: <code>/delete</code>","parse_mode":"HTML"})
    if mode.startswith("prizedel:"):
        _,period,place_s=mode.split(":",2);place=int(place_s);p=await db()
        async with p.acquire() as c:res=await c.execute("DELETE FROM zako_rank_prizes WHERE period=$1 AND place=$2",period,place)
        return await tg("sendMessage",{"chat_id":uid,"text":f"🗑 #{place} sovrin o‘chirildi." if res=="DELETE 1" else f"ℹ️ #{place} sovrin bo‘sh edi."})

    if mode.startswith("prizeadd:"):
        period=mode.split(":",1)[1];title="Haftalik" if period=="week" else "Oylik"
        p=await db()
        async with p.acquire() as c:rows=await c.fetch("SELECT place FROM zako_rank_prizes WHERE period=$1 AND prize<>''",period)
        used={int(x["place"]) for x in rows};place=next((i for i in range(1,11) if i not in used),None)
        if place is None:return await tg("sendMessage",{"chat_id":uid,"text":f"ℹ️ {title} TOP 10 allaqachon to‘liq."})
        admin_state[uid]={"mode":"prize_edit","period":period,"place":place}
        return await tg("sendMessage",{"chat_id":uid,"text":f"🎁 {title} #{place} uchun sovrin nomini yuboring."})
    if mode.startswith("prizeclear:"):
        period=mode.split(":",1)[1];p=await db()
        async with p.acquire() as c:await c.execute("DELETE FROM zako_rank_prizes WHERE period=$1",period)
        return await tg("sendMessage",{"chat_id":uid,"text":f"🗑 {'Haftalik' if period=='week' else 'Oylik'} sovrinlarning barchasi o‘chirildi."})
    if mode=="grantcoins":
        admin_state[uid]={"mode":"grant_coins_user"}
        return await tg("sendMessage",{"chat_id":uid,"text":"🪙 <b>Coin to‘ldirish</b>\n\nUserning <b>@username</b>ini yuboring.\nMasalan: <code>@azizbek</code>","parse_mode":"HTML"})
    if mode=="grantxp":
        admin_state[uid]={"mode":"grant_xp_user"}
        return await tg("sendMessage",{"chat_id":uid,"text":"⭐ <b>XP to‘ldirish</b>\n\nUserning <b>@username</b>ini yuboring.\nMasalan: <code>@azizbek</code>","parse_mode":"HTML"})
    if mode=="shop":
        p=await db()
        async with p.acquire() as c:rows=await c.fetch("SELECT id,kind,title,coins_price,xp_price,stars_price,active FROM zako_shop_items ORDER BY id")
        lines=["🛍 <b>Coin Shop boshqaruvi</b>",""]
        for x in rows:lines.append(f"#{x['id']} {'🎁' if x['kind']=='gift' else '🪙' if x['kind']=='coin_pack' else '🖼️'} {htmlmod.escape(x['title'])} — XP:{int(x['xp_price'])} / Coin:{int(x['coins_price'])} / ⭐:{int(x['stars_price'])} — {'ON' if x['active'] else 'OFF'}")
        lines += ["", "➕ Yangi sovg‘a: /addgift", "➕ Coin paketi: /addcoin", "🖼️ Yangi ramka: /addframe", "✏️ Tahrirlash: /editshop ID", "🗑 O‘chirish: /delshop ID"]
        kb={"inline_keyboard":[
            [{"text":"🪙 Coin to‘ldirish","callback_data":"ad:grantcoins"},{"text":"⭐ XP to‘ldirish","callback_data":"ad:grantxp"}],
            [{"text":"🔄 Yangilash","callback_data":"ad:shop"}],
            [{"text":"⬅️ Admin panel","callback_data":"admin"}]
        ]}
        return await tg("sendMessage",{"chat_id":uid,"text":"\n".join(lines),"parse_mode":"HTML","reply_markup":kb})
    if mode=="tasks":
        p=await db()
        async with p.acquire() as c:
            rows=await c.fetch("SELECT id,title,reward_xp,reward_coins,active FROM zako_tasks ORDER BY id")
        lines=["🎯 <b>Topshiriqlar boshqaruvi</b>",""]
        for x in rows:
            lines.append(f"#{int(x['id'])} — {htmlmod.escape(x['title'])} — ⭐{int(x['reward_xp'])} 🪙{int(x['reward_coins'])} — {'ON' if x['active'] else 'OFF'}")
        kb=[[{"text":"➕ Kanal topshirig‘i qo‘shish","callback_data":"ad:taskadd"}],
            [{"text":"📋 Yangilash","callback_data":"ad:tasks"}],
            [{"text":"⬅️ Admin panel","callback_data":"admin"}]]
        for x in rows:
            kb.insert(-1,[{"text":f"✏️ #{int(x['id'])}","callback_data":f"ad:taskedit:{int(x['id'])}"},
                          {"text":f"🗑 #{int(x['id'])}","callback_data":f"ad:taskdel:{int(x['id'])}"}])
        text="\n".join(lines) if rows else "🎯 <b>Topshiriqlar</b>\n\nHali topshiriq yo‘q."
        return await tg("sendMessage",{"chat_id":uid,"text":text,"parse_mode":"HTML","reply_markup":{"inline_keyboard":kb}})
    if mode=="taskadd":
        admin_state[uid]={"mode":"task_add"}
        return await tg("sendMessage",{"chat_id":uid,"text":"📢 Kanal topshirig‘i uchun yuboring:\n\n<code>Nomi|@kanal|XP|Coin</code>\n\nMasalan:\n<code>KINO BOT kanaliga qo‘shiling|@kino_bot|0|5</code>\n\nBot kanalga administrator bo‘lishi shart.","parse_mode":"HTML"})
    if mode.startswith("taskedit:"):
        tid=int(mode.split(":",1)[1]);p=await db()
        async with p.acquire() as c: row=await c.fetchrow("SELECT * FROM zako_tasks WHERE id=$1",tid)
        if not row:return await tg("sendMessage",{"chat_id":uid,"text":"❌ Topshiriq topilmadi."})
        admin_state[uid]={"mode":"task_edit","task_id":tid}
        return await tg("sendMessage",{"chat_id":uid,"text":f"✏️ <b>#{tid}</b>\n\nHozirgi: {htmlmod.escape(row['title'])}\nKanal: <code>{htmlmod.escape(row['chat_id'])}</code>\nMukofot: ⭐{int(row['reward_xp'])} 🪙{int(row['reward_coins'])}\n\nYangi format:\n<code>Nomi|@kanal|XP|Coin</code>","parse_mode":"HTML"})
    if mode.startswith("taskdel:"):
        tid=int(mode.split(":",1)[1]);p=await db()
        async with p.acquire() as c:res=await c.execute("DELETE FROM zako_tasks WHERE id=$1",tid)
        return await tg("sendMessage",{"chat_id":uid,"text":"🗑 Topshiriq o‘chirildi." if res=="DELETE 1" else "❌ Topshiriq topilmadi."})

    if mode=="cleanup":
        p=await db()
        async with p.acquire() as c:
            res=await c.execute("DELETE FROM zako_challenges WHERE created_at < now()-interval '7 days'")
        return await tg("sendMessage",{"chat_id":uid,"text":f"🧹 Eski challenge'lar tozalandi: {res}."})

async def admin_flow(m):
    uid=int(m["from"]["id"]);st=admin_state.pop(uid,None)
    text=(m.get("text") or "").strip()
    if uid in ADMIN_IDS and text in {"/addgift","/addcoin","/addframe"}:
        admin_state[uid]={"mode":"shop_add","kind":"gift" if text=="/addgift" else "coin_pack" if text=="/addcoin" else "frame"}
        return await tg("sendMessage",{"chat_id":uid,"text":"Yuboring: <code>Nomi|Tavsif|XP|Coin|Stars</code>\n\nGift uchun XP=0, Stars=0.\nRamka uchun XP yoki Coin narxidan birini qo‘yish mumkin.","parse_mode":"HTML"})
    if uid in ADMIN_IDS and text == "/editshop":
        return await tg("sendMessage",{"chat_id":uid,"text":"✏️ Format: /editshop ID"})
    if uid in ADMIN_IDS and text.startswith("/editshop "):
        try:item_id=int(text.split()[1])
        except:return await tg("sendMessage",{"chat_id":uid,"text":"❌ ID noto‘g‘ri."})
        admin_state[uid]={"mode":"shop_edit","item_id":item_id}
        return await tg("sendMessage",{"chat_id":uid,"text":"Yangi qiymat: <code>Nomi|Tavsif|XP|Coin|Stars|ON/OFF</code>","parse_mode":"HTML"})
    if uid in ADMIN_IDS and text == "/delshop":
        return await tg("sendMessage",{"chat_id":uid,"text":"🗑 Format: /delshop ID"})
    if uid in ADMIN_IDS and text.startswith("/delshop "):
        try:item_id=int(text.split()[1])
        except:return await tg("sendMessage",{"chat_id":uid,"text":"❌ ID noto‘g‘ri."})
        p=await db()
        async with p.acquire() as c:res=await c.execute("DELETE FROM zako_shop_items WHERE id=$1",item_id)
        return await tg("sendMessage",{"chat_id":uid,"text":"🗑 O‘chirildi." if res=="DELETE 1" else "❌ Bunday ID topilmadi."})
    if not st:return
    mode=st.get("mode")
    if mode in {"grant_coins_user","grant_xp_user"}:
        username=text.strip()
        if username.startswith("@"):
            username=username[1:]
        username=username.strip()
        if not username or not re.fullmatch(r"[A-Za-z0-9_]{3,32}",username):
            admin_state[uid]={"mode":mode}
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Username noto‘g‘ri. Masalan: <code>@azizbek</code>","parse_mode":"HTML"})
        p=await db()
        async with p.acquire() as c:
            row=await c.fetchrow("SELECT telegram_id,username,first_name FROM zako_users WHERE lower(username)=lower($1) LIMIT 1",username)
        if not row:
            admin_state[uid]={"mode":mode}
            return await tg("sendMessage",{"chat_id":uid,"text":f"❌ <b>@{htmlmod.escape(username)}</b> ZAKO foydalanuvchilari orasidan topilmadi.\n\nUser botni avval ishga tushirgan va username'i ZAKO bazasida saqlangan bo‘lishi kerak.","parse_mode":"HTML"})
        admin_state[uid]={"mode":"grant_coins_amount" if mode=="grant_coins_user" else "grant_xp_amount","target":int(row["telegram_id"]),"username":row["username"] or username}
        label="Coin" if mode=="grant_coins_user" else "XP"
        return await tg("sendMessage",{"chat_id":uid,"text":f"👤 <b>@{htmlmod.escape(row['username'] or username)}</b>\n\n{('🪙' if label=='Coin' else '⭐')} Qancha {label} qo‘shilsin?\nMasalan: <code>100</code>","parse_mode":"HTML"})

    if mode in {"grant_coins_amount","grant_xp_amount"}:
        try:amount=int(text)
        except:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Faqat musbat butun son yuboring."})
        if amount<=0 or amount>10_000_000:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Miqdor 1 dan 10 000 000 gacha bo‘lishi kerak."})
        field="coins" if mode=="grant_coins_amount" else "xp"
        icon="🪙" if field=="coins" else "⭐"
        p=await db()
        async with p.acquire() as c:
            res=await c.execute(f"UPDATE zako_users SET {field}={field}+$2 WHERE telegram_id=$1",st["target"],amount)
            row=await c.fetchrow("SELECT xp,coins FROM zako_users WHERE telegram_id=$1",st["target"])
        if res!="UPDATE 1":
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ User topilmadi yoki hisob yangilanmadi."})
        return await tg("sendMessage",{"chat_id":uid,"text":f"✅ <b>@{htmlmod.escape(st['username'])}</b> hisobiga {icon} <b>+{amount:,}</b> qo‘shildi.\n\n⭐ XP: {int(row['xp']):,}\n🪙 Coin: {int(row['coins']):,}","parse_mode":"HTML"})

    if mode in {"task_add","task_edit"}:
        parts=[x.strip() for x in text.split("|")]
        # Qulay formatlar:
        # 1) Nomi | @kanal | Coin   -> XP=0
        # 2) Nomi | @kanal | XP | Coin
        if len(parts)==3:
            title,channel,coins=parts
            xps="0"
        elif len(parts)==4:
            title,channel,xps,coins=parts
        else:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Format: Nomi | @kanal | Coin  yoki  Nomi | @kanal | XP | Coin"})
        if not title or not channel or not channel.startswith("@"):
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Nom va @kanal to‘g‘ri kiritilsin."})
        try:
            rx=int(xps); rc=int(coins)
            if rx < 0 or rc < 0:
                raise ValueError
        except:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ XP va Coin 0 yoki undan katta raqam bo‘lishi kerak."})
        if not title or rx<0 or rc<0:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Ma’lumotlar noto‘g‘ri."})
        ch,url=normalize_channel(channel)
        if not ch:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ @username yoki -100... kanal ID yuboring."})
        ok,info=await verify_channel(ch)
        if not ok:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ "+info})
        p=await db()
        async with p.acquire() as c:
            if mode=="task_add":
                await c.execute("INSERT INTO zako_tasks(kind,title,chat_id,url,reward_xp,reward_coins) VALUES('channel',$1,$2,$3,$4,$5)",title,ch,url,rx,rc)
                msg="✅ Kanal topshirig‘i qo‘shildi."
            else:
                res=await c.execute("UPDATE zako_tasks SET title=$2,chat_id=$3,url=$4,reward_xp=$5,reward_coins=$6 WHERE id=$1",int(st["task_id"]),title,ch,url,rx,rc)
                msg="✅ Topshiriq tahrirlandi." if res=="UPDATE 1" else "❌ Topshiriq topilmadi."
        return await tg("sendMessage",{"chat_id":uid,"text":msg})

    if mode=="prize_edit":
        period=st["period"];place=int(st["place"])
        if text.lower()=="/delete":
            p=await db()
            async with p.acquire() as c:await c.execute("DELETE FROM zako_rank_prizes WHERE period=$1 AND place=$2",period,place)
            return await tg("sendMessage",{"chat_id":uid,"text":f"🗑 #{place} sovrin o‘chirildi."})
        if not text or len(text)>200:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Sovrin nomi 1–200 belgidan iborat bo‘lsin."})
        p=await db()
        async with p.acquire() as c:await c.execute("INSERT INTO zako_rank_prizes(period,place,prize) VALUES($1,$2,$3) ON CONFLICT(period,place) DO UPDATE SET prize=EXCLUDED.prize",period,place,text)
        return await tg("sendMessage",{"chat_id":uid,"text":f"✅ #{place} sovrin saqlandi."})
    if mode=="channel":
        channel,derived_url=normalize_channel(text)
        if not channel:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Kanal noto‘g‘ri. Masalan: @zako_kanal yoki -1001234567890"})
        ok,info=await verify_channel(channel)
        if not ok:
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ "+info+"\n\nBotni kanalga administrator qiling va yana shu kanal ID/username'ini yuboring."})
        if derived_url:
            await set_setting("channel",channel);await set_setting("channel_url",derived_url)
            return await tg("sendMessage",{"chat_id":uid,"text":f"✅ <b>{htmlmod.escape(info)}</b> ulandi.\n\nEndi foydalanuvchi shu kanalga obuna bo‘lmasa ZAKO ochilmaydi.","parse_mode":"HTML"})
        admin_state[uid]={"mode":"channel_url","channel":channel}
        return await tg("sendMessage",{"chat_id":uid,"text":"🔗 Bu private kanalga o‘xshaydi. Endi <b>invite link</b>ni yuboring.\n\nMasalan: https://t.me/+AbCd...","parse_mode":"HTML"})
    if mode=="channel_url":
        if not (text.startswith("https://t.me/") or text.startswith("https://telegram.me/")):
            admin_state[uid]=st
            return await tg("sendMessage",{"chat_id":uid,"text":"❌ Invite link https://t.me/... ko‘rinishida bo‘lsin."})
        await set_setting("channel",st["channel"]);await set_setting("channel_url",text)
        return await tg("sendMessage",{"chat_id":uid,"text":"✅ Majburiy obuna saqlandi. Kanal va bot huquqi tekshirildi."})
    if mode=="user_id":
        try:target=int(text)
        except Exception:
            admin_state[uid]=st;return await tg("sendMessage",{"chat_id":uid,"text":"❌ Faqat Telegram ID raqamini yuboring."})
        admin_state[uid]={"mode":"send_user","target":target}
        return await tg("sendMessage",{"chat_id":uid,"text":"✍️ Endi yuboriladigan xabarni yuboring."})
    if mode=="send_user":
        r=await tg("copyMessage",{"chat_id":st["target"],"from_chat_id":uid,"message_id":m["message_id"]})
        return await tg("sendMessage",{"chat_id":uid,"text":"✅ Xabar yuborildi." if r.get("ok") else "❌ Xabar yuborilmadi. User botni avval ishga tushirgan bo‘lishi kerak."})
    if mode=="broadcast_prepare":
        admin_state[uid]={"mode":"broadcast_confirm","message_id":m["message_id"]}
        return await tg("sendMessage",{"chat_id":uid,"text":"⚠️ Shu xabarni HAMMA userga yuboraymi?\n\n/yes — yuborish\n/cancel — bekor qilish"})

async def do_broadcast(uid):
    st=admin_state.pop(uid,None)
    if not st or st.get("mode")!="broadcast_confirm":return await tg("sendMessage",{"chat_id":uid,"text":"❌ Broadcast topilmadi."})
    p=await db()
    async with p.acquire() as c:rows=await c.fetch("SELECT telegram_id FROM zako_users")
    ok=bad=0
    for r in rows:
        z=await tg("copyMessage",{"chat_id":int(r["telegram_id"]),"from_chat_id":uid,"message_id":st["message_id"]})
        if z.get("ok"):ok+=1
        else:bad+=1
        await asyncio.sleep(0.06)
    await tg("sendMessage",{"chat_id":uid,"text":f"📣 Yakunlandi.\n\n✅ Yetdi: {ok}\n❌ Yetmadi: {bad}"})

async def handle_update(upd):
    if "message" in upd:
        m=upd["message"];fr=m.get("from") or {}
        if not fr.get("id"):return
        await save_user(fr)
        if m.get("chat",{}).get("type")!="private":return
        if m.get("successful_payment"):
            sp=m["successful_payment"];payload=sp.get("invoice_payload","");uid=int(fr["id"]);p=await db()
            async with p.acquire() as c:
                pay=await c.fetchrow("SELECT * FROM zako_payments WHERE payload=$1 FOR UPDATE",payload)
                if pay and pay["status"]!="paid":
                    await c.execute("UPDATE zako_users SET coins=coins+$2 WHERE telegram_id=$1",uid,int(pay["coins"]))
                    await c.execute("UPDATE zako_payments SET status='paid',paid_at=now() WHERE payload=$1",payload)
                    await tg("sendMessage",{"chat_id":uid,"text":f"✅ To‘lov qabul qilindi!\n🪙 +{int(pay['coins'])} Coin hisobingizga qo‘shildi."})
            return
        text=(m.get("text") or "").strip()
        if text.startswith("/start"):
            parts=text.split(maxsplit=1);arg=parts[1].strip() if len(parts)>1 else ""
            ch=arg[3:] if arg.startswith("ch_") else None
            ref=arg[4:] if arg.startswith("ref_") else None
            if ref and ref.isdigit() and int(fr["id"]) not in ADMIN_IDS:
                if await register_referral(fr["id"],int(ref)):
                    p=await db()
                    async with p.acquire() as c:
                        await c.execute("UPDATE zako_users SET coins=coins+5 WHERE telegram_id=$1",int(ref))
                        await c.execute("UPDATE zako_users SET referral_rewarded=true WHERE telegram_id=$1",int(fr["id"]))
            if ch:
                p=await db()
                async with p.acquire() as c:exists=await c.fetchval("SELECT 1 FROM zako_challenges WHERE token=$1 AND used=false",ch)
                if exists:return await welcome_message(fr["id"],ch)
            return await welcome_message(fr["id"])
        if text=="/admin" and fr["id"] in ADMIN_IDS:return await send_admin(fr["id"])
        if text=="/yes" and fr["id"] in ADMIN_IDS and admin_state.get(fr["id"],{}).get("mode")=="broadcast_confirm":return await do_broadcast(fr["id"])
        if text=="/cancel" and fr["id"] in ADMIN_IDS:
            admin_state.pop(fr["id"],None);return await tg("sendMessage",{"chat_id":fr["id"],"text":"❌ Bekor qilindi."})
        if fr["id"] in ADMIN_IDS:return await admin_flow(m)
        return
    if "pre_checkout_query" in upd:
        q=upd["pre_checkout_query"];payload=q.get("invoice_payload","");p=await db()
        async with p.acquire() as c:ok=await c.fetchval("SELECT 1 FROM zako_payments WHERE payload=$1 AND status='pending'",payload)
        await tg("answerPreCheckoutQuery",{"pre_checkout_query_id":q["id"],"ok":bool(ok),"error_message":None if ok else "To‘lov topilmadi."})
        return
    if "callback_query" in upd:
        cq=upd["callback_query"];fr=cq.get("from") or {};uid=int(fr.get("id",0));cb=cq.get("data","")
        await tg("answerCallbackQuery",{"callback_query_id":cq["id"]});await save_user(fr)
        if cb=="admin" and uid in ADMIN_IDS:return await send_admin(uid)
        if cb.startswith("subcheck"):
            ch=cb.split(":",1)[1] if ":" in cb else None
            if not await is_subscribed(uid):return await tg("sendMessage",{"chat_id":uid,"text":"❌ Hali kanalga obuna bo‘lmagansiz."})
            return await tg("sendMessage",{"chat_id":uid,"text":"✅ Obuna tasdiqlandi. Endi ZAKO'ni oching.","reply_markup":open_keyboard(ch)})
        if cb.startswith("ad:") and uid in ADMIN_IDS:return await admin_callback(uid,cb[3:])

app=FastAPI(title="ZAKO")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["GET","POST","HEAD"],allow_headers=["*"])

@app.get("/",response_class=HTMLResponse)
async def root():return HTMLResponse(HTML,headers={"Cache-Control":"no-store, no-cache, must-revalidate, max-age=0"})

@app.head("/")
async def head():return ""

@app.get("/welcome.png")
async def welcome():
    if not WELCOME.exists():raise HTTPException(404,"welcome.png topilmadi")
    return FileResponse(WELCOME,media_type="image/png")

@app.get("/health")
async def health():return {"ok":True,"version":"zako-beqiyos-1"}

@app.post("/api/score")
async def api_score(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""))
    await save_user(u)
    b=await r.json()
    cat=b.get("category")
    attempt=str(b.get("attempt_id","")).strip()
    try:pct=int(b.get("pct"))
    except:raise HTTPException(400,"Ball noto‘g‘ri.")
    if cat not in DATA["core"] or not attempt or len(attempt)>100 or not 0<=pct<=100:
        raise HTTPException(400,"Natija noto‘g‘ri.")
    uid=int(u["id"]);p=await db()
    async with p.acquire() as c:
        async with c.transaction():
            inserted=await c.fetchrow("""INSERT INTO zako_daily_scores
                (telegram_id,category,pct,attempt_id,score_day)
                VALUES($1,$2,$3,$4,(now() AT TIME ZONE 'Asia/Tashkent')::date)
                ON CONFLICT(telegram_id,category,score_day) DO NOTHING RETURNING id""",
                uid,cat,pct,attempt)
            if not inserted:
                return {"ok":True,"ranked":False,"already_done":True}
            xp_gain=100+pct
            await c.execute("UPDATE zako_users SET xp=xp+$2,last_seen=now() WHERE telegram_id=$1",uid,xp_gain)
            today=await c.fetchval("SELECT (now() AT TIME ZONE 'Asia/Tashkent')::date")
            passed=await c.fetchval("""SELECT count(*) FROM zako_daily_scores
                WHERE telegram_id=$1 AND score_day=$2 AND pct>=60""",uid,today)
            streak_inc=False
            if int(passed)==4:
                row=await c.fetchrow("SELECT streak,streak_day FROM zako_users WHERE telegram_id=$1 FOR UPDATE",uid)
                if row["streak_day"]!=today:
                    yesterday=today-datetime.timedelta(days=1)
                    ns=(int(row["streak"])+1) if row["streak_day"]==yesterday else 1
                    await c.execute("""UPDATE zako_users SET streak=$2,streak_day=$3
                        WHERE telegram_id=$1""",uid,ns,today)
                    streak_inc=True
    return {"ok":True,"ranked":True,"xp_gain":xp_gain,"pct":pct,
            "streak_inc":streak_inc,"all_four_passed":int(passed)==4}

@app.post("/api/xp/convert")
async def xp_convert(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);uid=int(u["id"]);p=await db()
    async with p.acquire() as c:
        async with c.transaction():
            row=await c.fetchrow("SELECT xp,coins FROM zako_users WHERE telegram_id=$1 FOR UPDATE",uid)
            amount=(int(row["xp"])//1000)*1000
            if amount<1000:return {"ok":False,"xp":int(row["xp"]),"coins":int(row["coins"]),"converted":0}
            add=amount//100
            await c.execute("UPDATE zako_users SET xp=xp-$2,coins=coins+$3 WHERE telegram_id=$1",uid,amount,add)
            return {"ok":True,"xp":int(row["xp"])-amount,"coins":int(row["coins"])+add,"converted":add}

@app.get("/api/wallet")
async def wallet(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);uid=int(u["id"]);p=await db()
    async with p.acquire() as c:
        row=await c.fetchrow("""SELECT xp,coins,streak,premium_until,streak_premium_claimed,frame_id
            FROM zako_users WHERE telegram_id=$1""",uid)
        week=await c.fetchval("""SELECT COALESCE(SUM(pct),0)::int FROM zako_daily_scores
            WHERE telegram_id=$1 AND score_day >= ((now() AT TIME ZONE 'Asia/Tashkent')::date - 6)""",uid)
        month=await c.fetchval("""SELECT COALESCE(SUM(pct),0)::int FROM zako_daily_scores
            WHERE telegram_id=$1 AND score_day >= date_trunc('month',(now() AT TIME ZONE 'Asia/Tashkent'))::date""",uid)
        my_week=await c.fetchval("""SELECT COALESCE(SUM(pct),0)::int FROM zako_daily_scores
            WHERE telegram_id=$1 AND score_day >= ((now() AT TIME ZONE 'Asia/Tashkent')::date - 6)""",uid)
        rank=await c.fetchval("""WITH totals AS (
            SELECT telegram_id,SUM(pct)::int score FROM zako_daily_scores
            WHERE score_day >= ((now() AT TIME ZONE 'Asia/Tashkent')::date - 6)
            GROUP BY telegram_id)
            SELECT 1+COUNT(*) FROM totals WHERE score>$1""",int(my_week or 0))
        done=await c.fetch("""SELECT category,pct FROM zako_daily_scores
            WHERE telegram_id=$1 AND score_day=(now() AT TIME ZONE 'Asia/Tashkent')::date""",uid)
    return {"xp":int(row["xp"]),"coins":int(row["coins"]),"streak":int(row["streak"]),
            "week":int(week or 0),"month":int(month or 0),"rank":int(rank or 1),
            "premium_until":row["premium_until"].isoformat() if row["premium_until"] else None,
            "premium_claimed":bool(row["streak_premium_claimed"]),
            "frame_id":int(row["frame_id"]) if row["frame_id"] else None,
            "done":{x["category"]:int(x["pct"]) for x in done}}

@app.get("/api/shop")
async def shop_api(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);p=await db()
    async with p.acquire() as c:
        rows=await c.fetch("""SELECT id,kind,title,description,coins_price,xp_price,stars_price
            FROM zako_shop_items WHERE active=true ORDER BY sort_order,id""")
    return {"items":[{"id":int(x["id"]),"kind":x["kind"],"title":x["title"],
                      "description":x["description"],"coins_price":int(x["coins_price"]),
                      "xp_price":int(x["xp_price"]),"stars_price":int(x["stars_price"])} for x in rows]}

@app.post("/api/shop/redeem")
async def shop_redeem(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);b=await r.json();uid=int(u["id"])
    try:item_id=int(b.get("item_id"))
    except:raise HTTPException(400,"Sovg‘a noto‘g‘ri.")
    p=await db()
    async with p.acquire() as c:
        async with c.transaction():
            item=await c.fetchrow("""SELECT * FROM zako_shop_items
                WHERE id=$1 AND active=true AND kind IN ('gift','frame') FOR UPDATE""",item_id)
            if not item:raise HTTPException(404,"Sovg‘a topilmadi.")
            row=await c.fetchrow("SELECT xp,coins FROM zako_users WHERE telegram_id=$1 FOR UPDATE",uid)
            xpprice=int(item["xp_price"]);coinprice=int(item["coins_price"])
            if xpprice>0:
                if int(row["xp"])<xpprice:raise HTTPException(400,"XP yetarli emas.")
                await c.execute("""UPDATE zako_users SET xp=xp-$2,
                    frame_id=CASE WHEN $3='frame' THEN $4 ELSE frame_id END WHERE telegram_id=$1""",
                    uid,xpprice,item["kind"],item_id)
            else:
                if int(row["coins"])<coinprice:raise HTTPException(400,"Coin yetarli emas.")
                await c.execute("""UPDATE zako_users SET coins=coins-$2,
                    frame_id=CASE WHEN $3='frame' THEN $4 ELSE frame_id END WHERE telegram_id=$1""",
                    uid,coinprice,item["kind"],item_id)
            if item["kind"]=="gift":
                await c.execute("""INSERT INTO zako_redemptions
                    (telegram_id,item_id,item_title,coins_spent) VALUES($1,$2,$3,$4)""",
                    uid,item_id,item["title"],coinprice)
    if item["kind"]=="gift":
        try:
            await tg("sendMessage",{"chat_id":next(iter(ADMIN_IDS)),
                "text":f"🎁 <b>Coin Shop buyurtmasi</b>\n\n👤 User: <code>{uid}</code>\n🎁 {htmlmod.escape(item['title'])}\n🪙 {coinprice} Coin","parse_mode":"HTML"})
        except Exception:pass
    return {"ok":True,"message":"Ramka taqildi." if item["kind"]=="frame" else "Sovg‘a buyurtma qilindi."}

@app.get("/api/tasks")
async def tasks_api(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);uid=int(u["id"]);p=await db()
    async with p.acquire() as c:
        rows=await c.fetch("""SELECT t.*, EXISTS(
            SELECT 1 FROM zako_task_claims x WHERE x.task_id=t.id AND x.telegram_id=$1
            ) claimed FROM zako_tasks t WHERE t.active=true ORDER BY t.id""",uid)
    return {"items":[{"id":int(x["id"]),"title":x["title"],"url":x["url"],
                      "reward_xp":int(x["reward_xp"]),"reward_coins":int(x["reward_coins"]),
                      "claimed":bool(x["claimed"])} for x in rows]}

@app.post("/api/tasks/claim")
async def task_claim(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);uid=int(u["id"]);b=await r.json()
    try:tid=int(b.get("task_id"))
    except:raise HTTPException(400,"Topshiriq noto‘g‘ri.")
    p=await db()
    async with p.acquire() as c:
        async with c.transaction():
            task=await c.fetchrow("SELECT * FROM zako_tasks WHERE id=$1 AND active=true FOR UPDATE",tid)
            if not task:raise HTTPException(404,"Topshiriq topilmadi.")
            old=await c.fetchval("SELECT 1 FROM zako_task_claims WHERE task_id=$1 AND telegram_id=$2",tid,uid)
            if old:return {"ok":True,"claimed":False,"already":True}
            check=await tg("getChatMember",{"chat_id":task["chat_id"],"user_id":uid})
            if not check.get("ok"):
                raise HTTPException(502,"Kanal obunasini tekshirib bo‘lmadi. Birozdan keyin urinib ko‘ring.")
            member=check.get("result") or {};ms=member.get("status")
            if not (ms in ("creator","administrator","member") or (ms=="restricted" and bool(member.get("is_member")))):
                raise HTTPException(403,"Avval kanalga obuna bo‘ling.")
            await c.execute("INSERT INTO zako_task_claims(task_id,telegram_id) VALUES($1,$2)",tid,uid)
            await c.execute("UPDATE zako_users SET xp=xp+$2,coins=coins+$3 WHERE telegram_id=$1",
                            uid,int(task["reward_xp"]),int(task["reward_coins"]))
    return {"ok":True,"claimed":True,"xp":int(task["reward_xp"]),"coins":int(task["reward_coins"])}

@app.get("/api/referrals")
async def referrals_api(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);uid=int(u["id"]);p=await db()
    async with p.acquire() as c:
        rows=await c.fetch("""SELECT telegram_id,first_name,username FROM zako_users
            WHERE referred_by=$1 ORDER BY joined_at DESC LIMIT 100""",uid)
    return {"link":f"https://t.me/{BOT_USERNAME}?start=ref_{uid}","count":len(rows),
            "items":[{"id":int(x["telegram_id"]),"name":x["first_name"] or x["username"] or "User"} for x in rows]}

@app.post("/api/streak/premium")
async def streak_premium(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);uid=int(u["id"]);p=await db()
    async with p.acquire() as c:
        async with c.transaction():
            row=await c.fetchrow("""SELECT streak,streak_premium_claimed,premium_until
                FROM zako_users WHERE telegram_id=$1 FOR UPDATE""",uid)
            if int(row["streak"])<30:raise HTTPException(400,"30 kunlik streakga hali yetmadingiz.")
            if row["streak_premium_claimed"]:
                return {"ok":True,"claimed":False,"already":True,
                        "premium_until":row["premium_until"].isoformat() if row["premium_until"] else None}
            await c.execute("""UPDATE zako_users SET
                premium_until=GREATEST(COALESCE(premium_until,now()),now())+interval '30 days',
                streak_premium_claimed=true WHERE telegram_id=$1""",uid)
            until=await c.fetchval("SELECT premium_until FROM zako_users WHERE telegram_id=$1",uid)
    return {"ok":True,"claimed":True,"premium_until":until.isoformat()}

@app.get("/api/ranking")
async def ranking(period:str="week"):
    period=period if period in {"week","month"} else "week";p=await db();where="score_day >= ((now() AT TIME ZONE 'Asia/Tashkent')::date - 6)" if period=="week" else "score_day >= date_trunc('month',(now() AT TIME ZONE 'Asia/Tashkent'))::date"
    async with p.acquire() as c:
        rows=await c.fetch(f"SELECT u.telegram_id,u.first_name,u.username,SUM(s.pct)::int score FROM zako_users u JOIN zako_daily_scores s ON s.telegram_id=u.telegram_id WHERE {where} GROUP BY u.telegram_id ORDER BY score DESC,u.telegram_id LIMIT 10")
        prizes=await c.fetch("SELECT place,prize FROM zako_rank_prizes WHERE period=$1 ORDER BY place",period)
    return {"period":period,"rows":[{"id":int(x["telegram_id"]),"name":x["first_name"] or x["username"] or "ZAKO","score":int(x["score"])} for x in rows],"prizes":[{"place":int(x["place"]),"prize":x["prize"]} for x in prizes]}

@app.get("/api/friends")
async def friends(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);uid=int(u["id"]);p=await db()
    async with p.acquire() as c:
        rows=await c.fetch("""SELECT r.challenger_id,r.kind,r.pct,r.created_at,u.first_name,u.username FROM zako_social_results r LEFT JOIN zako_users u ON u.telegram_id=r.challenger_id WHERE r.creator_id=$1 ORDER BY r.created_at DESC LIMIT 30""",uid)
    return {"items":[{"id":int(x["challenger_id"]),"name":x["first_name"] or x["username"] or "Do‘st","kind":x["kind"],"pct":int(x["pct"]),"created_at":x["created_at"].isoformat()} for x in rows]}

@app.get("/api/me")
async def me(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);uid=int(u["id"]);p=await db()
    async with p.acquire() as c:
        w=await c.fetchrow("SELECT xp,coins,streak FROM zako_users WHERE telegram_id=$1",uid)
        week=await c.fetchval("SELECT COALESCE(SUM(pct),0)::int FROM zako_daily_scores WHERE telegram_id=$1 AND score_day>=CURRENT_DATE-INTERVAL '6 days'",uid)
        month=await c.fetchval("SELECT COALESCE(SUM(pct),0)::int FROM zako_daily_scores WHERE telegram_id=$1 AND score_day>=date_trunc('month',CURRENT_DATE)::date",uid)
    return {"xp":int(w["xp"]),"coins":int(w["coins"]),"streak":int(w["streak"]),"week":int(week or 0),"month":int(month or 0)}

@app.post("/api/coin/invoice")
async def coin_invoice(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);b=await r.json();uid=int(u["id"])
    try:item_id=int(b.get("item_id"))
    except:raise HTTPException(400,"Coin paketi noto‘g‘ri.")
    p=await db()
    async with p.acquire() as c:item=await c.fetchrow("SELECT * FROM zako_shop_items WHERE id=$1 AND active=true AND kind='coin_pack'",item_id)
    if not item or int(item["stars_price"])<=0:raise HTTPException(404,"Coin paketi topilmadi.")
    payload="zako_coin_"+secrets.token_urlsafe(12)
    async with p.acquire() as c:await c.execute("INSERT INTO zako_payments(telegram_id,payload,coins,stars) VALUES($1,$2,$3,$4)",uid,payload,int(item["coins_price"]),int(item["stars_price"]))
    inv=await tg("createInvoiceLink",{"title":item["title"],"description":item["description"] or f"{item['coins_price']} Coin","payload":payload,"currency":"XTR","prices":[{"label":item["title"],"amount":int(item["stars_price"])}]})
    if not inv.get("ok"):raise HTTPException(500,"Coin to‘lov oynasi ochilmadi.")
    return {"ok":True,"invoice":inv["result"]}

@app.post("/api/social/create")
async def social_create(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u);b=await r.json()
    kind=b.get("kind");qids=b.get("q_ids");answers=b.get("answers")
    if kind not in DATA["social"] or not isinstance(qids,list) or not isinstance(answers,list) or len(qids)!=6 or len(answers)!=6:raise HTTPException(400,"Test ma’lumotlari noto‘g‘ri.")
    allowed={q["id"] for q in DATA["social"][kind]}
    if len(set(qids))!=6 or any(q not in allowed for q in qids):raise HTTPException(400,"Savollar noto‘g‘ri.")
    if not await is_subscribed(u["id"]):raise HTTPException(403,"Avval kanalga obuna bo‘ling.")
    qmap={q["id"]:q for q in DATA["social"][kind]}
    for i,qid in enumerate(qids):
        q=qmap[qid];v=answers[i]
        if q["type"]=="month":
            if not isinstance(v,int) or not 0<=v<12:raise HTTPException(400,"Oy javobi noto‘g‘ri.")
        elif q["type"]=="slider":
            if not isinstance(v,(int,float)) or not 0<=float(v)<=100:raise HTTPException(400,"Slider javobi noto‘g‘ri.")
        else:
            if not isinstance(v,int) or not 0<=v<len(q["opts"]):raise HTTPException(400,"Javob noto‘g‘ri.")
    token=secrets.token_urlsafe(16)
    p=await db()
    async with p.acquire() as c:
        await c.execute("""INSERT INTO zako_challenges(token,creator_id,kind,q_ids,answers) VALUES($1,$2,$3,$4::jsonb,$5::jsonb)""",token,int(u["id"]),kind,json.dumps(qids),json.dumps(answers))
    return {"ok":True,"url":f"https://t.me/{BOT_USERNAME}?start=ch_{quote(token,safe='')}"}

@app.get("/api/social/get")
async def social_get(token:str,r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u)
    if not await is_subscribed(u["id"]):raise HTTPException(403,"Avval kanalga obuna bo‘ling.")
    p=await db()
    async with p.acquire() as c:row=await c.fetchrow("SELECT kind,q_ids,used FROM zako_challenges WHERE token=$1",token)
    if not row or row["used"]:raise HTTPException(404,"Bu test topilmadi yoki allaqachon ishlangan.")
    raw_qids=row["q_ids"]
    qids=json.loads(raw_qids) if isinstance(raw_qids,str) else raw_qids
    qmap={q["id"]:q for q in DATA["social"][row["kind"]]};out=[]
    for qid in qids:
        q=qmap.get(qid)
        if not q:raise HTTPException(404,"Savol topilmadi.")
        out.append({k:q[k] for k in ("id","q","type","opts")})
    return {"kind":row["kind"],"questions":out}

@app.post("/api/social/finish")
async def social_finish(r:FRequest):
    u=validate_init(r.headers.get("X-Telegram-Init-Data",""));await save_user(u)
    if not await is_subscribed(u["id"]):raise HTTPException(403,"Avval kanalga obuna bo‘ling.")
    b=await r.json();token=str(b.get("token","")).strip();answers=b.get("answers")
    if not token or not isinstance(answers,list) or len(answers)!=6:raise HTTPException(400,"Javoblar noto‘g‘ri.")
    p=await db()
    async with p.acquire() as c:
        async with c.transaction():
            row=await c.fetchrow("SELECT * FROM zako_challenges WHERE token=$1 FOR UPDATE",token)
            if not row:raise HTTPException(404,"Test topilmadi.")
            if row["used"]:raise HTTPException(409,"Bu test allaqachon ishlangan.")
            if int(row["creator_id"])==int(u["id"]):raise HTTPException(400,"O‘z testingizni o‘zingiz ishlay olmaysiz.")
            raw_qids=row["q_ids"]; raw_saved=row["answers"]
            qids=json.loads(raw_qids) if isinstance(raw_qids,str) else raw_qids
            saved=json.loads(raw_saved) if isinstance(raw_saved,str) else raw_saved
            qmap={q["id"]:q for q in DATA["social"][row["kind"]]};total=0.0
            for i,qid in enumerate(qids):
                q=qmap.get(qid)
                if not q:raise HTTPException(404,"Savol topilmadi.")
                x=saved[i];y=answers[i]
                if q["type"]=="slider":
                    if not isinstance(y,(int,float)) or not 0<=float(y)<=100:raise HTTPException(400,"Slider javobi noto‘g‘ri.")
                    total+=max(0.0,1.0-abs(float(x)-float(y))/100.0)
                elif q["type"]=="month":
                    if not isinstance(y,int) or not 0<=y<12:raise HTTPException(400,"Oy javobi noto‘g‘ri.")
                    if int(x)==y:total+=1
                else:
                    if not isinstance(y,int) or not 0<=y<len(q["opts"]):raise HTTPException(400,"Javob noto‘g‘ri.")
                    if int(x)==y:total+=1
            pct=round(total/6*100);creator=int(row["creator_id"]);kind=row["kind"]
            await c.execute("UPDATE zako_challenges SET used=true WHERE token=$1",token)
            await c.execute("INSERT INTO zako_social_results(challenge_token,creator_id,challenger_id,kind,pct) VALUES($1,$2,$3,$4,$5)",token,creator,int(u["id"]),kind,pct)
    name=htmlmod.escape(u.get("first_name") or u.get("username") or "Do‘st")
    label="Meni qanchalik bilasan?" if kind=="love" else "Do‘stingni qanchalik bilasan?"
    reaction=("🔥 Voy! Seni juda yaxshi biladi!" if pct>=90 else "❤️ Juda yaxshi biladi!" if pct>=70 else "🙂 Yomon emas, hali sirlar bor." if pct>=50 else "👀 Ancha adashibdi..." if pct>=30 else "😂 Qanday do‘st bu?!")
    msg=f"💌 <b>{label}</b>\n\n👤 <b>{name}</b> seni <b>{pct}%</b> bilar ekan!\n📊 6 ta savoldan mosligi: <b>{pct}%</b>\n\n{reaction}"
    sent=await tg("sendMessage",{"chat_id":creator,"text":msg,"parse_mode":"HTML"})
    if not sent.get("ok"):print(f"[SOCIAL NOTIFY FAILED] {sent}",flush=True)
    return {"ok":True,"pct":pct,"reaction":reaction}

@app.on_event("startup")
async def startup():
    await init_db()
    me=await tg("getMe",{})
    if not me.get("ok"):raise RuntimeError(f"Telegram getMe ishlamadi: {me}")
    wh=await tg("setWebhook",{"url":PUBLIC_URL+"/telegram/webhook","secret_token":WEBHOOK_SECRET,"allowed_updates":["message","callback_query","pre_checkout_query"]})
    if not wh.get("ok"):raise RuntimeError(f"Webhook o‘rnatilmadi: {wh}")
    print("[ZAKO] startup OK",flush=True)

@app.on_event("shutdown")
async def shutdown():
    global pool
    if pool:
        await pool.close();pool=None

@app.post("/telegram/webhook")
async def webhook(r:FRequest):
    got=r.headers.get("X-Telegram-Bot-Api-Secret-Token","")
    if not hmac.compare_digest(got,WEBHOOK_SECRET):raise HTTPException(403,"Forbidden")
    try:await handle_update(await r.json())
    except Exception as e:print(f"[WEBHOOK ERROR] {type(e).__name__}: {e}",flush=True)
    return {"ok":True}
