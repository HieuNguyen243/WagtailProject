document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[action*='/analyze/'], form[action*='/email/'], form[action*='/generate/']").forEach((form) => {
    form.addEventListener("submit", () => {
      const button = form.querySelector("button[type='submit']");
      if (!button) return;
      button.disabled = true;
      button.dataset.originalText = button.textContent;
      button.textContent = "Đang xử lý…";
    });
  });

  document.querySelectorAll(".crm-row-action").forEach((link) => {
    link.addEventListener("click", () => {
      link.classList.add("crm-row-action--loading");
    });
  });
});
