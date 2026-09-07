(() => {
    const player = document.getElementById("video-player");
    const watchNext = document.querySelector("[data-watch-next]");
    const nextCard = watchNext?.querySelector("[data-watch-next-url]");
    const toggle = watchNext?.querySelector("[data-autoplay-toggle]");
    const status = watchNext?.querySelector("[data-autoplay-status]");
    if (!player || !nextCard || !toggle || !status) return;

    const STORAGE_KEY = "videoshare.autoplayNext";
    const COUNTDOWN_SECONDS = 5;
    let timer = null;
    let secondsRemaining = COUNTDOWN_SECONDS;

    const readEnabled = () => {
        try {
            return window.localStorage.getItem(STORAGE_KEY) !== "false";
        } catch (_) {
            return true;
        }
    };
    let enabled = readEnabled();

    const syncToggle = () => {
        toggle.textContent = enabled ? "Autoplay on" : "Autoplay off";
        toggle.setAttribute("aria-pressed", enabled ? "true" : "false");
    };

    const clearCountdown = () => {
        if (timer !== null) window.clearInterval(timer);
        timer = null;
        status.textContent = "";
        secondsRemaining = COUNTDOWN_SECONDS;
    };

    const navigateNext = () => {
        window.location.assign(nextCard.dataset.watchNextUrl);
    };

    const startCountdown = () => {
        clearCountdown();
        if (!enabled) return;
        status.textContent = `Next video in ${secondsRemaining}s`;
        timer = window.setInterval(() => {
            secondsRemaining -= 1;
            if (secondsRemaining <= 0) {
                clearCountdown();
                navigateNext();
                return;
            }
            status.textContent = `Next video in ${secondsRemaining}s`;
        }, 1000);
    };

    toggle.addEventListener("click", () => {
        enabled = !enabled;
        try {
            window.localStorage.setItem(STORAGE_KEY, String(enabled));
        } catch (_) {
            // Autoplay still works for this page when storage is unavailable.
        }
        syncToggle();
        if (!enabled) clearCountdown();
        else if (player.ended) startCountdown();
    });

    player.addEventListener("ended", startCountdown);
    player.addEventListener("play", clearCountdown);
    syncToggle();
})();
