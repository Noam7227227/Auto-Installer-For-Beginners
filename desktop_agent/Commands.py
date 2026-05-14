import requests
import os
import subprocess
import logging
import re
import winreg
import ctypes

def handleDownloadFileCommand(URL, save_path):
    try:
        # Ensure the directory exists before downloading
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

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
        logging.error(f"Failed to download {URL}: {e}")
        return False

def handleRunProcess(command, outputValidator):
    try:
        # Run the command and capture both stdout and stderr
        result = subprocess.run(command, 
                                check=True, 
                                capture_output=True, 
                                text=True, 
                                shell=True)
        
        # Combine output streams for comprehensive validation
        full_output = (result.stdout + result.stderr).strip()
        logging.info(f"Command Output: {result.stdout}")

        if outputValidator:
            # Use re.search to find the pattern anywhere in the output
            # re.IGNORECASE makes it more robust against minor CLI variations
            if re.search(outputValidator, full_output, re.IGNORECASE | re.DOTALL):
                logging.info(f"Validation passed for: {outputValidator}")
                return True
            else:
                logging.warning(f"Validation failed. Pattern '{outputValidator}' not found.")
                return False
        
        return True # Success if no validator was provided

    except subprocess.CalledProcessError as e:
        logging.error(f"Execution failed: {e.stderr}")
        return False

def handleAddToPath(new_path: str):
    """
    Add a directory to the Windows SYSTEM PATH environment variable
    using direct registry access.

    Requires administrator privileges.
    """

    new_path = os.path.abspath(new_path)

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

