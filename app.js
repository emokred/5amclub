// ==================== THE 5 AM CLUB MINI APP ====================
// Senior Full-Stack Engineering Edition: Multi-Language, Audio FX, Confetti, Dynamic Time & LocalStorage

const I18N = {
    uz: {
        rankNovice: "🌅 Tonggi Yangi A'zo",
        rankPhoenix: "⚡ Porlayotgan Qaqnus",
        rankWarrior: "⚔️ Intizom Jangchisi",
        rankMaster: "🏆 Ertalabki Usta",
        rankLegend: "👑 5 AM Afsonasi",
        tabDashboard: "Bosh sahifa",
        tabCalendar: "Taqvim",
        tabMarket: "Bozor",
        tabArena: "Arena",
        tabRanks: "Reyting",
        windowBadge: "● JONLI OYNA",
        windowTitle: "Ertalabki Check-In Oynasi",
        hoursLabel: "Soat",
        minsLabel: "Daqiqa",
        secsLabel: "Soniya",
        btnCheckin: "SOLO CHECK-IN (+10 TANGA)",
        photoTitle: "Kunlik Foto Topshiriq",
        photoBadge: "📸 FOTO TOPSHIRIQ",
        missionText: "☕ <b>Topshiriq:</b> Tonggi kofe, choy yoki toza suv stakaningiz rasmini oling!",
        uploadBtn: "📷 Foto Isbot Yuborish (+25 Tanga)",
        verifiedStamp: "✅ VERIFIED 5 AM CLUB",
        wisdomQuote: "“Ertalabki vaqtingizga egalik qiling. Hayotingizni yuksaltiring. G'alabalar tong otmasdan yaratiladi.”",
        wisdomAuthor: "— Robin Sharma",
        calendarTitle: "📅 30 Kunlik Uyg'onish Matritsasi",
        calendarSub: "Yashil kataklar muvaffaqiyatli 5 AM uyg'onishlarini bildiradi!",
        habitTitle: "🏆 21 Kunlik Odat Maratoni",
        habitSub: "Oltin Sertifikatni ochish uchun 21 kunlik streakka erishing!",
        shopTitle: "🛒 5 AM Bozori",
        arenaTitle: "⚔️ 1v1 Uyg'onish Dueli",
        arenaSub: "50 tanga tikib, erta uyg'onish bo'yicha do'stingiz bilan bellashing!",
        matchBtn: "🎲 Tasodifiy Raqib Qidirish",
        matchSearching: "⌛ Raqib qidirilmoqda...",
        matchFound: "⚔️ Raqib topildi! Duel faol!",
        duoTitle: "🤝 Duo Combo Sherik",
        duoSub: "Sherik bilan birgalikda uyg'onib, har kuni +50 bonus tanga oling!",
        ranksTitle: "🏆 Global Shon-Sharaf Zali",
        toastCheckinOk: "⚡ Solo Check-In muvaffaqiyatli! +{coins} Tanga! 🔥",
        toastPhotoOk: "📸 Foto tasdiqlandi! +{coins} Tanga! 🚀",
        toastBought: "🎉 {item} sotib olindi ({price} Tanga)!",
        toastNoCoins: "❌ Tangalar yetarli emas! Sizga {price} tanga kerak."
    },
    ru: {
        rankNovice: "🌅 Рассветный Новичок",
        rankPhoenix: "⚡ Восходящий Феникс",
        rankWarrior: "⚔️ Воин Дисциплины",
        rankMaster: "🏆 Мастер Утра",
        rankLegend: "👑 Легенда 5 AM",
        tabDashboard: "Главная",
        tabCalendar: "Календарь",
        tabMarket: "Рынок",
        tabArena: "Арена",
        tabRanks: "Рейтинг",
        windowBadge: "● ЖИВОЕ ОКНО",
        windowTitle: "Окно Утреннего Подъема",
        hoursLabel: "Часы",
        minsLabel: "Мин",
        secsLabel: "Сек",
        btnCheckin: "СОЛО CHECK-IN (+10 МОНЕТ)",
        photoTitle: "Ежедневное Фото-Задание",
        photoBadge: "📸 ФОТО ПОДТВЕРЖДЕНИЕ",
        missionText: "☕ <b>Задание:</b> Сделайте фото утреннего кофе, чая или стакана воды!",
        uploadBtn: "📷 Загрузить Фото (+25 Монет)",
        verifiedStamp: "✅ VERIFIED 5 AM CLUB",
        wisdomQuote: "«Владейте своим утром. Поднимите свою жизнь. Победы куются до рассвета.»",
        wisdomAuthor: "— Робин Шарма",
        calendarTitle: "📅 30-Дневная Матрица Подъема",
        calendarSub: "Зеленые плитки отражают подтвержденные подъемы в 5:00 утра!",
        habitTitle: "🏆 21-Дневный Марафон Привычки",
        habitSub: "Достигните 21 дня для получения Золотого Сертификата!",
        shopTitle: "🛒 Рынок 5 AM",
        arenaTitle: "⚔️ Дуэль 1v1 на Подъем",
        arenaSub: "Поставьте 50 монет и соревнуйтесь в раннем подъеме!",
        matchBtn: "🎲 Найти Случайного Соперника",
        matchSearching: "⌛ Поиск соперника...",
        matchFound: "⚔️ Соперник найден! Дуэль активна!",
        duoTitle: "🤝 Парный Комбо Партнер",
        duoSub: "Просыпайтесь вместе с партнером и получайте +50 монет ежедневно!",
        ranksTitle: "🏆 Зал Славы 5 AM",
        toastCheckinOk: "⚡ Соло Check-In успешен! +{coins} Монет! 🔥",
        toastPhotoOk: "📸 Фото подтверждено! +{coins} Монет! 🚀",
        toastBought: "🎉 Куплено: {item} за {price} монет!",
        toastNoCoins: "❌ Недостаточно монет! Требуется {price} монет."
    },
    en: {
        rankNovice: "🌅 Dawn Novice",
        rankPhoenix: "⚡ Rising Phoenix",
        rankWarrior: "⚔️ Discipline Warrior",
        rankMaster: "🏆 Morning Master",
        rankLegend: "👑 5 AM Legend",
        tabDashboard: "Dashboard",
        tabCalendar: "Calendar",
        tabMarket: "Market",
        tabArena: "Arena",
        tabRanks: "Ranks",
        windowBadge: "● LIVE WINDOW",
        windowTitle: "Morning Check-In Window",
        hoursLabel: "Hours",
        minsLabel: "Mins",
        secsLabel: "Secs",
        btnCheckin: "SOLO CHECK-IN (+10 COINS)",
        photoTitle: "Daily Photo Mission",
        photoBadge: "📸 PHOTO PROOF",
        missionText: "☕ <b>Mission:</b> Snap a photo of your morning coffee, tea or fresh glass of water!",
        uploadBtn: "📷 Upload Photo Proof (+25 Coins)",
        verifiedStamp: "✅ VERIFIED 5 AM CLUB",
        wisdomQuote: "“Own your morning. Elevate your life. Victories are created before dawn.”",
        wisdomAuthor: "— Robin Sharma",
        calendarTitle: "📅 30-Day Wake-Up Matrix",
        calendarSub: "Green tiles represent verified 5 AM wake-ups!",
        habitTitle: "🏆 21-Day Habit Challenge",
        habitSub: "Reach a 21-day streak to unlock your Official Golden Certificate!",
        shopTitle: "🛒 5 AM Marketplace",
        arenaTitle: "⚔️ 1v1 Wake-Up Duels",
        arenaSub: "Challenge a friend or random player for a 50 coin pool!",
        matchBtn: "🎲 Find Random Matchmaking",
        matchSearching: "⌛ Searching for Partner...",
        matchFound: "⚔️ Match Found! Duel Active!",
        duoTitle: "🤝 Duo Combo Partner",
        duoSub: "Team up with a partner. Wake up together for +50 daily bonus coins!",
        ranksTitle: "🏆 Global Hall of Fame",
        toastCheckinOk: "⚡ Solo Check-In Successful! +{coins} Coins! 🔥",
        toastPhotoOk: "📸 Photo Verified! +{coins} Coins! 🚀",
        toastBought: "🎉 Purchased {item} for {price} Coins!",
        toastNoCoins: "❌ Insufficient Coins! You need {price} Coins."
    }
};

