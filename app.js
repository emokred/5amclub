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
        tabWheel: "G'ildirak",
        tabSquad: "Guruhlar",
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
        textShareStory: "Story'ga Joylash",
        badgeMultiverse: "🌌 MULTIVERSE REALM",
        titleMultiverse: "Multiverse Realm & Engine",
        descMultiverse: "Tanlangan olamga mos ravishda Mini App dizayni, unvonlar va audio effektlar o'zgaradi!",
        labelRoleplayToggle: "🎭 Roleplay Mode",
        descRoleplayToggle: "RPG hikoya unvonlari, olam quiplari & lore",
        labelInteractiveToggle: "🎮 Interactive Arena Mode",
        descInteractiveToggle: "Jonli audio synth FX, zarralar & arena vizuallari",
        badgeMatrixGoal: "🎯 TARGET GOAL MATRIX",
        titleTargetMatrix: "Target Goal Matrix Tracker",
        descTargetMatrix: "Intizom maqsadini tanlang va kunlik uyg'onish natijangizni real vaqtda kuzatib boring!",
        badgeWheelStatus: "🎡 KUNLIK OMAD G'ILDIRAGI",
        titleWheelHeader: "Daily Wheel of Fortune",
        descWheelHeader: "Har kuni omad g'ildiragini aylantiring va tangalar, XP va Streak Freeze qalqonlarini yutib oling!",
        btnSpin: "G'ILDIRAGNI AYLANTIRISH (BEPUL)",
        titleWheelPrizes: "🎁 Sovrinlar Jamg'armasi",
        badgeSquadStatus: "🛡️ MENING GURUHIM",
        titleMySquad: "Squad Dashboard",
        badgeTopSquads: "🏆 GURUHLAR REYTINGI",
        titleTopSquads: "Top Discipline Guilds",
        descTopSquads: "Ertalabki uyg'onish intizomi va umumiy streak bo'yicha eng kuchli guruhlar!",
        badgeCreateSquad: "🛡️ YANGI GURUH",
        titleCreateSquad: "Yangi Squad Tuzish",
        labelSquadName: "Squad Nomi:",
        labelSquadTag: "Squad Tagi (3-5 harf):",
        labelSquadMotto: "Shior (Motto):",
        textBtnCreateSquad: "Squad Tuzish (100 Coins)",
        labelBadgeCondition: "Ochish talabi:",
        textBadgeModalClose: "Tushunarli 👍",
        rarityCommon: "Oddiy",
        rarityUncommon: "O'rtacha",
        rarityRare: "Noyob",
        rarityLegendary: "Afsonaviy"
    },
    ru: {
        rankNovice: "🌅 Рассветный Новичок",
        rankPhoenix: "⚡ Восходящий Феникс",
        rankWarrior: "⚔️ Воин Дисциплины",
        rankMaster: "🏆 Мастер Утра",
        rankLegend: "👑 Легенда 5 AM",
        tabDashboard: "Главная",
        tabCalendar: "Календарь",
        tabWheel: "Колесо",
        tabSquad: "Кланы",
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
        textShareStory: "В Сторис",
        badgeMultiverse: "🌌 МУЛЬТИВСЕЛЕННАЯ",
        titleMultiverse: "Мультивселенная & Движок",
        descMultiverse: "В зависимости от выбранного мира меняются дизайн, звания и аудиоэффекты!",
        labelRoleplayToggle: "🎭 Режим Roleplay",
        descRoleplayToggle: "RPG титулы, сюжетная история и лор миров",
        labelInteractiveToggle: "🎮 Интерактивная Арена",
        descInteractiveToggle: "Живые синтез-аудио FX, частицы и арена-визуал",
        badgeMatrixGoal: "🎯 МАТРИЦА ЦЕЛЕЙ",
        titleTargetMatrix: "Трекер Матрицы Целей",
        descTargetMatrix: "Выберите целевой марафон дисциплины и отслеживайте прогресс подъема!",
        badgeWheelStatus: "🎡 ЕЖЕДНЕВНОЕ КОЛЕСО УДАЧИ",
        titleWheelHeader: "Ежедневное Колесо Удачи",
        descWheelHeader: "Крутите колесо удачи каждый день и выигрывайте монеты, XP и защитные щиты!",
        btnSpin: "КРУТИТЬ КОЛЕСО (БЕСПЛАТНО)",
        titleWheelPrizes: "🎁 Призовой Фонд",
        badgeSquadStatus: "🛡️ МОЙ КЛАН",
        titleMySquad: "Дашборд Клана",
        badgeTopSquads: "🏆 РЕЙТИНГ КЛАНОВ",
        titleTopSquads: "Лучшие Гильдии Дисциплины",
        descTopSquads: "Самые сильные кланы по дисциплине утреннего подъема и общему стрику!",
        badgeCreateSquad: "🛡️ НОВЫЙ КЛАН",
        titleCreateSquad: "Создать Новый Клан",
        labelSquadName: "Название Клана:",
        labelSquadTag: "Тег Клана (3-5 букв):",
        labelSquadMotto: "Девиз Клана:",
        textBtnCreateSquad: "Создать Клан (100 Монет)",
        labelBadgeCondition: "Условие разблокировки:",
        textBadgeModalClose: "Понятно 👍",
        rarityCommon: "Обычный",
        rarityUncommon: "Необычный",
        rarityRare: "Редкий",
        rarityLegendary: "Легендарный"
    },
    en: {
        rankNovice: "🌅 Dawn Novice",
        rankPhoenix: "⚡ Rising Phoenix",
        rankWarrior: "⚔️ Discipline Warrior",
        rankMaster: "🏆 Morning Master",
        rankLegend: "👑 5 AM Legend",
        tabDashboard: "Dashboard",
        tabCalendar: "Calendar",
        tabWheel: "Wheel",
        tabSquad: "Squads",
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
        textShareStory: "Share on Story",
        badgeMultiverse: "🌌 MULTIVERSE REALM",
        titleMultiverse: "Multiverse Realm & Engine",
        descMultiverse: "Themes, titles, and audio effects adapt dynamic UI to your chosen universe!",
        labelRoleplayToggle: "🎭 Roleplay Mode",
        descRoleplayToggle: "RPG lore titles, universe quips & story narration",
        labelInteractiveToggle: "🎮 Interactive Arena Mode",
        descInteractiveToggle: "Live audio synth FX, particle glow & arena visual engine",
        badgeMatrixGoal: "🎯 TARGET GOAL MATRIX",
        titleTargetMatrix: "Target Goal Matrix Tracker",
        descTargetMatrix: "Choose your discipline target goal and track daily wake-up progress in real time!",
        badgeWheelStatus: "🎡 DAILY WHEEL OF FORTUNE",
        titleWheelHeader: "Daily Wheel of Fortune",
        descWheelHeader: "Spin the wheel of fortune daily to win coins, XP, and streak freeze shields!",
        btnSpin: "SPIN THE WHEEL (FREE)",
        titleWheelPrizes: "🎁 Prize Pool Showcase",
        badgeSquadStatus: "🛡️ MY SQUAD",
        titleMySquad: "Squad Dashboard",
        badgeTopSquads: "🏆 TOP SQUADS",
        titleTopSquads: "Top Discipline Guilds",
        descTopSquads: "Top performing squads ranked by total morning discipline and streak!",
        badgeCreateSquad: "🛡️ NEW SQUAD",
        titleCreateSquad: "Create New Squad",
        labelSquadName: "Squad Name:",
        labelSquadTag: "Squad Tag (3-5 chars):",
        labelSquadMotto: "Squad Motto:",
        textBtnCreateSquad: "Create Squad (100 Coins)",
        labelBadgeCondition: "Unlock Condition:",
        textBadgeModalClose: "Got It 👍",
        rarityCommon: "Common",
        rarityUncommon: "Uncommon",
        rarityRare: "Rare",
        rarityLegendary: "Legendary"
    }
};

