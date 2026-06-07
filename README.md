# 3C 结构件成本估算工作台

Python + Streamlit 实现的消费电子结构件早期成本估算工具。当前版本重点包含注塑件成本函数，并扩展 CNC 铝件、钣金件、锌合金压铸和 3D 打印的规则估算，支持报告预览和 PDF 下载。

## 本地运行

推荐直接运行项目根目录下的一键脚本：

```powershell
cd D:\work\codex\03-cost
.\run_app.ps1
```

如果 PowerShell 执行策略拦截，可以运行：

```powershell
cd D:\work\codex\03-cost
powershell -ExecutionPolicy Bypass -File .\run_app.ps1
```

也可以双击或执行：

```powershell
D:\work\codex\03-cost\run_app.cmd
```

脚本会自动检查 `.venv` 是否使用兼容的普通 Python 3.10-3.12。如果发现旧环境是 Python 3.13t/free-threaded，会把旧 `.venv` 改名为 `.venv.unsupported-时间戳`，然后优先使用 Python 3.12/3.11/3.10 重新创建虚拟环境。

手动运行方式：

```powershell
cd D:\work\codex\03-cost
pip install -r requirements.txt
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 9005
```

打开：

```text
http://localhost:9005/
```

## 免费云端部署

本项目已准备 Streamlit Community Cloud 入口文件，并在 `requirements.txt` 中加入 `cadquery==2.7.0` 用于云端 STEP 几何解析：

```text
streamlit_app.py
```

部署时在 Streamlit Community Cloud 填：

- Repository：你的 GitHub 仓库
- Branch：`main`
- Main file path：`streamlit_app.py`
- Python version：`3.12`

详细步骤见 [DEPLOY_STREAMLIT_CLOUD.md](DEPLOY_STREAMLIT_CLOUD.md)。

## 测试

```powershell
python -m pytest tests/test_cost_engine.py -v
```

完整测试：

```powershell
python -m pytest tests -v
```

推荐使用项目脚本自动安装依赖并运行完整测试：

```powershell
cd D:\work\codex\03-cost
.\verify_app.ps1
```

如果 PowerShell 执行策略拦截：

```powershell
cd D:\work\codex\03-cost
powershell -ExecutionPolicy Bypass -File .\verify_app.ps1
```

注意：如果当前 PowerShell 路径是 `C:\Windows\System32`，直接运行 `pip install -r requirements.txt` 会找不到项目文件。请先 `cd D:\work\codex\03-cost`，或使用上面的一键脚本。

## Codex 权限审批说明

当前 Codex 会话的提权请求由自动审核器处理，不一定会弹出人工批准窗口。如果自动审核器超时，Codex 端会看到权限请求超时，而用户界面不会出现可点击弹窗。

因此本项目把需要系统权限或网络权限的操作整理成脚本，由用户在本机 PowerShell 执行：

- `verify_app.ps1`：安装依赖并运行测试。
- `run_app.ps1`：安装依赖并启动 Streamlit。

这两个脚本都会先切换到项目目录，并优先使用 `.venv` 虚拟环境，避免把依赖装到系统 Python。

## Python 版本说明

不建议使用 Python 3.13t/free-threaded 运行本项目。该版本目前容易遇到部分依赖没有预编译 wheel 的情况，pip 会尝试本地编译扩展模块，例如 `httptools`，从而报错：

```text
Microsoft Visual C++ 14.0 or greater is required
```

推荐安装并使用普通 Python 3.11 或 3.12。可用版本可以用下面命令查看：

```powershell
py -0p
```

如果没有普通 Python 3.10-3.12，可以运行项目里的安装脚本：

```powershell
cd D:\work\codex\03-cost
.\install_python_312.ps1
```

安装完成后关闭并重新打开 PowerShell，再运行：

```powershell
cd D:\work\codex\03-cost
.\run_app.ps1
```

## 注塑件公式

- 材料费 = 产品克重 / 1000 * 材料每公斤单价
- 加工费 = 注塑周期 * 机台秒费率 / 一模出数
- 模具分摊费 = 用户输入的单件摊销
- 不良率调整 = 基准小计 / (1 - 不良率) - 基准小计
- 最终单件预估价 = 良率调整后小计 * (1 + 15% 供应商管理利润率)

内置机台费率：

- 90T = 0.016 元/秒
- 120T = 0.022 元/秒
- 160T = 0.028 元/秒

## 报告

页面底部提供两页报告预览：

- 第一页：分析与成本
- 第二页：局部优化建议

PDF 使用 `reportlab` 生成，支持中文报告内容。

## STEP 几何内核

基础应用不强制安装 CAD 几何内核。未安装时，STEP 上传模块会读取文件名、大小、STEP schema 和实体数量，并提示缺少几何内核。

如需真实 3D 几何分析，安装 CadQuery/OpenCascade：

```powershell
cd D:\work\codex\03-cost
.\install_geometry_kernel.ps1
```

安装后重启应用：

```powershell
cd D:\work\codex\03-cost
.\run_app.ps1
```

接入后 STEP 模块会计算：

- 最大外形长宽高
- 包围盒体积
- 实际体积
- 体积利用率
- 外表面积近似
- 基于体积和材料密度的默认克重
