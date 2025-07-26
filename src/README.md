# 📁 src/ 目录结构说明

## 🗂️ 文件组织

```
src/
├── 📁 components/     # React组件库
├── 📁 config/         # 配置文件
├── 📁 constants/      # 常量定义
├── 📁 data/          # 静态数据
├── 📁 hooks/         # 自定义Hooks
├── 📁 services/      # API服务层
├── 📁 styles/        # 样式文件
├── 📁 types/         # TypeScript类型
└── 📄 DEVELOPMENT.md # 开发笔记
```

## ⭐ 核心文件

### 🔥 关键组件
- `components/AddressAutocomplete.tsx` - **地址自动完成组件**
- `components/DevAuthComponent.tsx` - 开发模式认证组件
- `components/WebPortal.tsx` - Web端Portal支持

### 🔧 配置文件
- `config/env.ts` - **环境变量管理**
- `constants/index.ts` - 项目常量（包含开发模式配置）

### 🌐 服务层
- `services/api.ts` - **API服务层**（地址搜索 + 认证）

### 🎨 样式文件
- `styles/addressStyles.ts` - **地址组件专用样式**
- `styles/globalStyles.ts` - 全局样式
- `styles/inputStyles.ts` - 输入框样式

## 🧹 已清理文件

### ❌ 已删除
- `services/getSuggestion.py` - Python实现已废弃
- `components/AddressInputExample.tsx` - 示例组件
- `components/EnvDebugComponent.tsx` - 调试组件

### 📝 已整合
- 根目录多个说明文档 → `README.md`
- 开发笔记 → `src/DEVELOPMENT.md`

## 📋 文件职责

| 目录 | 职责 | 核心文件 |
|------|------|----------|
| `components/` | UI组件 | `AddressAutocomplete.tsx` |
| `config/` | 配置管理 | `env.ts` |
| `services/` | 业务逻辑 | `api.ts` |
| `styles/` | 样式定义 | `addressStyles.ts` |
| `types/` | 类型定义 | `index.ts` |

## 🔍 代码质量

### ✅ 已完成
- 统一的文件命名规范
- 完整的TypeScript类型定义
- 详细的JSDoc注释
- 清晰的目录结构

### 📈 代码统计
- **组件总数**: 12个
- **核心组件**: 3个（地址、认证、Portal）
- **API接口**: 4个（搜索、验证码、登录、邀请码）
- **样式文件**: 5个
- **配置文件**: 2个

---

**整理完成！** 项目结构现在更加清晰和易于维护。