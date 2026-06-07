# Streamlit Community Cloud 部署指南

本项目可以免费部署到 Streamlit Community Cloud。云端入口文件使用：

```text
streamlit_app.py
```

## 部署前确认

- GitHub 仓库已创建，并且本项目代码已经 push 到 GitHub。
- 仓库根目录包含 `streamlit_app.py`、`app.py`、`requirements.txt` 和 `cost_workbench/`。
- 不要上传 `.venv/`、`.pytest_cache/`、`__pycache__/`、`.streamlit/secrets.toml`、`cost需求文档.txt`、`docs/superpowers/`。
- 当前版本已把 `cadquery==2.7.0` 放入 `requirements.txt`，并用 `runtime.txt` 固定 Python 3.12，用于在 Streamlit Community Cloud 上启用 STEP 几何解析。首次构建会比普通 Streamlit 应用更慢。

## Streamlit Cloud 页面填写

打开：

```text
https://share.streamlit.io/
```

选择 `Create app`，然后填写：

```text
Repository: 你的 GitHub 用户名/仓库名
Branch: main
Main file path: streamlit_app.py
App URL: 自定义一个可用名称，例如 cost-workbench-3c
Python version: 3.12
```

本项目暂时不需要 Secrets。

## 如果部署失败

先看 Streamlit Cloud 右侧日志，常见问题：

- `ModuleNotFoundError`：依赖没有写进 `requirements.txt`。
- `No such file or directory`：入口文件路径没有填 `streamlit_app.py`。
- 上传 STEP 后提示缺少几何内核：检查 Cloud 构建日志里 `cadquery` 是否安装成功，并确认 Python version 是 3.12。

## 后续升级路线

如果 Streamlit Community Cloud 因资源限制导致 CadQuery 安装或导入失败，建议把 CadQuery 几何解析拆成独立后端，部署到国内云服务器或 Docker 平台；Streamlit Community Cloud 负责网页交互。
