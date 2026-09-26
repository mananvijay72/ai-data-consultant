"""
eval_rag_retrieval.py
----------------------
Sanity-checks that the retriever actually returns the right source document
for a set of known questions. This is the test that answers the interview
question "how do you know your RAG works" instead of just eyeballing it.

Usage:
    python -m src.evaluation.eval_rag_retrieval
"""
import json
from src.rag.retriever import query


def run_eval():
    with open("src/evaluation/golden_datasets/rag_qa_pairs.json") as f:
        pairs = json.load(f)

    total, correct = 0, 0
    for domain, cases in pairs.items():
        print(f"\n=== Domain: {domain} ===")
        for case in cases:
            total += 1
            results = query(domain, case["question"], top_k=3)
            retrieved_sources = [r.source for r in results]
            hit = case["expected_source"] in retrieved_sources
            correct += int(hit)
            status = "PASS" if hit else "FAIL"
            print(f"[{status}] Q: {case['question']}")
            if not hit:
                print(f"       expected: {case['expected_source']}, got: {retrieved_sources}")

    print(f"\nRetrieval accuracy: {correct}/{total} ({100*correct/total:.1f}%)")


if __name__ == "__main__":
    run_eval()
