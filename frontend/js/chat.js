const MARLETTY_CHAT_STORAGE_KEY = "marletty_session_id";

function getSessionId() {
  let sessionId = localStorage.getItem(MARLETTY_CHAT_STORAGE_KEY);

  if (!sessionId) {
    if (window.crypto && crypto.randomUUID) {
      sessionId = crypto.randomUUID();
    } else {
      sessionId = `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }

    localStorage.setItem(MARLETTY_CHAT_STORAGE_KEY, sessionId);
  }

  return sessionId;
}

let sessionId = getSessionId();
let isSendingMessage = false;

function createChatWidget() {
  const widget = document.createElement("section");
  widget.className = "chat-widget";

  widget.innerHTML = `
    <button class="chat-toggle" type="button" aria-label="Abrir chat de Marletty">
      <span>💬</span>
    </button>

    <div class="chat-panel" aria-live="polite">
      <div class="chat-header">
        <div class="chat-header-info">
          <span class="chat-status-dot"></span>
          <strong>Marlette 🍞</strong>
          <small id="chatStatusText">En línea</small>
        </div>

        <div class="chat-header-actions">
          <button class="chat-reset" type="button" aria-label="Limpiar conversación" title="Limpiar conversación">
            ↻
          </button>

          <button class="chat-close" type="button" aria-label="Cerrar chat">
            ×
          </button>
        </div>
      </div>

      <div class="chat-messages" id="chatMessages"></div>

      <form class="chat-form" id="chatForm">
        <input
          id="chatInput"
          type="text"
          placeholder="Pregúntale a Marlette..."
          autocomplete="off"
          maxlength="2000"
          required
        />
        <button id="chatSubmitButton" type="submit" aria-label="Enviar mensaje">
          Enviar
        </button>
      </form>
    </div>
  `;

  document.body.appendChild(widget);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function addMessage(content, sender = "bot", renderHtml = false, variant = "") {
  const messagesContainer = document.getElementById("chatMessages");

  const message = document.createElement("div");
  message.className = `chat-message ${sender}`;

  if (variant) {
    message.classList.add(variant);
  }

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";

  if (renderHtml) {
    bubble.innerHTML = content;
  } else {
    bubble.innerHTML = escapeHtml(content);
  }

  message.appendChild(bubble);
  messagesContainer.appendChild(message);
  scrollChatToBottom();
}

function scrollChatToBottom() {
  const messagesContainer = document.getElementById("chatMessages");

  if (!messagesContainer) {
    return;
  }

  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function setChatStatus(text) {
  const statusText = document.getElementById("chatStatusText");

  if (statusText) {
    statusText.textContent = text;
  }
}

function setFormState(disabled) {
  const input = document.getElementById("chatInput");
  const submitButton = document.getElementById("chatSubmitButton");

  input.disabled = disabled;
  submitButton.disabled = disabled;

  if (disabled) {
    submitButton.textContent = "Enviando";
  } else {
    submitButton.textContent = "Enviar";
  }
}

function addTypingMessage() {
  const messagesContainer = document.getElementById("chatMessages");

  const typing = document.createElement("div");
  typing.className = "chat-message bot";
  typing.id = "typingMessage";

  typing.innerHTML = `
    <div class="chat-bubble typing-bubble" aria-label="Marlette está escribiendo">
      <span></span>
      <span></span>
      <span></span>
    </div>
  `;

  messagesContainer.appendChild(typing);
  scrollChatToBottom();
  setChatStatus("Escribiendo...");
}

function removeTypingMessage() {
  const typing = document.getElementById("typingMessage");

  if (typing) {
    typing.remove();
  }

  setChatStatus("En línea");
}

async function sendMessageToBackend(message) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error("No se pudo obtener respuesta del servidor.");
  }

  return response.json();
}

async function resetSessionOnBackend() {
  const response = await fetch("/api/reset-session", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error("No se pudo limpiar la sesión.");
  }

  return response.json();
}

function showWelcomeMessage() {
  addMessage(
    "¡Hola! Soy Marlette 🍞, tu asistente virtual de Panadería Marletty. Puedo ayudarte con productos, horarios, ubicación, pedidos, tortas personalizadas y cotizaciones 🎂",
    "bot",
    false
  );
}

function clearChatMessages() {
  const messagesContainer = document.getElementById("chatMessages");

  if (messagesContainer) {
    messagesContainer.innerHTML = "";
  }
}

async function handleResetConversation() {
  const resetButton = document.querySelector(".chat-reset");

  if (resetButton) {
    resetButton.disabled = true;
  }

  try {
    await resetSessionOnBackend();

    localStorage.removeItem(MARLETTY_CHAT_STORAGE_KEY);
    sessionId = getSessionId();

    clearChatMessages();

    addMessage(
      "Listo 🍞 Limpié esta conversación. Podemos empezar de nuevo.",
      "bot",
      false,
      "system"
    );

    showWelcomeMessage();
  } catch (error) {
    addMessage(
      "No pude limpiar la conversación en este momento. Intenta nuevamente.",
      "bot",
      false,
      "error"
    );

    console.error(error);
  } finally {
    if (resetButton) {
      resetButton.disabled = false;
    }
  }
}

function setupChatEvents() {
  const widget = document.querySelector(".chat-widget");
  const toggle = document.querySelector(".chat-toggle");
  const close = document.querySelector(".chat-close");
  const reset = document.querySelector(".chat-reset");
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");

  toggle.addEventListener("click", () => {
    widget.classList.add("is-open");
    input.focus();
    scrollChatToBottom();
  });

  close.addEventListener("click", () => {
    widget.classList.remove("is-open");
  });

  reset.addEventListener("click", async () => {
    await handleResetConversation();
    input.focus();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (isSendingMessage) {
      return;
    }

    const message = input.value.trim();

    if (!message) {
      return;
    }

    isSendingMessage = true;

    addMessage(message, "user", false);
    input.value = "";
    setFormState(true);
    addTypingMessage();

    try {
      const data = await sendMessageToBackend(message);

      removeTypingMessage();

      if (data.error) {
        addMessage(data.response, "bot", true, "error");
      } else if (data.blocked) {
        addMessage(data.response, "bot", false, "system");
      } else {
        addMessage(data.response, "bot", true);
      }
    } catch (error) {
      removeTypingMessage();

      addMessage(
        "Lo siento, en este momento no pude responder. Revisa tu conexión o intenta de nuevo en unos segundos.",
        "bot",
        false,
        "error"
      );

      console.error(error);
    } finally {
      isSendingMessage = false;
      setFormState(false);
      input.focus();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  createChatWidget();
  setupChatEvents();
  showWelcomeMessage();

  console.log("Marletty AI Agent chat premium cargado correctamente.");
});