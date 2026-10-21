"""J01: verified corrections and an auditable source retrieval ledger."""
from __future__ import annotations

import concurrent.futures
import re

import requests

from .common import PROJECT, TASK, csv_write, sha, write

ALIASES = {'zou2024poisonedrag':'zou2025poisonedrag', 'wallace2024instruction':'wallace2024instructionhierarchy',
           'westfall2010multiple':'westfall1993resampling', 'hofer2026automated':'hofer2026assessing',
           'wang2024isolate':'wu2025isolategpt'}
SOURCES = {
 'owasp2026':'https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/',
 'nistaml2025':'https://doi.org/10.6028/NIST.AI.100-2e2025',
 'nistzt2020':'https://doi.org/10.6028/NIST.SP.800-207',
 'mitreatlas2026':'https://atlas.mitre.org/',
 'greshake2023indirect':'https://doi.org/10.1145/3605764.3623985',
 'zou2023universal':'https://arxiv.org/abs/2307.15043',
 'debenedetti2025camel':'https://arxiv.org/abs/2503.18813',
 'wallace2024instructionhierarchy':'https://arxiv.org/abs/2404.13208',
 'zhan2025adaptive':'https://aclanthology.org/2025.findings-naacl.395/',
 'wu2025isolategpt':'https://www.ndss-symposium.org/wp-content/uploads/2025-1131-paper.pdf',
 'shi2025progent':'https://arxiv.org/abs/2504.11703',
 'debenedetti2024agentdojo':'https://arxiv.org/abs/2406.13352',
 'lewis2020rag':'https://arxiv.org/abs/2005.11401',
 'chen2025struq':'https://www.usenix.org/conference/usenixsecurity25/presentation/chen-sizhe',
 'chen2025secalign':'https://arxiv.org/abs/2410.05451',
 'hines2024spotlighting':'https://arxiv.org/abs/2403.14720',
 'zou2025poisonedrag':'https://www.usenix.org/conference/usenixsecurity25/presentation/zou-poisonedrag',
 'abdin2024phi3':'https://arxiv.org/abs/2404.14219',
 'qwen25techreport2024':'https://arxiv.org/abs/2412.15115',
 'wilson1927probable':'https://doi.org/10.1080/01621459.1927.10502953',
 'mcnemar1947note':'https://doi.org/10.1007/BF02295996',
 'cohen1960kappa':'https://doi.org/10.1177/001316446002000104',
 'westfall1993resampling':'https://www.wiley.com/en-us/Resampling+Based+Multiple+Testing%3A+Examples+and+Methods+for+p+Value+Adjustment-p-9780471557616',
 'hofer2026assessing':'https://arxiv.org/abs/2606.10525',
 'hsine2026middleware':'https://api.crossref.org/works/10.3390/electronics15163554',
}

