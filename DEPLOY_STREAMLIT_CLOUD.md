# Streamlit Community Cloud 部署指南

本项目可以免费部署到 Streamlit Community Cloud。云端入口文件使用：

```text
streamlit_app.py
```

## 部署前确认

- GitHub 仓库已创建，并且本项目代码已经 push 到 GitHub。
- 仓库根目录包含 `streamlit_app.py`、`app.py`、`requirements.txt` 和 `cost_workbench/`。
- 不要上传 `.venv/`、`.pytest_cache/`、`__pycache__/`、`.streamlit/secrets.toml`、`cost需求文档.txt`、`docs/superpowers/`。
- 当前免费部署版本不把 `cadquery` 放入 `requirements.txt`，否则云端构建可能因为 CAD/OpenCascade 依赖过重而失败。STEP 上传仍可读取文件信息和基础实体统计；真实 3D 几何内核建议后续放到国内云服务器或独立后端服务。

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
- 上传 STEP 后提示缺少几何内核：这是免费云端版本的预期降级，不影响成本表单、工艺路线、优化建议和 PDF 下载。

## 后续升级路线

如果要稳定支持真实 3D STEP 体积/表面积分析，建议把 CadQuery 几何解析拆成独立后端，部署到国内云服务器或 Docker 平台；Streamlit Community Cloud 负责网页交互。