// ==================== STATE MANAGEMENT ====================
const defaultState = {
    user: {
        id: 6377617416,
        name: "Morning Champion",
        username: "champion",
        streak: 12,
        coins: 450,
        multiplier: 1.2,
        rank: "🏆 Morning Master",
        photoCount: 5,
        freezeCount: 1,
        refCount: 3,
        badges: ["Early Bird", "Photo Master"],
        checkedInToday: false
    },
    lang: "uz"
};

// Load saved state or use default
let state = (() => {
    try {
        const saved = localStorage.getItem("5amclub_state");
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
        localStorage.setItem("5amclub_state", JSON.stringify(state));
    } catch (e) {
        console.warn("Storage write error", e);
    }
}

// ==================== AUDIO SYNTHESIZER (WEB AUDIO API) ====================
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

    playTone(freq, type, duration, startDelay = 0) {
        try {
            this.init();
            if (!this.ctx) return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, this.ctx.currentTime + startDelay);
            gain.gain.setValueAtTime(0.15, this.ctx.currentTime + startDelay);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + startDelay + duration);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(this.ctx.currentTime + startDelay);
            osc.stop(this.ctx.currentTime + startDelay + duration);
        } catch (e) {
            // Audio context policy safe fallback
        }
    }

    click() {
        this.playTone(600, "sine", 0.05);
    }

    coin() {
        this.playTone(987.77, "triangle", 0.1, 0);
        this.playTone(1318.51, "triangle", 0.25, 0.08);
    }

    victory() {
        this.playTone(523.25, "triangle", 0.1, 0);
        this.playTone(659.25, "triangle", 0.1, 0.1);
        this.playTone(783.99, "triangle", 0.1, 0.2);
        this.playTone(1046.50, "triangle", 0.35, 0.3);
    }
}
const sfx = new SoundEffects();

