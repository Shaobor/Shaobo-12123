/**
 * 12123 integration helper.
 * Keep the configuration dialog open while local help pages open in a new tab.
 */
(function () {
  if (typeof window === "undefined" || window._jiaoguan12123HelperInitialized) return;
  window._jiaoguan12123HelperInitialized = true;

  function handleAnchorClick(event) {
    try {
      const path = event.composedPath ? event.composedPath() : [];
      let anchor = null;
      for (const element of path) {
        if (element && element.tagName === "A" && element.href) {
          anchor = element;
          break;
        }
      }
      if (!anchor || !anchor.href || !anchor.href.includes("/api/12123/capture_tutorial")) return;

      event.preventDefault();
      event.stopPropagation();
      if (typeof event.stopImmediatePropagation === "function") event.stopImmediatePropagation();
      window.open(anchor.href, "_blank", "noopener,noreferrer");
    } catch (error) {
      // A help link must never break the configuration flow.
    }
  }

  // Capture phase also sees clicks emitted from Home Assistant's shadow DOM.
  window.addEventListener("click", handleAnchorClick, true);
})();
