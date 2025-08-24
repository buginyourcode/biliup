# B站批量视频上传工具使用指南

## 🎯 功能概述

基于 [biliup](https://github.com/biliup/biliup) 项目开发的批量视频上传工具，能够自动扫描本地文件夹中的视频文件并批量上传到哔哩哔哩。

## 📦 安装和准备

### 1. 环境要求

- Python 3.7+
- pip包管理器

### 2. 安装依赖

```bash
pip install rsa aiohttp requests
```

### 3. 获取B站登录凭据

#### 方法一：使用浏览器获取Cookies（推荐）

1. 打开浏览器，登录 [https://www.bilibili.com](https://www.bilibili.com)
2. 按 `F12` 打开开发者工具
3. 进入 `Application` (或 `存储`) → `Cookies` → `https://www.bilibili.com`
4. 复制以下cookie值：
   - `SESSDATA`
   - `bili_jct`
   - `DedeUserID`
   - `DedeUserID__ckMd5`

#### 方法二：使用biliup-rs工具

```bash
# 下载biliup-rs: https://github.com/ForgQi/biliup-rs/releases
./biliup-rs login
# 会生成cookies.json文件
```

## 🚀 快速开始

### 1. 设置登录凭据

```bash
python batch_bilibili_uploader.py --setup
```

按照提示输入你的B站cookies信息。

### 2. 扫描视频文件（可选）

```bash
python batch_bilibili_uploader.py /path/to/your/videos --scan-only
```

这会扫描指定文件夹中的所有视频文件，但不会上传。

### 3. 开始批量上传

```bash
# 基本上传（顺序上传）
python batch_bilibili_uploader.py /path/to/your/videos

# 并发上传（推荐，提高效率）
python batch_bilibili_uploader.py /path/to/your/videos -t 3
```

### 4. 使用GUI界面

```bash
python batch_uploader_gui.py
```

## ⚙️ 配置说明

首次运行会自动创建 `upload_config.json` 配置文件：

```json
{
  "cookies": {
    "SESSDATA": "你的SESSDATA",
    "bili_jct": "你的bili_jct",
    "DedeUserID": "你的DedeUserID",
    "DedeUserID__ckMd5": "你的DedeUserID__ckMd5"
  },
  "copyright": 2,
  "tid": 171,
  "tags": ["biliup", "批量上传"],
  "description": "通过批量上传工具上传",
  "threads": 3,
  "max_retries": 3,
  "video_extensions": [".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".webm"],
  "min_file_size": 1048576,
  "max_file_size": 8589934592
}
```

### 重要配置参数

| 参数 | 说明 | 建议值 |
|------|------|--------|
| `copyright` | 版权类型 (1-自制, 2-转载) | 根据实际情况 |
| `tid` | 分区ID | 171(电竞), 17(单机游戏), 174(生活) |
| `threads` | 并发上传线程数 | 2-5 |
| `max_retries` | 最大重试次数 | 3 |

## 🔧 使用技巧

### 1. 优化上传速度

- **合理设置并发数**: 建议2-5个线程，过多可能影响稳定性
- **选择合适时间**: 避开B站高峰期（晚上8-11点）
- **网络稳定**: 确保网络连接稳定

### 2. 文件管理

- **文件命名**: 使用有意义的文件名，会作为视频标题
- **文件大小**: 单个文件不超过8GB（B站限制）
- **文件格式**: 推荐使用MP4格式，兼容性最好

### 3. 分区选择

常用分区ID参考：

```
171 - 电子竞技      17 - 单机游戏
172 - 手机游戏     65 - 网络游戏  
174 - 生活其他    188 - 科技数码
181 - 影视         3 - 音乐
129 - 舞蹈         5 - 娱乐
```

### 4. 标签优化

- 使用相关性强的标签
- 每个视频最多10个标签
- 标签用逗号分隔：`"游戏,攻略,教程"`

## 📝 使用示例

### 示例1：游戏录播批量上传

```bash
# 1. 创建专用配置
cp upload_config_example.json game_config.json

# 2. 编辑配置文件
{
  "copyright": 1,
  "tid": 17,
  "tags": ["游戏", "录播", "攻略"],
  "description": "游戏录播视频",
  "threads": 3
}

# 3. 使用专用配置上传
python batch_bilibili_uploader.py /path/to/game/videos -c game_config.json -t 3
```

### 示例2：教程视频批量上传

```bash
# 配置文件设置
{
  "copyright": 1,
  "tid": 188,
  "tags": ["教程", "编程", "技术"],
  "description": "编程教程系列视频"
}
```

## 🐛 故障排除

### 常见问题

1. **提示"未设置B站登录凭据"**
   - 运行 `python batch_bilibili_uploader.py --setup`
   - 确保cookies信息正确

2. **上传失败，提示认证错误**
   - cookies可能已过期，重新获取
   - 检查网络连接

3. **文件被跳过**
   - 检查文件大小是否在限制范围内
   - 确认文件扩展名在支持列表中

4. **上传速度慢**
   - 调整并发线程数
   - 检查网络带宽
   - 尝试不同时间段上传

### 日志分析

程序会生成详细日志：
- 控制台输出：实时进度
- 日志文件：`upload_YYYYMMDD_HHMMSS.log`

关注以下信息：
- `INFO`: 正常操作信息
- `WARNING`: 警告信息（如文件被跳过）
- `ERROR`: 错误信息（如上传失败）

## 🔒 安全注意事项

1. **保护cookies信息**
   - 不要分享配置文件
   - 定期更新cookies

2. **遵守B站规定**
   - 确保视频内容合规
   - 选择正确的分区
   - 不要频繁大量上传

3. **备份重要文件**
   - 上传前备份原视频文件
   - 保存配置文件副本

## 📞 获取帮助

- 查看详细文档：[README_BatchUploader.md](README_BatchUploader.md)
- 运行示例代码：`python example_usage.py`
- 执行测试：`python test_uploader.py`
- GitHub Issues：[项目地址](https://github.com/buginyourcode/biliup)

---

**祝您使用愉快！如果这个工具对您有帮助，请给项目点个星⭐**