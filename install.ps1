# ForgeOS V1 - one-command installer (Windows PowerShell).
#
# Usage:  powershell -ExecutionPolicy Bypass -File install.ps1
#
# Installs `uv` if needed, then installs ForgeOS so the `forgeos` command works
# from any terminal. Safe to re-run (idempotent).
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "ForgeOS installer"
Write-Host "================="

# 1. Ensure uv is available.
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "-> Installing uv ..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is installed but not on PATH. Open a NEW PowerShell window and re-run install.ps1."
    exit 1
}
Write-Host "-> uv: $(uv --version)"

# 2. Install ForgeOS (and dependencies) as a global command.
Set-Location $ScriptDir
Write-Host "-> Installing ForgeOS (first run can take a minute) ..."
uv tool install --force .

# Make the global 'forgeos' command available in new terminals (adds uv's tool
# bin directory to PATH). Harmless if already configured.
uv tool update-shell

Write-Host ""
Write-Host "Done. ForgeOS is installed - 'forgeos' is now a global command."
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. forgeos init"
Write-Host '  2. $env:ANTHROPIC_API_KEY="sk-ant-..."      # or: forgeos provider use ollama'
Write-Host "  3. forgeos doctor"
Write-Host "  4. forgeos wizard                            # full getting-started walkthrough"
Write-Host ""
Write-Host "If 'forgeos' is not found, open a NEW PowerShell window (uv adds it to PATH)."
