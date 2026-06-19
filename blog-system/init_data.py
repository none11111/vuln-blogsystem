import sqlite3
import hashlib
import secrets
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'blog.db')


def hash_password(password):
    """密码哈希（使用SHA256加盐）"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}${hash_obj.hexdigest()}"


def add_sample_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    sample_users = [
        ('admin', 'Admin@123'),      # 管理员
        ('user1', 'User1@123'),      # 测试用户1
        ('user2', 'User2@123'),      # 测试用户2
        ('guest', 'Guest@123')       # 访客用户
    ]
    
    for username, password in sample_users:
        hashed_password = hash_password(password)
        try:
            cursor.execute('INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)',
                         (username, hashed_password, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            print(f"用户 '{username}' 创建成功 (密码: {password})")
        except sqlite3.IntegrityError:
            print(f"用户 '{username}' 已存在，跳过")
    
    sample_posts = [
        (1, '欢迎来到我的博客', '这是我的第一篇博客文章！很高兴能在这里分享我的技术心得和生活感悟。\n\n博客系统功能包括：\n- 用户注册和登录\n- 文章发布和管理\n- 文章编辑和删除\n- 文章搜索功能\n- 用户中心\n\n希望大家喜欢！', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        
        (1, 'Flask框架入门教程', 'Flask是一个轻量级的Python Web框架，非常适合快速开发Web应用。\n\n## 安装Flask\n```bash\npip install flask\n```\n\n## 创建简单应用\n```python\nfrom flask import Flask\napp = Flask(__name__)\n\n@app.route("/")\ndef hello():\n    return "Hello, World!"\n\nif __name__ == "__main__":\n    app.run()\n```\n\nFlask的特点是简洁易用，扩展性强。', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        
        (2, 'Python学习笔记', 'Python是一门非常优雅的编程语言，语法简洁，功能强大。\n\n### 数据类型\n- int: 整数\n- str: 字符串\n- list: 列表\n- dict: 字典\n\n### 常用库\n- requests: HTTP请求\n- pandas: 数据分析\n- numpy: 数值计算\n\nPython的应用领域非常广泛。', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        
        (2, '信息安全基础知识', '信息安全是当今互联网时代非常重要的话题。\n\n## 三大安全目标\n1. **保密性**: 确保信息不被未授权访问\n2. **完整性**: 确保信息不被篡改\n3. **可用性**: 确保信息在需要时可用\n\n## 常见威胁\n- SQL注入\n- XSS攻击\n- CSRF攻击\n\n学习信息安全知识对于每个开发者都很重要。', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        
        (3, 'Web开发最佳实践', '在Web开发中，有很多值得注意的最佳实践。\n\n### 安全方面\n- 使用参数化查询防止SQL注入\n- 对用户输入进行验证和过滤\n- 使用HTTPS加密传输\n- 添加CSRF令牌保护\n\n### 性能方面\n- 合理使用缓存\n- 优化数据库查询\n- 压缩静态资源\n\n遵循最佳实践可以大大提高应用的质量。', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        
        (3, '数据库设计原则', '良好的数据库设计是构建可靠应用的基础。\n\n## 设计原则\n1. **规范化**: 减少数据冗余\n2. **索引优化**: 加快查询速度\n3. **外键约束**: 保证数据完整性\n\n## 注意事项\n- 避免过度规范化\n- 选择合适的数据类型\n- 定期维护和优化\n\n推荐使用SQLite进行小型项目开发。', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        
        (4, '算法与数据结构', '算法和数据结构是计算机科学的基础。\n\n## 常用数据结构\n- 数组\n- 链表\n- 树\n- 图\n- 哈希表\n\n## 排序算法\n- 冒泡排序\n- 快速排序\n- 归并排序\n\n选择合适的数据结构可以大大提高算法效率。', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    ]
    
    for author_id, title, content, created_at in sample_posts:
        try:
            cursor.execute('INSERT INTO posts (title, content, author_id, created_at) VALUES (?, ?, ?, ?)',
                         (title, content, author_id, created_at))
            print(f"文章 '{title}' 创建成功")
        except Exception as e:
            print(f"文章 '{title}' 创建失败: {e}")
    
    conn.commit()
    conn.close()
    print("\n示例数据添加完成！")
    print("\n测试账号:")
    print("- admin / Admin@123 (管理员)")
    print("- user1 / User1@123")
    print("- user2 / User2@123")
    print("- guest / Guest@123")


if __name__ == '__main__':
    add_sample_data()