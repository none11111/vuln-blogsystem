import sqlite3
import hashlib
import secrets

DATABASE = 'blog.db'

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# 添加审核状态字段
try:
    cursor.execute("ALTER TABLE posts ADD COLUMN status TEXT DEFAULT 'pending'")
    cursor.execute("ALTER TABLE posts ADD COLUMN reviewed_by INTEGER")
    cursor.execute("ALTER TABLE posts ADD COLUMN reviewed_at TEXT")
    print('审核字段添加成功')
except sqlite3.OperationalError:
    print('字段已存在')

# 创建管理员账号（如果不存在）
cursor.execute("SELECT id FROM users WHERE username = 'admin'")
result = cursor.fetchone()
if not result:
    salt = secrets.token_hex(16)
    password = 'Admin@123'
    hashed_password = f'{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}'
    cursor.execute('INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)', 
                  ('admin', hashed_password, '2026-06-19 00:00:00'))
    print('管理员账号创建成功')
else:
    print('管理员账号已存在')

conn.commit()
conn.close()
print('操作完成')
