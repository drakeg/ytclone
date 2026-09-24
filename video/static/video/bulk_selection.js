document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-bulk-selection]").forEach((form) => {
    const itemName = form.dataset.itemName;
    const selectAll = form.querySelector("[data-bulk-select-all]");
    const status = form.querySelector("[data-bulk-selection-status]");
    const submit = form.querySelector("[data-bulk-submit]");
    if (!itemName || !selectAll || !status || !submit) return;

    const items = Array.from(document.querySelectorAll(
      `input[type="checkbox"][name="${CSS.escape(itemName)}"][form="${CSS.escape(form.id)}"]`
    ));

    const update = () => {
      const selected = items.filter((item) => item.checked).length;
      status.textContent = `${selected} selected`;
      submit.disabled = selected === 0;
      selectAll.checked = items.length > 0 && selected === items.length;
      selectAll.indeterminate = selected > 0 && selected < items.length;
    };

    selectAll.addEventListener("change", () => {
      items.forEach((item) => {
        item.checked = selectAll.checked;
      });
      update();
    });

    items.forEach((item) => item.addEventListener("change", update));
    update();
  });
});
