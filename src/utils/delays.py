import random
import time
import logging

def add_random_delay(min_seconds=1, max_seconds=3):
    """
    Apply a randomized delay to mimic human behavior.

    Args:
        min_seconds (int): Minimum delay in seconds.
        max_seconds (int): Maximum delay in seconds.
    """
    delay = random.uniform(min_seconds, max_seconds)
    logging.info(f"Applying a delay of {delay:.2f} seconds...")
    time.sleep(delay)
