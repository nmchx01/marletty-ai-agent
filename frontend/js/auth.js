import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const state = { client: null, session: null };

function createAuthModal() {
  const modal = document.createElement("div");
  modal.className = "auth-overlay";
  modal.id = "authModal";
  modal.innerHTML = `
    <section class="auth-card" role="dialog" aria-modal="true" aria-labelledby="authTitle">
      <button class="auth-dismiss" type="button" aria-label="Cerrar">×</button>
      <span class="auth-mark" aria-hidden="true"><svg viewBox="0 0 48 48"><path d="M24 39V13m0 8c-7 0-11-4-12-9 7 0 11 4 12 9Zm0 8c-7 0-11-4-12-9 7 0 11 4 12 9Zm0-8c7 0 11-4 12-9-7 0-11 4-12 9Zm0 8c7 0 11-4 12-9-7 0-11 4-12 9Z"/></svg></span>
      <p class="eyebrow dark">Bienvenido a Marletty</p>
      <h2 id="authTitle">Una experiencia más dulce</h2>
      <p>Inicia sesión para conversar con Marlette y recibir atención personalizada.</p>
      <button class="auth-google" id="googleLogin" type="button">
        <span aria-hidden="true">G</span> Continuar con Google
      </button>
      <div class="auth-divider"><span>o usa tu correo</span></div>
      <form id="emailLogin" class="auth-email">
        <input id="authEmail" type="email" placeholder="tu@correo.com" required />
        <button type="submit">Enviarme un enlace</button>
      </form>
      <label class="auth-consent">
        <input id="marketingConsent" type="checkbox" />
        Quiero recibir novedades y ofertas de Marletty. Puedo retirarme cuando quiera.
      </label>
      <p class="auth-message" id="authMessage" role="status"></p>
      <small>Tu cuenta es necesaria para usar el asistente. Las ofertas son opcionales.</small>
    </section>`;
  document.body.appendChild(modal);
}

function setMessage(message, error = false) {
  const element = document.getElementById("authMessage");
  element.textContent = message;
  element.classList.toggle("is-error", error);
}

function showModal(force = false) {
  if (!state.session || force) document.getElementById("authModal")?.classList.add("is-visible");
}

function hideModal() {
  document.getElementById("authModal")?.classList.remove("is-visible");
}

async function saveConsent() {
  if (!state.session) return;
  const user = state.session.user;
  const pendingConsent = localStorage.getItem("marletty_pending_marketing_consent");
  const profile = {
    user_id: user.id,
    email: user.email,
    full_name: user.user_metadata?.full_name || user.user_metadata?.name || null,
    updated_at: new Date().toISOString(),
  };

  let result;
  if (pendingConsent !== null) {
    const consent = pendingConsent === "true";
    result = await state.client.from("customer_profiles").upsert({
      ...profile,
      marketing_consent: consent,
      marketing_consent_at: consent ? new Date().toISOString() : null,
    });
    localStorage.removeItem("marletty_pending_marketing_consent");
  } else {
    result = await state.client.from("customer_profiles").insert({
      ...profile,
      marketing_consent: false,
    });
    if (result.error?.code === "23505") return;
  }
  const { error } = result;
  if (error) console.error("No se pudo guardar el perfil", error);
}

function rememberConsent() {
  const consent = document.getElementById("marketingConsent")?.checked || false;
  localStorage.setItem("marletty_pending_marketing_consent", String(consent));
}

async function finishSession(session) {
  state.session = session;
  if (session) {
    await saveConsent();
    hideModal();
  }
  window.dispatchEvent(new CustomEvent("marletty-auth-change", { detail: { session } }));
}

async function initialize() {
  createAuthModal();
  const response = await fetch("/api/auth-config");
  const config = await response.json();
  if (!config.enabled) {
    setMessage("El acceso todavía no está configurado por Marletty.", true);
    showModal(true);
    return;
  }

  state.client = createClient(config.url, config.anonKey);
  const { data } = await state.client.auth.getSession();
  await finishSession(data.session);
  state.client.auth.onAuthStateChange((_event, session) => finishSession(session));

  if (!state.session && !sessionStorage.getItem("marletty_auth_dismissed")) {
    setTimeout(() => showModal(), 700);
  }

  document.getElementById("googleLogin").addEventListener("click", async () => {
    rememberConsent();
    setMessage("Abriendo Google…");
    const { error } = await state.client.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin },
    });
    if (error) setMessage(error.message, true);
  });

  document.getElementById("emailLogin").addEventListener("submit", async (event) => {
    event.preventDefault();
    rememberConsent();
    const email = document.getElementById("authEmail").value.trim();
    const { error } = await state.client.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin },
    });
    setMessage(error ? error.message : "Revisa tu correo: te enviamos un enlace de acceso.", !!error);
  });

  document.querySelector(".auth-dismiss").addEventListener("click", () => {
    sessionStorage.setItem("marletty_auth_dismissed", "1");
    hideModal();
  });
}

window.marlettyAuth = {
  getAccessToken: () => state.session?.access_token || null,
  isAuthenticated: () => !!state.session,
  showLogin: () => showModal(true),
};

initialize().catch((error) => {
  console.error("No se pudo iniciar Supabase Auth", error);
  setMessage("No pudimos cargar el inicio de sesión. Intenta recargar la página.", true);
  showModal(true);
});
