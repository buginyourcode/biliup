# B站批量视频上传工具

基于 [biliup](https://github.com/biliup/biliup) 项目开发的批量视频上传工具，支持扫描本地文件夹并批量上传视频到哔哩哔哩。

## 功能特点

- ✅ **批量上传**: 支持扫描文件夹中的所有视频文件并批量上传
- ✅ **智能过滤**: 支持按文件类型、大小过滤视频文件
- ✅ **并发上传**: 支持多线程并发上传，提高上传效率
- ✅ **重试机制**: 上传失败自动重试，提高成功率
- ✅ **进度显示**: 实时显示上传进度和详细日志
- ✅ **配置管理**: 支持配置文件管理上传参数
- ✅ **错误处理**: 完善的错误处理和异常恢复机制

## 安装依赖

### 1. 安装Python依赖

首先确保你已经安装了biliup及其依赖：

```bash
# 安装biliup
pip install biliup

# 或者如果已经克隆了biliup项目
pip install -e .
```

### 2. 获取B站登录凭据

#### 方法一：使用biliup-rs工具（推荐）

```bash
# 下载并安装biliup-rs
# 访问 https://github.com/ForgQi/biliup-rs/releases 下载对应平台的版本

# 使用biliup-rs登录
./biliup-rs login

# 登录成功后会生成cookies.json文件
```

#### 方法二：手动获取cookies

1. 打开浏览器，登录B站
2. 按F12打开开发者工具
3. 进入Application/Storage -> Cookies -> https://www.bilibili.com
4. 复制以下cookie值：
   - `SESSDATA`
   - `bili_jct`
   - `DedeUserID`
   - `DedeUserID__ckMd5`

## 使用方法

### 1. 设置登录凭据

首次使用需要设置B站登录凭据：

```bash
python batch_bilibili_uploader.py --setup
```

按照提示输入cookies信息或access_token。

### 2. 扫描视频文件

可以先扫描文件夹查看有哪些视频文件：

```bash
python batch_bilibili_uploader.py /path/to/video/folder --scan-only
```

### 3. 批量上传视频

```bash
# 基本上传（顺序上传）
python batch_bilibili_uploader.py /path/to/video/folder

# 并发上传（3个线程）
python batch_bilibili_uploader.py /path/to/video/folder -t 3

# 使用自定义配置文件
python batch_bilibili_uploader.py /path/to/video/folder -c my_config.json
```

### 4. 命令行参数

```bash
python batch_bilibili_uploader.py [文件夹路径] [选项]

选项:
  -h, --help            显示帮助信息
  -c, --config CONFIG   指定配置文件路径 (默认: upload_config.json)
  -t, --threads THREADS 并发上传线程数 (默认: 1)
  --setup              设置B站登录凭据
  --scan-only          仅扫描文件，不上传
```

## 配置文件说明

首次运行会自动创建 `upload_config.json` 配置文件，你可以根据需要修改：

```json
{
  "cookies": {
    "SESSDATA": "你的SESSDATA",
    "bili_jct": "你的bili_jct",
    "DedeUserID": "你的DedeUserID",
    "DedeUserID__ckMd5": "你的DedeUserID__ckMd5"
  },
  "access_token": "",
  "copyright": 2,
  "tid": 171,
  "tags": ["biliup", "批量上传"],
  "description": "通过批量上传工具上传",
  "dynamic": "",
  "lines": "AUTO",
  "threads": 3,
  "max_retries": 3,
  "video_extensions": [".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".webm"],
  "min_file_size": 1048576,
  "max_file_size": 8589934592
}
```

### 配置参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `cookies` | B站登录cookies | `{}` |
| `access_token` | B站API访问令牌 | `""` |
| `copyright` | 版权类型 (1-自制, 2-转载) | `2` |
| `tid` | 投稿分区ID | `171` (电子竞技) |
| `tags` | 视频标签 | `["biliup", "批量上传"]` |
| `description` | 视频描述 | `"通过批量上传工具上传"` |
| `dynamic` | 动态内容 | `""` |
| `lines` | 上传线路 | `"AUTO"` |
| `threads` | 上传线程数 | `3` |
| `max_retries` | 最大重试次数 | `3` |
| `video_extensions` | 支持的视频格式 | `[".mp4", ".avi", ...]` |
| `min_file_size` | 最小文件大小 (字节) | `1048576` (1MB) |
| `max_file_size` | 最大文件大小 (字节) | `8589934592` (8GB) |

### B站分区ID参考

常用分区ID：

| 分区 | ID |
|------|-----|
| 生活，其他 | 174 |
| 电子竞技 | 171 |
| 单机游戏 | 17 |
| 手机游戏 | 172 |
| 网络游戏 | 65 |
| 科技，数码 | 188 |
| 娱乐，明星 | 5 |
| 电影，影视 | 181 |
| 音乐，音频 | 3 |
| 舞蹈 | 129 |

更多分区ID请参考：[biliup Wiki](https://github.com/ForgQi/biliup/wiki)

## 使用示例

### 示例1：基本批量上传

```bash
# 上传 /home/user/videos 文件夹中的所有视频
python batch_bilibili_uploader.py /home/user/videos
```

### 示例2：并发上传

```bash
# 使用3个线程并发上传
python batch_bilibili_uploader.py /home/user/videos -t 3
```

### 示例3：自定义配置

创建自定义配置文件 `game_config.json`：

```json
{
  "copyright": 1,
  "tid": 17,
  "tags": ["游戏", "实况", "攻略"],
  "description": "游戏实况录像",
  "threads": 2,
  "video_extensions": [".mp4", ".mkv"]
}
```

使用自定义配置上传：

```bash
python batch_bilibili_uploader.py /home/user/game_videos -c game_config.json
```

## 日志输出

程序运行时会生成详细的日志：

- **控制台输出**: 实时显示上传进度
- **日志文件**: 保存为 `upload_YYYYMMDD_HHMMSS.log`

日志内容包括：
- 文件扫描结果
- 上传进度
- 成功/失败统计
- 错误详情
- 重试信息

## 常见问题

### Q1: 提示"未设置B站登录凭据"

**A**: 首先运行 `python batch_bilibili_uploader.py --setup` 设置登录信息。

### Q2: 上传失败，提示cookies无效

**A**: cookies可能已过期，请重新获取并更新配置文件。

### Q3: 如何获取视频分区ID？

**A**: 参考上面的分区ID表格，或访问B站投稿页面查看分区对应的数字ID。

### Q4: 支持哪些视频格式？

**A**: 默认支持：mp4, avi, mkv, mov, flv, wmv, webm。可在配置文件中修改 `video_extensions`。

### Q5: 上传速度慢怎么办？

**A**: 
- 可以增加并发线程数 (`-t` 参数)
- 在配置文件中修改 `lines` 参数尝试不同上传线路
- 检查网络连接质量

### Q6: 如何处理大文件上传？

**A**: 
- 确保文件大小在8GB以内（B站限制）
- 大文件上传时间较长，建议使用较少的并发线程
- 如果上传中断，程序会自动重试

## 注意事项

1. **文件大小限制**: B站单个视频文件不能超过8GB
2. **上传速度**: 建议合理设置并发数，过多并发可能影响上传质量
3. **网络稳定性**: 上传过程中保持网络稳定，避免频繁断线
4. **账号安全**: 妥善保管cookies信息，避免泄露
5. **版权合规**: 确保上传的视频内容符合B站社区规范
6. **分区选择**: 选择合适的分区，避免分区不当导致审核问题

## 更新日志

### v1.0.0 (2024-08-24)
- 初始版本发布
- 支持批量扫描和上传视频文件
- 支持并发上传和重试机制
- 完整的配置文件管理
- 详细的日志记录和进度显示

## 相关项目

- [biliup](https://github.com/biliup/biliup) - B站录播上传工具
- [biliup-rs](https://github.com/ForgQi/biliup-rs) - B站命令行投稿工具

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。

## 许可证

本项目基于MIT许可证开源。