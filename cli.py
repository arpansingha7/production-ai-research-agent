import sys
import argparse
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

from research_agent.orchestrator import ResearchOrchestrator

def main():
    parser = argparse.ArgumentParser(description="AuraResearchAgent: Production-Oriented AI Research Agent")
    parser.add_argument("question", type=str, help="Research question or topic to investigate")
    parser.add_argument("--provider", type=str, choices=["gemini", "groq"], default=None,
                        help="LLM Provider to use (defaults to setting in .env)")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("           AuraResearchAgent - PRODUCTION-ORIENTED AI RESEARCH AGENT          ")
    print("=" * 80)
    
    orchestrator = ResearchOrchestrator(provider=args.provider)
    
    try:
        report = orchestrator.run_research(args.question)
        
        print("\n" + "=" * 80)
        print("                                 FINAL REPORT                                ")
        print("=" * 80)
        print(f"\nQUERY: {report.user_question}\n")
        print("EXECUTIVE SUMMARY:")
        print(report.executive_summary)
        print("\nKEY FINDINGS:")
        for finding in report.key_findings:
            print(f"- {finding}")
            
        print("\nVERIFIED SOURCES:")
        for src in report.sources:
            print(f"[{src.index}] {src.title} (Score: {src.credibility_score}/10)")
            print(f"    URL: {src.url}")
            print(f"    Reasoning: {src.relevance_reasoning}")
            
        print(f"\nCONFIDENCE LEVEL: {report.confidence_level}")
        print(f"Reasoning: {report.confidence_reasoning}")
        
        print("\nLIMITATIONS AND ASSUMPTIONS:")
        for limit in report.limitations_and_assumptions:
            print(f"- {limit}")
            
        print("\nSUGGESTED NEXT STEPS:")
        for step in report.suggested_next_steps:
            print(f"- {step}")
            
        print("\n" + "=" * 80)
        print("Research finished successfully!")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] Research run failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
