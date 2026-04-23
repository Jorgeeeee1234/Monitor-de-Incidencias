$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$envName = "proyecto_seguridad_env"
$promptGuardPort = 8001
$apiHost = "127.0.0.1"
$apiPort = 8000
$envPython = $null

Set-Location $repoRoot

function Test-CondaAvailable {
    if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
        throw "No se encontro 'conda' en PATH. Abre una terminal con Conda inicializado o usa Anaconda Prompt."
    }
}

function Get-CondaBase {
    $condaBase = (& conda info --base).Trim()
    if (-not $condaBase) {
        throw "No se pudo resolver la ruta base de Conda."
    }
    return $condaBase
}

function Resolve-EnvPython {
    $condaBase = Get-CondaBase
    $pythonPath = Join-Path $condaBase "envs\$envName\python.exe"
    if (-not (Test-Path $pythonPath)) {
        throw "No se encontro el interprete del entorno en '$pythonPath'. Crea primero el entorno '$envName'."
    }
    return $pythonPath
}

function Test-EnvFile {
    $envPath = Join-Path $repoRoot ".env"
    if (-not (Test-Path $envPath)) {
        Write-Host "No existe .env. Copiando .env.example..." -ForegroundColor Yellow
        Copy-Item (Join-Path $repoRoot ".env.example") $envPath
    }
}

function Start-PromptGuardWindow {
    $healthUrl = "http://127.0.0.1:$promptGuardPort/health"

    try {
        Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 2 | Out-Null
        Write-Host "Prompt Guard ya esta activo en $healthUrl" -ForegroundColor Green
        return
    }
    catch {
        Write-Host "Iniciando Prompt Guard en una nueva ventana..." -ForegroundColor Cyan
    }

    $promptGuardCommand = @"
Set-Location '$repoRoot'
& '$envPython' -m model.serve_prompt_guard
"@

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-NoProfile",
        "-Command",
        $promptGuardCommand
    ) | Out-Null
}

Test-CondaAvailable
$envPython = Resolve-EnvPython
Test-EnvFile
Start-PromptGuardWindow

Write-Host "Iniciando API principal en http://$apiHost`:$apiPort ..." -ForegroundColor Cyan
& $envPython -m uvicorn app.main:app --reload --host $apiHost --port $apiPort
