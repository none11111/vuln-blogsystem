with open('templates/login.html', 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - TechBlog</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            width: 100%;
            max-width: 420px;
        }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo-icon {
            width: 64px; height: 64px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 16px;
            display: flex; justify-content: center; align-items: center;
            margin: 0 auto 16px;
        }
        .logo-icon svg { width: 32px; height: 32px; fill: white; }
        .logo-title { font-size: 24px; font-weight: 700; color: #1a1a2e; }
        .logo-subtitle { font-size: 14px; color: #666; margin-top: 4px; }
        .form-group { margin-bottom: 20px; }
        .form-label { display: block; font-size: 14px; font-weight: 600; color: #333; margin-bottom: 8px; }
        .form-input {
            width: 100%; padding: 14px 16px;
            border: 2px solid #e0e0e0; border-radius: 12px;
            font-size: 16px; background: #f8f9fa;
        }
        .form-input:focus {
            outline: none; border-color: #667eea;
            background: white;
        }
        .error-message {
            background: #fee2e2; color: #dc2626;
            padding: 12px 16px; border-radius: 8px;
            margin-bottom: 16px; font-size: 14px;
        }
        .login-btn {
            width: 100%; padding: 14px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; border: none; border-radius: 12px;
            font-size: 16px; font-weight: 600; cursor: pointer;
        }
        .register-link { text-align: center; margin-top: 20px; font-size: 14px; color: #666; }
        .register-link a { color: #667eea; text-decoration: none; }
        .back-home { text-align: center; margin-top: 12px; font-size: 13px; }
        .back-home a { color: #999; text-decoration: none; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <div class="logo-icon">
                <svg viewBox="0 0 24 24">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                </svg>
            </div>
            <div class="logo-title">TechBlog</div>
            <div class="logo-subtitle">登录您的账户</div>
        </div>
        <form method="post">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            {% if error %}<div class="error-message">{{ error }}</div>{% endif %}
            <div class="form-group"><label class="form-label">用户名</label><input type="text" name="username" class="form-input" required autofocus placeholder="请输入用户名"></div>
            <div class="form-group"><label class="form-label">密码</label><input type="password" name="password" class="form-input" required placeholder="请输入密码"></div>
            <button type="submit" class="login-btn">登录</button>
        </form>
        <div class="register-link">还没有账号？<a href="{{ url_for('register') }}">立即注册</a></div>
        <div class="back-home"><a href="{{ url_for('index') }}">← 返回首页</a></div>
    </div>
</body>
</html>''')
print('done')