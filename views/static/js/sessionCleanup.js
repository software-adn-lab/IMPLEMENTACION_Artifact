(function () {
  const INTERNAL_NAV_KEY = "__internal_nav__";
  const CLEANUP_SENT_KEY = "__cleanup_sent__";

  // Si venimos de una navegacion interna previa, se limpia la marca para esta nueva vista.
  sessionStorage.removeItem(INTERNAL_NAV_KEY);
  sessionStorage.removeItem(CLEANUP_SENT_KEY);

  function marcarNavegacionInterna() {
    sessionStorage.setItem(INTERNAL_NAV_KEY, "1");
  }

  function esNavegacionInternaMarcada() {
    return sessionStorage.getItem(INTERNAL_NAV_KEY) === "1";
  }

  function yaSeEnvioLimpieza() {
    return sessionStorage.getItem(CLEANUP_SENT_KEY) === "1";
  }

  function marcarLimpiezaEnviada() {
    sessionStorage.setItem(CLEANUP_SENT_KEY, "1");
  }

  // Detecta clics sobre enlaces internos para no limpiar en cambios de pagina dentro de la app.
  document.addEventListener(
    "click",
    (event) => {
      const anchor = event.target && event.target.closest ? event.target.closest("a[href]") : null;
      if (!anchor) {
        return;
      }

      if (anchor.target === "_blank" || anchor.hasAttribute("download")) {
        return;
      }

      const href = anchor.getAttribute("href") || "";
      if (href.startsWith("#")) {
        return;
      }

      const url = new URL(anchor.href, window.location.origin);
      if (url.origin === window.location.origin) {
        marcarNavegacionInterna();
      }
    },
    true
  );

  function enviarSolicitudLimpieza() {
    const projectKey = (sessionStorage.getItem("projectName") || "").trim();
    if (!projectKey || yaSeEnvioLimpieza()) {
      return;
    }

    const payload = JSON.stringify({ project_key: projectKey });
    marcarLimpiezaEnviada();

    // sendBeacon es la opcion mas estable durante cierre de pestana/navegador.
    const beaconOk = navigator.sendBeacon(
      "/api/cleanup-session-repo",
      new Blob([payload], { type: "application/json" })
    );

    // Fallback para navegadores donde sendBeacon falle.
    if (!beaconOk) {
      fetch("/api/cleanup-session-repo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true,
      }).catch(() => {
        // No hacer nada: durante cierre no conviene bloquear UX por errores de red.
      });
    }
  }

  function manejarSalidaDePagina() {
    if (esNavegacionInternaMarcada()) {
      return;
    }
    enviarSolicitudLimpieza();
  }

  window.addEventListener("pagehide", manejarSalidaDePagina);
  window.addEventListener("beforeunload", manejarSalidaDePagina);

  // Permite que otras vistas marquen navegacion interna cuando redirigen por JS.
  window.__markInternalNavigationForCleanup = marcarNavegacionInterna;
})();
