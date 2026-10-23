"""Actual four-stage manuscript builds; missing inputs fail explicitly."""
from .common import *
import subprocess

def compile_one(directory,main,log):
    directory=Path(directory);env=dict(os.environ);env['TEXINPUTS']=str(directory/'vendor/soul')+':'
    output=[]
    for command in (["pdflatex","-interaction=nonstopmode","-halt-on-error",main],["bibtex",Path(main).stem],
                    ["pdflatex","-interaction=nonstopmode","-halt-on-error",main],["pdflatex","-interaction=nonstopmode","-halt-on-error",main]):
        r=subprocess.run(command,cwd=directory,env=env,text=True,capture_output=True);output.append('$ '+' '.join(command)+'\n'+r.stdout+r.stderr)
        write(log,'\n'.join(output))
        if r.returncode:raise RuntimeError('TeX failed: '+str(log))
    pdf=directory/Path(main).with_suffix('.pdf')
    if not pdf.is_file() or pdf.stat().st_size==0 or not pdf.read_bytes().startswith(b'%PDF'):raise ValueError('Missing/invalid PDF')
    print('compiled',main,pdf.stat().st_size,flush=True)

def main():
    for folder,main in [('journal','HETE_JOURNAL_V4_3.tex'),('preprint','HETE_PREPRINT_V3.tex')]:
        compile_one(TASK/'paper'/folder,main,TASK/'logs'/('build_'+folder+'.txt'))

if __name__=='__main__':main()
