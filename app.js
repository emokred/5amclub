// ==================== THE 5 AM CLUB MINI APP ====================
// Senior Full-Stack Engineering Edition: WebApp HMAC Auth, RPG XP & Leveling, Stamina Engine, HD Canvas Certificate & Web Audio Synth

const I18N = {
    uz: {
        rankNovice: "🌅 Tonggi Yangi A'zo",
        rankPhoenix: "⚡ Porlayotgan Qaqnus",
        rankWarrior: "⚔️ Intizom Jangchisi",
        rankMaster: "🏆 Ertalabki Usta",
        rankLegend: "👑 5 AM Afsonasi",
        tabDashboard: "Bosh sahifa",
        tabCalendar: "Taqvim",
        tabInventory: "Xaridorlik",
        tabMarket: "Bozor",
        tabArena: "Arena",
        tabRanks: "Reyting",
        labelStreak: "Kun",
        labelCoins: "Tanga",
        labelMultiplier: "Koeff",
        labelTournament: "Turnir",
        labelStamina: "Stamina Vitality",
        windowBadge: "● JONLI OYNA",
        windowTitle: "Ertalabki Check-In Oynasi",
        hoursLabel: "Soat",
        minsLabel: "Daqiqa",
        secsLabel: "Soniya",
        btnCheckin: "SOLO CHECK-IN (+10 TANGA, +50 XP)",
        photoTitle: "Kunlik Foto Topshiriq",
        photoBadge: "📸 FOTO TOPSHIRIQ",
        missionText: "☕ <b>Topshiriq:</b> Bugungi tonggi kofe, choy yoki toza suv stakaningiz rasmini yuboring!",
        uploadBtn: "📷 Foto Isbot Yuborish (+25 Tanga, +100 XP)",
        verifiedStamp: "✅ VERIFIED 5 AM CLUB",
        badgeBedtime: "🌙 21:30 UYQU PROTOKOLI",
        titleBedtime: "Robin Sharma Uyqu Rejimi",
        descBedtime: "🛌 <i>“Ertalabki vaqtingizga egalik qilish uchun uyqungizni asrang!”</i><br>Ekranlarni o'chiring va 7.5 soatlik shifobaxsh uyquga yoting.",
        btnBedtime: "Men Uxlashga Yotdim (+20 XP & 100% Stamina)",
        wisdomQuote: "“Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring. G'alabalar tong otmasdan yaratiladi.”",
        wisdomAuthor: "— Robin Sharma",
        calendarTitle: "📅 30 Kunlik Uyg'onish Matritsasi",
        calendarSub: "Yashil kataklar muvaffaqiyatli 5 AM uyg'onishlarini bildiradi!",
        habitTitle: "🏆 21 Kunlik Odat Maratoni",
        habitSub: "Oltin Sertifikatni ochish uchun 21 kunlik streakka erishing!",
        btnQuickCert: "Sertifikatni Ko'rish 📜",
        inventoryBadge: "🎒 INVENTORY",
        inventoryHeader: "Mening Xaridorligim & Buyumlar",
        labelInvFreezes: "Streak Qalqoni",
        labelInvPhotos: "Tasdiqlangan Foto",
        labelInvBoost: "Coin Koeffitsiyent",
        labelInvTourney: "Turnir Ballari",
        titleOwnedItems: "📦 Faol Buyumlar & Sertifikatlar",
        itemFreezeTitle: "Streak Freeze Qalqoni",
        itemFreezeDesc: "Uxlab qolganda streakni 0 ga tushishdan avtomatik 1 kun saqlaydi.",
        itemCertTitle: "21-Day Gold Certificate",
        itemCertDesc: "21 kun ertalab soat 5:00 da uyg'onganingiz uchun beriladigan rasmiy mukofot.",
        titleBadgesCabinet: "🏅 Trophy Cabinet (Nishonlar)",
        btnViewCert: "Ochish 📜",
        btnUseShield: "Ko'rish",
        shopTitle: "🛒 5 AM Bozori",
        labelBalance: "Hisob:",
        shopItem1Title: "Streak Freeze",
        shopItem1Desc: "Uxlab qolganda streakni saqlab qoluvchi maxsus qalqon.",
        shopItem2Title: "Lion Riser Nishoni",
        shopItem2Desc: "Profilingizda aks etuvchi eksklyuziv oltin arslon nishoni.",
        shopItem3Title: "Speed Demon Unvoni",
        shopItem3Desc: "Guruhdagi eng chaqqon va erta uyg'onuvchilar uchun unvon.",
        shopItem4Title: "VIP Mastermind Kirish",
        shopItem4Desc: "Maxsus 5 AM Mastermind yopiq guruhiga taklifnoma.",
        btnBuy: "Sotib olish",
        arenaTitle: "⚔️ 1v1 Uyg'onish Dueli",
        arenaSub: "50 tanga tikib, erta uyg'onish bo'yicha do'stingiz yoki random o'yinchi bilan bellashing!",
        matchBtn: "🎲 Tasodifiy Raqib Qidirish (-20 Stamina)",
        matchSearching: "⌛ Raqib qidirilmoqda...",
        matchFound: "⚔️ Raqib topildi! Duel faol!",
        duoTitle: "🤝 Duo Combo Sherik",
        duoSub: "Sherik bilan birgalikda uyg'onib, har kuni +50 bonus tanga va +25 XP oling!",
        labelPartner: "Hozirgi Sherik:",
        ranksTitle: "🏆 Shon-Sharaf Zali & Turnir",
        badgeTourney: "⚔️ HAFTALIK TOURNAMENT",
        titleTourneyBanner: "5 AM Weekly Championship",
        descTourney: "Haftalik 1,000 Coin sovrin jamg'armasi uchun kurashing! Yakshanba 23:59 da yangilanadi.",
        toastCheckinOk: "⚡ Solo Check-In muvaffaqiyatli! +{coins} Tanga, +50 XP! 🔥",
        toastPhotoOk: "📸 Foto tasdiqlandi! +{coins} Tanga, +100 XP! 🚀",
        toastPhotoRejected: "❌ Rasm juda qorong'u yoki talabga javob bermaydi! Iltimos, yorug'roq rasm yuboring! 📸",
        toastBought: "🎉 {item} sotib olindi ({price} Tanga)!",
        toastNoCoins: "❌ Tangalar yetarli emas! Sizga {price} tanga kerak.",
        toastBedtimeOk: "😴 Xayrli tun! +20 XP berildi va Staminangiz 100% tiklandi!",
        toastNoStamina: "⚡ Staminangiz yetarli emas! Kamida 20 Stamina kerak.",
        textDownloadCert: "Yuklab Olish (HD PNG)",
        textShareStory: "Story'ga Joylash"
    },
    ru: {
        rankNovice: "🌅 Рассветный Новичок",
        rankPhoenix: "⚡ Восходящий Феникс",
        rankWarrior: "⚔️ Воин Дисциплины",
        rankMaster: "🏆 Мастер Утра",
        rankLegend: "👑 Легенда 5 AM",
        tabDashboard: "Главная",
        tabCalendar: "Календарь",
        tabInventory: "Инвентарь",
        tabMarket: "Рынок",
        tabArena: "Арена",
        tabRanks: "Рейтинг",
        labelStreak: "Дней",
        labelCoins: "Монет",
        labelMultiplier: "Множ",
        labelTournament: "Турнир",
        labelStamina: "Энергия (Stamina)",
        windowBadge: "● ЖИВОЕ ОКНО",
        windowTitle: "Окно Утреннего Подъема",
        hoursLabel: "Часы",
        minsLabel: "Мин",
        secsLabel: "Сек",
        btnCheckin: "СОЛО CHECK-IN (+10 МОНЕТ, +50 XP)",
        photoTitle: "Ежедневное Фото-Задание",
        photoBadge: "📸 ФОТО ПОДТВЕРЖДЕНИЕ",
        missionText: "☕ <b>Задание:</b> Сделайте фото утреннего кофе, чая или стакана воды!",
        uploadBtn: "📷 Загрузить Фото (+25 Монет, +100 XP)",
        verifiedStamp: "✅ VERIFIED 5 AM CLUB",
        badgeBedtime: "🌙 21:30 ПРОТОКОЛ СНА",
        titleBedtime: "Режим Сна Робина Шармы",
        descBedtime: "🛌 <i>«Чтобы владеть своим утром, защищайте свой сон!»</i><br>Выключите экраны и приготовьтесь к 7.5 часам глубокого сна.",
        btnBedtime: "Я Ложусь Спать (+20 XP & 100% Энергия)",
        wisdomQuote: "«Владейте своим утром. Поднимите свою жизнь. Победы куются до рассвета.»",
        wisdomAuthor: "— Робин Шарма",
        calendarTitle: "📅 30-Дневная Матрица Подъема",
        calendarSub: "Зеленые плитки отражают подтвержденные подъемы в 5:00 утра!",
        habitTitle: "🏆 21-Дневный Марафон Привычки",
        habitSub: "Достигните 21 дня для получения Золотого Сертификата!",
        btnQuickCert: "Сертификат 📜",
        inventoryBadge: "🎒 ИНВЕНТАРЬ",
        inventoryHeader: "Мой Инвентарь & Награды",
        labelInvFreezes: "Защита Стрика",
        labelInvPhotos: "Фото-Подтверждений",
        labelInvBoost: "Множитель Монет",
        labelInvTourney: "Турнирные Очки",
        titleOwnedItems: "📦 Активные Предметы & Сертификаты",
        itemFreezeTitle: "Streak Freeze (Защита)",
        itemFreezeDesc: "Автоматически спасает стрик от сброса при пропуске 1 дня.",
        itemCertTitle: "21-Day Gold Certificate",
        itemCertDesc: "Официальный сертификат за 21 день непрерывного подъема в 5:00 утра.",
        titleBadgesCabinet: "🏅 Витрина Наград (Значки)",
        btnViewCert: "Открыть 📜",
        btnUseShield: "Смотреть",
        shopTitle: "🛒 Рынок 5 AM",
        labelBalance: "Баланс:",
        shopItem1Title: "Streak Freeze",
        shopItem1Desc: "Защитный щит для сохранения стрика при пропуске дня.",
        shopItem2Title: "Значок Lion Riser",
        shopItem2Desc: "Эксклюзивный золотой значок льва в вашем профиле.",
        shopItem3Title: "Титул Speed Demon",
        shopItem3Desc: "Особый титул для самых быстрых участников клуба.",
        shopItem4Title: "Вход в VIP Mastermind",
        shopItem4Desc: "Доступ в закрытую элитную группу 5 AM Mastermind.",
        btnBuy: "Купить",
        arenaTitle: "⚔️ Дуэль 1v1 на Подъем",
        arenaSub: "Поставьте 50 монет и соревнуйтесь в раннем подъеме!",
        matchBtn: "🎲 Найти Соперника (-20 Энергии)",
        matchSearching: "⌛ Поиск соперника...",
        matchFound: "⚔️ Соперник найден! Дуэль активна!",
        duoTitle: "🤝 Парный Комбо Партнер",
        duoSub: "Просыпайтесь вместе с партнером и получайте +50 монет и +25 XP ежедневно!",
        labelPartner: "Текущий Партнер:",
        ranksTitle: "🏆 Зал Славы & Турнир",
        badgeTourney: "⚔️ НЕДЕЛЬНЫЙ ТУРНИР",
        titleTourneyBanner: "5 AM Weekly Championship",
        descTourney: "Соревнуйтесь за призовой фонд 1,000 монет! Обновляется каждое воскресенье в 23:59.",
        toastCheckinOk: "⚡ Соло Check-In успешен! +{coins} Монет, +50 XP! 🔥",
        toastPhotoOk: "📸 Фото подтверждено! +{coins} Монет, +100 XP! 🚀",
        toastPhotoRejected: "❌ Фото слишком темное или не соответствует требованиям! 📸",
        toastBought: "🎉 Куплено: {item} за {price} монет!",
        toastNoCoins: "❌ Недостаточно монет! Требуется {price} монет.",
        toastBedtimeOk: "😴 Спокойной ночи! +20 XP начислено, энергия 100%!",
        toastNoStamina: "⚡ Недостаточно энергии! Требуется минимум 20 Stamina.",
        textDownloadCert: "Скачать (HD PNG)",
        textShareStory: "В Сторис"
    },
    en: {
        rankNovice: "🌅 Dawn Novice",
        rankPhoenix: "⚡ Rising Phoenix",
        rankWarrior: "⚔️ Discipline Warrior",
        rankMaster: "🏆 Morning Master",
        rankLegend: "👑 5 AM Legend",
        tabDashboard: "Dashboard",
        tabCalendar: "Calendar",
        tabInventory: "Inventory",
        tabMarket: "Market",
        tabArena: "Arena",
        tabRanks: "Ranks",
        labelStreak: "Days",
        labelCoins: "Coins",
        labelMultiplier: "Mult",
        labelTournament: "Tourney",
        labelStamina: "Stamina Vitality",
        windowBadge: "● LIVE WINDOW",
        windowTitle: "Morning Check-In Window",
        hoursLabel: "Hours",
        minsLabel: "Mins",
        secsLabel: "Secs",
        btnCheckin: "SOLO CHECK-IN (+10 COINS, +50 XP)",
        photoTitle: "Daily Photo Mission",
        photoBadge: "📸 PHOTO PROOF",
        missionText: "☕ <b>Mission:</b> Snap a photo of your morning coffee, tea or fresh glass of water!",
        uploadBtn: "📷 Upload Photo Proof (+25 Coins, +100 XP)",
        verifiedStamp: "✅ VERIFIED 5 AM CLUB",
        badgeBedtime: "🌙 21:30 BEDTIME PROTOCOL",
        titleBedtime: "Robin Sharma Sleep Routine",
        descBedtime: "🛌 <i>“To own your morning, protect your sleep!”</i><br>Turn off screens and prepare for 7.5 hours of restorative sleep.",
        btnBedtime: "I'm Going to Sleep (+20 XP & 100% Stamina)",
        wisdomQuote: "“Own your morning. Elevate your life. Victories are created before dawn.”",
        wisdomAuthor: "— Robin Sharma",
        calendarTitle: "📅 30-Day Wake-Up Matrix",
        calendarSub: "Green tiles represent verified 5 AM wake-ups!",
        habitTitle: "🏆 21-Day Habit Challenge",
        habitSub: "Reach a 21-day streak to unlock your Official Golden Certificate!",
        btnQuickCert: "View Certificate 📜",
        inventoryBadge: "🎒 INVENTORY",
        inventoryHeader: "My Inventory & Assets",
        labelInvFreezes: "Streak Freezes",
        labelInvPhotos: "Verified Photos",
        labelInvBoost: "Coin Multiplier",
        labelInvTourney: "Tourney Points",
        titleOwnedItems: "📦 Active Items & Certificates",
        itemFreezeTitle: "Streak Freeze Shield",
        itemFreezeDesc: "Protects your streak from resetting to 0 if you miss 1 day.",
        itemCertTitle: "21-Day Gold Certificate",
        itemCertDesc: "Official verified discipline award for 21 consecutive 5 AM wake-ups.",
        titleBadgesCabinet: "🏅 Trophy Cabinet (Badges)",
        btnViewCert: "View 📜",
        btnUseShield: "View",
        shopTitle: "🛒 5 AM Marketplace",
        labelBalance: "Balance:",
        shopItem1Title: "Streak Freeze",
        shopItem1Desc: "Protects your streak if you miss 1 morning check-in.",
        shopItem2Title: "Lion Riser Badge",
        shopItem2Desc: "Exclusive gold lion badge displayed on your profile.",
        shopItem3Title: "Speed Demon Title",
        shopItem3Desc: "Title awarded to the fastest riser in the group.",
        shopItem4Title: "VIP Group Access",
        shopItem4Desc: "Unlock access to the Mastermind 5 AM Group.",
        btnBuy: "Buy",
        arenaTitle: "⚔️ 1v1 Wake-Up Duels",
        arenaSub: "Challenge a friend or random player for a 50 coin pool!",
        matchBtn: "🎲 Find Matchmaking (-20 Stamina)",
        matchSearching: "⌛ Searching for Partner...",
        matchFound: "⚔️ Match Found! Duel Active!",
        duoTitle: "🤝 Duo Combo Partner",
        duoSub: "Team up with a partner. Wake up together for +50 coins and +25 XP daily!",
        labelPartner: "Current Partner:",
        ranksTitle: "🏆 Hall of Fame & Tournament",
        badgeTourney: "⚔️ WEEKLY TOURNAMENT",
        titleTourneyBanner: "5 AM Weekly Championship",
        descTourney: "Compete for the weekly 1,000 Coin prize pool! Resets every Sunday at 23:59.",
        toastCheckinOk: "⚡ Solo Check-In Successful! +{coins} Coins, +50 XP! 🔥",
        toastPhotoOk: "📸 Photo Verified! +{coins} Coins, +100 XP! 🚀",
        toastPhotoRejected: "❌ Image is too dark or does not meet requirements! 📸",
        toastBought: "🎉 Purchased {item} for {price} Coins!",
        toastNoCoins: "❌ Insufficient Coins! You need {price} Coins.",
        toastBedtimeOk: "😴 Good night! +20 XP awarded and Stamina refilled to 100%!",
        toastNoStamina: "⚡ Insufficient stamina! You need at least 20 Stamina.",
        textDownloadCert: "Download (HD PNG)",
        textShareStory: "Share on Story"
    }
};