const MULTIVERSE_REALM_TITLES = {
    marvel: {
        badge: "🦸 Quantum Avengers",
        quip: "Avengers Assemble at 5 AM! Quantum energy surges through your veins! ⚡",
        ranks: {
            uz: [[1, "🦸 Kvant Shogird"], [5, "⚡ Qasaskor Jangchi"], [10, "🛡️ Vibranium Titan"], [20, "👑 Koinot Himoyachisi"]],
            ru: [[1, "🦸 Квантовый Ученик"], [5, "⚡ Воин-Мститель"], [10, "🛡️ Вибраниумовый Титан"], [20, "👑 Защитник Вселенной"]],
            en: [[1, "🦸 Quantum Initiate"], [5, "⚡ Avenger Warrior"], [10, "🛡️ Vibranium Titan"], [20, "👑 Universe Defender"]]
        }
    },
    samurai: {
        badge: "🗡️ Bushido Sunrise",
        quip: "The blade of discipline cuts down morning sleepiness! Bushido Way activated! ⚔️",
        ranks: {
            uz: [[1, "🗡️ Ronin Shogird"], [5, "⚔️ Bushido Jangchisi"], [10, "🏯 Katana Master"], [20, "👑 Shogun Afsonasi"]],
            ru: [[1, "🗡️ Ученик-Ронин"], [5, "⚔️ Воин Бусидо"], [10, "🏯 Мастер Катаны"], [20, "👑 Легендарный Сёгун"]],
            en: [[1, "🗡️ Ronin Initiate"], [5, "⚔️ Bushido Warrior"], [10, "🏯 Katana Master"], [20, "👑 Legendary Shogun"]]
        }
    },
    feudal: {
        badge: "🏯 Shogun Era",
        quip: "By order of the Emperor! The dawn belongs to the honorable Shogun Clan! 🏯",
        ranks: {
            uz: [[1, "🏯 Saroy Posboni"], [5, "🥷 Shinobi Sobiq"], [10, "🏯 Imperiya Masteri"], [20, "👑 Buyuk Shogun"]],
            ru: [[1, "🏯 Страж Дворца"], [5, "🥷 Мастер-Шиноби"], [10, "🏯 Имперский Мастер"], [20, "👑 Великий Сёгун"]],
            en: [[1, "🏯 Palace Guard"], [5, "🥷 Shinobi Master"], [10, "🏯 Imperial Master"], [20, "👑 Grand Shogun"]]
        }
    },
    mafia: {
        badge: "🎩 Don's Syndicate",
        quip: "An offer the pillow couldn't refuse! Welcome to the Dawn Syndicate! 🎩",
        ranks: {
            uz: [[1, "🎩 Sindikat A'zosi"], [5, "🔫 Caporegime"], [10, "💼 Consigliere"], [20, "👑 Godfather 5 AM"]],
            ru: [[1, "🎩 Член Синдиката"], [5, "🔫 Капореджиме"], [10, "💼 Консильери"], [20, "👑 Дон 5 AM"]],
            en: [[1, "🎩 Syndicate Associate"], [5, "🔫 Caporegime"], [10, "💼 Consigliere"], [20, "👑 Godfather 5 AM"]]
        }
    },
    cyberpunk: {
        badge: "⚡ Neon 2077",
        quip: "Neural wake-up sequence complete! Cybernetic upgrades active! ⚡",
        ranks: {
            uz: [[1, "⚡ Neon Shogird"], [5, "🔌 Netrunner"], [10, "🦾 Cyber Samurai"], [20, "👑 Cyberpunk Afsonasi"]],
            ru: [[1, "⚡ Неоновый Ученик"], [5, "🔌 Нетраннер"], [10, "🦾 Кибер-Самурай"], [20, "👑 Легенда 2077"]],
            en: [[1, "⚡ Neon Initiate"], [5, "🔌 Netrunner"], [10, "🦾 Cyber Samurai"], [20, "👑 Legend of 2077"]]
        }
    },
    olympus: {
        badge: "🏛️ Zeus Dawn",
        quip: "Zeus strikes sleep with golden lightning! Mount Olympus honors your awakening! 🏛️",
        ranks: {
            uz: [[1, "🏛️ Olimpiya Qahramoni"], [5, "⚡ Zevs Yashini"], [10, "⚔️ Sparta Jangchisi"], [20, "👑 Xudolar Qiroli"]],
            ru: [[1, "🏛️ Герой Олимпа"], [5, "⚡ Молния Зевса"], [10, "⚔️ Спартанский Воин"], [20, "👑 Владыка Олимпа"]],
            en: [[1, "🏛️ Olympus Hero"], [5, "⚡ Zeus Lightning"], [10, "⚔️ Spartan Warrior"], [20, "👑 Sovereign of Olympus"]]
        }
    },
    anime: {
        badge: "🥷 Konoha & Saiyans",
        quip: "Dattebayo! Ninja Way wake-up sequence activated! Kamehameha morning boost! 🥷⚡",
        ranks: {
            uz: [[1, "🥷 Konoha Ninjasi"], [5, "🏴‍☠️ Pirate Captain (Luffy)"], [10, "⚡ Hokage (Naruto)"], [20, "💥 Super Saiyan (Goku)"], [35, "👑 Saitama One-Punch"]],
            ru: [[1, "🥷 Ниндзя Конохи"], [5, "🏴‍☠️ Капитан Пиратов (Луффи)"], [10, "⚡ Хокаге (Наруто)"], [20, "💥 Супер Сайян (Гоку)"], [35, "👑 Сайтама One-Punch"]],
            en: [[1, "🥷 Leaf Ninja (Naruto)"], [5, "🏴‍☠️ Pirate Captain (Luffy)"], [10, "⚡ Shadow Hokage"], [20, "💥 Super Saiyan (Goku)"], [35, "👑 Saitama One-Punch"]]
        }
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
        bedtimeRecordedToday: false,
        active_universe: "marvel",
        roleplay_enabled: true,
        interactive_enabled: true,
        target_goal: "21",
        lastWheelSpinDate: null,
        squad: {
            id: "sq_1",
            name: "Dawn Titans",
            tag: "TITAN",
            motto: "Birgalikda 5 AM ga egalik qilamiz!",
            streak: 142,
            membersCount: 12,
            role: "Leader"
        }
    },
    soundEnabled: true,
    lang: "uz"
};

