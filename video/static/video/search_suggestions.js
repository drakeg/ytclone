(() => {
    const inputs = document.querySelectorAll("[data-search-suggestions]");

    inputs.forEach((input) => {
        const endpoint = input.dataset.searchSuggestions;
        const listId = input.getAttribute("list");
        const list = listId ? document.getElementById(listId) : null;
        if (!endpoint || !list) return;

        let timer = null;
        let requestNumber = 0;
        let currentSuggestions = new Set();

        const clearSuggestions = () => {
            list.replaceChildren();
            currentSuggestions = new Set();
        };

        input.addEventListener("input", () => {
            window.clearTimeout(timer);
            const query = input.value.trim();
            if (query.length < 2) {
                requestNumber += 1;
                clearSuggestions();
                return;
            }

            const currentRequest = ++requestNumber;
            timer = window.setTimeout(async () => {
                try {
                    const url = new URL(endpoint, window.location.origin);
                    url.searchParams.set("query", query);
                    const response = await fetch(url, {
                        headers: { Accept: "application/json" },
                    });
                    if (!response.ok || currentRequest !== requestNumber) return;

                    const payload = await response.json();
                    if (currentRequest !== requestNumber) return;
                    const suggestions = Array.isArray(payload.suggestions)
                        ? payload.suggestions
                        : [];

                    list.replaceChildren(
                        ...suggestions.map((value) => {
                            const option = document.createElement("option");
                            option.value = value;
                            return option;
                        })
                    );
                    currentSuggestions = new Set(suggestions);
                } catch (_) {
                    if (currentRequest === requestNumber) clearSuggestions();
                }
            }, 150);
        });

        input.addEventListener("change", () => {
            if (currentSuggestions.has(input.value)) input.form?.requestSubmit();
        });
    });
})();
