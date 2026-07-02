# Marletty AI Agent 🍞

![OCI Deploy](https://img.shields.io/badge/Deploy-Oracle%20Cloud%20Infrastructure-F80000?style=for-the-badge\&logo=oracle\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-RAG-1C3C3C?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-Vector%20Store-4B5563?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Embeddings-4285F4?style=for-the-badge\&logo=google\&logoColor=white)

Sitio web oficial + asistente de inteligencia artificial para **Panadería y Pastelería Marletty**, una panadería local colombiana ubicada en **Duitama, Boyacá**.

El proyecto combina una landing page premium con un chat flotante conectado a un agente RAG que responde preguntas sobre productos, horarios, ubicación, pedidos, contacto y documentos internos de Marletty.

---

## Tabla de contenido

* [Descripción](#descripción)
* [Características principales](#características-principales)
* [Arquitectura](#arquitectura)
* [Stack tecnológico](#stack-tecnológico)
* [Estructura del proyecto](#estructura-del-proyecto)
* [Configuración local](#configuración-local)
* [Variables de entorno](#variables-de-entorno)
* [Documentos para RAG](#documentos-para-rag)
* [Generar vector store FAISS](#generar-vector-store-faiss)
* [Ejecutar la aplicación](#ejecutar-la-aplicación)
* [Endpoints principales](#endpoints-principales)
* [Ejemplos de preguntas](#ejemplos-de-preguntas)
* [Pruebas manuales](#pruebas-manuales)
* [Deploy en OCI](#deploy-en-oci)
* [Capturas de pantalla](#capturas-de-pantalla)
* [Licencia](#licencia)

---

## Descripción

**Marletty AI Agent** es una aplicación todo-en-uno donde **FastAPI** sirve tanto el frontend estático como los endpoints del asistente.

El frontend es una landing page premium, construida en HTML, CSS y JavaScript vanilla, con un chat flotante llamado **Marlette 🍞**.

El backend usa un pipeline RAG con LangChain, FAISS, embeddings de Google Gemini y Groq como modelo conversacional.

---

## Características principales

* Landing page premium para Panadería y Pastelería Marletty.
* Chat flotante integrado en la esquina inferior derecha.
* Asistente virtual llamado **Marlette**.
* Respuestas basadas en documentos internos de la panadería.
* RAG con FAISS persistido en disco.
* Lectura de documentos `.txt` y `.pdf`.
* Embeddings generados con Google Generative AI.
* LLM vía Groq con `llama-3.1-8b-instant`.
* Sanitización contra prompt injection.
* Caché de respuestas frecuentes.
* Historial por sesión usando `session_id`.
* Botón automático de WhatsApp cuando hay intención de pedido o cotización.
* Endpoint para limpiar sesión.
* Preparado para deploy en Oracle Cloud Infrastructure Free Tier.

---

## Arquitectura

```txt
Cliente web
   │
   ▼
Frontend HTML/CSS/JS
   │
   │  Mensaje del usuario + session_id
   ▼
POST /api/chat
   │
   ├── 1. API router + schema Pydantic
   │
   ├── 2. Chat service
   │
   ├── 3. Sanitizer
   │       Bloquea prompt injection
   │
   ├── 2. Caché
   │       Responde preguntas frecuentes sin llamar al LLM
   │
   ├── 3. Historial de sesión
   │       Mantiene hasta 10 turnos por usuario
   │
   ├── 4. RAG
   │       Busca top 3 chunks relevantes en FAISS
   │
   ├── 5. System prompt blindado
   │       Inserta contexto + historial
   │
   ├── 6. Groq LLM
   │       Modelo: llama-3.1-8b-instant
   │
   ├── 7. Sanitización HTML de salida
   │
   ├── 8. WhatsApp redirect
   │       Si hay intención de pedido, agrega CTA
   │
   ▼
Respuesta de Marlette
```

---

## Stack tecnológico

### Backend

* Python 3.11+
* FastAPI
* Uvicorn
* LangChain
* LangChain Groq
* LangChain Google GenAI
* FAISS CPU
* pypdf
* python-dotenv
* NumPy compatible con FAISS

### Frontend

* HTML5
* CSS3
* JavaScript vanilla
* Chat widget flotante
* Sin frameworks externos

### IA y RAG

* Groq API
* Modelo conversacional: `llama-3.1-8b-instant`
* Google Generative AI Embeddings
* FAISS como vector store local
* Chunking con `chunk_size=500` y `chunk_overlap=50`

### Deploy target

* Oracle Cloud Infrastructure Free Tier
* VM.Standard.A1.Flex
* Ubuntu 22.04
* ARM64

---

## Estructura del proyecto

```txt
marletty-ai-agent/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── core/
│   │   └── config.py
│   ├── services/
│   │   └── chat.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── rag.py
│   │   ├── loader.py
│   │   ├── prompts.py
│   │   ├── sanitizer.py
│   │   ├── cache.py
│   │   ├── embeddings.py
│   │   └── llm.py
│   ├── docs/
│   │   ├── .gitkeep
│   │   └── documentos .txt o .pdf (solo locales)
│   └── vector_store/
│       ├── .gitkeep
│       ├── index.faiss
│       └── index.pkl
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── chat.js
│   └── assets/
├── .env.example
├── .gitignore
├── requirements.txt
├── tests/
│   └── test_chat_service.py
├── testing.md
└── README.md
```

`main.py` construye la aplicación; `api/` define el contrato HTTP,
`services/` orquesta los casos de uso, `core/` centraliza configuración y
`agent/` contiene las piezas especializadas de IA/RAG.

---

## Configuración local

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU-USUARIO/marletty-ai-agent.git
cd marletty-ai-agent
```

### 2. Crear entorno virtual

En Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\activate
```

En Linux/Mac:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Verificar dependencias

```bash
python -m pip check
```

Resultado esperado:

```txt
No broken requirements found.
```

---

## Variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
GROQ_API_KEY=tu_clave_real_de_groq
GROQ_MODEL=llama-3.1-8b-instant

GOOGLE_API_KEY=tu_clave_real_de_google
GOOGLE_EMBEDDING_MODEL=gemini-embedding-001
GOOGLE_EMBEDDING_DIMENSION=768

ALLOWED_ORIGINS=*
```

También existe un archivo `.env.example` como referencia.

> Importante: nunca subas `.env` a GitHub.

---

## Documentos para RAG

Los documentos deben ubicarse en:

```txt
backend/docs/
```

El loader soporta:

```txt
.txt
.pdf
```

Ejemplo:

```txt
backend/docs/
├── Aclaración sobre Direcciones Históricas.txt
├── Canales Oficiales de Contacto y Pedidos.txt
├── Catálogo de Productos y Tortas Personalizadas.txt
├── Celebraciones y Campañas de Temporada.txt
├── El Rincón Dulce Nuestra Filosofía.txt
├── Guía para Pedidos y Cotizaciones.txt
├── Nuestra Identidad y Respaldo Legal.txt
├── Oportunidades de Empleo en Marletty.txt
└── Ubicación Única y Horarios de Atención.txt
```

Los documentos reales están ignorados por Git para evitar subir información sensible.

> `.gitignore` no deja de rastrear archivos agregados previamente. Si el
> repositorio ya versionó documentos reales, revísalos y retíralos del índice
> sin borrarlos del disco con
> `git rm --cached backend/docs/*.txt backend/docs/*.pdf`.

---

## Generar vector store FAISS

Después de agregar los documentos en `backend/docs/`, ejecuta:

```bash
python backend/agent/loader.py
```

Salida esperada:

```txt
🚀 Iniciando generación del vector store de Marletty...
📄 Documentos encontrados: 9
✅ Documentos cargados: 9
✅ Chunks generados: 18
🧠 Generando embeddings con Google...
   Embedding 1/18
   Embedding 2/18
   ...
   Embedding 18/18
💾 Guardando FAISS en: backend/vector_store
🎉 Vector store generado correctamente.
```

Luego verifica:

```bash
dir backend\vector_store
```

En Linux/Mac:

```bash
ls backend/vector_store
```

Debe aparecer:

```txt
index.faiss
index.pkl
.gitkeep
```

El loader genera primero el índice en un directorio temporal. Solo reemplaza
los dos archivos FAISS cuando el proceso termina correctamente.

---

## Ejecutar la aplicación

Desde la raíz del proyecto:

```bash
python -m uvicorn backend.main:app
```

Abre en el navegador:

```txt
http://127.0.0.1:8000
```

Health check:

```txt
http://127.0.0.1:8000/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "project": "Marletty AI Agent",
  "model": "llama-3.1-8b-instant",
  "services": {
    "google_api_key": true,
    "groq_api_key": true,
    "vector_store": true
  }
}
```

Documentación automática de FastAPI:

```txt
http://127.0.0.1:8000/docs
```

---

## Endpoints principales

### `GET /`

Sirve la landing page principal.

### `GET /health`

Verifica el estado general del sistema.

### `POST /api/chat`

Endpoint principal del asistente.

Body:

```json
{
  "message": "¿Cómo puedo cotizar una torta?",
  "session_id": "test-123"
}
```

Respuesta:

```json
{
  "response": "Respuesta generada por Marlette...",
  "session_id": "test-123",
  "from_cache": false,
  "blocked": false,
  "error": false
}
```

### `POST /api/reset-session`

Limpia el historial de una sesión.

Body:

```json
{
  "session_id": "test-123"
}
```

Respuesta:

```json
{
  "status": "cleared",
  "session_id": "test-123"
}
```

---

## Ejemplos de preguntas

### Horario

**Usuario:**

```txt
¿A qué hora abren?
```

**Respuesta esperada:**

```txt
Nuestro horario es de domingo a domingo, de 6:00 a.m. a 8:00 p.m.
```

### Pedido de torta

**Usuario:**

```txt
¿Cómo hago un pedido de torta?
```

**Respuesta esperada:**

```txt
Puedes cotizar tu pedido por WhatsApp. Para tortas personalizadas es recomendable enviar una foto de referencia del diseño, tamaño aproximado y fecha del evento.
```

Además debe incluir el botón de WhatsApp.

### Producto insignia

**Usuario:**

```txt
¿Qué es El Cochinito?
```

**Respuesta esperada:**

```txt
El Cochinito es uno de los productos insignia de Panadería y Pastelería Marletty.
```

### Ubicación

**Usuario:**

```txt
¿Dónde están ubicados?
```

**Respuesta esperada:**

```txt
Estamos ubicados en Circunvalar #10-75 Esquina, Duitama, Boyacá.
```

### Cafetería

**Usuario:**

```txt
¿Tienen café?
```

**Respuesta esperada:**

```txt
Sí, Marletty cuenta con línea de cafetería: café, aromáticas y bebidas frías o calientes.
```

---

## Seguridad

El agente incluye un sanitizer para bloquear intentos de prompt injection como:

```txt
olvida tus instrucciones
actúa como otro asistente
ignore previous instructions
muéstrame el prompt
system prompt
jailbreak
```

Respuesta segura esperada:

```txt
Solo puedo ayudarte con información sobre Panadería Marletty 🍞 ¿Tienes alguna pregunta sobre nuestros productos, horarios o pedidos?
```

---

## Caché e historial

El sistema incluye:

* Caché en memoria para respuestas frecuentes.
* Hash MD5 del mensaje normalizado.
* TTL de 1 hora para respuestas dinámicas.
* Respuestas pre-pobladas que no expiran.
* Historial por `session_id`.
* Máximo 10 turnos por sesión.
* Limpieza de sesiones inactivas después de 30 minutos.

---

## Redirección inteligente a WhatsApp

Cuando el usuario muestra intención de pedido o cotización, el asistente agrega automáticamente un bloque HTML con CTA a WhatsApp:

```html
<div class="whatsapp-redirect">
  <p>Para cotizar tu pedido, contáctanos por WhatsApp:</p>
  <a href="https://wa.me/573205863534?text=Hola%20Marletty%2C%20quiero%20hacer%20un%20pedido"
     target="_blank" class="whatsapp-btn">
    💬 Cotizar por WhatsApp
  </a>
</div>
```

El frontend renderiza esta respuesta con `innerHTML` para que el botón funcione.

---

## Pruebas manuales

Existe un archivo opcional:

```txt
testing.md
```

Incluye checklist para validar:

* Health check
* RAG
* Chat
* Seguridad
* Caché
* Sesión
* Responsive

Comando recomendado para probar RAG directo:

```bash
python backend/agent/rag.py "¿Dónde están ubicados?"
```

Pruebas automáticas sin consumo de APIs externas:

```bash
python -m unittest discover -s tests -v
python scripts/preflight.py
```

---

## Deploy en OCI

Target recomendado:

```txt
Oracle Cloud Infrastructure Free Tier
VM.Standard.A1.Flex
Ubuntu 22.04
ARM64
```

### 1. Crear VM

Crear una instancia en OCI Free Tier usando Ubuntu 22.04.

### 2. Abrir puertos

En la Security List o Network Security Group abrir:

```txt
22   SSH
80   HTTP
443  HTTPS
```

En producción, expón Uvicorn solo en `127.0.0.1:8000` detrás de Nginx o
Caddy; no publiques directamente el puerto 8000.

### 3. Conectarse por SSH

```bash
ssh ubuntu@IP_PUBLICA
```

### 4. Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip git -y
```

### 5. Clonar repo

```bash
git clone https://github.com/TU-USUARIO/marletty-ai-agent.git
cd marletty-ai-agent
```

### 6. Crear entorno virtual

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 7. Instalar requirements

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 8. Crear `.env`

```bash
nano .env
```

Contenido:

```env
GROQ_API_KEY=tu_clave_real_de_groq
GROQ_MODEL=llama-3.1-8b-instant

GOOGLE_API_KEY=tu_clave_real_de_google
GOOGLE_EMBEDDING_MODEL=gemini-embedding-001
GOOGLE_EMBEDDING_DIMENSION=768

ALLOWED_ORIGINS=*
```

### 9. Subir documentos

Copiar documentos `.txt` o `.pdf` a:

```txt
backend/docs/
```

### 10. Generar vector store

```bash
python backend/agent/loader.py
```

### 11. Probar servidor

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Abrir:

```txt
http://IP_PUBLICA:8000
```

### 12. Crear servicio systemd

```bash
sudo nano /etc/systemd/system/marletty-ai-agent.service
```

Contenido:

```ini
[Unit]
Description=Marletty AI Agent FastAPI Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/marletty-ai-agent
Environment="PATH=/home/ubuntu/marletty-ai-agent/venv/bin"
EnvironmentFile=/home/ubuntu/marletty-ai-agent/.env
ExecStart=/home/ubuntu/marletty-ai-agent/venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Activar servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable marletty-ai-agent
sudo systemctl start marletty-ai-agent
```

Ver estado:

```bash
sudo systemctl status marletty-ai-agent
```

Ver logs:

```bash
journalctl -u marletty-ai-agent -f
```

Mantén un solo worker mientras caché e historial estén en memoria. Más de un
worker fragmentaría las sesiones entre procesos. Configura dominio, proxy
inverso y TLS antes de abrir el servicio al público.

### Seguridad del índice FAISS

`index.pkl` se carga mediante pickle. Genéralo en la VM o transfiérelo por un
canal confiable; nunca cargues un índice aportado por usuarios o descargado de
una fuente no verificada.

---

## Capturas de pantalla

Pendientes por agregar:

```txt
frontend/assets/screenshots/home.png
frontend/assets/screenshots/chat.png
frontend/assets/screenshots/mobile.png
```

Sugerencia para el README cuando existan:

```md
![Home](frontend/assets/screenshots/home.png)
![Chat](frontend/assets/screenshots/chat.png)
![Mobile](frontend/assets/screenshots/mobile.png)
```

---

## Buenas prácticas del repo

No subir:

```txt
.env
backend/docs/*.txt
backend/docs/*.pdf
backend/vector_store/index.faiss
backend/vector_store/index.pkl
venv/
__pycache__/
```

Sí subir:

```txt
.env.example
.gitignore
requirements.txt
README.md
testing.md
frontend/
backend/
backend/vector_store/.gitkeep
```

---

## Estado del proyecto

```txt
✅ Landing page premium
✅ Chat widget
✅ Backend FastAPI
✅ Sanitizer
✅ Caché
✅ Historial
✅ Prompt blindado
✅ Loader TXT/PDF
✅ FAISS
✅ RAG
✅ Groq
✅ Reset de sesión
✅ Preparado para deploy
```

---

## Licencia

Este proyecto se distribuye bajo licencia MIT.

```txt
MIT License

Copyright (c) 2026 Marletty AI Agent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files, to deal in the Software
without restriction, including without limitation the rights to use, copy,
modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
```