let state = (() => {
    try {
        const saved = localStorage.getItem("5amclub_state_v2");
        if (saved) {
            const parsed = JSON.parse(saved);
            if (!parsed.user) parsed.user = {};
            if (!parsed.user.active_universe) parsed.user.active_universe = "marvel";
            if (parsed.user.roleplay_enabled === undefined) parsed.user.roleplay_enabled = true;
            if (parsed.user.interactive_enabled === undefined) parsed.user.interactive_enabled = true;
            if (!parsed.user.target_goal) parsed.user.target_goal = "21";
            if (parsed.user.squad === undefined) parsed.user.squad = defaultState.user.squad;
            return parsed;
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
        try {
            if (!this.ctx) {
                const AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (AudioCtx) this.ctx = new AudioCtx();
            }
            if (this.ctx && this.ctx.state === "suspended") {
                this.ctx.resume();
            }
        } catch (e) {}
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

    wheelTick() {
        this.playTone(800 + Math.random() * 200, "triangle", 0.03, 0, 0.08);
    }

    wheelWin() {
        this.playTone(523.25, "sine", 0.1, 0, 0.15);
        this.playTone(659.25, "sine", 0.1, 0.08, 0.15);
        this.playTone(783.99, "sine", 0.1, 0.16, 0.15);
        this.playTone(1046.50, "sine", 0.3, 0.24, 0.22);
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

    realmSwitch() {
        if (state.user && !state.user.interactive_enabled) return;
        this.playTone(523.25, "sawtooth", 0.06, 0, 0.15);
        this.playTone(659.25, "sawtooth", 0.08, 0.05, 0.18);
        this.playTone(783.99, "sawtooth", 0.12, 0.11, 0.2);
    }
}
const sfx = new SoundEffects();
window.addEventListener("touchstart", () => { sfx.init(); }, { passive: true });
window.addEventListener("click", () => { sfx.init(); }, { passive: true });

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

// ==================== MULTIVERSE DYNAMIC UI ENGINE & TARGET GOAL MATRIX ====================
function applyMultiverseTheme(realm) {
    const validRealms = ["marvel", "samurai", "feudal", "mafia", "cyberpunk", "olympus", "anime"];
    if (!validRealms.includes(realm)) realm = "marvel";

    state.user.active_universe = realm;

    validRealms.forEach(r => document.body.classList.remove(`theme-${r}`));
    document.body.classList.add(`theme-${realm}`);

    document.querySelectorAll(".realm-card").forEach(card => {
        if (card.getAttribute("data-realm") === realm) {
            card.classList.add("active");
        } else {
            card.classList.remove("active");
        }
    });

    updateMultiverseRoleplayHUD();
}

function updateMultiverseRoleplayHUD() {
    const realm = state.user.active_universe || "marvel";
    const realmData = MULTIVERSE_REALM_TITLES[realm] || MULTIVERSE_REALM_TITLES.marvel;
    const userRankEl = document.getElementById("user-rank");

    if (userRankEl) {
        if (state.user.roleplay_enabled) {
            const lang = state.lang || "uz";
            const ranksList = realmData.ranks[lang] || realmData.ranks.uz;
            let activeTitle = ranksList[0][1];
            const lvl = state.user.level || 1;
            for (const [minLvl, title] of ranksList) {
                if (lvl >= minLvl) activeTitle = title;
            }
            userRankEl.textContent = activeTitle;
        } else {
            userRankEl.textContent = getRankTitle(state.user.streak, state.lang);
        }
    }
}

function initMultiverseEngine() {
    const roleplayCheckbox = document.getElementById("roleplay-toggle-checkbox");
    const interactiveCheckbox = document.getElementById("interactive-toggle-checkbox");

    if (roleplayCheckbox) {
        roleplayCheckbox.checked = state.user.roleplay_enabled !== false;
        roleplayCheckbox.addEventListener("change", (e) => {
            state.user.roleplay_enabled = e.target.checked;
            saveState();
            updateUI();
            syncMultiverseStateWithBackend();
            showToast(state.user.roleplay_enabled ? "🎭 Roleplay Mode Enabled!" : "🎭 Roleplay Mode Disabled");
        });
    }

    if (interactiveCheckbox) {
        interactiveCheckbox.checked = state.user.interactive_enabled !== false;
        interactiveCheckbox.addEventListener("change", (e) => {
            state.user.interactive_enabled = e.target.checked;
            saveState();
            syncMultiverseStateWithBackend();
            showToast(state.user.interactive_enabled ? "🎮 Interactive Arena FX Enabled!" : "🎮 Interactive Arena FX Muted");
        });
    }

    const realmCards = document.querySelectorAll(".realm-card");
    realmCards.forEach(card => {
        card.addEventListener("click", () => {
            const targetRealm = card.getAttribute("data-realm");
            if (!targetRealm) return;
            sfx.realmSwitch();
            applyMultiverseTheme(targetRealm);
            saveState();
            syncMultiverseStateWithBackend();
            
            const realmName = targetRealm.toUpperCase();
            showToast(`🌌 Multiverse Realm Switched: ${realmName}!`);
            triggerHapticFeedback("medium");
        });
    });
}

function initTargetGoalMatrix() {
    const goalBtns = document.querySelectorAll(".goal-btn");
    goalBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.getAttribute("data-goal");
            if (!target) return;
            sfx.click();
            state.user.target_goal = String(target);
            saveState();
            renderTargetGoalMatrix();
            syncMultiverseStateWithBackend();
            showToast(`🎯 Target Goal set to ${target} Days!`);
            triggerHapticFeedback("light");
        });
    });
}

