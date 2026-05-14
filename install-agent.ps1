# Install the desktop-agent as a service

## Remove if it already exists
tools/nssm64.exe stop AIFB
tools/nssm64.exe remove AIFB confirm

## Install the service
tools/nssm64.exe install AIFB "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\desktop_agent\main.py"
tools/nssm64.exe start AIFB

# Ensure chocolatey is installed

## Check if Chocolatey is installed
try {
    $version = choco --version
    Write-Host "Chocolatey version: $version"
}
catch {
    Write-Host "Chocolatey is NOT installed."
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}
