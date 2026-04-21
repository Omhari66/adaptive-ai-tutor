import sqlite3
c = sqlite3.connect("./rag.db")
print("Tables:", [i[0] for i in c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()])