function renderTargetGoalMatrix() {
    const currentGoal = parseInt(state.user.target_goal || "21", 10);
    const streak = state.user.streak || 0;

    document.querySelectorAll(".goal-btn").forEach(btn => {
        const g = parseInt(btn.getAttribute("data-goal"), 10);
        if (g === currentGoal) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    const ratioText = document.getElementById("matrix-ratio-text");
    const percentageText = document.getElementById("matrix-percentage-text");
    const progressFill = document.getElementById("matrix-progress-fill");
    const daysLeftText = document.getElementById("matrix-days-left-text");
    const milestoneBadge = document.getElementById("matrix-milestone-badge");

    const pct = Math.min(100, Math.round((streak / currentGoal) * 100));
    const daysLeft = Math.max(0, currentGoal - streak);

    if (ratioText) ratioText.textContent = `${streak} / ${currentGoal} Days`;
    if (percentageText) percentageText.textContent = `${pct}% Completed`;
    if (progressFill) progressFill.style.width = `${pct}%`;

    const lang = state.lang || "uz";
    const daysLeftLabel = {
        uz: `⏳ ${daysLeft} kun qoldi`,
        ru: `⏳ Осталось ${daysLeft} дн.`,
        en: `⏳ ${daysLeft} day(s) left`
    };
    if (daysLeftText) daysLeftText.textContent = daysLeftLabel[lang] || daysLeftLabel.uz;

    let milestone = "🏆 Standard Goal";
    if (currentGoal === 7) milestone = "⚡ 7-Day Sprint";
    else if (currentGoal === 21) milestone = "🏆 21-Day Gold Cert";
    else if (currentGoal === 66) milestone = "🌌 66-Day Transformation";
    else if (currentGoal === 100) milestone = "👑 100-Day Centurion Legend";

    if (milestoneBadge) milestoneBadge.textContent = milestone;
}

async function syncMultiverseStateWithBackend() {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
        try {
            await fetch("/api/auth/validate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    initData: window.Telegram.WebApp.initData,
                    active_universe: state.user.active_universe,
                    roleplay_enabled: state.user.roleplay_enabled,
                    interactive_enabled: state.user.interactive_enabled,
                    target_goal: state.user.target_goal
                })
            });
        } catch (e) {
            console.warn("Backend sync warning:", e);
        }
    }
}

