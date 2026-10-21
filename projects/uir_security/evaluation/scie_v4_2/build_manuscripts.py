"""Four-stage TeX builds with explicit task-local missing-package dependency."""
from .common import *
import os
import subprocess


def build(directory,main,log):
    directory=Path(directory);env=dict(os.environ)
    soul=directory/'vendor/soul'
    if not soul.is_dir():soul=OLD/'resources/tex_packages/extracted/usr/share/texlive/texmf-dist/tex/generic/soul'
    env['TEXINPUTS']=str(soul)+':'
    runs=[]
    for command in (["pdflatex","-interaction=nonstopmode","-halt-on-error",main],
                    ["bibtex",Path(main).stem],
                    ["pdflatex","-interaction=nonstopmode","-halt-on-error",main],
                    ["pdflatex","-interaction=nonstopmode","-halt-on-error",main]):
        result=subprocess.run(command,cwd=directory,env=env,capture_output=True,text=True)
        runs.append('$ '+' '.join(command)+'\n'+result.stdout+result.stderr)
        write(log,'\n'.join(runs))
        if result.returncode:raise RuntimeError(f'Build failed: {command}; see {log}')
    pdf=directory/Path(main).with_suffix('.pdf')
    if pdf.stat().st_size==0 or not pdf.read_bytes().startswith(b'%PDF'):raise ValueError('Invalid PDF')
    print(pdf, pdf.stat().st_size,flush=True)
    return pdf


def main():
    for folder,source in [('manuscript_preprint','HETE_PREPRINT_V2.tex'),('manuscript_electronics','HETE_JOURNAL_V4_2.mdpi.tex')]:
        build(TASK/folder,source,TASK/'logs'/f'{folder}_clean_build.txt')


if __name__=='__main__':main()
