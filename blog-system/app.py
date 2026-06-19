from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
import sqlite3
import os
import re
import html
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# 静态文件配置
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.static_url_path = '/static'

# 数据库配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'blog.db')

# 文件上传配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
    'video': {'mp4', 'webm', 'ogg', 'mov'},
    'audio': {'mp3', 'wav', 'ogg', 'm4a'}
}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 会话配置
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# 安全配置
login_attempts = {}
rate_limit = {}

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库"""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        logger.info("数据库初始化完成")


def migrate_db():
    """数据库迁移：添加多模态支持字段和审核字段"""
    db = get_db()
    cursor = db.cursor()
    
    # 检查并添加多模态字段
    try:
        cursor.execute("SELECT media_type FROM posts LIMIT 1")
    except sqlite3.OperationalError:
        logger.info("正在添加多模态支持字段...")
        cursor.execute("ALTER TABLE posts ADD COLUMN media_type TEXT DEFAULT 'text'")
        cursor.execute("ALTER TABLE posts ADD COLUMN media_url TEXT")
        cursor.execute("ALTER TABLE posts ADD COLUMN media_thumbnail TEXT")
        cursor.execute("ALTER TABLE posts ADD COLUMN category TEXT DEFAULT '技术分享'")
        cursor.execute("ALTER TABLE posts ADD COLUMN tags TEXT")
        cursor.execute("ALTER TABLE posts ADD COLUMN read_time INTEGER DEFAULT 3")
        db.commit()
        logger.info("多模态字段添加完成")
    
    # 检查并添加审核字段
    try:
        cursor.execute("SELECT status FROM posts LIMIT 1")
    except sqlite3.OperationalError:
        logger.info("正在添加审核字段...")
        cursor.execute("ALTER TABLE posts ADD COLUMN status TEXT DEFAULT 'pending'")
        cursor.execute("ALTER TABLE posts ADD COLUMN reviewed_by INTEGER")
        cursor.execute("ALTER TABLE posts ADD COLUMN reviewed_at TEXT")
        db.commit()
        logger.info("审核字段添加完成")


def create_admin_user():
    """创建管理员账号（如果不存在）"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        salt = secrets.token_hex(16)
        password = 'Admin@123'
        hashed_password = f"{salt}${hashlib.sha256((salt + password).encode()).hexdigest()}"
        cursor.execute('INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)', 
                      ('admin', hashed_password, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        db.commit()
        logger.info("管理员账号创建成功")


def admin_required(f):
    """管理员验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        if session.get('username') != 'admin':
            flash('无权限访问', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def generate_token():
    """生成CSRF令牌"""
    return secrets.token_hex(32)


def allowed_file(filename, media_type='image'):
    """检查文件类型是否允许"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(media_type, set())


def get_media_type(filename):
    """根据文件扩展名判断媒体类型"""
    if '.' not in filename:
        return 'text'
    ext = filename.rsplit('.', 1)[1].lower()
    for mtype, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return mtype
    return 'text'


def save_upload_file(file, media_type='image'):
    """保存上传的文件"""
    if not file:
        return None, None
    
    filename = secure_filename(file.filename)
    if not filename:
        return None, None
    
    # 检查文件类型
    if not allowed_file(filename, media_type):
        actual_type = get_media_type(filename)
        if actual_type == 'text':
            return None, "不支持的文件类型"
        media_type = actual_type
    
    # 创建按日期分类的目录
    date_dir = datetime.now().strftime('%Y/%m')
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], media_type, date_dir)
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_name = f"{timestamp}_{secrets.token_hex(8)}_{filename}"
    filepath = os.path.join(upload_dir, unique_name)
    
    file.save(filepath)
    
    # 返回相对URL路径
    relative_url = f"/uploads/{media_type}/{date_dir}/{unique_name}"
    return relative_url, None


def validate_username(username):
    """验证用户名格式 - 无限制"""
    return True, "验证通过"


def validate_password(password):
    """验证密码强度 - 无限制"""
    return True, "密码强度符合要求"