// ==================== INITIALIZATION ====================
document.addEventListener("DOMContentLoaded", () => {
    initTelegramWebApp();
    initSoundToggle();
    initLanguage();
    initTabs();
    initLiveCountdown();
    initMultiverseEngine();
    initTargetGoalMatrix();
    applyMultiverseTheme(state.user.active_universe || "marvel");
    renderTargetGoalMatrix();
    renderCalendar();
    renderInventory();
    renderLeaderboard();
    renderWheelCanvas(0);
    renderSquadsTab();
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

                        if (data.user.active_universe) state.user.active_universe = data.user.active_universe;
                        if (data.user.roleplay_enabled !== undefined) state.user.roleplay_enabled = data.user.roleplay_enabled;
                        if (data.user.interactive_enabled !== undefined) state.user.interactive_enabled = data.user.interactive_enabled;
                        if (data.user.target_goal) state.user.target_goal = String(data.user.target_goal);
                        
                        applyMultiverseTheme(state.user.active_universe);
                        renderTargetGoalMatrix();
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
    setElementText("tab-nav-wheel", t.tabWheel);
    setElementText("tab-nav-squad", t.tabSquad);
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

    // Wheel Tab
    setElementText("badge-wheel-status", t.badgeWheelStatus);
    setElementText("title-wheel-header", t.titleWheelHeader);
    setElementText("desc-wheel-header", t.descWheelHeader);
    setElementText("text-btn-spin", t.btnSpin);
    setElementText("title-wheel-prizes", t.titleWheelPrizes);
    setElementText("rarity-common-1", t.rarityCommon);
    setElementText("rarity-common-2", t.rarityCommon);
    setElementText("rarity-common-3", t.rarityCommon);
    setElementText("rarity-common-4", t.rarityCommon);
    setElementText("rarity-uncommon-1", t.rarityUncommon);
    setElementText("rarity-rare-1", t.rarityRare);
    setElementText("rarity-rare-2", t.rarityRare);
    setElementText("rarity-legendary-1", t.rarityLegendary);

    // Squad Tab & Modal
    setElementText("badge-squad-status", t.badgeSquadStatus);
    setElementText("title-my-squad", t.titleMySquad);
    setElementText("badge-top-squads", t.badgeTopSquads);
    setElementText("title-top-squads", t.titleTopSquads);
    setElementText("desc-top-squads", t.descTopSquads);
    setElementText("badge-create-squad", t.badgeCreateSquad);
    setElementText("title-create-squad", t.titleCreateSquad);
    setElementText("label-squad-name", t.labelSquadName);
    setElementText("label-squad-tag", t.labelSquadTag);
    setElementText("label-squad-motto", t.labelSquadMotto);
    setElementText("text-btn-create-squad", t.textBtnCreateSquad);

    // Badge Modal
    setElementText("label-badge-condition", t.labelBadgeCondition);
    setElementText("text-badge-modal-close", t.textBadgeModalClose);

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

    // Multiverse & Matrix Tracker Labels
    setElementText("badge-multiverse", t.badgeMultiverse);
    setElementText("title-multiverse", t.titleMultiverse);
    setElementText("desc-multiverse", t.descMultiverse);
    setElementText("label-roleplay-toggle", t.labelRoleplayToggle);
    setElementText("desc-roleplay-toggle", t.descRoleplayToggle);
    setElementText("label-interactive-toggle", t.labelInteractiveToggle);
    setElementText("desc-interactive-toggle", t.descInteractiveToggle);
    setElementText("badge-matrix-goal", t.badgeMatrixGoal);
    setElementText("title-target-matrix", t.titleTargetMatrix);
    setElementText("desc-target-matrix", t.descTargetMatrix);

    if (typeof renderSquadsTab === "function") renderSquadsTab();
    if (typeof renderWheelCanvas === "function") renderWheelCanvas(wheelCurrentAngle);
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

    // Update Target Goal Matrix & Roleplay HUD
    if (typeof renderTargetGoalMatrix === "function") renderTargetGoalMatrix();
    if (typeof updateMultiverseRoleplayHUD === "function") updateMultiverseRoleplayHUD();

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
        btn.addEventListener("click", (e) => {
            try { sfx.click(); } catch(err) {}
            const targetTab = btn.getAttribute("data-tab");

            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const targetContent = document.getElementById(targetTab);
            if (targetContent) targetContent.classList.add("active");

            try { triggerHapticFeedback("light"); } catch(err) {}
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
    if (cabinet && typeof BADGES_DATABASE !== "undefined") {
        const lang = state.lang || "uz";
        cabinet.innerHTML = BADGES_DATABASE.map(b => {
            const unlocked = b.current(state.user) >= b.target;
            const bName = b.name[lang] || b.name.uz;
            return `
                <div class="badge-card ${unlocked ? 'unlocked' : 'locked'}" onclick="openBadgeModal('${b.id}')">
                    <span class="b-icon">${b.icon}</span>
                    <span class="b-name">${bName}</span>
                    <small class="b-status">${unlocked ? '✅ Unlocked' : b.req}</small>
                </div>
            `;
        }).join("");
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
        checkinBtn.addEventListener("click", async () => {
            const todayStr = new Date().toISOString().split("T")[0];
            if (state.user.lastCheckinDate === todayStr || state.user.checkedInToday) {
                sfx.click();
                showToast("⚠️ Siz bugun allaqachon check-in qildingiz! Ertagacha! 🌅");
                return;
            }

            if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
                try {
                    const res = await fetch("/api/action/checkin", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ initData: window.Telegram.WebApp.initData })
                    });
                    const data = await res.json();
                    if (data.status === "not_in_window") {
                        sfx.click();
                        showToast(`⚠️ ${data.message || "Hozir check-in vaqti emas!"}`);
                        return;
                    } else if (data.status === "already") {
                        sfx.click();
                        showToast("⚠️ Siz bugun allaqachon check-in qildingiz! Ertagacha! 🌅");
                        state.user.lastCheckinDate = todayStr;
                        state.user.checkedInToday = true;
                        saveState();
                        return;
                    } else if (data.status === "ok" && data.user) {
                        sfx.coin();
                        state.user.streak = data.user.streak;
                        state.user.coins = data.user.coins;
                        state.user.xp = data.user.xp;
                        state.user.level = data.user.level;
                        state.user.stamina = 100;
                        state.user.lastCheckinDate = todayStr;
                        state.user.checkedInToday = true;
                        
                        showToast(`⚡ Check-In Muvaffaqiyatli! +${data.user.coins_earned} Coin, +${data.user.xp_earned} XP 🎉`);
                        updateUI();
                        renderCalendar();
                        renderHDCanvasCertificate();
                        launchConfetti();
                        triggerHapticFeedback("medium");
                        return;
                    }
                } catch (e) {
                    console.warn("Backend checkin offline, using local verification:", e);
                }
            }

            sfx.coin();
            const earnedCoins = Math.round(10 * state.user.multiplier);
            state.user.streak += 1;
            state.user.coins += earnedCoins;
            state.user.stamina = 100;
            state.user.tourneyPoints = (state.user.tourneyPoints || 0) + 50;
            state.user.lastCheckinDate = todayStr;
            state.user.checkedInToday = true;

            addXP(50);
            updateUI();
            renderCalendar();
            renderHDCanvasCertificate();
            launchConfetti();
            triggerHapticFeedback("medium");
            showToast(`⚡ Check-In Muvaffaqiyatli! (+${earnedCoins} Tanga, +50 XP) 🎉`);
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

// ==================== WHEEL OF FORTUNE ENGINE ====================
const WHEEL_SEGMENTS = [
    { label: "+15 Coins", icon: "🪙", type: "coins", val: 15, color: "#f59e0b", rarity: "common" },
    { label: "+50 XP", icon: "⚡", type: "xp", val: 50, color: "#10b981", rarity: "common" },
    { label: "Shield 🛡️", icon: "🛡️", type: "shield", val: 1, color: "#3b82f6", rarity: "rare" },
    { label: "+30 Coins", icon: "🪙", type: "coins", val: 30, color: "#d97706", rarity: "uncommon" },
    { label: "+100 XP", icon: "⚡", type: "xp", val: 100, color: "#8b5cf6", rarity: "rare" },
    { label: "+5 Coins", icon: "🪙", type: "coins", val: 5, color: "#f59e0b", rarity: "common" },
    { label: "+20 XP", icon: "⚡", type: "xp", val: 20, color: "#10b981", rarity: "common" },
    { label: "Jackpot 👑", icon: "👑", type: "jackpot", val: 100, color: "#ef4444", rarity: "legendary" }
];

let wheelCurrentAngle = 0;
let isSpinningWheel = false;

function renderWheelCanvas(angle = 0) {
    const canvas = document.getElementById("wheel-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const size = canvas.width;
    const center = size / 2;
    const radius = center - 12;
    const sliceAngle = (Math.PI * 2) / WHEEL_SEGMENTS.length;

    ctx.clearRect(0, 0, size, size);

    ctx.save();
    ctx.translate(center, center);
    ctx.rotate(angle);

    // Draw outer ring
    ctx.beginPath();
    ctx.arc(0, 0, radius + 8, 0, Math.PI * 2);
    ctx.fillStyle = "#0f172a";
    ctx.fill();
    ctx.strokeStyle = "#fbbf24";
    ctx.lineWidth = 6;
    ctx.stroke();

    // Draw slices
    WHEEL_SEGMENTS.forEach((seg, i) => {
        const startAngle = i * sliceAngle;
        const endAngle = startAngle + sliceAngle;

        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.arc(0, 0, radius, startAngle, endAngle);
        ctx.closePath();

        const segGrad = ctx.createRadialGradient(0, 0, 10, 0, 0, radius);
        if (i % 2 === 0) {
            segGrad.addColorStop(0, "#1e293b");
            segGrad.addColorStop(1, "#0f172a");
        } else {
            segGrad.addColorStop(0, "#334155");
            segGrad.addColorStop(1, "#1e293b");
        }
        ctx.fillStyle = segGrad;
        ctx.fill();

        ctx.strokeStyle = "rgba(251, 191, 36, 0.35)";
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.save();
        ctx.rotate(startAngle + sliceAngle / 2);
        ctx.textAlign = "right";
        ctx.fillStyle = seg.color || "#ffffff";
        ctx.font = "bold 13px 'Outfit', sans-serif";
        ctx.fillText(`${seg.icon} ${seg.label}`, radius - 20, 5);
        ctx.restore();
    });

    // Draw center hub
    ctx.beginPath();
    ctx.arc(0, 0, 32, 0, Math.PI * 2);
    ctx.fillStyle = "#fbbf24";
    ctx.fill();
    ctx.strokeStyle = "#090d16";
    ctx.lineWidth = 4;
    ctx.stroke();

    ctx.fillStyle = "#090d16";
    ctx.font = "bold 16px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("⭐", 0, 1);

    ctx.restore();
}

function spinWheel() {
    if (isSpinningWheel) return;

    const todayStr = new Date().toISOString().split("T")[0];
    if (state.user.lastWheelSpinDate === todayStr) {
        sfx.click();
        const msg = state.lang === "uz" 
            ? "❌ Siz bugungi bepul imkoniyatingizdan foydalandingiz! Ertaga yana keling!" 
            : (state.lang === "ru" ? "❌ Вы уже использовали бесплатное вращение сегодня! Приходите завтра!" : "❌ You have already used your free spin today! Come back tomorrow!");
        showToast(msg);
        triggerHapticFeedback("error");
        return;
    }

    isSpinningWheel = true;
    const btn = document.getElementById("btn-spin-wheel");
    if (btn) btn.disabled = true;

    const spinRotations = 6 + Math.floor(Math.random() * 4);
    const targetSliceIndex = Math.floor(Math.random() * WHEEL_SEGMENTS.length);
    const sliceArc = (Math.PI * 2) / WHEEL_SEGMENTS.length;
    const targetAngleOffset = (Math.PI * 2) - (targetSliceIndex * sliceArc + sliceArc / 2) - (Math.PI / 2);
    const totalRotation = spinRotations * (Math.PI * 2) + targetAngleOffset;

    const duration = 4500;
    const startTime = performance.now();
    const startAngle = wheelCurrentAngle % (Math.PI * 2);
    let lastTickSlice = -1;

    function animateSpin(now) {
        const elapsed = now - startTime;
        const progress = Math.min(1, elapsed / duration);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        wheelCurrentAngle = startAngle + easeOut * (totalRotation - startAngle);

        renderWheelCanvas(wheelCurrentAngle);

        const normalizedAngle = (2 * Math.PI - (wheelCurrentAngle + Math.PI / 2) % (2 * Math.PI)) % (2 * Math.PI);
        const currentSlice = Math.floor(normalizedAngle / sliceArc) % WHEEL_SEGMENTS.length;
        if (currentSlice !== lastTickSlice) {
            sfx.wheelTick();
            triggerHapticFeedback("light");
            lastTickSlice = currentSlice;
        }

        if (progress < 1) {
            requestAnimationFrame(animateSpin);
        } else {
            isSpinningWheel = false;
            if (btn) btn.disabled = false;
            state.user.lastWheelSpinDate = todayStr;
            saveState();

            const prize = WHEEL_SEGMENTS[targetSliceIndex];
            applyWheelPrize(prize);
        }
    }

    requestAnimationFrame(animateSpin);
}
window.spinWheel = spinWheel;

function applyWheelPrize(prize) {
    if (prize.type === "coins" || prize.type === "jackpot") {
        state.user.coins += prize.val;
    } else if (prize.type === "xp") {
        addXP(prize.val);
    } else if (prize.type === "shield") {
        state.user.freezeCount = (state.user.freezeCount || 0) + prize.val;
    }

    updateUI();
    renderInventory();
    sfx.wheelWin();
    launchConfetti();
    triggerHapticFeedback("heavy");

    const statusEl = document.getElementById("wheel-status-text");
    if (statusEl) {
        const spunMsg = state.lang === "uz" ? "✅ Bugungi bepul aylantirish ishlatildi!" : (state.lang === "ru" ? "✅ Использовано бесплатное вращение!" : "✅ Free spin used today!");
        statusEl.textContent = spunMsg;
    }

    const winTitle = state.lang === "uz" ? "🎉 G'ALABA!" : (state.lang === "ru" ? "🎉 ПОБЕДА!" : "🎉 WINNER!");
    showToast(`${winTitle} ${prize.icon} ${prize.label}!`);
}

// ==================== SQUAD / GUILD CLAN SYSTEM ====================
const TOP_SQUADS_DATA = [
    { id: "sq_1", name: "Dawn Titans", tag: "TITAN", streak: 450, membersCount: 15, motto: "Ertalabki 5 AM afsonalari!" },
    { id: "sq_2", name: "Bushido Sunrise", tag: "BUSHI", streak: 380, membersCount: 12, motto: "Katana intizomi va sabr!" },
    { id: "sq_3", name: "5 AM Phoenix", tag: "PHNX", streak: 310, membersCount: 10, motto: "Har kun quyosh bilan uyg'onamiz!" },
    { id: "sq_4", name: "Sun Chasers Clan", tag: "SUN", streak: 240, membersCount: 8, motto: "Nurlarga intiluvchilar" }
];

function renderSquadsTab() {
    const heroBox = document.getElementById("squad-info-box");
    const listEl = document.getElementById("squads-list");
    if (!heroBox || !listEl) return;

    if (state.user.squad) {
        const sq = state.user.squad;
        heroBox.innerHTML = `
            <div class="squad-active-header">
                <div class="squad-emblem">🛡️</div>
                <div class="squad-main-meta">
                    <h4>${sq.name} <span class="squad-tag-badge">[${sq.tag}]</span></h4>
                    <p class="squad-motto">“${sq.motto}”</p>
                </div>
            </div>
            <div class="squad-stats-row">
                <div class="squad-stat-item">
                    <span class="s-val">🔥 ${sq.streak}</span>
                    <small class="s-lbl">Umumiy Streak</small>
                </div>
                <div class="squad-stat-item">
                    <span class="s-val">👥 ${sq.membersCount || 1}</span>
                    <small class="s-lbl">A'zolar</small>
                </div>
                <div class="squad-stat-item">
                    <span class="s-val">👑 ${sq.role || "Member"}</span>
                    <small class="s-lbl">Maqom</small>
                </div>
            </div>
            <div class="squad-actions-row">
                <button class="secondary-btn action-sm-btn" onclick="leaveSquad()">Guruhdan Chiqish 🚪</button>
            </div>
        `;
    } else {
        heroBox.innerHTML = `
            <div class="squad-empty-box">
                <p>Siz hali hech qanday guruhga a'zo emassiz! Do'stlaringiz bilan birlashing va umumiy streak to'plang!</p>
                <div class="squad-btn-group">
                    <button class="primary-btn glow-btn" onclick="openSquadModal()">➕ Yangi Squad Tuzish (100 🪙)</button>
                    <button class="secondary-btn" onclick="joinRandomSquad()">🎲 Tasodifiy Squadga Qo'shilish</button>
                </div>
            </div>
        `;
    }

    listEl.innerHTML = TOP_SQUADS_DATA.map((sq, index) => `
        <div class="squad-item-card">
            <span class="sq-rank">#${index + 1}</span>
            <div class="sq-icon">🛡️</div>
            <div class="sq-details">
                <div class="sq-title-row">
                    <strong>${sq.name}</strong>
                    <span class="sq-tag">[${sq.tag}]</span>
                </div>
                <span class="sq-motto">${sq.motto}</span>
            </div>
            <div class="sq-right-stats">
                <span class="sq-streak">🔥 ${sq.streak} Kun</span>
                <span class="sq-members">👥 ${sq.membersCount}</span>
            </div>
        </div>
    `).join("");
}

function openSquadModal() {
    sfx.click();
    const modal = document.getElementById("squad-modal");
    if (modal) modal.style.display = "flex";
}
window.openSquadModal = openSquadModal;

function closeSquadModal() {
    const modal = document.getElementById("squad-modal");
    if (modal) modal.style.display = "none";
}
window.closeSquadModal = closeSquadModal;

function submitCreateSquad() {
    const nameInput = document.getElementById("input-squad-name");
    const tagInput = document.getElementById("input-squad-tag");
    const mottoInput = document.getElementById("input-squad-motto");

    const name = nameInput ? nameInput.value.trim() : "";
    const tag = tagInput ? tagInput.value.trim().toUpperCase() : "";
    const motto = mottoInput ? mottoInput.value.trim() : "5 AM Club Clan";

    if (!name || !tag) {
        showToast("❌ Squad nomi va tagini kiriting!");
        triggerHapticFeedback("error");
        return;
    }

    if (state.user.coins < 100) {
        showToast("❌ Squad tuzish uchun 100 tanga kerak!");
        triggerHapticFeedback("error");
        return;
    }

    state.user.coins -= 100;
    state.user.squad = {
        id: `sq_${Date.now()}`,
        name: name,
        tag: tag,
        motto: motto,
        streak: state.user.streak,
        membersCount: 1,
        role: "Leader",
        members: [{ name: state.user.name, streak: state.user.streak, rank: "Leader" }]
    };

    saveState();
    updateUI();
    renderSquadsTab();
    closeSquadModal();
    sfx.victory();
    launchConfetti();
    showToast(`🎉 Squad created: '${name}' [${tag}]!`);
}
window.submitCreateSquad = submitCreateSquad;

function joinRandomSquad() {
    sfx.click();
    const randomSq = TOP_SQUADS_DATA[Math.floor(Math.random() * TOP_SQUADS_DATA.length)];
    state.user.squad = {
        id: randomSq.id,
        name: randomSq.name,
        tag: randomSq.tag,
        motto: randomSq.motto,
        streak: randomSq.streak + state.user.streak,
        membersCount: randomSq.membersCount + 1,
        role: "Member"
    };

    saveState();
    renderSquadsTab();
    sfx.coin();
    showToast(`🎉 Joined '${randomSq.name}' [${randomSq.tag}]!`);
    triggerHapticFeedback("medium");
}
window.joinRandomSquad = joinRandomSquad;

function leaveSquad() {
    sfx.click();
    state.user.squad = null;
    saveState();
    renderSquadsTab();
    showToast("🚪 You left the squad.");
}
window.leaveSquad = leaveSquad;

// ==================== INTERACTIVE BADGE VAULT INSPECTOR ====================
const BADGES_DATABASE = [
    {
        id: "early_bird",
        icon: "⚡",
        name: { uz: "Early Bird", ru: "Ранняя Пташка", en: "Early Bird" },
        desc: { uz: "7 kun ketma-ket soat 5:00 da uyg'onish intizomi", ru: "7 дней подряд успешного подъема в 5:00", en: "7 consecutive days of verified 5 AM wake-ups" },
        req: "7 Days Streak",
        target: 7,
        current: (u) => u.streak
    },
    {
        id: "photo_master",
        icon: "📸",
        name: { uz: "Photo Master", ru: "Мастер Фото", en: "Photo Master" },
        desc: { uz: "5 ta tasdiqlangan kunlik kofe/suv foto isboti yuborildi", ru: "5 подтвержденных утренних фото-заданий", en: "5 verified morning photo proof missions" },
        req: "5 Photo Proofs",
        target: 5,
        current: (u) => u.photoCount || 0
    },
    {
        id: "elite_21",
        icon: "🏆",
        name: { uz: "Elite 21", ru: "Элита 21", en: "Elite 21" },
        desc: { uz: "21 kunlik odat maratonini to'liq yakunlab, Oltin Sertifikat olish", ru: "Завершение 21-дневного марафона и получение Золотого Сертификата", en: "Complete 21-day habit challenge & earn Golden Certificate" },
        req: "21 Days Streak",
        target: 21,
        current: (u) => u.streak
    },
    {
        id: "lion_legend",
        icon: "🦁",
        name: { uz: "5 AM Legend", ru: "Легенда 5 AM", en: "5 AM Legend" },
        desc: { uz: "30 kunlik intizom cho'qqisini fohishasiz bosib o'tish", ru: "Достижение 30 дней непрерывной дисциплины", en: "Reach ultimate 30-day discipline milestone" },
        req: "30 Days Streak",
        target: 30,
        current: (u) => u.streak
    },
    {
        id: "shielded",
        icon: "🛡️",
        name: { uz: "Shield Master", ru: "Мастер Щита", en: "Shield Master" },
        desc: { uz: "Bozordan kamida 1 ta Streak Freeze qalqonini xarid qilish", ru: "Приобретение хотя бы 1 Защитного Щита Стрика", en: "Possess at least 1 Streak Freeze shield" },
        req: "1 Streak Freeze",
        target: 1,
        current: (u) => u.freezeCount || 0
    },
    {
        id: "gladiator",
        icon: "⚔️",
        name: { uz: "Gladiator", ru: "Гладиатор", en: "Gladiator" },
        desc: { uz: "Turnirda va 1v1 duellarda 100 dan ortiq ball to'plash", ru: "Набрать более 100 очков в турнире и дуэлях", en: "Earn 100+ tournament & duel points" },
        req: "100 Tourney Pts",
        target: 100,
        current: (u) => u.tourneyPoints || 0
    }
];

function openBadgeModal(badgeId) {
    const b = BADGES_DATABASE.find(item => item.id === badgeId);
    if (!b) return;

    sfx.click();
    const lang = state.lang || "uz";
    const title = b.name[lang] || b.name.uz;
    const desc = b.desc[lang] || b.desc.uz;
    const currentVal = b.current(state.user);
    const isUnlocked = currentVal >= b.target;
    const pct = Math.min(100, Math.round((currentVal / b.target) * 100));

    setElementText("badge-modal-icon", b.icon);
    setElementText("badge-modal-title", title);
    setElementText("badge-modal-desc", desc);
    setElementText("badge-modal-req", b.req);

    const statusTag = document.getElementById("badge-modal-status");
    if (statusTag) {
        if (isUnlocked) {
            statusTag.textContent = "✅ UNLOCKED";
            statusTag.className = "badge-status-tag unlocked";
        } else {
            statusTag.textContent = "🔒 LOCKED";
            statusTag.className = "badge-status-tag locked";
        }
    }

    const fill = document.getElementById("badge-modal-progress-fill");
    const progressText = document.getElementById("badge-modal-progress-text");
    if (fill) fill.style.width = `${pct}%`;
    if (progressText) progressText.textContent = `Progress: ${currentVal} / ${b.target} (${pct}%)`;

    const modal = document.getElementById("badge-modal");
    if (modal) modal.style.display = "flex";
    triggerHapticFeedback("medium");
}
window.openBadgeModal = openBadgeModal;

function closeBadgeModal() {
    const modal = document.getElementById("badge-modal");
    if (modal) modal.style.display = "none";
}
window.closeBadgeModal = closeBadgeModal;
