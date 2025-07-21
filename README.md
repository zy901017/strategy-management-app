# 负成本持仓策略管理系统 - Vercel部署版

## 🚀 Vercel一键部署指南

这是专门为Vercel平台优化的部署版本，支持serverless环境下的完整功能。

### ⚡ 快速部署（5分钟完成）

#### 方法1：GitHub + Vercel（推荐）

1. **上传代码到GitHub**
   - 创建新的GitHub仓库
   - 上传本文件夹中的所有文件

2. **连接Vercel**
   - 访问 https://vercel.com
   - 使用GitHub账户登录
   - 点击"New Project"
   - 选择您的GitHub仓库

3. **自动部署**
   - Vercel自动检测Flask应用
   - 自动安装依赖
   - 自动部署到全球CDN

4. **获取域名**
   - 部署完成后获得免费域名
   - 格式：`your-app-name.vercel.app`

#### 方法2：Vercel CLI部署

```bash
# 安装Vercel CLI
npm i -g vercel

# 登录Vercel
vercel login

# 部署项目
vercel

# 生产环境部署
vercel --prod
```

#### 方法3：拖拽部署

1. 将整个文件夹压缩为ZIP
2. 访问 https://vercel.com/new
3. 拖拽ZIP文件到页面
4. 自动部署完成

### 📁 文件结构说明

```
Vercel_Deploy/
├── vercel_app.py          # Vercel优化的主应用文件
├── vercel.json           # Vercel配置文件
├── requirements.txt      # Python依赖
├── .vercelignore        # 部署忽略文件
├── api/
│   └── index.py         # API入口文件
├── templates/           # HTML模板
├── static/             # 静态资源
└── README.md           # 本说明文件
```

### 🔧 Vercel特殊优化

#### 数据库处理
- 使用临时文件系统（/tmp）
- 每次冷启动时重新初始化
- 适合演示和轻量级使用

#### 性能优化
- 10秒函数执行时间限制
- 自动缓存静态资源
- 全球CDN加速

#### 环境变量
- `FLASK_ENV=production`
- `SECRET_KEY=vercel-strategy-app-2025`

### ⚠️ 重要说明

#### 数据持久化
- Vercel使用serverless架构
- 数据在函数重启时会丢失
- 适合演示和测试使用
- 生产环境建议使用外部数据库

#### 功能限制
- 函数执行时间：10秒
- 内存限制：1024MB
- 文件上传限制：4.5MB

### 🎯 部署后操作

1. **访问应用**
   - 使用Vercel提供的域名
   - 例：`https://your-app.vercel.app`

2. **测试功能**
   - 添加股票信息
   - 记录交易数据
   - 查看策略分析

3. **自定义域名**（可选）
   - 在Vercel控制台添加自定义域名
   - 自动配置SSL证书

### 🔄 更新部署

#### GitHub自动部署
- 推送代码到GitHub
- Vercel自动重新部署

#### 手动重新部署
```bash
vercel --prod
```

### 📊 监控和日志

- Vercel控制台查看部署状态
- 实时函数日志
- 性能监控数据

### 🆓 免费额度

Vercel免费计划包括：
- 100GB带宽/月
- 100次部署/天
- 无限静态文件
- 自动SSL证书
- 全球CDN

### 🎉 部署完成

恭喜！您的负成本持仓策略管理系统已成功部署到Vercel！

现在您可以：
- 随时随地访问您的投资管理系统
- 享受全球CDN加速
- 获得免费的HTTPS安全连接
- 体验serverless的便利性

祝您投资顺利！🚀