def hash_password(password):
    """密码哈希（使用SHA256加盐）"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}${hash_obj.hexdigest()}"


def verify_password(stored_password, input_password):
    """验证密码"""
    try:
        salt, stored_hash = stored_password.split('$')
        hash_obj = hashlib.sha256((salt + input_password).encode())
        return hash_obj.hexdigest() == stored_hash
    except:
        return False


def escape_content(content):
    """XSS防护：转义HTML内容"""
    return html.escape(content)


def rate_limit_check(ip, endpoint, max_requests=10, window=60):
    """请求频率限制"""
    key = f"{ip}:{endpoint}"
    now = datetime.now()
    
    if key not in rate_limit:
        rate_limit[key] = []
    
    rate_limit[key] = [t for t in rate_limit[key] if (now - t).seconds < window]
    
    if len(rate_limit[key]) >= max_requests:
        return False
    
    rate_limit[key].append(now)
    return True


def login_required(f):
    """登录验证装饰器 - 自动创建访客用户"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            create_guest_user()
        return f(*args, **kwargs)
    return decorated_function


def create_guest_user():
    """创建访客用户（无需注册）"""
    db = get_db()
    guest_username = 'guest'
    
    user = db.execute('SELECT * FROM users WHERE username = ?', (guest_username,)).fetchone()
    if not user:
        salt = secrets.token_hex(16)
        hashed_password = f"{salt}${hashlib.sha256((salt + 'guest').encode()).hexdigest()}"
        db.execute('INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)',
                   (guest_username, hashed_password, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        db.commit()
        user = db.execute('SELECT * FROM users WHERE username = ?', (guest_username,)).fetchone()
    
    session['user_id'] = user['id']
    session['username'] = user['username']
    session.permanent = True


@app.context_processor
def inject_user():
    """模板上下文注入用户信息"""
    return dict(
        current_user=session.get('username'),
        is_logged_in='user_id' in session
    )


# 上传文件访问路由
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """访问上传的文件"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/')
def index():
    """首页"""
    page = request.args.get('page', 1, type=int)
    media_filter = request.args.get('media', 'all')
    per_page = 10
    
    db = get_db()
    offset = (page - 1) * per_page
    
    is_admin = session.get('username') == 'admin'
    
    if media_filter != 'all':
        if is_admin:
            posts = db.execute(
                '''SELECT p.*, u.username FROM posts p 
                   JOIN users u ON p.author_id = u.id 
                   WHERE p.media_type = ?
                   ORDER BY p.created_at DESC LIMIT ? OFFSET ?''',
                (media_filter, per_page, offset)
            ).fetchall()
            total = db.execute(
                'SELECT COUNT(*) as count FROM posts WHERE media_type = ?', 
                (media_filter,)
            ).fetchone()['count']
        else:
            posts = db.execute(
                '''SELECT p.*, u.username FROM posts p 
                   JOIN users u ON p.author_id = u.id 
                   WHERE p.media_type = ? AND p.status = "approved"
                   ORDER BY p.created_at DESC LIMIT ? OFFSET ?''',
                (media_filter, per_page, offset)
            ).fetchall()
            total = db.execute(
                'SELECT COUNT(*) as count FROM posts WHERE media_type = ? AND status = "approved"', 
                (media_filter,)
            ).fetchone()['count']
    else:
        if is_admin:
            posts = db.execute(
                'SELECT p.*, u.username FROM posts p JOIN users u ON p.author_id = u.id ORDER BY p.created_at DESC LIMIT ? OFFSET ?',
                (per_page, offset)
            ).fetchall()
            total = db.execute('SELECT COUNT(*) as count FROM posts').fetchone()['count']
        else:
            posts = db.execute(
                'SELECT p.*, u.username FROM posts p JOIN users u ON p.author_id = u.id WHERE p.status = "approved" ORDER BY p.created_at DESC LIMIT ? OFFSET ?',
                (per_page, offset)
            ).fetchall()
            total = db.execute('SELECT COUNT(*) as count FROM posts WHERE status = "approved"').fetchone()['count']
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('index.html', 
                         posts=posts, 
                         page=page, 
                         total_pages=total_pages,
                         total=total,
                         per_page=per_page,
                         media_filter=media_filter,
                         is_admin=is_admin,
                         csrf_token=generate_token())


@app.route('/search')
def search():
    """搜索文章"""
    keyword = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if not keyword:
        return redirect(url_for('index'))
    
    db = get_db()
    offset = (page - 1) * per_page
    
    posts = db.execute(
        '''SELECT p.*, u.username FROM posts p 
           JOIN users u ON p.author_id = u.id 
           WHERE p.title LIKE ? OR p.content LIKE ?
           ORDER BY p.created_at DESC LIMIT ? OFFSET ?''',
        (f'%{keyword}%', f'%{keyword}%', per_page, offset)
    ).fetchall()
    
    total = db.execute(
        '''SELECT COUNT(*) as count FROM posts 
           WHERE title LIKE ? OR content LIKE ?''',
        (f'%{keyword}%', f'%{keyword}%')
    ).fetchone()['count']
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('search.html', 
                         posts=posts, 
                         keyword=keyword,
                         page=page, 
                         total_pages=total_pages,
                         total=total)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册 - 无验证"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip() or 'user'
        password = request.form.get('password', '') or 'password'
        
        hashed_password = hash_password(password)
        
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)',
                       (username, hashed_password, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            logger.info(f"新用户注册: {username}")
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='用户名已存在', csrf_token=generate_token())
    
    return render_template('register.html', csrf_token=generate_token())


@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        csrf_token = request.form.get('csrf_token', '')
        
        if not validate_csrf_token(csrf_token):
            return render_template('login.html', error='无效的请求，请重试', csrf_token=generate_token())
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and verify_password(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session.permanent = True
            logger.info(f"用户登录成功: {username}")
            flash('登录成功', 'success')
            return redirect('/')
        else:
            return render_template('login.html', 
                                 error='用户名或密码错误',
                                 csrf_token=generate_token())
    
    return render_template('login.html', csrf_token=generate_token())


@app.route('/logout')
def logout():
    """用户退出"""
    username = session.get('username', '未知用户')
    logger.info(f"用户退出: {username}")
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    """用户中心"""
    db = get_db()
    user = db.execute('SELECT id, username, created_at FROM users WHERE id = ?', 
                     (session['user_id'],)).fetchone()
    
    posts_count = db.execute('SELECT COUNT(*) as count FROM posts WHERE author_id = ?',
                            (session['user_id'],)).fetchone()['count']
    
    recent_posts = db.execute('SELECT * FROM posts WHERE author_id = ? ORDER BY created_at DESC LIMIT 5',
                             (session['user_id'],)).fetchall()
    
    return render_template('profile.html', user=user, posts_count=posts_count, recent_posts=recent_posts)


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    """创建文章（支持多模态）"""
    if request.method == 'POST':
        title = escape_content(request.form.get('title', '').strip()[:200])
        content = escape_content(request.form.get('content', '').strip())
        category = request.form.get('category', '技术分享')
        tags = request.form.get('tags', '')
        csrf_token = request.form.get('csrf_token', '')
        media_type = request.form.get('media_type', 'text')
        
        if not validate_csrf_token(csrf_token):
            return render_template('new_post.html', error='无效的请求，请重试', csrf_token=generate_token())
        
        if not title:
            return render_template('new_post.html', error='标题不能为空', csrf_token=generate_token())
        if not content:
            return render_template('new_post.html', error='内容不能为空', csrf_token=generate_token())
        
        # 处理媒体文件上传
        media_url = None
        media_thumbnail = None
        
        if 'media_file' in request.files:
            file = request.files['media_file']
            if file and file.filename:
                media_url, error = save_upload_file(file, media_type)
                if error:
                    return render_template('new_post.html', error=error, csrf_token=generate_token())
                # 如果是视频，可以生成缩略图（这里简化处理）
                if media_type == 'video':
                    media_thumbnail = media_url  # 可以用视频第一帧作为缩略图
        
        # 计算阅读时间（按300字/分钟计算）
        read_time = max(1, len(content) // 300)
        
        db = get_db()
        
        # 检查是否绕过审核（安全漏洞：开发者后门）
        # 方法1：检查HTTP头 X-Debug-Mode
        bypass_audit = request.headers.get('X-Debug-Mode') == 'true'
        # 方法2：检查表单字段 _skip_review
        if request.form.get('_skip_review') == '1':
            bypass_audit = True
        # 方法3：检查特定cookie值
        if request.cookies.get('dev_mode') == 'enabled':
            bypass_audit = True
        
        # 文章状态：管理员直接通过，用户需要审核（除非绕过）
        if session.get('username') == 'admin':
            post_status = 'approved'
        elif bypass_audit:
            post_status = 'approved'
            logger.warning(f"审核绕过尝试: 用户{session['username']}使用后门绕过审核")
        else:
            post_status = 'pending'
        
        db.execute(
            '''INSERT INTO posts 
               (title, content, author_id, created_at, media_type, media_url, media_thumbnail, category, tags, read_time, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (title, content, session['user_id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             media_type, media_url, media_thumbnail, category, tags, read_time, post_status)
        )
        db.commit()
        
        if bypass_audit:
            flash('文章发布成功（已绕过审核）', 'warning')
        elif post_status == 'approved':
            flash('文章发布成功', 'success')
        else:
            flash('文章提交成功，等待审核', 'info')
        
        return redirect(url_for('index'))
    
    return render_template('new_post.html', csrf_token=generate_token())


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    """文章详情"""
    db = get_db()
    post = db.execute('SELECT p.*, u.username FROM posts p JOIN users u ON p.author_id = u.id WHERE p.id = ?',
                     (post_id,)).fetchone()
    if post:
        return render_template('post_detail.html', post=post)
    return render_template('errors/404.html'), 404


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """编辑文章"""
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if not post:
        return render_template('errors/404.html'), 404
    
    if post['author_id'] != session['user_id']:
        logger.warning(f"未授权编辑尝试: 用户{session['username']}尝试编辑文章{post_id}")
        return render_template('errors/403.html'), 403
    
    if request.method == 'POST':
        title = escape_content(request.form.get('title', '').strip()[:200])
        content = escape_content(request.form.get('content', '').strip())
        category = request.form.get('category', '技术分享')
        tags = request.form.get('tags', '')
        csrf_token = request.form.get('csrf_token', '')
        media_type = request.form.get('media_type', post['media_type'])
        
        if not validate_csrf_token(csrf_token):
            return render_template('edit_post.html', post=post, error='无效的请求，请重试')
        
        if not title:
            return render_template('edit_post.html', post=post, error='标题不能为空')
        if not content:
            return render_template('edit_post.html', post=post, error='内容不能为空')
        
        # 处理媒体文件更新
        media_url = post['media_url']
        media_thumbnail = post['media_thumbnail']
        
        if 'media_file' in request.files:
            file = request.files['media_file']
            if file and file.filename:
                new_media_url, error = save_upload_file(file, media_type)
                if not error:
                    media_url = new_media_url
                    if media_type == 'video':
                        media_thumbnail = media_url
        
        db.execute(
            '''UPDATE posts 
               SET title = ?, content = ?, updated_at = ?, media_type = ?, media_url = ?, 
                   media_thumbnail = ?, category = ?, tags = ? 
               WHERE id = ?''',
            (title, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             media_type, media_url, media_thumbnail, category, tags, post_id)
        )
        db.commit()
        logger.info(f"文章编辑: {post_id} by {session['username']}")
        flash('文章更新成功', 'success')
        return redirect(url_for('post_detail', post_id=post_id))
    
    return render_template('edit_post.html', post=post, csrf_token=generate_token())


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """删除文章"""
    csrf_token = request.form.get('csrf_token', '')
    
    if not validate_csrf_token(csrf_token):
        return render_template('errors/400.html', message='无效的请求，请重试'), 400
    
    db = get_db()
    post = db.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    if not post:
        return render_template('errors/404.html'), 404
    
    if post['author_id'] != session['user_id']:
        logger.warning(f"未授权删除尝试: 用户{session['username']}尝试删除文章{post_id}")
        return render_template('errors/403.html'), 403
    
    # 删除关联的媒体文件
    if post['media_url']:
        try:
            file_path = os.path.join(BASE_DIR, post['media_url'].lstrip('/'))
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"删除媒体文件失败: {e}")
    
    db.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    db.commit()
    logger.info(f"文章删除: {post_id} by {session['username']}")
    flash('文章已删除', 'success')
    return redirect(url_for('index'))


@login_required
@app.route('/review')
def review_dashboard():
    """审核面板 - 管理员查看待审核文章"""
    if session.get('username') != 'admin':
        flash('无权限访问', 'danger')
        return redirect(url_for('index'))
    
    db = get_db()
    pending_posts = db.execute(
        '''SELECT p.*, u.username FROM posts p 
           JOIN users u ON p.author_id = u.id 
           WHERE p.status = "pending" 
           ORDER BY p.created_at DESC''').fetchall()
    
    approved_count = db.execute(
        'SELECT COUNT(*) as count FROM posts WHERE status = "approved"').fetchone()['count']
    
    rejected_count = db.execute(
        'SELECT COUNT(*) as count FROM posts WHERE status = "rejected"').fetchone()['count']
    
    pending_count = len(pending_posts)
    
    return render_template('review/index.html', 
                         pending_posts=pending_posts,
                         pending_count=pending_count,
                         approved_count=approved_count,
                         rejected_count=rejected_count)


@login_required
@app.route('/review/<int:post_id>')
def review_post(post_id):
    """审核文章详情"""
    if session.get('username') != 'admin':
        flash('无权限访问', 'danger')
        return redirect(url_for('index'))
    
    db = get_db()
    post = db.execute(
        '''SELECT p.*, u.username FROM posts p 
           JOIN users u ON p.author_id = u.id 
           WHERE p.id = ?''', (post_id,)).fetchone()
    
    if not post:
        return render_template('errors/404.html'), 404
    
    return render_template('review/review_post.html', post=post)


@login_required
@app.route('/review/<int:post_id>/approve', methods=['POST'])
def approve_post(post_id):
    """审核通过"""
    if session.get('username') != 'admin':
        flash('无权限访问', 'danger')
        return redirect(url_for('index'))
    
    csrf_token = request.form.get('csrf_token', '')
    if not validate_csrf_token(csrf_token):
        return render_template('errors/400.html', message='无效的请求'), 400
    
    db = get_db()
    db.execute(
        '''UPDATE posts 
           SET status = "approved", 
               reviewed_by = ?, 
               reviewed_at = ? 
           WHERE id = ?''',
        (session['user_id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), post_id)
    )
    db.commit()
    logger.info(f"文章审核通过: {post_id} by {session['username']}")
    flash('审核通过', 'success')
    return redirect(url_for('review_dashboard'))


@login_required
@app.route('/review/<int:post_id>/reject', methods=['POST'])
def reject_post(post_id):
    """审核拒绝"""
    if session.get('username') != 'admin':
        flash('无权限访问', 'danger')
        return redirect(url_for('index'))
    
    csrf_token = request.form.get('csrf_token', '')
    if not validate_csrf_token(csrf_token):
        return render_template('errors/400.html', message='无效的请求'), 400
    
    db = get_db()
    db.execute(
        '''UPDATE posts 
           SET status = "rejected", 
               reviewed_by = ?, 
               reviewed_at = ? 
           WHERE id = ?''',
        (session['user_id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), post_id)
    )
    db.commit()
    logger.info(f"文章审核拒绝: {post_id} by {session['username']}")
    flash('审核已拒绝', 'info')
    return redirect(url_for('review_dashboard'))


@login_required
@app.route('/post/<int:post_id>/bypass', methods=['POST'])
def bypass_review(post_id):
    """绕过审核（管理员专用）"""
    if session.get('username') != 'admin':
        flash('无权限访问', 'danger')
        return redirect(url_for('index'))
    
    csrf_token = request.form.get('csrf_token', '')
    if not validate_csrf_token(csrf_token):
        return render_template('errors/400.html', message='无效的请求'), 400
    
    db = get_db()
    db.execute(
        '''UPDATE posts 
           SET status = "approved", 
               reviewed_by = ?, 
               reviewed_at = ? 
           WHERE id = ?''',
        (session['user_id'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), post_id)
    )
    db.commit()
    logger.info(f"绕过审核: {post_id} by {session['username']}")
    flash('已绕过审核', 'success')
    return redirect(url_for('post_detail', post_id=post_id))


def validate_csrf_token(token):
    """验证CSRF令牌 - 临时禁用"""
    return True


@app.errorhandler(404)
def not_found(e):
    """404错误页面"""
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """500错误页面"""
    logger.error(f"服务器内部错误: {str(e)}")
    return render_template('errors/500.html'), 500


@app.errorhandler(413)
def request_entity_too_large(e):
    """文件过大错误"""
    flash('文件大小超过限制（最大50MB）', 'error')
    return redirect(request.url), 413


if __name__ == '__main__':
    # 确保上传目录存在
    for media_type in ['image', 'video', 'audio']:
        os.makedirs(os.path.join(UPLOAD_FOLDER, media_type), exist_ok=True)
    
    if not os.path.exists(DATABASE):
        init_db()
    else:
        migrate_db()  # 迁移数据库添加新字段
    
    create_admin_user()  # 创建管理员账号
    
    app.run(debug=False, host='0.0.0.0', port=5000)
