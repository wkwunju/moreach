# 🔐 Moreach 认证系统

完整的用户注册和登录系统，支持邮箱密码认证。

## ✨ 功能特性

- ✅ **邮箱密码注册** - 安全的用户注册流程
- ✅ **JWT认证** - 基于token的无状态认证
- ✅ **密码加密** - bcrypt哈希保护
- ✅ **用户资料收集** - 行业、职位、使用类型等
- ✅ **表单验证** - 前后端双重验证
- ✅ **错误处理** - 友好的错误提示
- ✅ **自动登录** - 注册后自动登录
- ✅ **Token管理** - 7天有效期

## 🚀 快速开始

### 1. 安装和迁移

```bash
# 后端
cd backend
pip install -r requirements.txt
python scripts/migrate_add_users.py

# 前端
cd frontend
npm install
```

### 2. 启动服务

```bash
# 后端 (终端1)
cd backend
uvicorn app.main:app --reload

# 前端 (终端2)
cd frontend
npm run dev
```

### 3. 访问

- 注册: http://localhost:3000/register
- 登录: http://localhost:3000/login

## 📋 用户信息收集

### 必填信息
- **邮箱** - 用于登录
- **密码** - 最少8字符
- **全名** - 用户真实姓名
- **行业** - 11个选项（见下方）
- **使用类型** - 个人/代理/团队

### 可选信息
- **公司** - 公司名称
- **职位** - 工作职位

## 🏭 行业选项

系统支持以下与moreach相关的行业：

| 行业 | 说明 |
|------|------|
| E-commerce | 电商平台 |
| SaaS | 软件即服务 |
| Marketing Agency | 营销代理公司 |
| Content Creator | 内容创作者/网红 |
| Retail | 零售商 |
| Fashion & Beauty | 时尚美妆 |
| Health & Fitness | 健康健身 |
| Food & Beverage | 餐饮行业 |
| Technology | 科技公司 |
| Education | 教育培训 |
| Other | 其他行业 |

## 💼 使用类型

| 类型 | 说明 |
|------|------|
| Personal Use | 个人使用 - 为自己的业务使用 |
| Agency Use | 代理使用 - 为客户管理营销活动 |
| Team Use | 团队使用 - 营销团队的一员 |

## 🔒 安全特性

1. **密码加密** - bcrypt哈希，不可逆
2. **JWT Token** - 签名验证，7天过期
3. **邮箱唯一** - 防止重复注册
4. **账户状态** - 支持账户激活/停用
5. **前后端验证** - 双重数据验证

## 📚 文档

- **[快速启动](QUICKSTART_AUTH.md)** - 3步启动系统
- **[设置指南](SETUP_AUTH.md)** - 详细配置说明

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代Python Web框架
- **SQLAlchemy** - ORM
- **SQLite** - 数据库
- **python-jose** - JWT处理
- **passlib** - 密码加密
- **pydantic** - 数据验证

### 前端
- **Next.js 13+** - React框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架

## 📡 API端点

### 注册
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "company": "Acme Inc.",
  "job_title": "Marketing Manager",
  "industry": "SaaS",
  "usage_type": "Personal Use"
}
```

### 登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### 获取当前用户
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

## 🧪 测试

### 自动测试
```bash
cd backend
python scripts/test_auth.py
```

### 手动测试
1. 访问 http://localhost:3000/register
2. 填写表单并提交
3. 自动跳转到 `/reddit`
4. 检查localStorage中的token

## 🔧 配置

### 环境变量

在生产环境中，设置以下环境变量：

```bash
# .env
SECRET_KEY=your-very-secure-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7天
```

### 生产环境检查清单

- [ ] 更改 `SECRET_KEY` 为随机密钥
- [ ] 启用HTTPS
- [ ] 配置CORS域名
- [ ] 设置速率限制
- [ ] 启用日志记录
- [ ] 配置邮件服务（用于验证）
- [ ] 设置数据库备份
- [ ] 添加监控和告警

## 🎯 使用示例

### 前端 - 注册用户
```typescript
const response = await fetch("http://localhost:8000/api/v1/auth/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password123",
    full_name: "John Doe",
    industry: "SaaS",
    usage_type: "Personal Use"
  })
});

const data = await response.json();
localStorage.setItem("token", data.access_token);
```

### 前端 - 认证请求
```typescript
const token = localStorage.getItem("token");

const response = await fetch("http://localhost:8000/api/v1/some-endpoint", {
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  }
});
```

### 后端 - 保护路由
```python
from app.core.auth import get_current_user
from app.models.tables import User

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Hello {current_user.full_name}",
        "email": current_user.email,
        "industry": current_user.industry.value
    }
```

## 🐛 故障排除

### 问题: "Email already registered"
**解决**: 该邮箱已被使用，请使用其他邮箱或登录。

### 问题: "Incorrect email or password"
**解决**: 检查邮箱和密码是否正确，密码区分大小写。

### 问题: "Could not validate credentials"
**解决**: Token可能已过期，请重新登录。

### 问题: 后端连接失败
**解决**: 
1. 确保后端运行在 http://localhost:8000
2. 检查CORS配置
3. 查看浏览器控制台错误

### 问题: 数据库错误
**解决**: 运行迁移脚本
```bash
cd backend
python scripts/migrate_add_users.py
```

## 📈 后续改进

### 短期 (1-2周)
- [ ] 邮箱验证
- [ ] 密码重置
- [ ] 用户资料更新
- [ ] 记住我功能

### 中期 (1-2月)
- [ ] OAuth登录 (Google, GitHub)
- [ ] 双因素认证 (2FA)
- [ ] 会话管理
- [ ] API速率限制

### 长期 (3-6月)
- [ ] 用户活动日志
- [ ] 高级权限系统
- [ ] 团队管理
- [ ] SSO集成

## 💡 最佳实践

1. **永远不要**在日志中记录密码
2. **始终**使用HTTPS传输敏感数据
3. **定期**更新依赖包
4. **实施**速率限制防止暴力攻击
5. **监控**异常登录活动
6. **备份**用户数据
7. **测试**所有认证流程

## 🤝 贡献

如需改进认证系统，请：
1. 创建feature分支
2. 实现功能并测试
3. 更新文档
4. 提交PR

## 📄 许可

本项目遵循项目主许可证。

## 📞 支持

如有问题，请查看：
- [快速启动](QUICKSTART_AUTH.md)
- [详细文档](SETUP_AUTH.md)

---

**版本**: 1.0.0  
**更新日期**: 2026-01-23  
**状态**: ✅ 生产就绪

