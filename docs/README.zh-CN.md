# CPS - Codex Profile Switcher

[English](../README.md) | 简体中文 | [日本語](README.ja.md) | [한국어](README.ko.md)

CPS 是一个 Codex 配置切换工具，用来管理不同的 Codex profile，并把登录态和 API 路由清晰地组合起来。

它可以帮助你快速切换：

- 不同 Codex 账号；
- 不同 OpenAI API Key；
- 不同 `base_url`；
- 不同 provider / model 配置；
- 不同 `config.toml`；
- 不同 `auth.json`；
- 不同项目或环境下的 Codex 配置。

推荐用法是直接进入 TUI：

```bash
cps
```

在 TUI 中选择 Auth 和 API / Route 两列，按 `m` 应用组合，按 `R` 重启 Codex。比如你可以使用 personal 的 ChatGPT 登录态，同时让模型请求走 work 的 API route。

CPS 会把多套 Codex 配置保存在：

```bash
~/.codex-profiles
```

当前正在使用的配置仍然放在 Codex 默认目录：

```bash
~/.codex
```

也可以用命令行直接组合：

```bash
cps mix personal work
```

CPS 会把 `personal` 的 `auth.json` 和 `work` 的 `config.toml` 组合到 `~/.codex`，Codex 下次启动时就会使用这套 active 配置。

## 这个工具适合谁

如果你只固定使用一个 Codex 账号，可能不需要 CPS。

但如果你有下面这些情况，CPS 会很方便：

- 一个电脑上同时使用个人 Codex 账号和工作 Codex 账号；
- 有多个 OpenAI API Key，需要按项目切换；
- 有时使用官方 OpenAI API，有时使用自定义 `base_url`；
- 想保留 ChatGPT 登录态，但临时把模型请求路由到自定义 API；
- 需要在不同模型、不同 provider、不同配置文件之间切换；
- 不想每次都手动编辑 `~/.codex/config.toml`；
- 不想把个人账号、工作账号、代理配置混在一起。

## 下载与安装

### 方式一：直接从 GitHub 安装

如果你只是想使用 CPS，这是最快的安装方式：

```bash
python3 -m pip install "git+https://github.com/ZijiYu/CPS-codex_profile_switcher.git"
```

安装完成后检查命令是否可用：

```bash
cps --help
```

如果终端提示 `cps: command not found`，通常是 Python 的 scripts 目录没有加入 `PATH`。可以先用下面这个命令验证包是否安装成功：

```bash
python3 -m codex_profile_switcher.cli --help
```

### 方式二：下载源码后本地安装

如果你想看代码、改代码，或者使用本地最新版，推荐用这种方式。

使用 Git 克隆：

```bash
git clone https://github.com/ZijiYu/CPS-codex_profile_switcher.git
cd CPS-codex_profile_switcher
python3 -m pip install -e .
```

如果你不熟悉 Git，也可以在 GitHub 页面下载 ZIP：

```text
Code -> Download ZIP -> 解压 -> 在终端中进入解压后的文件夹
```

然后在解压后的项目目录里安装：

```bash
cd CPS-codex_profile_switcher
python3 -m pip install -e .
```

注意：GitHub 下载 ZIP 后，文件夹名字可能是：

```text
CPS-codex_profile_switcher-main
```

这时就使用实际的文件夹名：

```bash
cd CPS-codex_profile_switcher-main
python3 -m pip install -e .
```

安装后会得到这些命令：

```text
cps
cpx
codex-profiles
```

日常使用推荐 `cps`。

### 可选：使用 pipx 隔离安装

如果你习惯用 `pipx` 安装命令行工具：

```bash
pipx install "git+https://github.com/ZijiYu/CPS-codex_profile_switcher.git"
```

## 快速开始

启动终端 UI：

```bash
cps
```

主流程：

```text
1. 选择一个 Auth profile
2. 选择一个 API / Route profile
3. 按 m 应用当前组合
4. 按 R 重启 Codex
```

创建 Auth profile，并进入 Codex 登录流程：

```bash
cps init auth personal
```

这个命令会为 `personal` 准备独立 profile 目录，然后运行 `codex login`，让这个 Auth profile 拥有自己的 `auth.json`。

从当前 `~/.codex` 创建一个 API / Route profile：

```bash
cps init route work
```

给指定 profile 登录 Codex：

```bash
cps login personal
```

组合 personal 登录态和 work API 路由：

```bash
cps mix personal work
```

切换后重启 Codex，让它重新读取当前的 `~/.codex` 配置：

```bash
cps restart
```

## Hybrid Route

除了 Auth + Route 组合，CPS 也支持只编辑当前模型请求路由。

