# Install the desktop-agent as a service
## Remove if it already exists
tools/nssm64.exe stop AIFB
tools/nssm64.exe remove AIFB confirm

## Install the service
tools/nssm64.exe install AIFB "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\desktop-agent\main.py"
tools/nssm64.exe start AIFB
