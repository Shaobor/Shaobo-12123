<div align="center">

# 🚗 12123 (Shaobo 12123)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/default)
[![version](https://img.shields.io/badge/Version-3.0-blue.svg?style=for-the-badge)](https://github.com/Shaobor/Shaobo-12123)
[![license](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Home Assistant](https://img.shields.io/badge/Home--Assistant-2026.1%2B-blueviolet.svg?style=for-the-badge)](https://www.home-assistant.io/)

**专为 Home Assistant 打造的 12123 官方品质数据监控与管理集成**  
实时监控驾驶证记分、机动车状态、检验有效期、未处理违法违章及业务提醒通知。

[✨ 特性亮点](#-特性亮点) • [📊 传感器实体清单](#-传感器实体清单) • [🎴 12123 面板卡片](#-12123-面板卡片) • [🚀 安装与配置](#-安装与配置) • [📄 许可证](#-许可证)

---

</div>

## ✨ 特性亮点

- 🛡️ **国密通信与安全隔离**：深度支持国密 SM2/SM3/SM4 加解密体系，集成与服务端采用独立专属 Token 鉴权，支持设备机器码锁机校验，防止跨账户越权与盗用。
- 🚗 **全方位机动车与驾驶人状态监控**：
  - **驾驶证监控**：驾驶证号、准驾车型、累积记分、清分日期、有效期至、证件状态。
  - **机动车状态**：车牌号码、号牌种类、检验有效期至、强制报废期至、交强险终止期、车辆状态、未处理违章总数。
  - **违法违章现场取证**：自动获取违章时间、地点、违法行为、罚款金额与记分，并自动下载官方现场违章取证照片到本地保存。
  - **消息中心**：官方业务告知、交警业务提醒、未读公告分类展示与通知。
- 🎴 **开箱即用专属 Lovelace 卡片**：自动注册专属前端卡片（`custom:ha-12123-card`），支持总览、车辆、违章（含取证照片预览与一键刷新）、消息四个页签切换，支持暗色与亮色主题自适应。
- ⚙️ **精细化刷新策略**：支持在集成选项中独立设置普通数据、违章信息和消息中心的刷新间隔，兼顾数据实时性与服务端风控防刷。
- 💾 **本地原生专属持久化**：采用 Home Assistant 标准 Storage 存储规范，车主凭据、车辆指标与离线缓存持久化保存于 `.storage/Shaobo_12123` 中，HA 重启无缝恢复。

---

## 📊 传感器实体清单

集成接入后将自动创建以下规范的核心分类传感器：

| 传感器名称 | 默认实体 ID | 核心属性与说明 |
| :--- | :--- | :--- |
| **用户信息** | `sensor.12123_user_info` | 姓名、脱敏身份证号、脱敏手机号、所属城市、发证机关 |
| **驾驶证信息** | `sensor.12123_driver_info` | 档案编号、准驾车型（C1 等）、累积记分、清分日期、有效起止期、证件状态 |
| **机动车信息** | `sensor.12123_vehicle_info` | 绑定名下所有车辆列表、车牌号、号牌种类、检验有效期、交强险截止期、抵押状态 |
| **违章信息** | `sensor.12123_violation_info` | 未处理违章总数、有违章车辆数、预计待扣分值、详细违章记录列表与取证照片路径 |
| **业务告知** | `sensor.12123_business_notice` | 业务待办通知、机动车审验/换证等法定业务通知 |
| **服务提醒** | `sensor.12123_service_remind` | 违法处理提醒、交强险到期提醒等推送信息 |
| **服务状态** | `sensor.12123_status` | 在线状态、网关延迟、数据最后同步时间 |

---

## 🎴 12123 面板卡片

集成启动后会自动向 Home Assistant 注册前端卡片资源。

### 添加到仪表盘
在概览仪表盘中点击“添加卡片”，搜索 **12123**，或直接使用 YAML 配置：

```yaml
type: custom:ha-12123-card
title: 12123
size: large
```

### 卡片功能
- **总览看板**：直观展示驾驶人当前记分、名下机动车概览卡片、未处理违章数字徽章。
- **机动车卡片**：展示名下所有车辆详细信息、审验倒计时、强制报废倒计时与保险状态。
- **违章与取证**：直观展示每条违章的详细信息，右上角提供“更新违章信息”按钮强制刷新违章并下载最新现场照片；图片保存在本地 `/config/12123/violations/`，通过 `/12123-images/` 安全访问。
- **消息列表**：分类展示官方告知与服务提醒，支持上一页/下一页翻页查看。

---

## 🚀 安装与配置

### 方式一：HACS 自定义存储库安装（推荐）
1. 打开 Home Assistant 的 **HACS** -> **Integrations**。
2. 点击右上角菜单中的 **Custom repositories（自定义存储库）**。
3. 填入本仓库地址，类别选择 **Integration（集成）**。
4. 在列表中搜索 **12123** 并点击下载安装，随后重启 Home Assistant。

### 方式二：手动安装
1. 下载本项目发布包中的 `custom_components/shaobo_12123` 文件夹。
2. 将其复制到 Home Assistant 配置目录下的 `custom_components/` 目录中：
   ```text
   /config/custom_components/shaobo_12123/
   ```
3. 重启 Home Assistant。

### 配置流程
1. 进入 Home Assistant **设置 -> 设备与服务 -> 添加集成**。
2. 搜索并选择 **12123**（`shaobo_12123`）。
3. 输入您的专属授权码，系统将自动绑定当前 HA 实例的机器码并获取访问凭据。
4. 若授权码尚未录入车主会话，系统会引导输入抓包登录凭据完成首次绑定。


---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 授权。仅供智能家居爱好者学习交流研究使用，严禁用于任何商业用途或非法侵犯他人隐私行为。
