import requests
import os
import subprocess
import logging
import re
import winreg
import ctypes

def handleDownloadFileCommand(args):
    URL = args.get("URL")
    save_path = args.get("save_path")
    try:
        # Stream=True allows us to download in chunks
        with requests.get(URL, stream=True, timeout=30) as r:
            r.raise_for_status() # Check if the URL is valid/accessible
            
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        
        logging.info(f"Successfully downloaded to: {save_path}")
        return True

    except Exception as e:
        logging.error(f"Failed to download {URL} to {save_path}: {e}")
        return False

ALLOWED_COMMANDS = [
    "pip install",
    "npm install",
    "choco install",
    "winget install",
]

def handleRunProcess(args):
    command = args.get("Command")
    outputValidator = args.get("OutputValidator")
    validate_command = any(command.lower().startswith(ac) for ac in ALLOWED_COMMANDS)
    if not validate_command:
        logging.error(f"Command '{command}' is not allowed.")
        return False
    if command.lower().startswith("choco install"):
        if not command.lower().endswith(" -y"):
            command += " -y"
    try:
        # Run the command and capture both stdout and stderr
        result = subprocess.run(command, 
                                check=True, 
                                capture_output=True, 
                                text=True,
                                encoding="utf-8",
                                shell=True)

        # Combine output streams for comprehensive validation
        full_output = (result.stdout + result.stderr).strip()
        logging.info(f"Command Output: {result.stdout}")

        if outputValidator:
            # Use re.search to find the pattern anywhere in the output
            # re.IGNORECASE makes it more robust against minor CLI variations
            if re.search(outputValidator, full_output, re.IGNORECASE | re.DOTALL):
                logging.info(f"Validation passed for: {outputValidator}")
                return full_output
            else:
                logging.warning(f"Validation failed. Pattern '{outputValidator}' not found.")
                return ""
        
        return full_output # Success if no validator was provided

    except subprocess.CalledProcessError as e:
        logging.error(f"Execution failed: {e.stderr}")
        return ""

def handleAddToPath(args):
    """
    Add a directory to the Windows SYSTEM PATH environment variable
    using direct registry access.

    Requires administrator privileges.
    """
    new_path = os.path.abspath(args.get("Path"))

    reg_key = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"

    # Open the registry key with read/write access
    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        reg_key,
        0,
        winreg.KEY_READ | winreg.KEY_WRITE,
    ) as key:

        # Read current PATH
        current_path, reg_type = winreg.QueryValueEx(key, "Path")

        paths = current_path.split(";")

        # Avoid duplicates (case-insensitive)
        normalized = [p.lower().rstrip("\\") for p in paths]
        candidate = new_path.lower().rstrip("\\")

        if candidate in normalized:
            logging.info("Path already exists in SYSTEM PATH.")
            return

        # Append new path
        updated_path = current_path.rstrip(";") + ";" + new_path

        # Write updated PATH back to registry
        winreg.SetValueEx(
            key,
            "Path",
            0,
            reg_type,
            updated_path,
        )

    current_process_path = os.environ.get("PATH", "")

    process_paths = current_process_path.split(";")
    normalized_process = [p.lower().rstrip("\\") for p in process_paths]

    if candidate not in normalized_process:
        os.environ["PATH"] = (
            current_process_path.rstrip(";") + ";" + new_path
        )

    # Notify running applications that environment changed
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A

    ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        "Environment",
        0x0002,  # SMTO_ABORTIFHUNG
        5000,
        None,
    )

    logging.info(f"Added to SYSTEM PATH: {new_path}")

def handleChocolateyInstallCommand(args):
    package_name = args.get("PackageName")
    try:
        result = subprocess.run(
            ["choco", "install", package_name, "-y"],
            check=True,
            capture_output=True,
            text=True,
            shell=True
        )
        logging.info(f"Chocolatey install output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Chocolatey install failed: {e.stderr}")
        return False
