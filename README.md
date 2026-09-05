# 网易云每日推荐 → Spotify

每天读取网易云音乐「每日歌曲推荐」，在 Spotify 中保守匹配，并更新到你指定的私人 Playlist。

这个版本提供两种自动运行方式：

- **macOS 本机自动同步**：适合不想配置 GitHub Secrets 的用户；电脑休眠后会在唤醒时补跑。
- **GitHub Actions 云端同步**：不依赖本机长期在线。

无法可靠确认的歌曲会跳过，而不是强行加入同名但错误的歌曲。

## 特性

- 本地 Spotify OAuth 配置向导，自动接收 `127.0.0.1` 回调
- 密钥、Refresh Token 和网易云 Cookie 仅写入被 Git 忽略的 `.env`
- 支持简繁体、部分跨语言艺人名、专辑和时长辅助匹配
- 拒绝明显错误的 Live、Remix、Cover、Karaoke 等版本
- MusicBrainz / ISRC 辅助核验
- 写入前保护：没有可靠匹配时保留旧歌单
- 单次请求替换歌单，避免“先清空、后添加”时断网造成空歌单
- Spotify Access Token 过期时自动刷新并重试
- 本机任务断网失败后自动重试，每天只成功同步一次
- Dry Run 会生成报告，但不会修改 Spotify

## 快速开始

### 1. Fork 并下载

先 Fork 本仓库，然后克隆自己的 Fork：

```bash
git clone https://github.com/你的用户名/netease-to-spotify.git
cd netease-to-spotify
```

需要 Python 3.12 或更新版本。

### 2. 创建 Spotify App

1. 打开 [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) 并创建 App。
2. 在 App 设置中添加以下 Redirect URI：

   ```text
   http://127.0.0.1:8888/callback
   ```

3. 在 Spotify 中新建一个专门用于同步的**私人歌单**，复制歌单链接。

### 3. 完成 Spotify 授权

macOS 用户可以直接双击 `configure.command`。脚本会自动创建 Python 环境、安装依赖并启动配置向导。

也可以在终端运行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python setup.py
```

按提示输入 Spotify Client ID、Client Secret 和私人歌单链接。浏览器授权后，回调页面显示成功即可关闭。

> Client Secret 属于密码。只在本机配置窗口中输入，不要粘贴到聊天、Issue、截图或公开仓库。

### 4. 添加网易云 Cookie

1. 在浏览器登录 [网易云音乐网页版](https://music.163.com/)。
2. 打开开发者工具的 **Network**。
3. 刷新每日推荐页面，选择 `/weapi/v2/discovery/recommend/songs` 请求。
4. 在 **Request Headers → Cookie** 复制完整值，只复制内容，不要包含 `Cookie:` 字段名。
5. 双击 `add-netease-cookie.command`，在隐藏输入框中粘贴。

也可以运行：

```bash
.venv/bin/python set_netease_cookie.py
```

配置检查只显示 `SET` 或 `MISSING`，不会显示秘密内容：

```bash
.venv/bin/python check_config.py
```

### 5. 测试并首次同步

先执行不会修改歌单的 Dry Run：

```bash
.venv/bin/python -m src.dry_run
```

确认结果后执行正式同步：

```bash
.venv/bin/python -m src.main
```

正式同步会用当天成功匹配的歌曲替换目标歌单，请使用专门创建的 Playlist。

## macOS 每日自动同步（推荐）

完成首次配置后，双击 `install-automation.command`，或者运行：

```bash
.venv/bin/python automation.py install
```

任务会每 30 分钟检查一次，但每天只会在本地时间 06:00 后成功同步一次。这样电脑在 06:00 休眠时，唤醒后仍能补跑；断网失败也会自动重试。

查看任务状态：

```bash
.venv/bin/python automation.py status
```

日志位于：

```text
~/Library/Logs/netease-to-spotify.log
~/Library/Logs/netease-to-spotify-error.log
```

卸载自动任务（不会删除 `.env`）：

```bash
.venv/bin/python automation.py uninstall
```

## GitHub Actions 云端同步

如果希望电脑关机时也能运行，请在自己 Fork 的 **Settings → Secrets and variables → Actions** 中添加：

| Name | Value |
| --- | --- |
| `SPOTIFY_CLIENT_ID` | Spotify App Client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify App Client Secret |
| `SPOTIFY_REFRESH_TOKEN` | `setup.py` 获得的 Refresh Token |
| `SPOTIFY_PLAYLIST_ID` | Spotify Playlist ID，不是单曲 ID |
| `NETEASE_COOKIE` | 网易云完整 Cookie |

然后依次运行：

1. **Actions → NetEase Spotify Match Dry Run → Run workflow**
2. **Actions → Sync NetEase Daily Recommendations → Run workflow**

定时任务使用 `0 22 * * *`，即 UTC 22:00、北京时间次日约 06:00。GitHub 的实际调度时间可能稍有延迟。

## 常见问题

### 浏览器无法打开 `127.0.0.1:8888`

必须先运行 `setup.py`，让本机回调服务器启动，再在自动打开的 Spotify 页面授权。不要直接访问空白的 callback 地址。

### Spotify 返回 401

普通 Access Token 只有短期有效期。程序会自动使用 Refresh Token 续签，并重试当前歌曲及最终写入步骤。

### 某天没有更新

先检查错误日志。常见原因是电脑整天没有登录、网络不可用、网易云 Cookie 过期，或者 Spotify App 授权失效。失败不会把旧歌单清空。

### 为什么有些歌曲没有导入

Spotify 可能没有对应版权，或者歌曲/艺人信息不足以可靠确认。项目默认宁可跳过，也不加入错误版本。

## 安全说明

- `.env`、日志、匹配报告和 Python 环境均已加入 `.gitignore`。
- 不要在 Issue、PR、聊天或截图中公开 Client Secret、Refresh Token、网易云 Cookie。
- 如果秘密曾经公开，请立即在对应平台轮换。
- Spotify App 只申请 `playlist-modify-private` 权限。

## 来源与许可证

本项目基于 [swamass/netease-to-spotify](https://github.com/swamass/netease-to-spotify) 改进，感谢原作者。

MIT License，详见 [LICENSE](LICENSE)。
