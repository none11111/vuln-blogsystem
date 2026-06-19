import sqlite3

conn = sqlite3.connect('blog.db')
c = conn.cursor()

# 添加审核字段
try:
    c.execute("ALTER TABLE posts ADD COLUMN status TEXT DEFAULT 'pending'")
    c.execute("ALTER TABLE posts ADD COLUMN reviewed_by INTEGER")
    c.execute("ALTER TABLE posts ADD COLUMN reviewed_at TEXT")
    print('Columns added')
except:
    print('Columns exist')

conn.commit()
conn.close()
