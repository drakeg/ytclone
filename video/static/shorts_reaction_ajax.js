(() => {
  const feed = document.getElementById("shorts-feed");
  if (!feed) return;

  const inFlightItems = new WeakSet();

  const setReactionButtonsDisabled = (item, disabled) => {
    item.querySelectorAll('[data-short-reaction-form] button[type="submit"]').forEach((button) => {
      button.disabled = disabled;
    });
  };

  const syncReaction = (item, data) => {
    const like = item.querySelector("[data-short-like]");
    const dislike = item.querySelector("[data-short-dislike]");
    if (!like || !dislike) return;

    like.setAttribute("aria-pressed", data.liked ? "true" : "false");
    dislike.setAttribute("aria-pressed", data.disliked ? "true" : "false");
    like.classList.toggle("btn-primary", data.liked);
    like.classList.toggle("btn-outline-primary", !data.liked);
    dislike.classList.toggle("btn-secondary", data.disliked);
    dislike.classList.toggle("btn-outline-secondary", !data.disliked);

    const likeCount = like.querySelector("[data-like-count]");
    const dislikeCount = dislike.querySelector("[data-dislike-count]");
    if (likeCount) likeCount.textContent = data.like_count;
    if (dislikeCount) dislikeCount.textContent = data.dislike_count;
  };

  feed.addEventListener(
    "submit",
    async (event) => {
      const form = event.target.closest?.("[data-short-reaction-form]");
      if (!form || !feed.contains(form)) return;

      event.preventDefault();
      event.stopImmediatePropagation();

      const item = form.closest(".shorts-item");
      if (!item || inFlightItems.has(item)) return;

      const error = item.querySelector("[data-short-reaction-error]");
      if (error) error.style.display = "none";

      inFlightItems.add(item);
      setReactionButtonsDisabled(item, true);

      try {
        const response = await fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            Accept: "application/json",
          },
        });
        if (!response.ok) throw new Error("reaction request failed");
        syncReaction(item, await response.json());
      } catch (_) {
        if (error) error.style.display = "block";
      } finally {
        inFlightItems.delete(item);
        setReactionButtonsDisabled(item, false);
      }
    },
    true,
  );
})();
