"""（可选）关系型数据模型，记录文档元信息。

当前项目以 Milvus 为单一数据源，文档元信息（doc_id、chunk 数）通过聚合
Milvus 查询结果得到，无需额外关系库。如需持久化更丰富的元信息（上传时间、
文件大小、原始路径、入库状态等），可在此处引入 SQLAlchemy 模型。

启用方式：取消下方注释并安装 sqlalchemy，在 main.py 启动事件中建表。
"""

# from datetime import datetime
# from sqlalchemy import Column, String, Integer, DateTime
# from sqlalchemy.orm import declarative_base
#
# Base = declarative_base()
#
#
# class DocumentRecord(Base):
#     """文档元信息表（可选）。"""
#
#     __tablename__ = "documents"
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     kb_id = Column(String(128), index=True, nullable=False, comment="所属知识库")
#     doc_id = Column(String(256), nullable=False, comment="文档 ID（文件名）")
#     file_name = Column(String(256), nullable=False, comment="原始文件名")
#     file_size = Column(Integer, default=0, comment="字节数")
#     chunk_count = Column(Integer, default=0, comment="切分块数")
#     created_at = Column(DateTime, default=datetime.utcnow, comment="入库时间")
