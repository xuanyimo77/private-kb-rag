"""文本切分工具。

使用 LangChain 的递归字符切分器，按 config.CHUNK_SIZE / CHUNK_OVERLAP 配置切分。
"""

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

import config


def get_splitter(
    chunk_size: int = config.CHUNK_SIZE,
    chunk_overlap: int = config.CHUNK_OVERLAP,
) -> RecursiveCharacterTextSplitter:
    """获取切分器实例。

    优先按段落（\\n\\n）、换行、句号、空格递归切分，保证语义完整性。
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""],
        length_function=len,
    )


def split_text(text: str) -> List[str]:
    """将长文本切分为块列表。空文本返回空列表。"""
    if not text or not text.strip():
        return []
    splitter = get_splitter()
    return splitter.split_text(text)
