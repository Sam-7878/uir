"""Compatibility entry point; partial artifacts must fail scientific validity."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from evaluation.llm_security_v3_2.validate_publication_results import main
if __name__=='__main__':main()