const RPG_LEVEL_TITLES = {
    uz: [
        [1, "🌅 Tonggi Shogird"],
        [5, "⚡ Quyosh Quluvchisi"],
        [10, "⚔️ Temir Intizom Ritsari"],
        [20, "👑 Tonggi Master"],
        [35, "🌌 Koinot Buyuk Ustasi"]
    ],
    ru: [
        [1, "🌅 Новичок Рассвета"],
        [5, "⚡ Искатель Солнца"],
        [10, "⚔️ Рыцарь Дисциплины"],
        [20, "👑 Мастер Рассвета"],
        [35, "🌌 Грандмастер 5 AM"]
    ],
    en: [
        [1, "🌅 Dawn Initiate"],
        [5, "⚡ Sun Chaser"],
        [10, "⚔️ Iron Discipline Knight"],
        [20, "👑 Dawn Master"],
        [35, "🌌 Grandmaster of 5 AM Dawn"]
    ]
};

// ==================== STATE MANAGEMENT ====================
const defaultState = {
    user: {
        id: 6377617416,
        name: "Morning Champion",
        username: "champion",
        streak: 12,
        coins: 450,
        xp: 180,
        level: 2,
        stamina: 100,
        maxStamina: 100,
        lastStaminaUpdate: new Date().toISOString(),
        multiplier: 1.2,
        rank: "🏆 Morning Master",
        photoCount: 5,
        freezeCount: 1,
        refCount: 3,
        tourneyPoints: 350,
        badges: ["Early Bird", "Photo Master"],
        checkedInToday: false,
        bedtimeRecordedToday: false
    },
    soundEnabled: true,
    lang: "uz"
};

