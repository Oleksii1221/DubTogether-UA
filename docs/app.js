(() => {
  "use strict";
  const repository = "Oleksii1221/DubTogether-UA";
  const button = document.getElementById("download");
  const status = document.getElementById("release-status");

  fetch(`https://api.github.com/repos/${repository}/releases/latest`, {
    headers: { Accept: "application/vnd.github+json" }
  }).then(async (response) => {
    if (!response.ok) throw new Error(`GitHub ${response.status}`);
    const release = await response.json();
    const asset = (release.assets || []).find((entry) => entry.name === "DubTogether-UA-Installer.exe");
    if (!asset || !asset.browser_download_url) throw new Error("No Windows asset");
    button.href = asset.browser_download_url;
    status.textContent = `${release.tag_name} · Windows · ${(asset.size / 1048576).toFixed(1)} МБ · безкоштовно`;
  }).catch(() => { /* The direct download link works without the API. */ });

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
