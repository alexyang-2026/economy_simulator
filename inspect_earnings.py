import database
import numpy as np

conn = database.connect_db()

current_day = conn.execute(
    "SELECT current_day FROM simulation_state WHERE id = 1"
).fetchone()[0]

print(f"Current game day: {current_day}")

rows = conn.execute("""
    SELECT corporation_id, start_day, end_day, profits
    FROM corporation_earnings_history
    ORDER BY corporation_id, start_day
""").fetchall()

for corporation_id, start_day, end_day, blob in rows:
    profits = np.frombuffer(blob, dtype=np.float64)

    print(f"\nCorporation: {corporation_id}")
    print(f"Chunk: Days {start_day}–{end_day}")
    print(f"Recorded days: {len(profits)}")
    print(f"Daily profits: {profits}")
    print(f"Total earnings: ${np.sum(profits):,.2f}")

conn.close()