import logging
from json import loads
from multiprocessing.connection import Listener
import os

address = ('localhost', 21973)

def handle(msg):
    if "recipe_name" not in msg:
        logging.warning("Received message without 'recipe_name' field")
        return
    recipe_name = msg["recipe_name"]
    logging.info(f"Received message for recipe: {recipe_name}")
    # TODO - handle according to type

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
