"""LLM 统一封装（OpenAI 兼容协议）。

当前对接 DeepSeek-V4-Flash（OpenAI 兼容端点）。
通过 base_url + api_key 在 config.py 统一配置，切换厂商只需改配置。
"""

from typing import List, Optional

from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

import config


class LLMError(Exception):
    """LLM 调用业务异常基类。"""


class LLMAuthError(LLMError):
    """认证失败（API Key 错误/失效）。"""


class LLMRateLimitError(LLMError):
    """触发限流/并发上限。"""


class LLMConnectionError(LLMError):
    """网络连接失败。"""

# RAG 问答使用的系统 Prompt：约束 LLM 基于上下文回答，无答案时明确说明。
SYSTEM_PROMPT = (
    "你是一个严谨的知识库问答助手。请仅根据下方【参考资料】回答用户问题。"
    "若参考资料不足以回答，请直接说明\"根据现有知识库无法回答该问题\"，"
    "禁止编造、禁止使用参考资料以外的信息。"
    "回答需简洁、准确，并在适当处引用资料来源（如文档名）。"
)

RAG_TEMPLATE = """【参考资料】
{context}

【用户问题】
{question}
"""

# 查询改写 Prompt：将含指代的最新问题改写为可独立检索的问题
REWRITE_SYSTEM_PROMPT = (
    "你是一个查询改写助手。请根据对话历史，把用户的最新问题改写为一个"
    "语义完整、可独立用于知识库检索的问题（消解\"它/这个/那\"等指代词，"
    "补全省略的主语）。要求：只输出改写后的问题本身，不要任何解释、引号或前缀；"
    "若最新问题本身已完整独立或无历史，则原样返回。"
)


class LLMClient:
    """LLM 客户端：基于 OpenAI 兼容协议的 Chat Completions 封装。"""

    def __init__(self) -> None:
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """惰性初始化客户端。"""
        if self._client is None:
            self._client = OpenAI(
                api_key=config.LLM_API_KEY,
                base_url=config.LLM_BASE_URL,
            )
        return self._client

    def _raise_for_api_error(self, e: Exception) -> None:
        """将 OpenAI SDK 异常统一转换为业务异常。"""
        if isinstance(e, AuthenticationError):
            raise LLMAuthError(f"API Key 无效或已失效: {e}") from e
        if isinstance(e, RateLimitError):
            raise LLMRateLimitError(f"触发 DeepSeek 限流/并发上限，请稍后重试: {e}") from e
        if isinstance(e, APIConnectionError):
            raise LLMConnectionError(f"无法连接 LLM 服务，请检查网络/地址: {e}") from e
        if isinstance(e, APIError):
            raise LLMError(f"LLM 调用失败（{e.status_code}）: {e.message}") from e
        raise LLMError(f"LLM 调用失败: {e}") from e

    def chat(
        self,
        question: str,
        context_chunks: List[str],
    ) -> str:
        """基于检索片段组装 Prompt 并调用 LLM 生成回答。

        Args:
            question: 用户问题
            context_chunks: Reranker 精排后的上下文片段列表

        Returns:
            LLM 生成的回答文本
        """
        context = "\n---\n".join(
            f"[片段{i + 1}] {c}" for i, c in enumerate(context_chunks)
        )
        user_content = RAG_TEMPLATE.format(context=context, question=question)

        try:
            resp = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
            )
        except Exception as e:  # noqa: BLE001 - 统一转换为业务异常
            self._raise_for_api_error(e)

        # 返回结果保护：choices 为空或 content 为 None 时给出明确兜底
        if not resp.choices:
            raise LLMError("LLM 返回结果为空，无可用候选")
        content = resp.choices[0].message.content
        if not content or not content.strip():
            raise LLMError("LLM 返回内容为空，可能因 max_tokens 过小或思考未产出答案")
        return content

    def rewrite_question(
        self,
        question: str,
        history: Optional[List[dict]] = None,
    ) -> str:
        """结合对话历史，将最新问题改写为可独立检索的问题（指代消解）。

        Args:
            question: 本轮用户问题
            history: [{"role": "user"/"assistant", "content": "..."}] 历史消息

        Returns:
            改写后的独立检索问题；改写失败时兜底返回原问题，不阻塞主流程
        """
        if not history:
            return question
        try:
            messages = [{"role": "system", "content": REWRITE_SYSTEM_PROMPT}]
            # 只取最近若干轮，避免 prompt 过长
            for msg in history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": question})
            resp = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=0.0,  # 改写要求确定性
                max_tokens=256,
            )
            rewritten = (resp.choices[0].message.content or "").strip()
            # 去掉可能的引号/前缀
            rewritten = rewritten.strip("\"'“”‘’ \n")
            return rewritten or question
        except Exception:
            # 改写失败不应阻塞问答，回退为原问题
            return question

    def chat_stream(
        self,
        question: str,
        context_chunks: List[str],
        history: Optional[List[dict]] = None,
    ):
        """流式生成回答，逐 token yield 文本片段。

        Args:
            question: 本轮用户问题
            context_chunks: Reranker 精排后的上下文片段列表
            history: 对话历史（多轮上下文）

        Yields:
            str: 答案文本增量（仅正文 content，忽略思考过程 reasoning_content）

        Raises:
            LLMError 及其子类：连接/认证/限流等错误（在迭代中抛出，由上层捕获）
        """
        context = "\n---\n".join(
            f"[片段{i + 1}] {c}" for i, c in enumerate(context_chunks)
        )
        user_content = RAG_TEMPLATE.format(context=context, question=question)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        # 多轮：拼接历史对话（历史答案不重复携带参考资料，仅作上下文）
        if history:
            for msg in history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_content})

        try:
            stream = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                stream=True,
            )
        except Exception as e:  # noqa: BLE001
            self._raise_for_api_error(e)
            return  # 仅为类型检查，实际已 raise

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            # DeepSeek 思考模式下 reasoning_content 为思考过程，不展示；只转发正文
            piece = getattr(delta, "content", None)
            if piece:
                yield piece


# 单例
llm_client = LLMClient()