let state = (() => {
    try {
        const saved = localStorage.getItem("5amclub_state_v2");
        if (saved) {
            return JSON.parse(saved);
        }
    } catch (e) {
        console.warn("Storage read error", e);
    }
    return defaultState;
})();

function saveState() {
    try {
        localStorage.setItem("5amclub_state_v2", JSON.stringify(state));
    } catch (e) {
        console.warn("Storage write error", e);
    }
}

// ==================== WEB AUDIO API SYNTHESIZER ====================
class SoundEffects {
    constructor() {
        this.ctx = null;
    }

    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) this.ctx = new AudioCtx();
        }
    }

    playTone(freq, type, duration, startDelay = 0, gainLevel = 0.15) {
        if (!state.soundEnabled) return;
        try {
            this.init();
            if (!this.ctx) return;
            if (this.ctx.state === "suspended") this.ctx.resume();

            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, this.ctx.currentTime + startDelay);
            gain.gain.setValueAtTime(gainLevel, this.ctx.currentTime + startDelay);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + startDelay + duration);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(this.ctx.currentTime + startDelay);
            osc.stop(this.ctx.currentTime + startDelay + duration);
        } catch (e) {}
    }

    click() {
        this.playTone(650, "sine", 0.04, 0, 0.1);
    }

    coin() {
        this.playTone(987.77, "triangle", 0.09, 0, 0.18);
        this.playTone(1318.51, "triangle", 0.22, 0.07, 0.18);
    }

    staminaRefill() {
        this.playTone(440, "sine", 0.08, 0, 0.12);
        this.playTone(554.37, "sine", 0.08, 0.06, 0.14);
        this.playTone(659.25, "sine", 0.12, 0.12, 0.16);
        this.playTone(880, "sine", 0.25, 0.18, 0.2);
    }

    victory() {
        this.playTone(523.25, "triangle", 0.1, 0, 0.18);
        this.playTone(659.25, "triangle", 0.1, 0.09, 0.18);
        this.playTone(783.99, "triangle", 0.1, 0.18, 0.2);
        this.playTone(1046.50, "triangle", 0.35, 0.27, 0.22);
    }

    levelUp() {
        this.playTone(440, "triangle", 0.12, 0, 0.2);
        this.playTone(554.37, "triangle", 0.12, 0.1, 0.2);
        this.playTone(659.25, "triangle", 0.12, 0.2, 0.22);
        this.playTone(880, "triangle", 0.15, 0.3, 0.25);
        this.playTone(1108.73, "triangle", 0.45, 0.42, 0.28);
    }

    bedtime() {
        this.playTone(392.00, "sine", 0.3, 0, 0.12);
        this.playTone(329.63, "sine", 0.35, 0.2, 0.12);
        this.playTone(261.63, "sine", 0.5, 0.45, 0.14);
    }

    duelClash() {
        this.playTone(220, "sawtooth", 0.08, 0, 0.15);
        this.playTone(330, "sawtooth", 0.15, 0.06, 0.18);
    }
}
const sfx = new SoundEffects();

