"""Streamlit 演示前端（可选）。

启动：streamlit run frontend.py
默认后端地址 http://127.0.0.1:8000，可通过下方输入框修改。
"""

import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="私有知识库 RAG", page_icon="📚", layout="wide")
st.title("📚 私有知识库 RAG 系统")

# 侧边栏：知识库管理
st.sidebar.header("知识库管理")
kb_id = st.sidebar.text_input("知识库 ID", value="ecommerce_kb_01")
base = st.sidebar.text_input("后端地址", value=API_BASE)

col1, col2, col3 = st.sidebar.columns(3)
if col1.button("创建"):
    try:
        r = requests.post(f"{base}/kb/create", params={"kb_id": kb_id}, timeout=10)
        st.sidebar.success(r.json().get("message", r.text))
    except Exception as e:
        st.sidebar.error(f"创建失败: {e}")

if col2.button("列表"):
    try:
        r = requests.get(f"{base}/kb/list", timeout=10).json()
        st.sidebar.json(r)
    except Exception as e:
        st.sidebar.error(f"查询失败: {e}")

if col3.button("删除"):
    try:
        r = requests.delete(f"{base}/kb/delete", params={"kb_id": kb_id}, timeout=10)
        st.sidebar.warning(r.json().get("message", r.text))
    except Exception as e:
        st.sidebar.error(f"删除失败: {e}")

# 文档上传
st.subheader("文档上传")
uploaded = st.file_uploader(
    "选择文件（PDF/TXT/MD）",
    type=["pdf", "txt", "md"],
)
if uploaded is not None and st.button("入库"):
    try:
        files = {"file": (uploaded.name, uploaded.getvalue())}
        r = requests.post(
            f"{base}/doc/upload",
            params={"kb_id": kb_id},
            files=files,
            timeout=120,
        )
        st.success(r.json().get("message", r.text))
    except Exception as e:
        st.error(f"上传失败: {e}")

# 文档列表
with st.expander("已入库文档"):
    try:
        r = requests.get(f"{base}/doc/list", params={"kb_id": kb_id}, timeout=10).json()
        st.json(r)
    except Exception as e:
        st.warning(f"获取列表失败: {e}")

# RAG 问答
st.subheader("RAG 问答")
question = st.text_input("输入问题", value="破壁机Pro-01有加热功能吗？")
if st.button("提问") and question:
    with st.spinner("检索并生成回答中…"):
        try:
            r = requests.post(
                f"{base}/chat/query",
                json={"kb_id": kb_id, "question": question},
                timeout=60,
            ).json()
            st.markdown("#### 回答")
            st.write(r.get("answer", ""))
            st.markdown("#### 检索来源")
            for src in r.get("source", []):
                score = src.get("score")
                score_str = f"{score:.3f}" if score is not None else "N/A"
                st.markdown(
                    f"- **{src.get('doc_id')}** "
                    f"(sim={src.get('sim_score'):.3f}, rerank={score_str})"
                )
                st.caption(src.get("text", ""))
        except Exception as e:
            st.error(f"提问失败: {e}")
