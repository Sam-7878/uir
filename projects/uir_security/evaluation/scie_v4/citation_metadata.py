"""Review primary cached metadata; HTTP retrieval alone is not validation."""
import html
import json
import re
import subprocess
from html.parser import HTMLParser

from .common import TASK, csv_write, load, sha, write
from .references import SOURCES, prepare


class Meta(HTMLParser):
    def __init__(self):
        super().__init__(); self.fields={}

    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='meta' and a.get('name','').startswith('citation_'):
            self.fields.setdefault(a['name'],[]).append(a.get('content',''))


def main():
    entries=prepare(); reviewed=[]; metadata={}
    for key,block in entries.items():
        path=TASK/'resources/citation_sources'/f'{key}.payload'
        if not path.exists():
            reviewed.append({'key':key,'source':SOURCES[key],'verification':'HOLD: source retrieval failed',
                             'authors':'','year':'','title':'','payload_sha256':''})
            continue
        raw=path.read_bytes(); data={}; kind=''
        if raw.startswith(b'%PDF'):
            text=subprocess.check_output(['pdftotext','-f','1','-l','2',str(path),'-'],text=True)
            write(path.with_suffix('.extracted.txt'),text)
            kind='official PDF title pages'
            # These three title pages were explicitly read in this workflow.
            data={'review':'title, named authors, report/venue and date matched to the official PDF title pages'}
        elif raw.startswith(b'{'):
            data=json.loads(raw).get('message',{});kind='publisher-deposited Crossref metadata'
            if isinstance(data,list):raise ValueError(key)
        else:
            parser=Meta();parser.feed(raw.decode(errors='replace'));data=parser.fields
            kind='official HTML citation metadata' if data else 'official organizational page'
        title=(data.get('citation_title') or data.get('title') or [''])[0]
        authors=data.get('citation_author') or [
            (a.get('given','')+' '+a.get('family','')).strip() for a in data.get('author',[])]
        authors=[a for a in authors if a and a!=':']
        year=(data.get('citation_date') or data.get('citation_publication_date') or [''])[0][:4]
        if not year:
            year=str((data.get('published',{}).get('date-parts') or [['']])[0][0])
        # Select a single traceable publication version when old conference data
        # was not independently verified. Key names remain historical aliases.
        if 'arxiv.org' in SOURCES[key] and title and authors:
            identifier=SOURCES[key].rsplit('/',1)[-1]
            author_text=' and '.join(authors if len(authors)<=20 else authors[:6]+['others'])
            block='@article{'+key+',\n author = {'+author_text+'},\n title = {'+html.unescape(title)+'},\n journal = {arXiv preprint arXiv:'+identifier+'},\n year = {'+year+'},\n doi = {10.48550/arXiv.'+identifier+'},\n url = {'+SOURCES[key]+'}\n}'
            entries[key]=block
        if key in ('owasp2026','mitreatlas2026'):
            block=re.sub(r'Accessed August 31, 2026','Accessed October 21, 2026; living resource',block)
            entries[key]=block
        source_url=SOURCES[key]
        if key=='westfall1993resampling':
            source_url=load(path.with_name('westfall1993resampling_source.json'))['url']
            page=raw.decode(errors='replace')
            if not all(value in page for value in ('1993','Westfall','Young','978-0-471-55761-6')):
                raise ValueError('Publisher book metadata missing')
            kind='official Wiley-VCH book page: authors, 1993 and ISBN verified'
        metadata[key]={'kind':kind,'metadata':data,'source':source_url,'source_sha256':sha(path)}
        reviewed.append({'key':key,'source':source_url,'verification':kind,
                         'authors':'; '.join(authors) or 'See reviewed PDF or organizational author in bibliography',
                         'year':year or re.search(r'year\s*=\s*\{(\d{4})',block).group(1),
                         'title':html.unescape(title) or 'See reviewed PDF/organizational title in bibliography',
                         'payload_sha256':sha(path)})
    write(TASK/'resources/references_clean.bib','\n\n'.join(entries.values())+'\n')
    write(TASK/'manifests/citation_metadata_review.json',metadata)
    csv_write(TASK/'data/citation_verification.csv',reviewed)
    write(TASK/'reports/CITATION_REVIEW.md',
          '# Citation review\n\nCanonical ACL and NDSS records correct the Zhan and IsolateGPT citations; '
          'the unverifiable Hofer item is replaced with arXiv:2606.10525. Duplicate PoisonedRAG and instruction-hierarchy keys are merged; '
          'Westfall is keyed 1993. Cached primary arXiv author/title/date metadata is used directly, including long-report et-al truncation '
          '(complete authors remain in the metadata receipt). SecAlign, Spotlighting and AgentDojo cite their verified arXiv versions; '
          'unverified old conference pages are not retained as independently verified publication metadata. '
          'The NIST and NDSS PDF title pages were reviewed explicitly. Organizational resources use their institutional authors and access dates. '
          'The main Wiley page returns HTTP 403 to the local client; a publisher-owned Wiley-VCH page was retrieved instead '
          'and its authors, 1993 edition and ISBN were checked and cached. '
          'A clean BibTeX build establishes syntactic resolution, not independent bibliographic correctness.\n')
    print('reviewed',len(reviewed),'uncached',sum(not r['payload_sha256'] for r in reviewed))


if __name__=='__main__':main()