// ==================== RPG & LEVELING FORMULAS ====================
function calculateRPG(xp, lang = "uz") {
    let level = 1;
    while (true) {
        const nextReq = 50 * level * (level + 1);
        if (xp < nextReq) break;
        level += 1;
    }

    const currFloor = 50 * (level - 1) * level;
    const nextCeil = 50 * level * (level + 1);
    const xpInLevel = Math.max(0, xp - currFloor);
    const xpNeededLevel = Math.max(1, nextCeil - currFloor);
    const progressPct = Math.min(100, Math.round((xpInLevel / xpNeededLevel) * 100));

    const titles = RPG_LEVEL_TITLES[lang] || RPG_LEVEL_TITLES.uz;
    let title = titles[0][1];
    for (const [minLvl, tName] of titles) {
        if (level >= minLvl) title = tName;
    }

    return {
        level,
        xpInLevel,
        xpNeededLevel,
        nextLevelTotalXP: nextCeil,
        progressPct,
        title
    };
}

function calculateMultiplier(streak) {
    if (streak >= 30) return 2.0;
    if (streak >= 15) return 1.5;
    if (streak >= 7) return 1.2;
    return 1.0;
}

function getRankTitle(streak, lang) {
    const t = I18N[lang] || I18N.uz;
    if (streak >= 30) return t.rankLegend;
    if (streak >= 15) return t.rankMaster;
    if (streak >= 8) return t.rankWarrior;
    if (streak >= 4) return t.rankPhoenix;
    return t.rankNovice;
}

// ==================== INITIALIZATION ====================
document.addEventListener("DOMContentLoaded", () => {
    initTelegramWebApp();
    initSoundToggle();
    initLanguage();
    initTabs();
    initLiveCountdown();
    renderCalendar();
    renderInventory();
    renderLeaderboard();
    initActions();
    updateUI();
    renderHDCanvasCertificate();
});

// ==================== TELEGRAM WEBAPP SDK & HMAC AUTH ====================
async function initTelegramWebApp() {
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        const tgUser = tg.initDataUnsafe?.user;
        if (tgUser) {
            state.user.id = tgUser.id;
            state.user.name = tgUser.first_name + (tgUser.last_name ? " " + tgUser.last_name : "");
            state.user.username = tgUser.username || "user";
            
            const fighterName = document.getElementById("user-fighter-name");
            if (fighterName) fighterName.textContent = state.user.name;

            if (tgUser.photo_url) {
                const avatar = document.getElementById("user-avatar");
                if (avatar) avatar.src = tgUser.photo_url;
            }
        }

        // Authenticate initData with Backend HMAC-SHA256 Endpoint
        if (tg.initData) {
            try {
                const res = await fetch("/api/auth/validate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ initData: tg.initData })
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.status === "ok" && data.user) {
                        state.user.streak = data.user.streak;
                        state.user.coins = data.user.coins;
                        state.user.xp = data.user.xp || 0;
                        state.user.level = data.user.level || 1;
                        state.user.stamina = data.user.stamina !== undefined ? data.user.stamina : 100;
                        state.user.photoCount = data.user.photo_count || 0;
                        state.user.freezeCount = data.user.freeze_count || 0;
                        state.user.refCount = data.user.ref_count || 0;
                        state.user.tourneyPoints = data.user.tournament_points || 0;
                        if (data.user.lang) state.lang = data.user.lang;
                        updateUI();
                    }
                }
            } catch (e) {
                console.log("Backend auth sync offline, using local state", e);
            }
        }
    }
}

// ==================== SOUND TOGGLE ====================
function initSoundToggle() {
    const btn = document.getElementById("sound-toggle-btn");
    if (!btn) return;
    btn.textContent = state.soundEnabled ? "🔊" : "🔇";
    if (!state.soundEnabled) btn.classList.add("muted");

    btn.addEventListener("click", () => {
        state.soundEnabled = !state.soundEnabled;
        btn.textContent = state.soundEnabled ? "🔊" : "🔇";
        if (state.soundEnabled) {
            btn.classList.remove("muted");
            sfx.click();
            showToast("🔊 Sound Effects Enabled");
        } else {
            btn.classList.add("muted");
            showToast("🔇 Sound Effects Muted");
        }
        saveState();
    });
}

// ==================== MULTI-LANGUAGE SYSTEM ====================
function initLanguage() {
    const langBtns = document.querySelectorAll(".lang-btn");
    langBtns.forEach(btn => {
        if (btn.getAttribute("data-lang") === state.lang) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }

        btn.addEventListener("click", () => {
            sfx.click();
            state.lang = btn.getAttribute("data-lang");
            langBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            saveState();
            applyLanguage();
            updateUI();
            renderInventory();
            renderLeaderboard();
            renderHDCanvasCertificate();
        });
    });

    applyLanguage();
}

