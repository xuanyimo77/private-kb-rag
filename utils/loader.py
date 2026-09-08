"""文档加载器（PDF/TXT/MD）。

负责将不同格式文件统一解析为纯文本，供后续切分与向量化使用。
"""

from pathlib import Path
from typing import Optional

from pypdf import PdfReader


class UnsupportedFileError(Exception):
    """不支持的文件格式。"""


def load_pdf(file_path: str) -> str:
    """加载 PDF，逐页提取文本并拼接。"""
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text.strip())
    return "\n".join(p for p in pages if p)


def load_text(file_path: str, encoding: str = "utf-8") -> str:
    """加载 TXT/MD，原生读取（Markdown 不去除标记，保留语义结构）。"""
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()


def load_document(file_path: str) -> str:
    """根据扩展名分发到对应加载器，返回纯文本。

    Args:
        file_path: 文件绝对路径

    Returns:
        文件纯文本内容

    Raises:
        UnsupportedFileError: 文件格式不在允许列表内
        FileNotFoundError: 文件不存在
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(file_path)
    if suffix in {".txt", ".md"}:
        # TXT 可能有 GBK 编码，做一次回退
        try:
            return load_text(file_path)
        except UnicodeDecodeError:
            return load_text(file_path, encoding="gbk")
    raise UnsupportedFileError(f"不支持的文件格式: {suffix}，仅支持 PDF/TXT/MD")


def guess_doc_id(file_path: str) -> str:
    """用文件名（含扩展名）作为 doc_id，便于按文档增量删除与溯源展示。"""
    return Path(file_path).name


def safe_filename(file_name: str) -> Optional[str]:
    """校验文件名安全性，防止路径穿越。返回安全文件名或 None。"""
    if not file_name:
        return None
    # 仅保留文件名部分，去除任何目录前缀
    name = Path(file_name).name
    if not name or name in {".", ".."}:
        return None
    return name
