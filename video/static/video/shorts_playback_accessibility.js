(() => {
    const feed = document.getElementById("shorts-feed");
    if (!feed) return;

    const syncPlaybackButton = (video) => {
        const item = video.closest(".shorts-item");
        const button = item?.querySelector("[data-short-play]");
        if (!button) return;

        const title = video.getAttribute("aria-label") || "Short";
        const action = video.paused ? "Play" : "Pause";
        button.textContent = action;
        button.setAttribute("aria-label", `${action} ${title}`);
        button.removeAttribute("aria-pressed");
    };

    const syncAllPlaybackButtons = () => {
        feed.querySelectorAll(".shorts-video").forEach(syncPlaybackButton);
    };

    syncAllPlaybackButtons();
    feed.addEventListener("play", (event) => {
        if (event.target.matches?.(".shorts-video")) syncPlaybackButton(event.target);
    }, true);
    feed.addEventListener("pause", (event) => {
        if (event.target.matches?.(".shorts-video")) syncPlaybackButton(event.target);
    }, true);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) syncAllPlaybackButtons();
    });
})();
