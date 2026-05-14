import logging
from json import loads
from multiprocessing.connection import Listener
import os

from Commands import handleDownloadFileCommand, handleRunProcess, handleAddToPath, handleChocolateyInstallCommand

COMMANDS = {
    # "DownloadFile": handleDownloadFileCommand,
    "RunProcess": handleRunProcess,
    # "AddToPath": handleAddToPath,
    # "ChocoInstall": handleChocolateyInstallCommand
}

address = ('localhost', 21973)

def handle(msg):
    if "type" not in msg:
        logging.error("Received message without 'type' field.")
        return "Malformed message"
    command_type = msg.get("type")
    if command_type not in COMMANDS:
        logging.error(f"Received unknown command type: {command_type}")
        return f"Unknown command type {command_type}"
    try:
        res = COMMANDS[command_type](msg)
    except Exception as e:
        logging.error(f"Error while executing command '{command_type}': {e}")
        return f"Error executing command '{command_type}'"

def init_logging():
    logging.basicConfig(
        filename=os.path.join(os.path.dirname(__file__), 'agent.log'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    init_logging()

    listener = Listener(address)
    while True:
        conn = listener.accept()
        try:
            json_msg = conn.recv()
            logging.info(f"Received message: {json_msg}")
            msg = loads(json_msg)
            logging.info(f"Parsed message: {msg}")
            res = handle(msg)
            conn.send(res)
            conn.close()
        except Exception as e:
            logging.error(f"Error while handling message: {e}")

if __name__ == "__main__":
    main()
