(() => {
  const feed = document.getElementById("shorts-feed");
  if (!feed) return;

  const responseErrorMessage = async (response, fallback) => {
    if (response.status !== 403) return fallback;
    try {
      const data = await response.clone().json();
      return data?.error === "csrf_failed" && data?.message ? data.message : fallback;
    } catch (_) {
      return fallback;
    }
  };

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
    const fallback = "Could not update subscription.";

    if (error) { error.textContent = fallback; error.style.display = "none"; }
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
      if (!response.ok) {
        if (error) error.textContent = await responseErrorMessage(response, fallback);
        throw new Error("subscription request failed");
      }
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