function applyLanguage() {
    const t = I18N[state.lang] || I18N.uz;

    // Navigation
    setElementText("tab-nav-dashboard", t.tabDashboard);
    setElementText("tab-nav-calendar", t.tabCalendar);
    setElementText("tab-nav-inventory", t.tabInventory);
    setElementText("tab-nav-shop", t.tabMarket);
    setElementText("tab-nav-arena", t.tabArena);
    setElementText("tab-nav-ranks", t.tabRanks);

    // Profile header labels
    setElementText("label-streak", t.labelStreak);
    setElementText("label-coins", t.labelCoins);
    setElementText("label-multiplier", t.labelMultiplier);
    setElementText("label-tournament", t.labelTournament);
    setElementText("label-stamina", t.labelStamina);

    // Dashboard
    setElementText("badge-live-window", t.windowBadge);
    setElementText("title-checkin-window", t.windowTitle);
    setElementText("label-hours", t.hoursLabel);
    setElementText("label-mins", t.minsLabel);
    setElementText("label-secs", t.secsLabel);
    setElementText("text-btn-checkin", t.btnCheckin);

    // Photo Mission
    setElementText("badge-photo-proof", t.photoBadge);
    setElementText("title-photo-mission", t.photoTitle);
    const missionElem = document.getElementById("mission-text");
    if (missionElem) missionElem.innerHTML = t.missionText;
    setElementText("text-btn-upload", t.uploadBtn);

    // Bedtime Card
    setElementText("badge-bedtime", t.badgeBedtime);
    setElementText("title-bedtime", t.titleBedtime);
    const bedtimeDesc = document.getElementById("desc-bedtime");
    if (bedtimeDesc) bedtimeDesc.innerHTML = t.descBedtime;
    setElementText("text-btn-bedtime", t.btnBedtime);

    // Quotes & Challenge
    setElementText("daily-quote-text", t.wisdomQuote);
    setElementText("daily-quote-author", t.wisdomAuthor);
    setElementText("title-matrix", t.calendarTitle);
    setElementText("sub-matrix", t.calendarSub);
    setElementText("title-habit", t.habitTitle);
    setElementText("sub-habit", t.habitSub);
    setElementText("btn-quick-cert", t.btnQuickCert);

    // Inventory Tab
    setElementText("badge-inventory", t.inventoryBadge);
    setElementText("title-inventory-header", t.inventoryHeader);
    setElementText("label-inv-freezes", t.labelInvFreezes);
    setElementText("label-inv-photos", t.labelInvPhotos);
    setElementText("label-inv-boost", t.labelInvBoost);
    setElementText("label-inv-tourney", t.labelInvTourney);
    setElementText("title-owned-items", t.titleOwnedItems);
    setElementText("item-freeze-title", t.itemFreezeTitle);
    setElementText("item-freeze-desc", t.itemFreezeDesc);
    setElementText("item-cert-title", t.itemCertTitle);
    setElementText("item-cert-desc", t.itemCertDesc);
    setElementText("title-badges-cabinet", t.titleBadgesCabinet);
    setElementText("btn-view-cert", t.btnViewCert);
    setElementText("btn-use-shield", t.btnUseShield);

    // Shop
    setElementText("title-shop", t.shopTitle);
    setElementText("label-balance", t.labelBalance);
    setElementText("shop-item1-title", t.shopItem1Title);
    setElementText("shop-item1-desc", t.shopItem1Desc);
    setElementText("shop-item2-title", t.shopItem2Title);
    setElementText("shop-item2-desc", t.shopItem2Desc);
    setElementText("shop-item3-title", t.shopItem3Title);
    setElementText("shop-item3-desc", t.shopItem3Desc);
    setElementText("shop-item4-title", t.shopItem4Title);
    setElementText("shop-item4-desc", t.shopItem4Desc);

    // Arena & Tournament
    setElementText("title-arena", t.arenaTitle);
    setElementText("sub-arena", t.arenaSub);
    setElementText("duo-title-card", t.duoTitle);
    setElementText("duo-sub-card", t.duoSub);
    setElementText("label-partner", t.labelPartner);
    setElementText("title-ranks", t.ranksTitle);
    setElementText("badge-tourney", t.badgeTourney);
    setElementText("title-tournament-banner", t.titleTourneyBanner);
    setElementText("desc-tourney", t.descTourney);
    setElementText("text-btn-matchmaking", t.matchBtn);
    setElementText("text-download-cert", t.textDownloadCert);
    setElementText("text-share-story", t.textShareStory);
}

function setElementText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// ==================== UI UPDATE & RPG HUD ====================
function updateUI() {
    state.user.multiplier = calculateMultiplier(state.user.streak);
    state.user.rank = getRankTitle(state.user.streak, state.lang);

    const rpg = calculateRPG(state.user.xp, state.lang);

    setElementText("user-name", state.user.name);
    setElementText("user-rank", state.user.rank);
    setElementText("stat-streak", state.user.streak);
    setElementText("stat-coins", state.user.coins);
    setElementText("stat-multiplier", `${state.user.multiplier}X`);
    setElementText("stat-tournament", state.user.tourneyPoints || 0);
    setElementText("shop-balance-coins", `🪙 ${state.user.coins}`);

    // Update RPG HUD
    setElementText("hud-level-badge", `Lvl ${rpg.level}`);
    setElementText("hud-level-num", rpg.level);
    setElementText("hud-rpg-title", rpg.title);
    setElementText("hud-xp-text", `${rpg.xpInLevel} / ${rpg.xpNeededLevel} XP (${rpg.progressPct}%)`);
    
    const xpFill = document.getElementById("hud-xp-fill");
    if (xpFill) xpFill.style.width = `${rpg.progressPct}%`;

    // Update Stamina HUD
    const stamina = state.user.stamina !== undefined ? state.user.stamina : 100;
    setElementText("hud-stamina-text", `${stamina} / 100`);
    const staminaFill = document.getElementById("hud-stamina-fill");
    if (staminaFill) staminaFill.style.width = `${stamina}%`;

    const vitalityBadge = document.getElementById("hud-vitality-badge");
    const staminaStatus = document.getElementById("hud-stamina-status");
    if (stamina >= 80) {
        if (vitalityBadge) vitalityBadge.style.display = "inline-block";
        if (staminaStatus) staminaStatus.textContent = `${stamina}% Energetic 🟢`;
    } else if (stamina >= 40) {
        if (vitalityBadge) vitalityBadge.style.display = "none";
        if (staminaStatus) staminaStatus.textContent = `${stamina}% Normal 🟡`;
    } else {
        if (vitalityBadge) vitalityBadge.style.display = "none";
        if (staminaStatus) staminaStatus.textContent = `${stamina}% Fatigued 🔴`;
    }

    // Update 21-Day Challenge progress bar
    const progressFill = document.getElementById("cert-progress-fill");
    const progressLabel = document.getElementById("cert-progress-text");
    const progressPercent = Math.min(100, Math.round((state.user.streak / 21) * 100));
    
    if (progressFill) progressFill.style.width = `${progressPercent}%`;
    if (progressLabel) {
        const unit = state.lang === "uz" ? "Kun" : (state.lang === "ru" ? "Дней" : "Days");
        const doneText = state.lang === "uz" ? "Bajarildi" : (state.lang === "ru" ? "Завершено" : "Complete");
        progressLabel.textContent = `${state.user.streak} / 21 ${unit} (${progressPercent}% ${doneText})`;
    }

    renderInventory();
    saveState();
}

function addXP(amount) {
    const oldRPG = calculateRPG(state.user.xp, state.lang);
    state.user.xp += amount;
    const newRPG = calculateRPG(state.user.xp, state.lang);

    if (newRPG.level > oldRPG.level) {
        state.user.level = newRPG.level;
        state.user.coins += 50; // Level-up bonus
        triggerLevelUpCelebration(newRPG.level, newRPG.title);
    }
}

// ==================== TAB NAVIGATION ====================
function initTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            sfx.click();
            const targetTab = btn.getAttribute("data-tab");

            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const targetContent = document.getElementById(targetTab);
            if (targetContent) targetContent.classList.add("active");

            triggerHapticFeedback("light");
        });
    });
}

