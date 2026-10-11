# UIR Repository Multi-Project Reorganization (uir_base & uir_security)

현재 `uir` 저장소는 **`uir_base` (UIR Core / Baseline)** 와 **`uir_security` (UIR ZTA / LLM Security)** 총 2개의 연구 프로젝트를 공유하고 있습니다. 사용자가 이미 선행 작업한 `docs/` 및 `tests/` 구조(`uir_base/`, `uir_security/`)에 맞추어, **`results/`** 및 **`evaluation/`** 폴더를 2개 프로젝트 하위 디렉터리로 체계적으로 재배치하고, 이를 **`uir/docs/architecture/`** 에 마크다운 문서로 상세히 기록하는 작업 계획입니다.

---

## User Review Required

> [!IMPORTANT]
> **폴더 명칭 표준화**: 사용자가 `tests/`와 `docs/`에서 이미 적용한 명칭인 **`uir_base`** 와 **`uir_security`** 를 표준 디렉터리명으로 사용합니다. (설명 및 문서에는 `uir_baseline`을 동일한 의미로 명시)

> [!IMPORTANT]
> **테스트 및 파이썬 임포트 하위 호환성 보장**:
> `evaluation/` 폴더 하위 항목이 `evaluation/uir_base/` 및 `evaluation/uir_security/`로 이동함에 따라:
> 1. `evaluation/__init__.py`에서 기존 모듈 경로(예: `evaluation.llm_security_v3_2`, `evaluation.uir_phase4d` 등)를 투명하게 접근할 수 있도록 동적 패키지 alias / sys.path shim을 제공하여 기존 코드/테스트가 깨지지 않도록 보장합니다.
> 2. `tests/uir_security/` 내에서 발생한 경로 레벨 버그(`parents[2]` -> `parents[3]`) 및 새 경로를 동기화하여 전체 130개 단위 테스트가 100% 통과하도록 검증합니다.

---

## Proposed Changes

### 1. `results/` 폴더 재배치

`results/` 아래에 `uir_base`와 `uir_security` 디렉터리를 생성하고 각각 이동합니다.

#### A. `results/uir_security/` (보안 프로젝트 결과 데이터)
- `llm_security/`
- `llm_security_v2/`
- `llm_security_v3/`
- `llm_security_v3_1/`
- `llm_security_v3_1_preclosure/`
- `llm_security_v3_2/`
- `llm_security_v3_2_antigravity_incomplete_20260908/`
- `llm_security_v3_2_closure/`
- `llm_security_v3_2_interrupted_20260908/`
- `llm_security_v3_prevalidation/`
- `HETE_UIR_ZTA_V3_2_FINAL_PACKAGE/`
- `HETE_UIR_ZTA_V3_2_FINAL_PACKAGE.zip`
- `HETE_UIR_ZTA_V3_2_FINAL_PACKAGE.zip.sha256`
- `security_v3_2_final.zip`
- `security_v3_2_final.zip.sha256`

#### B. `results/uir_base/` (베이스라인 프로젝트 결과 데이터)
- `uir/`
- `uir_generalization/`
- `uir_phase3/`
- `uir_phase3b/`
- `uir_phase3c/`
- `uir_phase3d/`
- `uir_phase4/`
- `uir_phase4b/`
- `uir_phase4c/`
- `uir_phase4d/`
- `uir_phase4e/`
- `uir_phase4f/`
- `uir_slm/`

---

### 2. `evaluation/` 폴더 재배치 및 패키징

`evaluation/` 아래에 `uir_base`와 `uir_security` 디렉터리를 생성하고 평가 소스 코드를 재배치합니다.

#### A. `evaluation/uir_security/`
- `llm_security/`
- `llm_security_v3/`
- `llm_security_v3_1/`
- `llm_security_v3_2/`
- `__init__.py` [NEW]

#### B. `evaluation/uir_base/`
- `uir/`
- `uir_external/`
- `uir_generalization/`
- `uir_phase3b/`
- `uir_phase3d/`
- `uir_phase4/`
- `uir_phase4b/`
- `uir_phase4c/`
- `uir_phase4d/`
- `uir_phase4e/`
- `uir_phase4f/`
- `uir_slm/`
- `__init__.py` [NEW]

