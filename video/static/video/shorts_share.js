(() => {
  const feed = document.getElementById("shorts-feed");
  if (!feed) return;

  const copyShareUrl = async (url) => {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url);
      return true;
    }

    const area = document.createElement("textarea");
    area.value = url;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    const copied = document.execCommand("copy");
    area.remove();
    return copied;
  };

  const share = async (button) => {
    const url = new URL(button.dataset.shareUrl, window.location.origin).href;
    const title = button.dataset.shareTitle || document.title;
    const original = button.textContent;

    try {
      if (navigator.share) {
        await navigator.share({title, url});
        return;
      }

      const copied = await copyShareUrl(url);
      button.textContent = copied ? "Copied" : "Copy failed";
      window.setTimeout(() => {
        button.textContent = original;
      }, 1600);
    } catch (error) {
      if (error?.name === "AbortError") return;
      button.textContent = "Share failed";
      window.setTimeout(() => {
        button.textContent = original;
      }, 1600);
    }
  };

  feed.addEventListener(
    "click",
    (event) => {
      const button = event.target.closest?.("[data-short-share]");
      if (!button || !feed.contains(button)) return;

      event.preventDefault();
      event.stopImmediatePropagation();
      share(button);
    },
    true,
  );
})();
