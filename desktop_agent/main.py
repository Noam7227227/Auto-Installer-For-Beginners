import logging
from json import loads
from multiprocessing.connection import Listener
import tempfile
import os

from commands import handleDownloadFileCommand, handleRunProcess, handleAddToPath, handleChocolateyInstallCommand

COMMANDS = {
    # "DownloadFile": handleDownloadFileCommand,
    # "RunProcess": handleRunProcess,
    # "AddToPath": handleAddToPath,
    "ChocoInstall": handleChocolateyInstallCommand
}

address = ('localhost', 21973)

def handle(msg):
    if "recipe_name" not in msg:
        logging.error("Received message without 'recipe_name' field")
        return
    recipe_name = msg["recipe_name"]
    logging.info(f"Received message for recipe: {recipe_name}")
    if "script" not in msg:
        logging.error("Received message without 'script' field")
        return
    with tempfile.TemporaryDirectory() as tmpdirname:
        for step in msg["script"]:
            if "type" not in step:
                logging.error("Received script step without 'type' field")
                return
            step_type = step["type"]
            if step_type not in COMMANDS:
                logging.error(f"Unknown command type: {step_type}")
                return
            logging.info(f"Executing step of type: {step_type}")
            try:
                result = COMMANDS[step_type](step)
                if not result:
                    logging.error(f"Step of type {step_type} failed. Aborting recipe execution.")
                    return
            except Exception as e:
                logging.error(f"Error executing step of type {step_type}: {e}")
                return


def init_logging():
    logging.basicConfig(
        filename=os.path.join(os.path.dirname(__file__), 'agent.log'),
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def main():
    init_logging()

    listener = Listener(address)
    conn = listener.accept()
    try:
        while True:
            json_msg = conn.recv()
            msg = loads(json_msg)
            handle(msg)
    except Exception as e:
        logging.error(f"Error while handling message: {e}")
    listener.close()

if __name__ == "__main__":
    main()
