#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/"results/uir_phase3d"
def main():
    result=subprocess.run([sys.executable,"-m","pytest","-q","evaluation/uir_phase3d/tests/test_b6_integration.py"],cwd=ROOT,text=True,capture_output=True)
    data={"status":"passed" if result.returncode==0 else "failed","test_file":"evaluation/uir_phase3d/tests/test_b6_integration.py","required_test_count":8,"stdout":result.stdout.strip(),"stderr":result.stderr.strip()}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"b6_integration_tests.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    return result.returncode
if __name__=="__main__":raise SystemExit(main())