// ==================== INVENTORY TAB RENDERING ====================
function renderInventory() {
    setElementText("inv-freeze-count", state.user.freezeCount || 0);
    setElementText("inv-photo-count", state.user.photoCount || 0);
    setElementText("inv-multiplier-val", `${state.user.multiplier}X`);
    setElementText("inv-tourney-val", state.user.tourneyPoints || 0);

    const freezeBadge = document.getElementById("freeze-badge-count");
    if (freezeBadge) {
        const suffix = state.lang === "uz" ? "ta mavjud" : (state.lang === "ru" ? "шт. в наличии" : "Available");
        freezeBadge.textContent = `${state.user.freezeCount || 0} ${suffix}`;
    }

    const certBadge = document.getElementById("cert-badge-status");
    if (certBadge) {
        if (state.user.streak >= 21) {
            certBadge.textContent = "🏆 UNLOCKED (Gold)";
            certBadge.classList.add("unlocked");
        } else {
            certBadge.textContent = `${state.user.streak} / 21 Kun`;
            certBadge.classList.remove("unlocked");
        }
    }

    // Render Badges Cabinet
    const cabinet = document.getElementById("badges-cabinet-list");
    if (cabinet) {
        const badgesData = [
            { icon: "⚡", name: "Early Bird", req: "7 streak", unlocked: state.user.streak >= 7 },
            { icon: "📸", name: "Photo Master", req: "5 foto", unlocked: state.user.photoCount >= 5 },
            { icon: "👑", name: "Elite 21", req: "21 streak", unlocked: state.user.streak >= 21 },
            { icon: "🦁", name: "5 AM Legend", req: "30 streak", unlocked: state.user.streak >= 30 },
            { icon: "🛡", name: "Shielded", req: "1 freeze", unlocked: (state.user.freezeCount || 0) > 0 },
            { icon: "⚔️", name: "Gladiator", req: "100 pts", unlocked: (state.user.tourneyPoints || 0) >= 100 }
        ];

        cabinet.innerHTML = badgesData.map(b => `
            <div class="badge-card ${b.unlocked ? 'unlocked' : 'locked'}">
                <span class="b-icon">${b.icon}</span>
                <span class="b-name">${b.name}</span>
                <small class="b-status">${b.unlocked ? '✅ Faol' : b.req}</small>
            </div>
        `).join("");
    }
}

// ==================== LEADERBOARD & TOURNAMENT ====================
async function renderLeaderboard() {
    const list = document.getElementById("leaderboard-list");
    if (!list) return;

    let items = [
        { rank: "#4", name: "Alex Riser", streak: 19, coins: 820, points: 420 },
        { rank: "#5", name: "Sardor Dawn", streak: 16, coins: 640, points: 380 },
        { rank: "#6", name: "Elena Sunrise", streak: 14, coins: 510, points: 310 },
        { rank: "#7", name: "Dmitry 5AM", streak: 10, coins: 350, points: 260 },
        { rank: "#8", name: "Jasur Champion", streak: 8, coins: 280, points: 190 }
    ];

    try {
        const res = await fetch("/api/leaderboard");
        if (res.ok) {
            const data = await res.json();
            if (data.status === "ok" && data.leaderboard && data.leaderboard.length > 0) {
                items = data.leaderboard.slice(3).map((r, i) => ({
                    rank: `#${i + 4}`,
                    name: r.name,
                    streak: r.streak,
                    coins: r.coins,
                    points: r.xp || 0
                }));
            }
        }
    } catch (e) {}

    const unit = state.lang === "uz" ? "Kun" : (state.lang === "ru" ? "Дн" : "Days");
    list.innerHTML = items.map(b => `
        <li class="leader-item">
            <span class="rank">${b.rank}</span>
            <span class="leader-name">${b.name}</span>
            <span class="leader-streak">🔥 ${b.streak} ${unit}</span>
            <span class="leader-coins">🪙 ${b.coins}</span>
        </li>
    `).join("");
}

