# 🚀 认证系统快速启动指南

## 3步启动认证系统

### 步骤 1: 安装依赖并迁移数据库

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 运行数据库迁移
python scripts/migrate_add_users.py
```

### 步骤 2: 启动后端服务器

```bash
# 在backend目录下
uvicorn app.main:app --reload --port 8000
```

### 步骤 3: 启动前端服务器

```bash
# 在新终端，进入frontend目录
cd frontend
npm run dev
```

## 🎉 完成！

现在可以访问：

- **注册页面**: http://localhost:3000/register
- **登录页面**: http://localhost:3000/login

## 📝 快速测试

### 方法1: 使用浏览器
1. 打开 http://localhost:3000/register
2. 填写注册表单
3. 提交后自动登录并跳转到 `/reddit`

### 方法2: 使用测试脚本
```bash
cd backend
python scripts/test_auth.py
```

## 🔑 测试账户

```
邮箱: test@moreach.ai
密码: testpassword123
```

## 📋 注册表单字段

必填项：
- ✅ 邮箱
- ✅ 密码（最少8字符）
- ✅ 全名
- ✅ 行业（11个选项）
- ✅ 使用类型（个人/代理/团队）

可选项：
- 公司名称
- 职位

## 🏭 行业选项

1. E-commerce（电商）
2. SaaS
3. Marketing Agency（营销代理）
4. Content Creator（内容创作者）
5. Retail（零售）
6. Fashion & Beauty（时尚美妆）
7. Health & Fitness（健康健身）
8. Food & Beverage（餐饮）
9. Technology（科技）
10. Education（教育）
11. Other（其他）

## 💼 使用类型

1. **Personal Use** - 我自己使用
2. **Agency Use** - 为客户管理活动
3. **Team Use** - 营销团队成员

## 🔒 安全提示

⚠️ **生产环境必须做的事情**:

1. 更改 `SECRET_KEY` 为随机安全密钥
2. 使用HTTPS
3. 配置正确的CORS域名
4. 考虑使用环境变量管理配置

## 🐛 遇到问题？

### 后端无法启动
```bash
# 确保安装了所有依赖
pip install -r requirements.txt
```

### 数据库错误
```bash
# 重新运行迁移
python scripts/migrate_add_users.py
```

### 前端连接失败
- 确保后端运行在 `http://localhost:8000`
- 检查CORS配置

## 📚 详细文档

- 完整实现文档: `AUTH_IMPLEMENTATION.md`
- 详细设置指南: `SETUP_AUTH.md`

---

**就这么简单！** 🎊

