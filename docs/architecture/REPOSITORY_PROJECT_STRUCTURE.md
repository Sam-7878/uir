# UIR Repository Multi-Project Architecture Specification

## 1. 개요 (Overview)

본 저장소(`uir`)는 학술적 목표와 평가 대상이 구분되는 **총 2개의 프로젝트**를 공유하는 모노레포(Monorepo) 구조로 운영됩니다.

1. **`uir_base` (UIR Baseline / Core Protocol)**:
   - **학술 논문**: `docs/papers/_47_UIR/` (*"Universal Intermediate Representation for Large Language Models"*)
   - **연구 목표**: LLM/SLM 입출력의 구조적 정형화, EBNF 기반 UIR 문법 및 의미론(Formal Semantics), Rust 기반 고속 AST 컴파일러, 도메인 일반화(Generalization) 및 다단계 벤치마크 평가 (Phase 3 ~ Phase 4f).
   - **핵심 가치**: 언어/도메인 불변성(Invariance), 비가역적 정보 손실 방지, 엄격한 스키마 준수.

2. **`uir_security` (UIR Zero Trust Architecture / LLM Security)**:
   - **학술 논문**: `docs/papers/_47_1_UIR_for_ZTA/` (*"HETE UIR for Zero Trust Architecture: Securing SLM/LLM Systems Against Adaptive Prompt Injection"*)
   - **연구 목표**: Zero Trust Architecture(ZTA) 원칙에 기반한 SLM 보안 격리, 간접 프롬프트 주입(Indirect Prompt Injection) 방어, 4계층 봉쇄 파이프라인(Capability Gate, Provenance Verifier, Output Guard, Behavioral Judges), 14개 적응형 공격 연산자 평가, McNemar 통계적 우위성 검증.
   - **핵심 가치**: 오라클 불변성, 권한 불상승(Non-escalation), 다중 계층 오염 차단, 완전한 실증적 재현성.

---

## 2. 논문별 데이터 및 리포트 탐색 가이드 (Paper Data Retrieval Guide)

논문 작성 및 수치 인용 시, 각 논문에서 참조해야 하는 데이터 경로가 아래와 같이 프로젝트별로 완전히 분리되어 있습니다.

```
uir/
├── docs/papers/
│   ├── _47_UIR/                 <── [Paper 1] Baseline 논문
│   └── _47_1_UIR_for_ZTA/       <── [Paper 2] Security ZTA 논문
├── results/
│   ├── uir_base/                <── [Data 1] Paper 1 인용 데이터
│   └── uir_security/            <── [Data 2] Paper 2 인용 데이터
└── evaluation/
    ├── uir_base/                <── [Code 1] Paper 1 실험/벤치마크 러너
    └── uir_security/            <── [Code 2] Paper 2 실험/벤치마크 러너
```

### 2.1. Paper 1 (`_47_UIR`) 인용 데이터 매핑

| 논문 섹션 / 표 / 그래프 | 참조 결과 경로 (`results/uir_base/`) | 관련 평가 스크립트 (`evaluation/uir_base/`) |
| :--- | :--- | :--- |
| **코어 UIR 벤치마크 & Ablation** | `results/uir_base/uir/` | `evaluation/uir_base/uir/run_uir_benchmark.py` |
| **도메인 일반화 (Generalization)** | `results/uir_base/uir_generalization/` | `evaluation/uir_base/uir_generalization/` |
| **SLM Core 추론 결과** | `results/uir_base/uir_slm/` | `evaluation/uir_base/uir_slm/` |
| **Phase 3 (데이터셋 동결 & 진단)** | `results/uir_base/uir_phase3/` | `evaluation/uir_base/uir_generalization/` |
| **Phase 3b ~ 3d (AI 다중 심사 & 합의)** | `results/uir_base/uir_phase3b/`<br>`results/uir_base/uir_phase3c/`<br>`results/uir_base/uir_phase3d/` | `evaluation/uir_base/uir_phase3b/`<br>`evaluation/uir_base/uir_phase3d/` |
| **Phase 4 ~ 4b (견고성 & 레이턴시)** | `results/uir_base/uir_phase4/`<br>`results/uir_base/uir_phase4b/` | `evaluation/uir_base/uir_phase4/`<br>`evaluation/uir_base/uir_phase4b/` |
| **Phase 4c ~ 4f (실시간 런타임 & 컴파일)** | `results/uir_base/uir_phase4c/`<br>`results/uir_base/uir_phase4d/`<br>`results/uir_base/uir_phase4e/`<br>`results/uir_base/uir_phase4f/` | `evaluation/uir_base/uir_phase4c/`<br>`evaluation/uir_base/uir_phase4d/`<br>`evaluation/uir_base/uir_phase4e/`<br>`evaluation/uir_base/uir_phase4f/` |

### 2.2. Paper 2 (`_47_1_UIR_for_ZTA`) 인용 데이터 매핑