#### C. `evaluation/__init__.py` [MODIFY]
- 루트 `__init__.py`에 `uir_base` 및 `uir_security` 패키지 네임스페이스 자동 로드 및 하위 호환 shim 구성 (`sys.modules` alias 매핑으로 `evaluation.llm_security_v3_2` 및 `evaluation.uir_phase4d` 기존 임포트 완벽 지원).

---

### 3. `tests/` 단위 테스트 경로 보정

- `tests/uir_security/security_v3_1/test_opaque_runtime_identity.py`: `parents[2]` -> `parents[3]` 및 새 evaluation 경로 반영.
- `tests/uir_security/security_v3_1/test_provenance_anti_spoofing.py`: `parents[2]` -> `parents[3]` 및 새 evaluation 경로 반영.
- 기타 이동에 따른 테스트 코드 내 상대 경로 참조 점검.

---

### 4. 아키텍처 문서화

#### [NEW] [REPOSITORY_PROJECT_STRUCTURE.md](file:///d:/_Work/goat_bank/uir/docs/architecture/REPOSITORY_PROJECT_STRUCTURE.md)
`uir/docs/architecture/REPOSITORY_PROJECT_STRUCTURE.md`를 생성하여 다음 내용을 상세히 기록:
1. **프로젝트 분리 개요**:
   - `uir_base`: UIR 프로토콜 정의, 컴파일러, 정형 검증, 베이스라인 연구 (`_47_UIR.tex`)
   - `uir_security`: ZTA(Zero Trust Architecture) 기반 LLM 보안 파이프라인, 공격 벤치마크, 적응형 공격, 실증 메트릭 (`_47.1_UIR_ZTA.tex`)
2. **폴더 매핑 가이드**:
   - `docs/` (papers, formal, architecture, evaluation, work_reports 매핑)
   - `tests/` (uir_base vs uir_security)
   - `results/` (각 논문별 인용 데이터 위치)
   - `evaluation/` (각 실험/벤치마크 러너 소스 위치)
3. **논문 작성 시 데이터 탐색 가이드**:
   - Paper 1 (`_47_UIR`): `results/uir_base/...` 참조
   - Paper 2 (`_47_1_UIR_for_ZTA`): `results/uir_security/...` 참조
4. **향후 개발 및 확장 가이드라인**.

---

## Verification Plan

### Automated Tests
1. **Git 상태 보존 및 이동 검증**:
   - `git mv` 명령어를 통해 파일 히스토리를 유지하며 디렉터리 이동.
2. **단위 테스트 실행 (WSL2 Ubuntu 26.04.1)**:
   ```bash
   wsl -d Ubuntu bash -c "cd /mnt/d/_Work/goat_bank/uir && source .venv/bin/activate && PYTHONPATH=. pytest tests/ -v"
   ```
   - 130/130 단위 테스트 100% 통과 확인.
3. **LaTeX 논문 컴파일 검증**:
   - `_47_1_UIR_for_ZTA`:
     ```bash
     wsl -d Ubuntu bash -c "cd /mnt/d/_Work/goat_bank/uir/docs/papers/_47_1_UIR_for_ZTA && pdflatex -interaction=nonstopmode _47.1_UIR_ZTA.tex"
     ```
   - `_47_UIR`:
     ```bash
     wsl -d Ubuntu bash -c "cd /mnt/d/_Work/goat_bank/uir/docs/papers/_47_UIR && pdflatex -interaction=nonstopmode _47_UIR.tex"
     ```
     (PDF 정상 빌드 확인)

### Manual Verification
- `results/uir_base/` 및 `results/uir_security/` 폴더 트리 구조 확인.
- `evaluation/uir_base/` 및 `evaluation/uir_security/` 폴더 트리 구조 확인.
- `docs/architecture/REPOSITORY_PROJECT_STRUCTURE.md` 내용 검토.
