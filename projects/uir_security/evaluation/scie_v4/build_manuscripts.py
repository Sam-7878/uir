"""Fresh four-stage builds and source-bundle completeness checks."""
import json
import os
import re
import subprocess

from .common import TASK, sha, write


def main():
    directory=TASK/'manuscript_private';results=[]
    env=dict(os.environ)
    local_tex=TASK/'resources/tex_packages/extracted/usr/share/texlive/texmf-dist/tex/generic/soul'
    env['TEXINPUTS']=str(local_tex)+':'+env.get('TEXINPUTS','')
    for stem in ('HETE_PREPRINT_V1','HETE_JOURNAL.mdpi'):
        for ext in ('.aux','.bbl','.blg','.log','.out'):
            (directory/(stem+ext)).unlink(missing_ok=True)
        commands=[['pdflatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error',stem+'.tex'],
                  ['bibtex',stem],['pdflatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error',stem+'.tex'],
                  ['pdflatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error',stem+'.tex']]
        logs=[];codes=[];last=''
        for command in commands:
            result=subprocess.run(command,cwd=directory,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            logs.append('$ '+' '.join(command)+'\n'+result.stdout);codes.append(result.returncode);last=result.stdout
            if result.returncode:break
        write(TASK/f'logs/{stem}_build.log','\n'.join(logs))
        checks={'stem':stem,'exit_codes':codes,
                'undefined_citations':len(re.findall(r'Citation .* undefined',last)),
                'undefined_references':len(re.findall(r'Reference .* undefined|There were undefined references',last)),
                'multiply_defined_labels':len(re.findall(r'multiply defined',last)),
                'overfull_boxes':len(re.findall(r'Overfull',last)),
                'final_warnings':[s for s in last.splitlines() if 'Warning' in s],
                'pdf_sha256':sha(directory/(stem+'.pdf')) if (directory/(stem+'.pdf')).exists() else None}
        checks['passed']=codes==[0,0,0,0] and all(checks[k]==0 for k in ['undefined_citations','undefined_references','multiply_defined_labels','overfull_boxes'])
        results.append(checks)
        print(json.dumps(checks),flush=True)
        if codes[-1]!=0:print(last[-1600:],flush=True)
    write(TASK/'manifests/manuscript_build_audit.json',results)
    write(TASK/'reports/BUILD_REPORT.md','# Fresh manuscript builds\n\n'+json.dumps(results,indent=2)+'\n\n'
          'Built without shell escape, using a task-local copy of the official MDPI CDN template and a generic article preprint wrapper. '
          'Author statements remain pending; a PDF build is not an acceptance or publication event.\n')
    return 0 if all(r['passed'] for r in results) else 1


if __name__=='__main__':raise SystemExit(main())
