// ==================== STATE MANAGEMENT ====================
const state = {
    user: {
        id: 6377617416,
        name: "Super Admin",
        username: "owner",
        streak: 12,
        coins: 450,
        multiplier: 1.2,
        rank: "🏆 Morning Master",
        photoCount: 5,
        freezeCount: 1,
        refCount: 3
    },
    timer: {
        hours: 1,
        mins: 24,
        secs: 48
    }
};

// ==================== INITIALIZATION ====================
document.addEventListener("DOMContentLoaded", () => {
    initTelegramWebApp();
    initTabs();
    initTimer();
    renderCalendar();
    initActions();
});

// ==================== TELEGRAM WEBAPP SDK ====================
function initTelegramWebApp() {
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.expand(); // Expand WebApp to full height

        const tgUser = tg.initDataUnsafe?.user;
        if (tgUser) {
            state.user.id = tgUser.id;
            state.user.name = tgUser.first_name + (tgUser.last_name ? " " + tgUser.last_name : "");
            state.user.username = tgUser.username || "user";
            
            if (tgUser.photo_url) {
                document.getElementById("user-avatar").src = tgUser.photo_url;
            }
        }
    }
    updateUI();
}

function updateUI() {
    document.getElementById("user-name").textContent = state.user.name;
    document.getElementById("user-rank").textContent = state.user.rank;
    document.getElementById("stat-streak").textContent = state.user.streak;
    document.getElementById("stat-coins").textContent = state.user.coins;
    document.getElementById("stat-multiplier").textContent = `${state.user.multiplier}X`;
    document.getElementById("shop-balance-coins").textContent = `🪙 ${state.user.coins}`;
}

// ==================== TAB NAVIGATION ====================
function initTabs() {
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");

            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            document.getElementById(targetTab).classList.add("active");

            // Haptic Feedback if available
            triggerHapticFeedback();
        });
    });
}

// ==================== LIVE COUNTDOWN TIMER ====================
function initTimer() {
    setInterval(() => {
        if (state.timer.secs > 0) {
            state.timer.secs--;
        } else {
            state.timer.secs = 59;
            if (state.timer.mins > 0) {
                state.timer.mins--;
            } else {
                state.timer.mins = 59;
                if (state.timer.hours > 0) {
                    state.timer.hours--;
                }
            }
        }

        document.getElementById("time-hours").textContent = String(state.timer.hours).padStart(2, '0');
        document.getElementById("time-mins").textContent = String(state.timer.mins).padStart(2, '0');
        document.getElementById("time-secs").textContent = String(state.timer.secs).padStart(2, '0');
    }, 1000);
}

// ==================== 30-DAY MATRIX CALENDAR ====================
function renderCalendar() {
    const grid = document.getElementById("calendar-grid");
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

// ==================== INTERACTIVE ACTIONS ====================
function initActions() {
    // Solo Check-In Button
    const checkinBtn = document.getElementById("btn-main-checkin");
    checkinBtn.addEventListener("click", () => {
        const earnedCoins = Math.round(10 * state.user.multiplier);
        state.user.streak += 1;
        state.user.coins += earnedCoins;

        updateUI();
        renderCalendar();
        showToast(`⚡ Check-In Successful! Earned +${earnedCoins} Coins! 🔥`);
        triggerHapticFeedback();
    });

    // Upload Photo Button & Stamp Watermark Canvas
    const uploadBtn = document.getElementById("btn-upload-photo");
    const fileInput = document.getElementById("photo-file-input");

    uploadBtn.addEventListener("click", () => {
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

                // Draw Watermark Stamp Banner
                const bannerHeight = Math.max(60, img.height * 0.12);
                ctx.fillStyle = "rgba(15, 23, 42, 0.85)";
                ctx.fillRect(0, img.height - bannerHeight, img.width, bannerHeight);

                ctx.fillStyle = "#fbbf24";
                ctx.font = "bold 24px sans-serif";
                ctx.fillText(`✅ VERIFIED 5 AM CLUB | ${new Date().toLocaleTimeString()}`, 20, img.height - bannerHeight + 32);

                ctx.fillStyle = "#ffffff";
                ctx.font = "18px sans-serif";
                ctx.fillText(`👤 ${state.user.name} | 🔥 Streak: ${state.user.streak} Days | 🏅 ${state.user.rank}`, 20, img.height - bannerHeight + 56);

                const stampedDataUrl = canvas.toDataURL("image/jpeg");
                document.getElementById("stamped-preview-img").src = stampedDataUrl;
                document.getElementById("stamped-preview-container").style.display = "block";

                const photoEarned = Math.round(25 * state.user.multiplier);
                state.user.coins += photoEarned;
                state.user.photoCount += 1;

                updateUI();
                showToast(`📸 Photo Verified! Earned +${photoEarned} Coins! 🚀`);
                triggerHapticFeedback();
            };
            img.src = event.target.result;
        };
        reader.readAsDataURL(file);
    });

    // Matchmaking Search Simulation
    const matchBtn = document.getElementById("btn-start-matchmaking");
    matchBtn.addEventListener("click", () => {
        matchBtn.textContent = "⌛ Searching for Partner...";
        setTimeout(() => {
            document.getElementById("opponent-name").textContent = "@Riser_Samir";
            document.getElementById("opponent-status").textContent = "MATCHED 🔥";
            document.getElementById("opponent-status").className = "fighter-status ready";
            matchBtn.textContent = "⚔️ Match Found! Duel Active!";
            showToast("🎉 Match Found! Duel activated for 50 coins!");
            triggerHapticFeedback();
        }, 2000);
    });
}

// ==================== MARKETPLACE SYSTEM ====================
function buyItem(itemName, price) {
    if (state.user.coins >= price) {
        state.user.coins -= price;
        if (itemName === "Streak Freeze") {
            state.user.freezeCount += 1;
        }
        updateUI();
        showToast(`🎉 Purchased ${itemName} for ${price} Coins!`);
        triggerHapticFeedback();
    } else {
        showToast(`❌ Insufficient Coins! You need ${price} Coins.`);
    }
}

// ==================== TOAST & HAPTICS ====================
function showToast(message) {
    const toast = document.getElementById("toast");
    document.getElementById("toast-message").textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3000);
}

function triggerHapticFeedback() {
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.HapticFeedback) {
        window.Telegram.WebApp.HapticFeedback.impactOccurred("medium");
    }
}
