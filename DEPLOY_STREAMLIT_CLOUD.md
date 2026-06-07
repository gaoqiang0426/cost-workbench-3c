# Streamlit Community Cloud 部署指南

本项目可以免费部署到 Streamlit Community Cloud。云端入口文件使用：

```text
streamlit_app.py
```

## 部署前确认

- GitHub 仓库已创建，并且本项目代码已经 push 到 GitHub。
- 仓库根目录包含 `streamlit_app.py`、`app.py`、`requirements.txt` 和 `cost_workbench/`。
- 不要上传 `.venv/`、`.pytest_cache/`、`__pycache__/`、`.streamlit/secrets.toml`、`cost需求文档.txt`、`docs/superpowers/`。
- 当前免费云端版本不直接安装 `cadquery`，避免 Streamlit Community Cloud 在安装 OpenCascade/CAD 依赖时构建失败。云端会使用 STEP 文本中的 `CARTESIAN_POINT` 坐标做轻量外形尺寸识别；本地安装几何内核后仍可走真实 CAD 解析。

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
- 上传 STEP 后显示“轻量解析成功”：表示云端已根据 STEP 坐标点估算外形尺寸；真实实体体积和精确表面积需要本地或独立后端安装 CAD 几何内核。

## 后续升级路线

如果要稳定支持真实 3D STEP 体积/表面积分析，建议把 CadQuery 几何解析拆成独立后端，部署到国内云服务器或 Docker 平台；Streamlit Community Cloud 负责网页交互。
