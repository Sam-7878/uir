"""Extract manuscript ZIPs outside the repository and render their own inputs."""
import json
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

from .common import TASK, load, sha, write


def main():
    results=[]
    for archive,stem in [('HETE_PREPRINT_V1.zip','HETE_PREPRINT_V1'),('HETE_JOURNAL_SOURCE.zip','HETE_JOURNAL.mdpi')]:
        path=TASK/'resources'/archive
        with tempfile.TemporaryDirectory(prefix='hete-source-bundle-') as temporary:
            directory=Path(temporary)
            with zipfile.ZipFile(path) as z:
                for name in z.namelist():
                    p=Path(name)
                    if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe archive member')
                z.extractall(directory)
            manifest=load(directory/'MANIFEST.json')
            missing=[name for name,digest in manifest.items() if not (directory/name).is_file() or sha(directory/name)!=digest]
            if missing:raise ValueError(missing)
            env=dict(os.environ)
            env['TEXINPUTS']=str(TASK/'resources/tex_packages/extracted/usr/share/texlive/texmf-dist/tex/generic/soul')+':'
            commands=[['pdflatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error','-recorder',stem+'.tex'],
                      ['bibtex',stem],['pdflatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error','-recorder',stem+'.tex'],
                      ['pdflatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error','-recorder',stem+'.tex']]
            output=[];codes=[];last=''
            for command in commands:
                r=subprocess.run(command,cwd=directory,env=env,capture_output=True,text=True)
                output.append(r.stdout+r.stderr);codes.append(r.returncode);last=output[-1]
                if r.returncode:break
            write(TASK/'logs'/(stem+'_extracted_bundle_build.log'),'\n'.join(output))
            source_leaks=[]
            for line in (directory/(stem+'.fls')).read_text().splitlines():
                if line.startswith('INPUT ') and '/goat_bank/uir/' in line and '/tex_packages/' not in line:
                    source_leaks.append(line)
            pdf=directory/(stem+'.pdf');extracted=''
            if pdf.is_file():extracted=subprocess.check_output(['pdftotext',str(pdf),'-'],text=True)
            unexpected_header='submitted to Electronics' in ' '.join(extracted.split())
            warnings=bool(re.search(r'Citation .* undefined|Reference .* undefined|Overfull|multiply defined',last))
            result={'archive':archive,'zip_sha256':sha(path),'members_verified':len(manifest),
                    'exit_codes':codes,'unexpected_repository_inputs':source_leaks,
                    'unresolved_or_overflow':warnings,'misleading_submission_header':unexpected_header,
                    'same_host_fresh_directory':True,'fresh_operating_system':False}
            result['passed']=codes==[0,0,0,0] and not source_leaks and not warnings and not unexpected_header
            results.append(result);print(json.dumps(result),flush=True)
    write(TASK/'manifests/EXTRACTED_BUNDLE_VALIDATION.json',results)
    return int(not all(r['passed'] for r in results))


if __name__=='__main__':raise SystemExit(main())
