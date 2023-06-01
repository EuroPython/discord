import logging
import requests
import time

LOG_FILE = "update_tickets.log"

logger = logging.getLogger()

def update_and_sleep() -> None:
    while True:
        logger.info("Refreshing tickets...")
        url = "http://78.94.223.124:15748/tickets/refresh_all/"
        try:
            r = requests.get(url)
            data = r.json()
            message = ""
            if data:
                message = data["message"]
            logger.info(f"Request returned {r.status_code}: {message}")
        except Exception as ex:
            logger.error(ex)
        time.sleep(5*60)
    
    
if __name__ == "__main__":
    
    # configure logging
    file_handler = logging.FileHandler(
        filename=LOG_FILE, encoding="utf-8", mode="a"
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
    update_and_sleep()
