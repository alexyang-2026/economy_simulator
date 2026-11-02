from database import *

def main():
    initialize_database()
    conn = connect_db()

    try:
        print("Welcome to Economy Simulator!")

        ...

    finally:
        conn.close()

if __name__ == "__main__":
    main()