"""
cli.py
------
Command-line entry point for Phase 1 — build and test the RAG layer with
no agent/pipeline code involved.

Usage:
    python -m src.rag.cli build --domain restaurant
    python -m src.rag.cli build --domain ecommerce
    python -m src.rag.cli query --domain restaurant --q "healthy food cost percentage"
"""
import argparse
from src.rag.indexer import build_domain_collection
from src.rag.retriever import query as retrieve, format_context


def main():
    parser = argparse.ArgumentParser(description="Insight Desk RAG CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    build_p = sub.add_parser("build", help="Build/rebuild a domain's Chroma collection")
    build_p.add_argument("--domain", required=True, choices=["restaurant", "ecommerce"])

    query_p = sub.add_parser("query", help="Query a domain's Chroma collection")
    query_p.add_argument("--domain", required=True, choices=["restaurant", "ecommerce"])
    query_p.add_argument("--q", required=True, help="Question text")
    query_p.add_argument("--top_k", type=int, default=4)

    args = parser.parse_args()

    if args.command == "build":
        n = build_domain_collection(args.domain)
        print(f"Indexed {n} chunks into collection '{args.domain}'.")

    elif args.command == "query":
        chunks = retrieve(args.domain, args.q, top_k=args.top_k)
        print(f"\nTop {len(chunks)} results for: {args.q!r}\n")
        print(format_context(chunks))


if __name__ == "__main__":
    main()
