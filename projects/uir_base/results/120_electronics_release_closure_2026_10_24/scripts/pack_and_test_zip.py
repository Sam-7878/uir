import os
import zipfile
import tempfile
import subprocess

source_dir = r'/mnt/d/_Work/goat_bank/uir/projects/uir_base/paper/mdpi_electronics_120'
zip_dest = r'/mnt/d/_Work/goat_bank/uir/projects/uir_base/results/120_electronics_release_closure_2026_10_24/release/local_submission_sources_120.zip'

files_to_pack = [
    'main.tex',
    'main.pdf',
    'references.bib',
    'soul.sty',
    'soul-ori.sty',
]

with zipfile.ZipFile(zip_dest, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in files_to_pack:
        p = os.path.join(source_dir, f)
        zf.write(p, arcname=f)
    for root, dirs, files in os.walk(os.path.join(source_dir, 'Definitions')):
        for f in files:
            p = os.path.join(root, f)
            arcname = os.path.relpath(p, source_dir)
            zf.write(p, arcname=arcname)
    for root, dirs, files in os.walk(os.path.join(source_dir, 'figures')):
        for f in files:
            p = os.path.join(root, f)
            arcname = os.path.relpath(p, source_dir)
            zf.write(p, arcname=arcname)

size = os.path.getsize(zip_dest)
print(f'Successfully created {zip_dest} (size: {size} bytes)')

# Test unpack and build in tempdir
with tempfile.TemporaryDirectory() as tmpdir:
    print(f'Unpacking to {tmpdir} for clean room test build...')
    with zipfile.ZipFile(zip_dest, 'r') as zf:
        zf.extractall(tmpdir)
    res1 = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], cwd=tmpdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res2 = subprocess.run(['bibtex', 'main'], cwd=tmpdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res3 = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], cwd=tmpdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res4 = subprocess.run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], cwd=tmpdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pdf_out = os.path.join(tmpdir, 'main.pdf')
    if res4.returncode == 0 and os.path.exists(pdf_out):
        print(f'SUCCESS! Clean room build inside tempdir passed cleanly (PDF size: {os.path.getsize(pdf_out)} bytes)')
    else:
        print(f'FAILED: {res4.returncode}')
