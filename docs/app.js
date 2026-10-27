(() => {
  "use strict";
  const repository = "Oleksii1221/DubTogether-UA";
  const button = document.getElementById("download");
  const status = document.getElementById("release-status");
  const archive = document.getElementById("archive-list");

  fetch(`https://api.github.com/repos/${repository}/releases?per_page=20`, {
    headers: { Accept: "application/vnd.github+json" }
  }).then(async (response) => {
    if (!response.ok) throw new Error(`GitHub ${response.status}`);
    const releases = (await response.json()).filter((entry) => !entry.draft && !entry.prerelease);
    const release = releases[0];
    if (!release) throw new Error("No Windows releases");
    const asset = (release.assets || []).find((entry) => entry.name === "DubTogether-UA-Installer.exe");
    if (!asset || !asset.browser_download_url) throw new Error("No Windows asset");
    button.href = asset.browser_download_url;
    status.textContent = `${release.tag_name} · Windows · ${(asset.size / 1048576).toFixed(1)} МБ · безкоштовно`;
    const links = releases.slice(1).flatMap((item) => {
      const installer = (item.assets || []).find((entry) => entry.name === "DubTogether-UA-Installer.exe");
      if (!installer?.browser_download_url) return [];
      const link = document.createElement("a");
      link.href = installer.browser_download_url;
      link.dataset.umamiEvent = "download-windows-archive";
      link.dataset.umamiEventVersion = item.tag_name;
      link.textContent = `${item.tag_name} · ${(installer.size / 1048576).toFixed(1)} МБ`;
      return [link];
    });
    if (links.length) archive.replaceChildren(...links);
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
