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

const sessionId = getSessionId();

function createChatWidget() {
  const widget = document.createElement("section");
  widget.className = "chat-widget";
  widget.innerHTML = `
    <button class="chat-toggle" type="button" aria-label="Abrir chat de Marletty">
      <span>💬</span>
    </button>

    <div class="chat-panel" aria-live="polite">
      <div class="chat-header">
        <div>
          <span class="chat-status-dot"></span>
          <strong>Marlette 🍞</strong>
          <small>En línea</small>
        </div>

        <button class="chat-close" type="button" aria-label="Cerrar chat">
          ×
        </button>
      </div>

      <div class="chat-messages" id="chatMessages"></div>

      <form class="chat-form" id="chatForm">
        <input
          id="chatInput"
          type="text"
          placeholder="Escribe tu mensaje..."
          autocomplete="off"
          required
        />
        <button type="submit" aria-label="Enviar mensaje">
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

function addMessage(content, sender = "bot", renderHtml = false) {
  const messagesContainer = document.getElementById("chatMessages");

  const message = document.createElement("div");
  message.className = `chat-message ${sender}`;

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";

  if (renderHtml) {
    bubble.innerHTML = content;
  } else {
    bubble.innerHTML = escapeHtml(content);
  }

  message.appendChild(bubble);
  messagesContainer.appendChild(message);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingMessage() {
  const messagesContainer = document.getElementById("chatMessages");

  const typing = document.createElement("div");
  typing.className = "chat-message bot";
  typing.id = "typingMessage";
  typing.innerHTML = `
    <div class="chat-bubble typing-bubble">
      <span></span>
      <span></span>
      <span></span>
    </div>
  `;

  messagesContainer.appendChild(typing);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingMessage() {
  const typing = document.getElementById("typingMessage");

  if (typing) {
    typing.remove();
  }
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

function setupChatEvents() {
  const widget = document.querySelector(".chat-widget");
  const toggle = document.querySelector(".chat-toggle");
  const close = document.querySelector(".chat-close");
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");

  toggle.addEventListener("click", () => {
    widget.classList.add("is-open");
    input.focus();
  });

  close.addEventListener("click", () => {
    widget.classList.remove("is-open");
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = input.value.trim();

    if (!message) {
      return;
    }

    addMessage(message, "user", false);
    input.value = "";
    input.disabled = true;

    addTypingMessage();

    try {
      const data = await sendMessageToBackend(message);

      removeTypingMessage();
      addMessage(data.response, "bot", true);
    } catch (error) {
      removeTypingMessage();

      addMessage(
        "Lo siento, en este momento no pude responder. Intenta de nuevo en unos segundos.",
        "bot",
        false
      );

      console.error(error);
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
}

function showWelcomeMessage() {
  addMessage(
    "¡Hola! Soy Marlette 🍞, tu asistente virtual de Panadería Marletty. ¿En qué te puedo ayudar hoy? Puedo contarte sobre nuestros productos, horarios, ubicación o cómo hacer tu pedido 🎂",
    "bot",
    false
  );
}

document.addEventListener("DOMContentLoaded", () => {
  createChatWidget();
  setupChatEvents();
  showWelcomeMessage();

  console.log("Marletty AI Agent chat cargado correctamente.");
});