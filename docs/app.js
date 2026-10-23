(() => {
  "use strict";
  const repository = "Oleksii1221/DubTogether-UA";
  const releaseUrl = `https://github.com/${repository}/releases`;
  const buttons = [document.getElementById("download"), document.getElementById("download-bottom")];
  const status = document.getElementById("release-status");
  const count = document.getElementById("download-count");

  fetch(`https://api.github.com/repos/${repository}/releases/latest`, {
    headers: { Accept: "application/vnd.github+json" }
  }).then(async (response) => {
    if (!response.ok) throw new Error(`GitHub ${response.status}`);
    const release = await response.json();
    const asset = (release.assets || []).find((entry) => entry.name === "DubTogether-UA-Installer.exe");
    if (!asset || !asset.browser_download_url) throw new Error("No Windows asset");
    for (const link of buttons) {
      link.href = asset.browser_download_url;
      link.firstChild.textContent = "Завантажити для Windows ";
    }
    status.textContent = `${release.tag_name} · Windows · ${(asset.size / 1048576).toFixed(1)} МБ`;
    count.textContent = `Завантажень цього файлу на GitHub: ${asset.download_count.toLocaleString("uk-UA")}`;
  }).catch(() => {
    for (const link of buttons) link.href = releaseUrl;
    status.textContent = "Перший реліз готується. Слідкуй за оновленнями на GitHub.";
    count.textContent = "Завантаження з’явиться тут після першого релізу.";
  });

  const analytics = window.DUBUA_ANALYTICS || {};
  if (analytics.scriptUrl && analytics.websiteId) {
    try {
      const url = new URL(analytics.scriptUrl);
      if (url.protocol === "https:") {
        const script = document.createElement("script");
        script.defer = true;
        script.src = url.href;
        script.dataset.websiteId = analytics.websiteId;
        document.head.appendChild(script);
      }
    } catch (_) { /* Site remains usable without analytics. */ }
  }
})();