// ==================== DYNAMIC HIGH-DEFINITION CANVAS CERTIFICATE ENGINE ====================
function renderHDCanvasCertificate() {
    const canvas = document.getElementById("cert-canvas");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const width = 1200;
    const height = 800;
    canvas.width = width;
    canvas.height = height;

    // 1. Luxury Dark Obsidian / Celestial Gradient Background
    const bgGrad = ctx.createRadialGradient(width / 2, height / 2, 50, width / 2, height / 2, 700);
    bgGrad.addColorStop(0, "#131b2e");
    bgGrad.addColorStop(0.6, "#0b0f19");
    bgGrad.addColorStop(1, "#05070c");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    // 2. Subtle Star Dust Particles
    ctx.fillStyle = "rgba(251, 191, 36, 0.25)";
    for (let i = 0; i < 45; i++) {
        const x = (i * 97) % width;
        const y = (i * 123) % height;
        const r = (i % 3) + 1;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
    }

    // 3. Ornate Double Gold Outer Border
    ctx.strokeStyle = "#f59e0b";
    ctx.lineWidth = 8;
    ctx.strokeRect(30, 30, width - 60, height - 60);

    ctx.strokeStyle = "rgba(251, 191, 36, 0.4)";
    ctx.lineWidth = 2;
    ctx.strokeRect(42, 42, width - 84, height - 84);

    // 4. Corner Ornaments
    const drawCorner = (cx, cy) => {
        ctx.fillStyle = "#fbbf24";
        ctx.fillRect(cx - 6, cy - 6, 12, 12);
    };
    drawCorner(30, 30);
    drawCorner(width - 30, 30);
    drawCorner(30, height - 30);
    drawCorner(width - 30, height - 30);

    // 5. Crown Crest & Top Header
    ctx.textAlign = "center";
    ctx.font = "bold 42px 'Outfit', sans-serif";
    ctx.fillStyle = "#fbbf24";
    ctx.fillText("🏆 THE 5 AM CLUB 🏆", width / 2, 110);

    ctx.font = "600 18px 'Plus Jakarta Sans', sans-serif";
    ctx.fillStyle = "#94a3b8";
    ctx.letterSpacing = "4px";
    ctx.fillText("OFFICIAL DISCIPLINE & MASTERY CERTIFICATE", width / 2, 145);

    // 6. Presentation Line
    ctx.font = "500 16px 'Plus Jakarta Sans', sans-serif";
    ctx.fillStyle = "#cbd5e1";
    ctx.fillText("THIS CERTIFICATE IS PROUDLY CONFERRED UPON", width / 2, 220);

    // 7. Dynamic Recipient Name
    const recipientName = (state.user.name || "CHAMPION").toUpperCase();
    ctx.font = "900 52px 'Outfit', sans-serif";
    const nameGrad = ctx.createLinearGradient(width / 2 - 250, 0, width / 2 + 250, 0);
    nameGrad.addColorStop(0, "#fbbf24");
    nameGrad.addColorStop(0.5, "#ffffff");
    nameGrad.addColorStop(1, "#f59e0b");
    ctx.fillStyle = nameGrad;
    ctx.shadowColor = "rgba(245, 158, 11, 0.5)";
    ctx.shadowBlur = 16;
    ctx.fillText(`★ ${recipientName} ★`, width / 2, 300);
    ctx.shadowBlur = 0;

    // 8. Citation Paragraph
    ctx.font = "500 20px 'Plus Jakarta Sans', sans-serif";
    ctx.fillStyle = "#e2e8f0";
    ctx.fillText("For mastering morning discipline, waking up at 5:00 AM for 21 consecutive days,", width / 2, 380);
    ctx.fillText(`and elevating personal excellence to the prestigious rank of ${state.user.rank}.`, width / 2, 415);

    // 9. Motto
    ctx.font = "italic 600 22px 'Outfit', sans-serif";
    ctx.fillStyle = "#fbbf24";
    ctx.fillText("“Own Your Morning. Elevate Your Life.”", width / 2, 490);

    // 10. Seal & Verification Footer
    const todayStr = new Date().toLocaleDateString(state.lang === "uz" ? "uz-UZ" : (state.lang === "ru" ? "ru-RU" : "en-US"), {
        year: 'numeric', month: 'long', day: 'numeric'
    });

    // Left block: Date
    ctx.textAlign = "left";
    ctx.font = "600 15px 'Plus Jakarta Sans', sans-serif";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(`Date of Issue: ${todayStr}`, 80, 680);
    ctx.fillText(`Discipline Streak: ${state.user.streak} Days Verified`, 80, 710);

    // Right block: Security ID Hash
    ctx.textAlign = "right";
    const certUID = `5AM-${state.user.id.toString().slice(-4)}-${new Date().getFullYear()}`;
    ctx.fillText(`Verification Code: ${certUID}`, width - 80, 680);
    ctx.fillText("Robin Sharma 5 AM Club Standard", width - 80, 710);

    // Center Gold Seal
    ctx.textAlign = "center";
    ctx.beginPath();
    ctx.arc(width / 2, 675, 48, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(245, 158, 11, 0.15)";
    ctx.fill();
    ctx.strokeStyle = "#fbbf24";
    ctx.lineWidth = 3;
    ctx.stroke();

    ctx.font = "bold 12px 'Outfit', sans-serif";
    ctx.fillStyle = "#fbbf24";
    ctx.fillText("★ 5 AM CLUB ★", width / 2, 665);
    ctx.fillText("VERIFIED", width / 2, 680);
    ctx.fillText("GOLD SEAL", width / 2, 695);
}

function openCertificateModal() {
    renderHDCanvasCertificate();
    const modal = document.getElementById("cert-modal");
    if (modal) {
        modal.style.display = "flex";
        sfx.victory();
        launchConfetti();
    }
}
window.openCertificateModal = openCertificateModal;

function closeCertificateModal() {
    const modal = document.getElementById("cert-modal");
    if (modal) modal.style.display = "none";
}
window.closeCertificateModal = closeCertificateModal;

function downloadCertificateHD() {
    const canvas = document.getElementById("cert-canvas");
    if (!canvas) return;

    sfx.coin();
    try {
        const dataUrl = canvas.toDataURL("image/png", 1.0);
        const link = document.createElement("a");
        const safeName = (state.user.name || "Champion").replace(/[^a-z0-9]/gi, '_');
        link.download = `The_5AM_Club_Certificate_${safeName}.png`;
        link.href = dataUrl;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showToast("🎉 Certificate downloaded in Ultra-HD .PNG!");
        triggerHapticFeedback("heavy");
    } catch (e) {
        showToast("❌ Download failed. Please take a screenshot!");
    }
}
window.downloadCertificateHD = downloadCertificateHD;

function shareCertificateStory() {
    sfx.click();
    showToast("📲 Saved! You can now post your Golden Certificate to your Stories! 🚀");
    triggerHapticFeedback("medium");
}
window.shareCertificateStory = shareCertificateStory;

// ==================== LEVEL UP CELEBRATION MODAL ====================
function triggerLevelUpCelebration(newLevel, newTitle) {
    sfx.levelUp();
    launchConfetti();

    const modal = document.getElementById("level-up-modal");
    const badge = document.getElementById("lvl-up-badge");
    const rankElem = document.getElementById("lvl-up-rank-name");
    
    if (badge) badge.textContent = `LEVEL ${newLevel}`;
    if (rankElem) rankElem.textContent = newTitle;
    if (modal) modal.style.display = "flex";
}

function closeLevelUpModal() {
    const modal = document.getElementById("level-up-modal");
    if (modal) modal.style.display = "none";
    sfx.click();
}
window.closeLevelUpModal = closeLevelUpModal;

// ==================== DYNAMIC LIVE COUNTDOWN ====================
function initLiveCountdown() {
    function updateCountdown() {
        const now = new Date();
        const target = new Date();
        
        target.setHours(5, 0, 0, 0);
        if (now >= target) {
            target.setDate(target.getDate() + 1);
        }

        const diffMs = target - now;
        const totalSecs = Math.floor(diffMs / 1000);

        const hours = Math.floor(totalSecs / 3600);
        const mins = Math.floor((totalSecs % 3600) / 60);
        const secs = totalSecs % 60;

        setElementText("time-hours", String(hours).padStart(2, '0'));
        setElementText("time-mins", String(mins).padStart(2, '0'));
        setElementText("time-secs", String(secs).padStart(2, '0'));
    }

    updateCountdown();
    setInterval(updateCountdown, 1000);
}

// ==================== 30-DAY MATRIX CALENDAR ====================
function renderCalendar() {
    const grid = document.getElementById("calendar-grid");
    if (!grid) return;
    grid.innerHTML = "";

    for (let i = 1; i <= 30; i++) {
        const tile = document.createElement("div");
        tile.className = "tile";
        tile.textContent = i;

        if (i <= state.user.streak) {
            const level = (i % 3) + 1;
            tile.classList.add(`level-${level}`);
        }
        grid.appendChild(tile);
    }
}

// ==================== ACTIONS & SMART PHOTO VERIFICATION ====================
function initActions() {
    // 1. Solo Check-In Button
    const checkinBtn = document.getElementById("btn-main-checkin");
    if (checkinBtn) {
        checkinBtn.addEventListener("click", () => {
            sfx.coin();
            const earnedCoins = Math.round(10 * state.user.multiplier);
            state.user.streak += 1;
            state.user.coins += earnedCoins;
            state.user.stamina = 100; // Morning full vitality
            state.user.tourneyPoints = (state.user.tourneyPoints || 0) + 50;
            state.user.checkedInToday = true;

            addXP(50);
            updateUI();
            renderCalendar();
            renderHDCanvasCertificate();
            launchConfetti();

            const t = I18N[state.lang] || I18N.uz;
            showToast(t.toastCheckinOk.replace("{coins}", earnedCoins));
            triggerHapticFeedback("medium");
        });
    }

    // 2. Bedtime Protocol Button (21:30)
    const bedtimeBtn = document.getElementById("btn-bedtime-sleep");
    if (bedtimeBtn) {
        bedtimeBtn.addEventListener("click", async () => {
            sfx.bedtime();
            state.user.stamina = 100;
            state.user.tourneyPoints = (state.user.tourneyPoints || 0) + 25;
            state.user.bedtimeRecordedToday = true;
            addXP(20);
            updateUI();

            if (window.Telegram?.WebApp?.initData) {
                try {
                    await fetch("/api/action/bedtime", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ initData: window.Telegram.WebApp.initData })
                    });
                } catch (e) {}
            }

            const t = I18N[state.lang] || I18N.uz;
            showToast(t.toastBedtimeOk);
            triggerHapticFeedback("medium");
        });
    }

    // 3. Photo Upload & Smart Verification with Canvas
    const uploadBtn = document.getElementById("btn-upload-photo");
    const fileInput = document.getElementById("photo-file-input");

    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener("click", () => {
            sfx.click();
            fileInput.click();
        });

        fileInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement("canvas");
                    const ctx = canvas.getContext("2d");

                    canvas.width = img.width;
                    canvas.height = img.height;
                    ctx.drawImage(img, 0, 0);

                    // Brightness & Variance Analysis
                    try {
                        const sampleW = Math.min(100, img.width);
                        const sampleH = Math.min(100, img.height);
                        const sampleCanvas = document.createElement("canvas");
                        sampleCanvas.width = sampleW;
                        sampleCanvas.height = sampleH;
                        const sampleCtx = sampleCanvas.getContext("2d");
                        sampleCtx.drawImage(img, 0, 0, sampleW, sampleH);

                        const imgData = sampleCtx.getImageData(0, 0, sampleW, sampleH).data;
                        let totalBrightness = 0;
                        const brightnessList = [];

                        for (let i = 0; i < imgData.length; i += 4) {
                            const r = imgData[i];
                            const g = imgData[i+1];
                            const b = imgData[i+2];
                            const br = 0.299 * r + 0.587 * g + 0.114 * b;
                            totalBrightness += br;
                            brightnessList.push(br);
                        }

                        const avgBrightness = totalBrightness / brightnessList.length;
                        let variance = 0;
                        for (let b of brightnessList) {
                            variance += Math.pow(b - avgBrightness, 2);
                        }
                        const stdDev = Math.sqrt(variance / brightnessList.length);

                        if (avgBrightness < 26 || stdDev < 10) {
                            const t = I18N[state.lang] || I18N.uz;
                            showToast(t.toastPhotoRejected);
                            triggerHapticFeedback("error");
                            sfx.click();
                            return;
                        }
                    } catch (err) {}

                    // Apply Official Verified Watermark Banner
                    const bannerHeight = Math.max(60, img.height * 0.12);
                    ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
                    ctx.fillRect(0, img.height - bannerHeight, img.width, bannerHeight);

                    ctx.fillStyle = "#fbbf24";
                    ctx.font = `bold ${Math.max(16, Math.floor(bannerHeight * 0.32))}px sans-serif`;
                    ctx.fillText(`✅ VERIFIED 5 AM CLUB | ${new Date().toLocaleTimeString()}`, 20, img.height - bannerHeight + (bannerHeight * 0.42));

                    ctx.fillStyle = "#ffffff";
                    ctx.font = `${Math.max(12, Math.floor(bannerHeight * 0.24))}px sans-serif`;
                    ctx.fillText(`👤 ${state.user.name} | 🔥 Streak: ${state.user.streak} Days | 🏅 ${state.user.rank}`, 20, img.height - bannerHeight + (bannerHeight * 0.8));

                    const stampedDataUrl = canvas.toDataURL("image/jpeg", 0.92);
                    const previewImg = document.getElementById("stamped-preview-img");
                    const previewContainer = document.getElementById("stamped-preview-container");

                    if (previewImg && previewContainer) {
                        previewImg.src = stampedDataUrl;
                        previewContainer.style.display = "block";
                    }

                    const photoEarned = Math.round(25 * state.user.multiplier);
                    state.user.coins += photoEarned;
                    state.user.stamina = 100;
                    state.user.photoCount = (state.user.photoCount || 0) + 1;
                    state.user.tourneyPoints = (state.user.tourneyPoints || 0) + 100;

                    addXP(100);
                    updateUI();
                    renderHDCanvasCertificate();
                    sfx.victory();
                    launchConfetti();

                    const t = I18N[state.lang] || I18N.uz;
                    showToast(t.toastPhotoOk.replace("{coins}", photoEarned));
                    triggerHapticFeedback("heavy");
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(file);
        });
    }

    // 4. Matchmaking Arena Search (Stamina check)
    const matchBtn = document.getElementById("btn-start-matchmaking");
    if (matchBtn) {
        matchBtn.addEventListener("click", () => {
            const stamina = state.user.stamina !== undefined ? state.user.stamina : 100;
            if (stamina < 20) {
                sfx.click();
                const t = I18N[state.lang] || I18N.uz;
                showToast(t.toastNoStamina);
                triggerHapticFeedback("error");
                return;
            }

            sfx.duelClash();
            state.user.stamina -= 20;
            updateUI();

            const t = I18N[state.lang] || I18N.uz;
            matchBtn.textContent = t.matchSearching;
            matchBtn.disabled = true;

            setTimeout(() => {
                setElementText("opponent-name", "Alex_Riser (Lvl 3)");
                const oppStatus = document.getElementById("opponent-status");
                if (oppStatus) {
                    oppStatus.textContent = "MATCHED 🔥";
                    oppStatus.className = "fighter-status ready";
                }
                matchBtn.textContent = t.matchFound;
                matchBtn.disabled = false;
                sfx.coin();
                showToast("🎉 Match Found! 1v1 Duel active for 50 coins & +75 Turnir Balli!");
                triggerHapticFeedback("medium");
            }, 1800);
        });
    }
}

