"""Compatibility entry point for the audited full 850-case closure campaign.

The interrupted N=240 implementation is preserved under docs/security_v3_2/audit.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from evaluation.llm_security_v3_2.closure_campaign import main
if __name__=='__main__':main()
