import asyncio
import argparse
import os
from app.utils.repo_scanner import RepoScanner
from app.services.plagiarism.orchestrator import PlagiarismOrchestrator

async def main():
    parser = argparse.ArgumentParser(description="AIJudge Repo Scanner - Batch Plagiarism Detection")
    parser.add_argument("path", help="Path to the directory containing student submissions (each submission should be a sub-directory)")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"Error: Path {args.path} does not exist.")
        return

    # 1. Scan for submissions
    scanner = RepoScanner()
    submissions = scanner.scan_submissions_root(args.path)
    
    if not submissions:
        print("No valid submissions found. Ensure each student submission is in its own sub-directory.")
        return

    # 2. Run Analysis
    orchestrator = PlagiarismOrchestrator()
    reports = await orchestrator.run_batch_analysis(submissions)

    # 3. Output Results
    print("\n" + "="*50)
    print("DETECTION COMPLETE")
    print("="*50)
    
    if not reports:
        print("No suspicious pairs found above the shortlisting threshold.")
    else:
        # Sort by score descending
        reports.sort(key=lambda x: x.peer_plagiarism_percentage, reverse=True)
        
        for r in reports:
            print(f"\n[!] MATCH: {r.submission_id_a} vs {r.submission_id_b}")
            print(f"    SCORE: {r.peer_plagiarism_percentage}%")
            print(f"    RISK : {r.final_review_risk.upper()}")
            print(f"    REASON: {r.review_reason_summary}")
            print("    EVIDENCE:")
            for e in r.evidence_highlights:
                print(f"      - {e}")

if __name__ == "__main__":
    asyncio.run(main())