// ==================== MARKETPLACE SYSTEM ====================
function buyItem(itemName, price) {
    const t = I18N[state.lang] || I18N.uz;
    if (state.user.coins >= price) {
        state.user.coins -= price;
        sfx.victory();

        if (itemName === "Streak Freeze") {
            state.user.freezeCount = (state.user.freezeCount || 0) + 1;
        } else if (itemName === "Lion Badge") {
            state.user.rank = "🦁 Lion Riser";
            if (!state.user.badges.includes("Lion Badge")) state.user.badges.push("Lion Badge");
        } else if (itemName === "Speed Title") {
            state.user.rank = "⚡ Speed Demon";
            if (!state.user.badges.includes("Speed Title")) state.user.badges.push("Speed Title");
        } else if (itemName === "VIP Access") {
            if (!state.user.badges.includes("VIP Mastermind")) state.user.badges.push("VIP Mastermind");
        }

        updateUI();
        showToast(t.toastBought.replace("{item}", itemName).replace("{price}", price));
        triggerHapticFeedback("medium");
    } else {
        sfx.click();
        showToast(t.toastNoCoins.replace("{price}", price));
        triggerHapticFeedback("error");
    }
}
window.buyItem = buyItem;

// ==================== CONFETTI CELEBRATION ====================
function launchConfetti() {
    const colors = ["#fbbf24", "#f59e0b", "#10b981", "#34d399", "#3b82f6", "#ffffff"];
    const container = document.body;

    for (let i = 0; i < 40; i++) {
        const conf = document.createElement("div");
        conf.className = "confetti-piece";
        conf.style.left = `${Math.random() * 100}%`;
        conf.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        conf.style.animationDuration = `${1.2 + Math.random() * 1.5}s`;
        conf.style.animationDelay = `${Math.random() * 0.2}s`;
        container.appendChild(conf);

        setTimeout(() => conf.remove(), 2800);
    }
}

// ==================== TOAST NOTIFICATION & HAPTICS ====================
function showToast(message) {
    const toast = document.getElementById("toast");
    const toastMsg = document.getElementById("toast-message");
    if (!toast || !toastMsg) return;

    toastMsg.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3200);
}

function triggerHapticFeedback(type = "medium") {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
        if (type === "error") {
            window.Telegram.WebApp.HapticFeedback.notificationOccurred("error");
        } else {
            window.Telegram.WebApp.HapticFeedback.impactOccurred(type);
        }
    }
}
