# vuln-blogsystem
后门漏洞应用,(测试用)
应用介绍：
# 博客系统 (Blog System)
基于 Flask + SQLite 的轻量级博客系统。

## 功能特性

- **用户认证**：注册、登录、登出
- **文章管理**：发布、编辑、删除文章
- **多媒体支持**：支持文字、图片、视频、音频多种类型的文章
- **内容审核**：文章发布后需管理员审核
- **分类标签**：支持文章分类和标签管理
- **搜索功能**：支持按标题和内容搜索文章
- **用户中心**：查看和管理个人信息

## 技术栈

- **后端**：Flask (Python)
- **数据库**：SQLite
- **前端**：HTML + CSS + JavaScript
- **模板引擎**：Jinja2

## 项目结构

```
blog-system/
├── app.py              # 主应用文件
├── blog.db             # SQLite数据库
├── schema.sql          # 数据库模式
├── init_data.py        # 数据初始化脚本
├── setup_db.py         # 数据库设置脚本
├── static/
│   └── css/
│       └── style.css   # 样式文件
├── templates/
│   ├── base.html       # 基础模板
│   ├── base_simple.html # 简洁基础模板
│   ├── index.html      # 首页模板
│   ├── login.html      # 登录页面
│   ├── register.html   # 注册页面
│   ├── new_post.html   # 发布文章页面
│   ├── edit_post.html  # 编辑文章页面
│   ├── post_detail.html # 文章详情页面
│   ├── profile.html    # 用户中心页面
│   ├── search.html     # 搜索结果页面
│   ├── errors/         # 错误页面
│   └── review/         # 审核页面
└── README.md           # 项目说明文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install flask
```

### 2. 初始化数据库

```bash
python setup_db.py
```

### 3. 添加示例数据

```bash
python init_data.py
```

### 4. 启动服务器

```bash
python app.py
```

服务器启动后访问：http://127.0.0.1:5000

## 测试账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | Admin@123 | 管理员 |
| user1 | User1@123 | 普通用户 |
| user2 | User2@123 | 普通用户 |
| guest | Guest@123 | 访客用户 |

## 路由说明

### 公开路由
| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页 |
| `/login` | GET/POST | 登录 |
| `/register` | GET/POST | 注册 |
| `/post/<id>` | GET | 文章详情 |
| `/search` | GET | 搜索结果 |

### 需登录路由
| 路由 | 方法 | 说明 |
|------|------|------|
| `/post/new` | GET/POST | 发布文章 |
| `/post/<id>/edit` | GET/POST | 编辑文章 |
| `/post/<id>/delete` | POST | 删除文章 |
| `/profile` | GET | 用户中心 |
| `/logout` | GET | 退出登录 |

### 管理员路由
| 路由 | 方法 | 说明 |
|------|------|------|
| `/admin/review` | GET | 审核列表 |
| `/admin/review/<id>` | GET/POST | 审核文章 |
| `/admin/approve_all` | POST | 批量审核 |

## 文章类型

系统支持以下类型的文章：
- **text**：纯文字文章
- **image**：图文文章（带图片）
- **video**：视频文章（带视频）
- **audio**：音频文章（带音频）

## 内容审核

普通用户发布的文章需要管理员审核后才能在首页显示。
- 文章状态：`pending`（待审核）、`approved`（已通过）、`rejected`（已拒绝）
- 管理员发布的文章直接通过审核

## 数据库结构

### users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 用户ID |
| username | TEXT | 用户名 |
| password | TEXT | 密码（哈希） |
| created_at | TEXT | 创建时间 |

### posts 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 文章ID |
| title | TEXT | 标题 |
| content | TEXT | 内容 |
| author_id | INTEGER | 作者ID |
| created_at | TEXT | 创建时间 |
| media_type | TEXT | 媒体类型 |
| media_url | TEXT | 媒体URL |
| category | TEXT | 分类 |
| tags | TEXT | 标签 |
| status | TEXT | 审核状态 |

## 注意事项

1. 本系统仅供学习和开发测试使用
2. 生产环境请使用更安全的认证机制
3. 定期备份数据库文件
4. 注意保护用户隐私数据

## License

MIT License