这适合一种很常见的情况：你想保留当前 ChatGPT 登录态，但让模型请求走自定义 OpenAI-compatible API。

```bash
cps route custom \
  --base-url https://your-endpoint.example.com/v1 \
  --model gpt-5.5 \
  --api-key sk-...
```

这个命令只会更新当前 `~/.codex/config.toml` 里的 provider、model、base_url 和 API token，不会替换 `auth.json`。

也就是说：

- ChatGPT 登录态会保留；
- 当前 `auth.json` 不会被覆盖；
- 模型请求会切到自定义 provider；
- 切换前会自动备份当前配置。

如果想切回官方 OpenAI provider：

```bash
cps route official --model gpt-5.5
```

Hybrid routing 只编辑 `config.toml`。它会保留现有 `auth.json`，所以 ChatGPT 登录态仍然存在，而模型请求会走自定义 provider。

## 终端 UI

启动：

```bash
cps
```

TUI 布局：

```text
top       CPS logo 和当前 active 模式
left      Auth 和 API / Route 两列
right     activity 事件流
bottom    当前界面的快捷键状态栏
```

快捷键：

```text
Up/Down              选择 profile
Left/Right 或 Tab    切换 Auth / API 列
Enter                输入框为空时选择当前项
m                    应用当前选择的 Auth + API / Route
o                    打开菜单
R                    重启 Codex
Esc                  清空输入
?                    显示/隐藏帮助
r                    刷新
q                    退出
```

在 TUI 中，CPS 会把 profile 拆成两列展示：

```text
Auth                  API / Route
> * personal [AUTH]   > * work [API]
    ...
```

`>` 表示当前光标所在项，`*` 表示已经选中的项。用 `Tab` 或左右方向键切换列，`Enter` 选择当前项，选好 Auth 和 API / Route 后按 `m` 应用组合，按 `R` 重启 Codex。

## CLI 命令

```bash
cps status
cps list
cps deleted
cps path work
cps init auth personal
cps init route work
cps login personal
cps delete old-profile
cps restore old-profile-20260612-153000
cps mix personal work
cps use work
cps restart
cps route custom --base-url https://your-endpoint.example.com/v1 --model gpt-5.5 --api-key sk-...
cps route official --model gpt-5.5
```

`cps use <profile>` 会用某个 profile 整套替换 `~/.codex`。日常组合 Auth 和 API / Route 时，优先使用 TUI 的两列选择或 `cps mix <auth> <route>`。

## Profile 模式

Auth profile：

```toml
[model_providers.OpenAI]
requires_openai_auth = true
```

API profile：

```toml
[model_providers.OpenAI]
env_key = "OPENAI_API_KEY"
```

Hybrid route：

```toml
model_provider = "custom"
preferred_auth_method = "chatgpt"

[model_providers.custom]
base_url = "https://your-endpoint.example.com/v1"
requires_openai_auth = true
wire_api = "responses"
experimental_bearer_token = "sk-..."
```

API profile 的目录里可能仍然存在 `auth.json`，但当 profile 模式是 API 时，CPS 会把这个 auth 标记为 ignored。

## 常见问题

### `cps: command not found`

先试一下：

```bash
python3 -m codex_profile_switcher.cli --help
```

如果这个命令能运行，说明包已经安装成功，只是 `cps` 所在的 Python scripts 目录没有加入 `PATH`。

### `pip install -e .` 找不到项目

确认你现在位于项目根目录。运行：

```bash
ls
```

应该能看到：

```text
pyproject.toml
README.md
src/
```

如果看不到这些文件，说明你还没有进入正确的项目文件夹。

### 下载 ZIP 后无法进入目录

GitHub ZIP 解压后的目录名可能带 `-main` 后缀，例如：

```text
CPS-codex_profile_switcher-main
```

这时应该进入实际存在的目录：

```bash
cd CPS-codex_profile_switcher-main
python3 -m pip install -e .
```

## 安全性

`delete` 是可恢复的。它会把 profile 移动到：

```text
~/.codex-profiles/deleted/<profile>-<timestamp>
```

恢复：

```bash
cps restore <deleted-profile>
```

CPS 在切换 profile 或 route 前，会备份当前 active 的 `~/.codex` 配置。

## 文件结构

```text
~/.codex
  Codex Desktop 正在使用的 active 配置

~/.codex-profiles/<name>
  已保存的 profile 配置

~/.codex-profiles/deleted
  可恢复删除

~/.codex-profiles/backups
  切换时自动备份
```

## 卸载

```bash
python3 -m pip uninstall codex-profiles
```

卸载 Python 包不会自动删除 `~/.codex-profiles` 里的配置。这样可以避免误删你已经保存的 Codex profiles。