| 논문 섹션 / 표 / 지표 | 참조 결과 경로 (`results/uir_security/`) | 관련 평가 스크립트 (`evaluation/uir_security/`) |
| :--- | :--- | :--- |
| **6-System Baseline 비교 표 (`tab:heldout-baselines`)** | `results/uir_security/llm_security_v3_2/baseline_comparison.json` | `evaluation/uir_security/llm_security_v3_2/run_publication_campaign_v3_2.py` |
| **McNemar 통계 검정 표 (`tab:mcnemar`)** | `results/uir_security/llm_security_v3_2/statistical_tests.json` | `evaluation/uir_security/llm_security_v3_2/stats/exact_mcnemar.py` |
| **단일 구성요소 절제 표 (`tab:single-ablation`)** | `results/uir_security/llm_security_v3_2/ablation_results.json` | `evaluation/uir_security/llm_security_v3_2/run_publication_campaign_v3_2.py` |
| **적응형 공격 분석 (14 Operators, B=20)** | `results/uir_security/llm_security_v3_2/adaptive_attack_results.json` | `evaluation/uir_security/llm_security_v3_2/adaptive_attacks/` |
| **심사관 일치도 (Judge Agreement κ)** | `results/uir_security/llm_security_v3_2/judge_agreement.json` | `evaluation/uir_security/llm_security_v3_2/stats/judge_agreement.py` |
| **Multi-Model 일반화 (Phi-3.5 vs Qwen-2.5)** | `results/uir_security/llm_security_v3_2/multi_model_results.json` | `evaluation/uir_security/llm_security_v3_2/run_publication_campaign_v3_2.py` |
| **원시 실행 로그 (Raw Executions)** | `results/uir_security/llm_security_v3_2/raw_runs/` | `evaluation/uir_security/llm_security_v3_2/` |
| **이전 버전 벤치마크 기록 (v2, v3, v3.1)** | `results/uir_security/llm_security/`<br>`results/uir_security/llm_security_v2/`<br>`results/uir_security/llm_security_v3/`<br>`results/uir_security/llm_security_v3_1/` | `evaluation/uir_security/llm_security/`<br>`evaluation/uir_security/llm_security_v3/`<br>`evaluation/uir_security/llm_security_v3_1/` |
| **최종 봉쇄 납품 패키지 및 SHA-256** | `results/uir_security/HETE_UIR_ZTA_V3_2_FINAL_PACKAGE/`<br>`results/uir_security/HETE_UIR_ZTA_V3_2_FINAL_PACKAGE.zip` | `evaluation/uir_security/llm_security_v3_2/validate_v3_2_results.py` |

---

## 3. 상세 디렉터리 구조 매핑 (Detailed Directory Mapping)

### 3.1. `docs/` 디렉터리 구조

```
docs/
├── architecture/
│   ├── REPOSITORY_PROJECT_STRUCTURE.md  <── [본 문서] 전체 다중 프로젝트 구조 명세
│   └── uir_security/                    <── Security ZTA 전용 아키텍처 문서
│       └── HETE_UIR_SECURITY_ARCHITECTURE.md
├── evaluation/
│   └── uir_security/                    <── Security 벤치마크 명세서 (v2, v2_final 등)
├── formal/
│   └── uir_base/                        <── UIR EBNF 문법, 정형 명세(Spec), 의미론(Semantics)
├── papers/
│   ├── _47_UIR/                         <── UIR Core 학술 논문 (LaTeX 소스, figures)
│   └── _47_1_UIR_for_ZTA/               <── UIR ZTA 학술 논문 (LaTeX 소스, figures, metrics)
└── work_reports/
    ├── uir_base/                        <── UIR Core 진행 보고서
    └── uir_security/                    <── UIR Security 단계별 작업 보고서 (000 ~ 204)
```

### 3.2. `tests/` 디렉터리 구조

```
tests/
├── uir_base/
│   └── uir_phase4d/                     <── UIR Core 런타임, 어댑터, 컴파일러 단위 테스트
└── uir_security/
    ├── security_v3/                     <── 권한 불상승, 불변성, 오염 전파 테스트
    ├── security_v3_1/                   <── 불투명 런타임 식별자, 오라클 격리, 안티스푸핑 테스트
    ├── security_v3_2/                   <── Output Guard, 적응형 돌연변이, Mock 에이전시, McNemar 테스트
    ├── test_benign_util.py              <── 정상 입력 유틸리티 보존 테스트
    ├── test_llm_trust.py                <── llm_trust 코어 런타임 테스트
    └── test_security_benchmark_v2.py    <── v2 벤치마크 재현성 테스트
```

### 3.3. `results/` 디렉터리 구조

