"""RAG 端到端验证脚本（需 Milvus + Embedding + LLM 服务可用）。

用法：
    F:\\config\\python\\miniconda3\\envs\\private_kb\\python.exe tests/test_rag_e2e.py

覆盖 README 验证问题集：基础检索、边界测试（无答案应拒绝）、跨文档综合。
首次运行会下载本地 Reranker 模型（约 2.3GB，已配置 hf-mirror 镜像加速）。
"""

import requests

BASE = "http://127.0.0.1:8000"
KB_ID = "ecommerce_kb_01"

CASES = [
    # 基础检索（知识库内有答案）
    "便携式破壁机 Pro-01 多少钱，有没有加热功能？",
    "桌面加湿器 H-200 续航多久，能不能直接滴精油？",
    "7 天无理由退货运费谁承担？",
    "满多少包邮？新疆还要额外运费吗？",
    "V2 金卡会员有什么权益？生日有什么福利？",
    # 边界测试（知识库无答案，应拒绝编造）
    "破壁机 Pro-01 有没有红色版本？",
    "商城有没有卖冰箱？",
    "V4 会员权益是什么？",
    # 跨文档综合
    "我买了破壁机 Pro-01，摔地上坏了，可以保修吗？",
    "我在新疆买收纳箱，订单 110 元，需要付多少运费？",
]


def main() -> None:
    for i, q in enumerate(CASES, 1):
        print(f"\n{'=' * 70}\n[{i}/{len(CASES)}] 问题：{q}")
        try:
            r = requests.post(
                f"{BASE}/chat/query",
                json={"kb_id": KB_ID, "question": q},
                timeout=600,
            )
            if r.status_code != 200:
                print(f"  HTTP {r.status_code}: {r.text[:300]}")
                continue
            d = r.json()
            print(f"  回答：{d.get('answer', '')}")
            for s in d.get("source", []):
                score = s.get("score")
                score_str = f"{score:.3f}" if score is not None else "N/A"
                print(f"  来源：{s['doc_id']} | sim={s['sim_score']:.3f} rerank={score_str}")
        except Exception as e:
            print(f"  请求异常：{e}")


if __name__ == "__main__":
    main()
