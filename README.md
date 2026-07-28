# QRCD_M Windows / macOS 原生版

从 QQ 音乐搜索并下载 QRC 歌词，转换成通用 LRC。本项目不再调用原版的
`lib_qrc_decoder.exe` 或 `QQMusicCommon.dll`，也不需要 Wine、虚拟机或
QQ 音乐客户端，可在 Windows 和 macOS 上原生运行。

## 功能

- 按歌曲名、歌手搜索并选择 QQ 音乐歌曲
- 按 QQ 音乐歌曲 ID 直接下载
- 原文、中文翻译、罗马音歌词
- 原文和罗马音逐行/逐字 LRC
- 中文翻译逐行 LRC
- 原文逐字 + 中文翻译双语 LRC
- 保存未纳入时间轴的歌曲信息及搜索结果列表
- 自定义输出目录与网络超时

生成文件与原项目对应：

| 后缀 | 内容 |
| --- | --- |
| `og-line` | 原文逐行 |
| `og-char` | 原文逐字 |
| `ch-line` | 中文翻译逐行 |
| `rm-line` | 罗马音逐行 |
| `rm-char` | 罗马音逐字 |
| `og&ch-mix` | 原文逐字 + 中文翻译 |

## Windows 使用

需要 Windows 10/11 和 Python 3.10 或更高版本。安装 Python 时请勾选
`Add Python to PATH`。

最简单的使用方式：

1. 双击 `install.bat`，等待安装完成。
2. 以后双击 `run.bat` 启动。
3. 输入歌曲名并选择搜索结果，或输入 QQ 音乐歌曲 ID 直接下载。
4. 歌词默认保存在本目录的 `lyric` 文件夹。

如果 Windows SmartScreen 阻止脚本，请确认文件来自可信位置后选择
“更多信息”→“仍要运行”。

也可以在 PowerShell 中运行：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .

# 交互模式
.\.venv\Scripts\python.exe -m qrcd.cli

# 直接搜索
.\.venv\Scripts\python.exe -m qrcd.cli "晴天" --artist "周杰伦"

# 按 QQ 音乐歌曲 ID 直接下载
.\.venv\Scripts\python.exe -m qrcd.cli --song-id 323823965

# 自定义输出目录
.\.venv\Scripts\python.exe -m qrcd.cli "晴天" -a "周杰伦" -o "$HOME\Music\Lyrics"
```

## macOS 使用

需要 Python 3.10 或更高版本，可在终端运行 `python3 --version` 检查。

最简单的使用方式：

1. 双击 `install.command`，等待安装完成。
2. 以后双击 `run.command` 启动。
3. 输入歌曲名并选择搜索结果，或输入 QQ 音乐歌曲 ID 直接下载。
4. 歌词默认保存在本目录的 `lyric` 文件夹。

如果 macOS 首次阻止脚本运行，请按住 Control 点击文件，选择“打开”。

也可以在终端中运行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .

# 交互模式
.venv/bin/python -m qrcd.cli

# 直接搜索
.venv/bin/python -m qrcd.cli "晴天" --artist "周杰伦"

# 按 QQ 音乐歌曲 ID 直接下载
.venv/bin/python -m qrcd.cli --song-id 323823965

# 自定义输出目录
.venv/bin/python -m qrcd.cli "晴天" -a "周杰伦" -o ~/Music/Lyrics
```

安装后也会提供跨平台的 `qrcd` 命令。原有的 `qrcd-mac` 命令继续保留，
以兼容旧的使用方式。

## 搜索结果与歌曲 ID

交互模式可以输入普通歌名，也可以输入纯数字歌曲 ID 或 `id:歌曲ID`。输入
纯数字时，程序会先确认是按歌曲 ID 下载，还是将数字作为歌名搜索。

搜索结果保持 QQ 音乐接口的原始返回顺序，本工具不会按 ID 或其他字段重新
排序。上游项目所说的“ID 越大歌词越新”是一条经验判断：同名结果中，较大
ID 往往表示曲库条目较晚录入，歌词可能较新，但并非绝对。选择时应同时参考
歌手和专辑。

## 测试

macOS：

```bash
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m pytest -q
```

Windows PowerShell：

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m pytest -q
```

## 常见问题

### `pip` command not found

不要直接运行 `pip`，请使用对应 Python 环境中的 pip：

```text
macOS:  .venv/bin/python -m pip
Windows: .\.venv\Scripts\python.exe -m pip
```

### 双击脚本后安装或启动失败

脚本会停留在错误页面。请保留窗口中的完整报错，并确认 Python 版本不低于
3.10、网络可以访问 Python 软件包源。

## 说明

项目使用 QQ 音乐 PC 客户端的非公开歌词接口。接口由第三方控制，未来可能
发生变化。下载的歌词内容可能受版权保护，请仅在授权范围内个人使用。

本项目依据原 QRCD_M 的 MIT License 进行移植，版权声明见 `LICENSE`。
