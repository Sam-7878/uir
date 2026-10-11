# UIR Repository Multi-Project Reorganization Walkthrough

`uir` 저장소의 다중 프로젝트(`uir_base` 및 `uir_security`) 체계 재배치 작업을 완료했습니다.
사용자께서 선행 정리해 두신 `docs/` 및 `tests/`의 구조(`uir_base/`, `uir_security/`)에 맞추어 `results/` 및 `evaluation/` 폴더를 체계적으로 분리 배치하고, 하위 호환성 보장 및 아키텍처 문서를 완비했습니다.

---

## 1. 재배치 주요 결과 요약

```
uir/
├── docs/
│   ├── architecture/
│   │   ├── REPOSITORY_PROJECT_STRUCTURE.md  <── [NEW] 전체 다중 프로젝트 구조 명세서
│   │   └── uir_security/
│   ├── evaluation/uir_security/
│   ├── formal/uir_base/
│   ├── papers/
│   │   ├── _47_UIR/                         <── [Paper 1] Core UIR 논문
│   │   └── _47_1_UIR_for_ZTA/               <── [Paper 2] Security ZTA 논문
│   └── work_reports/
│       ├── uir_base/
│       └── uir_security/
├── tests/
│   ├── uir_base/
│   └── uir_security/
├── results/
│   ├── uir_base/                            <── [Paper 1 전용 결과 데이터 (13개 서브폴더)]
│   └── uir_security/                        <── [Paper 2 전용 결과 데이터 (15개 서브폴더)]
└── evaluation/
    ├── __init__.py                          <── [MODIFIED] 동적 __path__ 확장 (하위 호환 보장)
    ├── uir_base/                            <── [Paper 1 전용 평가 및 벤치마크 코드 (12개)]
    └── uir_security/                        <── [Paper 2 전용 평가 및 벤치마크 코드 (4개)]
```

---

## 2. 세부 변경 사항

### A. `results/` 폴더 분리
- **`results/uir_base/`**:
  - `uir/`, `uir_generalization/`, `uir_phase3/`, `uir_phase3b/`, `uir_phase3c/`, `uir_phase3d/`, `uir_phase4/`, `uir_phase4b/`, `uir_phase4c/`, `uir_phase4d/`, `uir_phase4e/`, `uir_phase4f/`, `uir_slm/`
- **`results/uir_security/`**:
  - `llm_security/`, `llm_security_v2/`, `llm_security_v3/`, `llm_security_v3_1/`, `llm_security_v3_1_preclosure/`, `llm_security_v3_2/`, `llm_security_v3_2_closure/`, `llm_security_v3_prevalidation/` 및 각종 v3.2 아카이브
  - `HETE_UIR_ZTA_V3_2_FINAL_PACKAGE/`, `HETE_UIR_ZTA_V3_2_FINAL_PACKAGE.zip`, `security_v3_2_final.zip`
- `git mv` 및 `git add` 연동으로 기존 git tracked 결과 파일(46개 파일)의 Rename 히스토리를 100% 보존.

### B. `evaluation/` 폴더 분리 및 패키징
- **`evaluation/uir_base/`**:
  - `uir/`, `uir_external/`, `uir_generalization/`, `uir_phase3b/`, `uir_phase3d/`, `uir_phase4/`, `uir_phase4b/`, `uir_phase4c/`, `uir_phase4d/`, `uir_phase4e/`, `uir_phase4f/`, `uir_slm/`
  - `evaluation/uir_base/__init__.py` 생성
- **`evaluation/uir_security/`**:
  - `llm_security/`, `llm_security_v3/`, `llm_security_v3_1/`, `llm_security_v3_2/`
  - `evaluation/uir_security/__init__.py` 생성
- **`evaluation/__init__.py`**:
  - `__path__` 동적 확장을 통해 레거시 임포트(`from evaluation.llm_security_v3_2...`, `from evaluation.uir_phase4d...`)와 신규 프로젝트 임포트(`from evaluation.uir_security...`, `from evaluation.uir_base...`)를 동시 지원.

### C. 단위 테스트 및 참조 경로 보정
- `tests/uir_security/security_v3_1/test_opaque_runtime_identity.py`: `parents[3]` 및 데이터셋 경로 보정.
- `tests/uir_security/security_v3_1/test_provenance_anti_spoofing.py`: `parents[3]` 및 매니페스트 경로 보정.
- `tests/uir_security/security_v3/test_no_label_leakage.py`: 파이프라인 파일 경로 보정.
- `tests/uir_security/test_security_benchmark_v2.py`: `DEV_DATASET` 경로 추상화.
- `evaluation/uir_base/uir_phase4d/common.py` 및 `runtime/`: 동적 `ROOT` 및 `EVAL_DIR` 해석 반영.

### D. 아키텍처 문서화
- **[REPOSITORY_PROJECT_STRUCTURE.md](file:///d:/_Work/goat_bank/uir/docs/architecture/REPOSITORY_PROJECT_STRUCTURE.md)**:
  - 두 연구 프로젝트의 학술적 정의 및 논문 매핑
  - 논문 작성 시 섹션/표/지표별 데이터 파일 위치 가이드
  - 전체 디렉터리 구조 및 공유 인프라 가이드라인 명시

---

## 3. 검증 결과

1. **Python 모듈 임포트 검증**:
   - `evaluation.llm_security_v3_2` (Legacy) ✅ OK
   - `evaluation.uir_security.llm_security_v3_2` (New) ✅ OK
   - `evaluation.uir_phase4d` (Legacy) ✅ OK
   - `evaluation.uir_base.uir_phase4d` (New) ✅ OK

2. **전체 단위 테스트 통과 (100% PASS)**:
   ```bash
   source .venv/bin/activate
   PYTHONPATH=. pytest tests/ -v
   ```
   - **130 passed in 7.76s (0 failed, 0 errors)**

3. **LaTeX 논문 컴파일 검증**:
   - `docs/papers/_47_1_UIR_for_ZTA/_47.1_UIR_ZTA.tex` -> `_47.1_UIR_ZTA.pdf` (18 pages, 0 errors) 정상 컴파일 완료 ✅
