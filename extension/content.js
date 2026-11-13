/* Source Hunter content script: highlight text -> floating trace button. */

(function () {
  let btn = null;

  function removeButton() {
    if (btn) {
      btn.remove();
      btn = null;
    }
  }

  function makeButton(text, x, y) {
    removeButton();
    btn = document.createElement("button");
    btn.id = "source-hunter-button";
    btn.textContent = "\u{1F41F} Trace with TinyFish";
    btn.style.left = Math.max(8, Math.min(x, window.innerWidth - 200)) + "px";
    btn.style.top = Math.max(8, y) + "px";
    btn.addEventListener("mousedown", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const claim = text.trim();
      removeButton();
      if (claim.length < 8) return;
      chrome.runtime.sendMessage({
        type: "TRACE",
        claim,
        pageUrl: location.href,
      });
    });
    document.body.appendChild(btn);
  }

  document.addEventListener("mouseup", (e) => {
    setTimeout(() => {
      const sel = window.getSelection();
      const text = sel ? sel.toString().trim() : "";
      if (text.length >= 8 && sel.rangeCount) {
        const rect = sel.getRangeAt(0).getBoundingClientRect();
        makeButton(
          text,
          rect.left + window.scrollX,
          rect.bottom + window.scrollY + 8,
        );
      } else {
        removeButton();
      }
    }, 10);
  });

  document.addEventListener("mousedown", (e) => {
    if (btn && e.target !== btn) removeButton();
  });
  window.addEventListener("scroll", removeButton, { passive: true });
})();
