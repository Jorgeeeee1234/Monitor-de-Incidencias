$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$envPath = Join-Path $repoRoot ".env"
$exampleEnvPath = Join-Path $repoRoot ".env.example"

Set-Location $repoRoot

function Test-DockerAvailable {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "No se encontro 'docker' en PATH. Instala Docker Desktop y vuelve a intentarlo."
    }

    try {
        docker info | Out-Null
    }
    catch {
        throw "Docker Desktop no parece estar arrancado. Abre Docker Desktop y vuelve a ejecutar el script."
    }
}

function Ensure-EnvFile {
    if (-not (Test-Path $envPath)) {
        if (-not (Test-Path $exampleEnvPath)) {
            throw "No existe .env ni .env.example."
        }

        Write-Host "No existe .env. Copiando .env.example..." -ForegroundColor Yellow
        Copy-Item $exampleEnvPath $envPath
    }
}

Test-DockerAvailable
Ensure-EnvFile

Write-Host "Levantando stack Docker (Ollama + Prompt Guard + API)..." -ForegroundColor Cyan
docker compose up --build
