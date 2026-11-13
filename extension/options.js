document.addEventListener("DOMContentLoaded", async () => {
  const input = document.getElementById("key");
  const d = await chrome.storage.sync.get(["tinyfishApiKey"]);
  if (d.tinyfishApiKey) input.value = d.tinyfishApiKey;
  document.getElementById("save").addEventListener("click", async () => {
    await chrome.storage.sync.set({ tinyfishApiKey: input.value.trim() });
    document.getElementById("saved").textContent = "saved ✓";
    setTimeout(() => (document.getElementById("saved").textContent = ""), 2000);
  });
});