// ==================== INITIALIZATION ====================
document.addEventListener("DOMContentLoaded", () => {
    initTelegramWebApp();
    initLanguage();
    initTabs();
    initLiveCountdown();
    renderCalendar();
    initActions();
    updateUI();
});

// ==================== TELEGRAM WEBAPP SDK ====================
function initTelegramWebApp() {
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();

        const tgUser = tg.initDataUnsafe?.user;
        if (tgUser) {
            state.user.id = tgUser.id;
            state.user.name = tgUser.first_name + (tgUser.last_name ? " " + tgUser.last_name : "");
            state.user.username = tgUser.username || "user";
            
            if (tgUser.photo_url) {
                const avatar = document.getElementById("user-avatar");
                if (avatar) avatar.src = tgUser.photo_url;
            }
        }
    }
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
        });
    });

    applyLanguage();
}

function getRankTitle(streak, lang) {
    const t = I18N[lang] || I18N.uz;
    if (streak >= 30) return t.rankLegend;
    if (streak >= 15) return t.rankMaster;
    if (streak >= 8) return t.rankWarrior;
    if (streak >= 4) return t.rankPhoenix;
    return t.rankNovice;
}

function calculateMultiplier(streak) {
    if (streak >= 30) return 2.0;
    if (streak >= 15) return 1.5;
    if (streak >= 7) return 1.2;
    return 1.0;
}