CORRECTIONS = {
 'zhan2025adaptive': r'''@inproceedings{zhan2025adaptive,
 author = {Qiusi Zhan and Richard Fang and Henil Shalin Panchal and Daniel Kang},
 title = {Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on {LLM} Agents},
 booktitle = {Findings of the Association for Computational Linguistics: NAACL 2025},
 pages = {7116--7132}, year = {2025}, publisher = {Association for Computational Linguistics},
 doi = {10.18653/v1/2025.findings-naacl.395},
 url = {https://aclanthology.org/2025.findings-naacl.395/}
}''',
 'hofer2026assessing': r'''@article{hofer2026assessing,
 author = {David Hofer and Edoardo Debenedetti and Florian Tram{\`e}r},
 title = {Assessing Automated Prompt Injection Attacks in Agentic Environments},
 journal = {arXiv preprint arXiv:2606.10525}, year = {2026},
 doi = {10.48550/arXiv.2606.10525}, url = {https://arxiv.org/abs/2606.10525}
}''',
 'wu2025isolategpt': r'''@inproceedings{wu2025isolategpt,
 author = {Yuhao Wu and Franziska Roesner and Tadayoshi Kohno and Ning Zhang and Umar Iqbal},
 title = {{IsolateGPT}: An Execution Isolation Architecture for {LLM}-Based Agentic Systems},
 booktitle = {Network and Distributed System Security (NDSS) Symposium}, year = {2025},
 doi = {10.14722/ndss.2025.241131},
 url = {https://www.ndss-symposium.org/wp-content/uploads/2025-1131-paper.pdf}
}''',
 'westfall1993resampling': r'''@book{westfall1993resampling,
 author = {Peter H. Westfall and S. Stanley Young},
 title = {Resampling-Based Multiple Testing: Examples and Methods for p-Value Adjustment},
 publisher = {John Wiley \& Sons}, year = {1993}, isbn = {9780471557616}
}''',
 'hsine2026middleware': r'''@article{hsine2026middleware,
 author = {Adam Ait Hsine and Abdullahi Arabo},
 title = {A Privacy-Preserving Middleware Architecture for Detecting Prompt Injection and Sensitive Data Exposure in Large-Language-Model Interactions},
 journal = {Electronics}, volume = {15}, number = {16}, pages = {3554}, year = {2026},
 doi = {10.3390/electronics15163554}, url = {https://doi.org/10.3390/electronics15163554}
}''',
}


def prepare():
    source = PROJECT/'paper/_47_1_UIR_ZTA/references.bib'
    blocks = re.findall(r'(?ms)^@.*?(?=^@|\Z)', source.read_text())
    entries = {}
    for block in blocks:
        old = re.match(r'@\w+\{([^,]+)',block).group(1)
        key = ALIASES.get(old,old)
        if key in entries:
            continue
        entries[key] = CORRECTIONS.get(key, block.strip())
    entries.update(CORRECTIONS)
    # Preserve original publication venues, but repair incomplete author lists
    # when the canonical arXiv page supplies the complete report authors.
    import html
    for key in ('abdin2024phi3','qwen25techreport2024'):
        page=TASK/'resources/citation_sources'/f'{key}.payload'
        if page.exists():
            authors=re.findall(r'<meta\s+name="citation_author"\s+content="([^"]+)"',page.read_text())
            authors=[html.unescape(a) for a in authors if a not in {':'}]
            if authors:
                entries[key]=re.sub(r'author\s*=\s*\{.*?\},\n',lambda _: 'author = {'+' and '.join(authors)+'},\n',entries[key],count=1,flags=re.S)
    target = TASK/'resources/references_clean.bib'
    write(target,'\n\n'.join(entries.values())+'\n')
    return entries


def fetch(key, url):
    target = TASK/'resources/citation_sources'/f'{key}.payload'
    if target.exists():
        return {'key':key,'url':url,'http_status':'cached','payload_sha256':sha(target),'status':'retrieved_not_automatically_metadata_verified'}
    session=requests.Session();session.trust_env=False
    try:
        response=session.get(url,timeout=35)
        if response.status_code!=200 and url.startswith('https://doi.org/'):
            response=session.get('https://api.crossref.org/works/'+url.removeprefix('https://doi.org/'),timeout=35)
        if response.status_code == 200:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(response.content)
        return {'key':key,'url':url,'http_status':response.status_code,
                'payload_sha256':sha(target) if target.exists() else '',
                'status':'retrieved_not_automatically_metadata_verified' if response.status_code == 200 else 'retrieval_failed'}
    except requests.RequestException as exc:
        return {'key':key,'url':url,'http_status':'error','payload_sha256':'','status':repr(exc)}


def main():
    entries=prepare()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        outcomes=list(pool.map(lambda kv:fetch(*kv), [(key,SOURCES[key]) for key in entries]))
    csv_write(TASK/'data/citation_verification.csv',outcomes)
    write(TASK/'manifests/citation_key_aliases.json',ALIASES)
    print('canonical bibliography entries',len(entries),'retrieval failures',sum(r['http_status'] not in {200,'cached'} for r in outcomes))


if __name__=='__main__':
    main()
