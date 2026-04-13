(function () {
  const importantHosts = ["vincentbastille.bandcamp.com", "open.spotify.com"];
  const keyFromHref = (href) => {
    if (!href) return "external_click";
    if (href.includes("/album/vincent-bastille-remixes-legacy")) return "album_main";
    if (href.includes("/album/vincent-bastille-medication-1")) return "medication_featured";
    if (href.includes("open.spotify.com/playlist/")) return "spotify_playlist";
    if (href.includes("open.spotify.com/intl-fr/artist/")) return "spotify_artist";
    if (href.includes("vincentbastille.bandcamp.com")) return "bandcamp_main";
    return "external_click";
  };

  function emit(eventName, payload) {
    try {
      const queue = JSON.parse(localStorage.getItem("vb_click_events") || "[]");
      queue.push({ eventName, payload, ts: new Date().toISOString() });
      localStorage.setItem("vb_click_events", JSON.stringify(queue.slice(-120)));
    } catch (_) {}

    if (window.gtag && window.VB_CONFIG?.gaMeasurementId) {
      window.gtag("event", eventName, payload);
    }
    if (window.plausible && window.VB_CONFIG?.plausibleDomain) {
      window.plausible(eventName, { props: payload });
    }
    if (window.umami && window.VB_CONFIG?.umamiWebsiteId) {
      window.umami.track(eventName, payload);
    }
  }

  document.addEventListener("click", function (evt) {
    const link = evt.target.closest("a[href]");
    if (!link) return;
    const href = link.getAttribute("href") || "";
    const isImportant = importantHosts.some((host) => href.includes(host));
    if (!isImportant && !link.dataset.trackKey) return;

    const key = link.dataset.trackKey || keyFromHref(href);
    emit("vb_outbound_click", {
      key,
      href,
      text: (link.textContent || "").trim().slice(0, 80),
      page: location.pathname,
    });
  });
})();
