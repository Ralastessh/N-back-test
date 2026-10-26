Jaeggi et al. (2008), "Improving Fluid Intelligence with Training on Working Memory" 논문을 PsychoPy로 재현하는 프로젝트를 만들어 줘.

**1. 개발 환경**
- macOS, Python, PsychoPy Coder
- 각 실험은 독립적으로 실행 가능해야 함
- 전체 프로젝트를 모듈화하고 유지보수하기 쉽게 설계할 것

**2. 프로젝트 구조**
```text
Jaeggi_2008_Replication/
├── main.py
├── config.py
├── tasks/
│   ├── dual_nback.py
│   ├── digit_span.py
│   └── reading_span.py
├── stimuli/
│   ├── visual.py
│   ├── auditory.py
│   └── audio/
├── utils/
│   ├── sequence.py
│   ├── scoring.py
│   └── data_logger.py
├── tests/
└── data/
```

**3. Dual N-back 구현**
논문의 Materials and Methods에 명시된 실험 조건을 최대한 정확하게 재현해 줘.

- 시각 자극: 8개 공간 위치에 사각형 표시
- 청각 자극: 8개 자음 오디오
- 자극 제시 500ms, ISI 2,500ms
- 시각 반응 A 키, 청각 반응 L 키
- 블록당 20+n Trial
- 세션당 20블록
- 블록마다 시각 Target 6개, 청각 Target 6개, 동시 Target 2개
- 수행 성과에 따른 Adaptive N-back 알고리즘
- 반응시간, 정답, 오답, 난이도 등 상세 기록

시각 자극과 청각 자극은 별도 모듈로 분리하되, 정확한 동기화를 위해 공통 타이밍은 dual_nback.py에서 관리해 줘.

**4. Digit Span 및 Reading Span**
- 두 검사 모두 Pretest/Posttest에서 사용 가능하도록 구현
- Digit Span은 Forward/Backward 방식 지원
- Reading Span은 문장 이해와 단어 회상 과제 구현
- 검사별 정확도와 수행 결과 기록

**5. 연구 재현 정확도**
논문에 명시된 조건과 명시되지 않은 조건을 반드시 구분해 줘. 임의로 결정한 설정은 재현 가정이라고 표시하고, config.py에서 수정 가능하게 해 줘.

**6. 검증 및 산출물**
- 전체 Python 소스코드
- 실행에 필요한 오디오 및 자극 자료
- README.md
- requirements.txt
- 핵심 알고리즘에 대한 단위 테스트
- macOS PsychoPy 설치 및 실행 방법
- 논문 조건과 실제 구현을 비교한 체크리스트

코드만 제시하지 말고 실제 프로젝트 파일을 생성해 줘. 먼저 Dual N-back을 구현하고 검증한 다음 Digit Span과 Reading Span을 추가해 줘. 가능한 테스트를 수행하고, 직접 확인하지 못한 기능은 명시해 줘.