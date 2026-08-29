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

    feed.querySelectorAll(".shorts-video").forEach((video) => {
        syncPlaybackButton(video);
        video.addEventListener("play", () => syncPlaybackButton(video));
        video.addEventListener("pause", () => syncPlaybackButton(video));
    });
})();
