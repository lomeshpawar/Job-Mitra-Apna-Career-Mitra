import sqlite3

conn = sqlite3.connect('jobmitra_local.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print("Tables in jobmitra_local.db:")
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cur.fetchone()[0]
    print(f"\nTable: {t} (Rows: {cnt})")
    cur.execute(f"PRAGMA table_info({t})")
    columns = cur.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]}) PK={col[5]} NOTNULL={col[3]} DEFAULT={col[4]}")
    cur.execute(f"PRAGMA index_list({t})")
    indexes = cur.fetchall()
    if indexes:
        print(f"  Indexes: {indexes}")
conn.close()

conn = sqlite3.connect('jobmitra_local.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
print("\n--- Jobs in Database ---")
for r in cur.execute("SELECT id, title, company, stream, is_verified, is_premium FROM jobs"):
    print(f"ID {r['id']}: {r['title']} @ {r['company']} [{r['stream']}] verified={r['is_verified']} premium={r['is_premium']}")
conn.close()