function applyLanguage() {
    const t = I18N[state.lang] || I18N.uz;

    // Navigation
    setElementText("tab-nav-dashboard", t.tabDashboard);
    setElementText("tab-nav-calendar", t.tabCalendar);
    setElementText("tab-nav-shop", t.tabMarket);
    setElementText("tab-nav-arena", t.tabArena);
    setElementText("tab-nav-ranks", t.tabRanks);

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

    // Quotes & Challenge
    setElementText("daily-quote-text", t.wisdomQuote);
    setElementText("daily-quote-author", t.wisdomAuthor);
    setElementText("title-matrix", t.calendarTitle);
    setElementText("sub-matrix", t.calendarSub);
    setElementText("title-habit", t.habitTitle);
    setElementText("sub-habit", t.habitSub);

    // Shop, Arena, Ranks
    setElementText("title-shop", t.shopTitle);
    setElementText("title-arena", t.arenaTitle);
    setElementText("sub-arena", t.arenaSub);
    setElementText("title-ranks", t.ranksTitle);
}

function setElementText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// ==================== UI UPDATE ====================
function updateUI() {
    state.user.multiplier = calculateMultiplier(state.user.streak);
    state.user.rank = getRankTitle(state.user.streak, state.lang);

    setElementText("user-name", state.user.name);
    setElementText("user-rank", state.user.rank);
    setElementText("stat-streak", state.user.streak);
    setElementText("stat-coins", state.user.coins);
    setElementText("stat-multiplier", `${state.user.multiplier}X`);
    setElementText("shop-balance-coins", `🪙 ${state.user.coins}`);

    // Update 21-Day Habit Challenge dynamic progress bar
    const progressFill = document.getElementById("cert-progress-fill");
    const progressLabel = document.getElementById("cert-progress-text");
    const progressPercent = Math.min(100, Math.round((state.user.streak / 21) * 100));
    
    if (progressFill) progressFill.style.width = `${progressPercent}%`;
    if (progressLabel) progressLabel.textContent = `${state.user.streak} / 21 Days (${progressPercent}% Complete)`;

    saveState();
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

// ==================== DYNAMIC LIVE COUNTDOWN ====================
function initLiveCountdown() {
    function updateCountdown() {
        const now = new Date();
        const target = new Date();
        
        // Target: next 05:00 AM window
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

// ==================== INTERACTIVE ACTIONS & WATERMARK ====================
function initActions() {
    // Solo Check-In Button
    const checkinBtn = document.getElementById("btn-main-checkin");
    if (checkinBtn) {
        checkinBtn.addEventListener("click", () => {
            sfx.coin();
            const earnedCoins = Math.round(10 * state.user.multiplier);
            state.user.streak += 1;
            state.user.coins += earnedCoins;
            state.user.checkedInToday = true;

            updateUI();
            renderCalendar();
            launchConfetti();

            const t = I18N[state.lang] || I18N.uz;
            showToast(t.toastCheckinOk.replace("{coins}", earnedCoins));
            triggerHapticFeedback("medium");
        });
    }

    // Photo Upload & Watermark Stamp Canvas
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

                    // Stamp Watermark Banner
                    const bannerHeight = Math.max(60, img.height * 0.12);
                    ctx.fillStyle = "rgba(15, 23, 42, 0.88)";
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
                    state.user.photoCount += 1;

                    updateUI();
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

    // Matchmaking Search Simulation
    const matchBtn = document.getElementById("btn-start-matchmaking");
    if (matchBtn) {
        matchBtn.addEventListener("click", () => {
            sfx.click();
            const t = I18N[state.lang] || I18N.uz;
            matchBtn.textContent = t.matchSearching;
            matchBtn.disabled = true;

            setTimeout(() => {
                setElementText("opponent-name", "@Riser_Samir");
                const oppStatus = document.getElementById("opponent-status");
                if (oppStatus) {
                    oppStatus.textContent = "MATCHED 🔥";
                    oppStatus.className = "fighter-status ready";
                }
                matchBtn.textContent = t.matchFound;
                matchBtn.disabled = false;
                sfx.coin();
                showToast("🎉 Match Found! 1v1 Duel active for 50 coins!");
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
            state.user.freezeCount += 1;
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

    for (let i = 0; i < 35; i++) {
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
