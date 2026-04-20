# Monitor de Incidencias

Aplicacion FastAPI para:
- analizar mensajes con reglas de seguridad,
- registrar incidentes en SQLite/JSONL,
- consultar dashboard y vista de base de datos,
- usar un modelo local en Ollama (sin API key externa).

## 1. Requisitos previos

- Windows + PowerShell
- Python 3.11+ instalado, 3.13.7
- `pip` disponible
- Conexion a internet para instalar dependencias/modelo la primera vez

## 2. Crear y activar entorno virtual

Desde la raiz del proyecto:

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
```

## 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

## 4. Configurar variables de entorno

Si no existe `.env`, crealo desde el ejemplo:

```powershell
Copy-Item .env.example .env
```

Valores esperados (por defecto):

```env
DATABASE_URL=sqlite:///./incidents.db
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:3b
```

## 5. Instalar Ollama (Windows)

```powershell
winget install --id Ollama.Ollama -e
```

## 6. Verificar Ollama y descargar modelo

Si `ollama` no se reconoce en terminal, usa ruta absoluta:

```powershell
$ollama = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (!(Test-Path $ollama)) { $ollama = "$env:ProgramFiles\Ollama\ollama.exe" }
if (!(Test-Path $ollama)) { throw "No encuentro ollama.exe" }

& $ollama --version
& $ollama pull qwen2.5:3b
& $ollama list
Invoke-WebRequest -UseBasicParsing http://localhost:11434/api/tags
```

Si devuelve `StatusCode: 200`, Ollama API esta accesible.

## 7. Levantar la API

Con el `.venv` activo:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 8. URLs de la aplicación

- Chat principal: `http://127.0.0.1:8000/`
- Dashboard: `http://127.0.0.1:8000/dashboard`
- ViewBD: `http://127.0.0.1:8000/viewbd`
- Panel check input: `http://127.0.0.1:8000/prompt-check`
- Swagger: `http://127.0.0.1:8000/docs`

## 9. Comprobaciones rapidas

En Swagger (`/docs`) puedes probar:

- `POST /api/sessions`
- `POST /api/messages/analyze`
- `GET /api/incidents`
- `GET /api/messages/detectors`
- `POST /api/prompt-check/analyze`
- `GET /api/prompt-check/detectors`

## 10. Datos y logs

- Base de datos SQLite: `incidents.db`
- Log JSONL: `logs/incidents.jsonl`

## 11. Memoria/RAM (Ollama)

Para ver los modelos cargados:

```powershell
$ollama = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (!(Test-Path $ollama)) { $ollama = "$env:ProgramFiles\Ollama\ollama.exe" }
if (!(Test-Path $ollama)) { throw "No encuentro ollama.exe" }

& $ollama ps
```

Para descargar un modelo de memoria:

```powershell
$ollama = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
if (!(Test-Path $ollama)) { $ollama = "$env:ProgramFiles\Ollama\ollama.exe" }
if (!(Test-Path $ollama)) { throw "No encuentro ollama.exe" }

& $ollama stop qwen2.5:3b
```
