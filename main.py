from database import *
from markets import *
import time

def main():
    initialize_database()
    conn = connect_db()

    try:
        print("Welcome to Economy Simulator!")

        ...

    finally:
        conn.close()

if __name__ == "__main__":
    current_state = 2
    next_update = schedule_next_market_update()

    while True:
        current_state, next_update = process_market_updates(current_state, next_update)
        time.sleep(1)