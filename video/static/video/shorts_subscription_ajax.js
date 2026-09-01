(() => {
  const feed = document.getElementById("shorts-feed");
  if (!feed) return;

  const syncSubscription = (form, data) => {
    const button = form.querySelector("[data-short-subscribe]");
    if (!button) return;

    button.textContent = data.subscribed ? "Subscribed" : "Subscribe";
    button.setAttribute("aria-pressed", data.subscribed ? "true" : "false");
    button.classList.toggle("btn-outline-secondary", data.subscribed);
    button.classList.toggle("btn-primary", !data.subscribed);
  };

  const submitSubscription = async (form) => {
    const row = form.closest(".shorts-channel-row");
    const error = row?.querySelector("[data-short-subscribe-error]");
    const button = form.querySelector("[data-short-subscribe]");

    if (error) error.style.display = "none";
    if (button) button.disabled = true;

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          Accept: "application/json",
        },
      });
      if (!response.ok) throw new Error("subscription request failed");
      syncSubscription(form, await response.json());
    } catch (_) {
      if (error) error.style.display = "inline";
    } finally {
      if (button) button.disabled = false;
    }
  };

  feed.addEventListener("submit", (event) => {
    const form = event.target.closest?.("[data-short-subscribe-form]");
    if (!form || !feed.contains(form)) return;
    event.preventDefault();
    submitSubscription(form);
  });
})();