```
results/
├── uir_base/
│   ├── uir/                             <── Baseline 원본 벤치마크 및 Ablation 데이터
│   ├── uir_generalization/              <── 도메인 일반화 평가 데이터
│   ├── uir_slm/                         <── SLM 베이스라인 원시 추론 로그
│   ├── uir_phase3/ ~ uir_phase3d/       <── Phase 3 세부 평가 데이터셋 및 AI 심사 기록
│   └── uir_phase4/ ~ uir_phase4f/       <── Phase 4 세부 평가 데이터셋 및 레이턴시 로그
└── uir_security/
    ├── llm_security/                    <── v1 보안 벤치마크 결과
    ├── llm_security_v2/                 <── v2 보안 벤치마크 결과
    ├── llm_security_v3/                 <── v3 보안 벤치마크 결과
    ├── llm_security_v3_1/               <── v3.1 실증 실행 결과
    ├── llm_security_v3_2/               <── v3.2 최종 논문 인용 결과 (캠페인 메트릭)
    ├── llm_security_v3_2_closure/       <── v3.2 독립 감사 및 무결성 검증 산출물
    ├── HETE_UIR_ZTA_V3_2_FINAL_PACKAGE/ <── 최종 논문 아티팩트 공식 패키지
    └── security_v3_2_final.zip          <── 공식 압축 배포본 및 SHA-256 해시
```

### 3.4. `evaluation/` 디렉터리 구조

```
evaluation/
├── __init__.py                          <── 하위 호환 import shim (__path__ 확장)
├── uir_base/
│   ├── __init__.py
│   ├── uir/                             <── UIR Core 벤치마크 생성 및 실행기
│   ├── uir_external/                    <── 외부 금융/공시 데이터셋 수집 및 고정
│   ├── uir_generalization/              <── 일반화 진단 및 누출 검사기
│   ├── uir_phase3b/ ~ uir_phase3d/      <── Phase 3 평가 러너 및 AI 심사 파이프라인
│   ├── uir_phase4/ ~ uir_phase4f/       <── Phase 4 평가 러너, 고장 주입, 런타임 파이프라인
│   └── uir_slm/                         <── SLM 추론 엔진 연동 하네스
└── uir_security/
    ├── __init__.py
    ├── llm_security/                    <── v2 보안 벤치마크 생성기/평가기
    ├── llm_security_v3/                 <── v3 적응형 공격 및 심사 파이프라인
    ├── llm_security_v3_1/               <── v3.1 불투명 신원 및 오라클 평가기
    └── llm_security_v3_2/               <── v3.2 최종 출판 캠페인 실행기, 적응형 공격 엔진,
                                             Output Guard 유효성 검증기, 독립 감사기
```

---

## 4. 공통 공유 인프라 (Shared Infrastructure)

두 프로젝트 간의 불필요한 코드 중복을 방지하기 위해 다음 컴포넌트들은 루트 레벨에서 공유됩니다.

- **`crates/`**: Rust 기반 UIR 코어 엔진 (`uir-syntax`, `uir-ast`, `uir-eval`, `uir-codegen`). 양쪽 프로젝트 모두에서 컴파일러 및 정형 파서 엔진으로 사용됩니다.
- **`llm_trust/`**: Zero Trust Policy Engine, Capability Gate, Ollama SLM 클라이언트 등 보안/신뢰성 런타임 모듈.
- **`.venv/`**: Ubuntu WSL2(26.04.1) 기반 공통 Python 3.12.13 가상환경.

---

## 5. 파이썬 임포트 및 하위 호환성 (Python Import Compatibility)

`evaluation/` 폴더가 `evaluation/uir_base/` 및 `evaluation/uir_security/`로 세분화되었으나, `evaluation/__init__.py`에서 `__path__` 동적 확장을 제공합니다.

따라서 기존 코드와 신규 코드가 모두 오류 없이 호환됩니다:

```python
# 1. 신규 권장 임포트 스타일 (프로젝트 명시적)
from evaluation.uir_security.llm_security_v3_2.baselines import UirV32SecurityPipeline
from evaluation.uir_base.uir_phase4d.runtime.policy_engine import PolicyEngine

# 2. 레거시 임포트 스타일 (evaluation/__init__.py에 의해 완벽 지원)
from evaluation.llm_security_v3_2.baselines import UirV32SecurityPipeline
from evaluation.uir_phase4d.runtime.policy_engine import PolicyEngine
```

---

## 6. 단위 테스트 및 검증 규칙 (Testing Guidelines)

저장소 루트에서 다음 명령어로 전체 단위 테스트(130개)를 단일 명령으로 검증할 수 있습니다.

```bash
# WSL2 Ubuntu 환경
source .venv/bin/activate
PYTHONPATH=. pytest tests/ -v
```

- **Core 테스트만 수행 시**: `PYTHONPATH=. pytest tests/uir_base/`
- **Security 테스트만 수행 시**: `PYTHONPATH=. pytest tests/uir_security/`
