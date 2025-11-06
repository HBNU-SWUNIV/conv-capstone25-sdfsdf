# 🤖 로컬 AI 학업 조교 챗봇  
_Local AI Academic Advisor Chatbot_

**데이터 기반 개인 맞춤형 학업 관리 시스템**  
모든 연산이 로컬에서 이루어져 개인정보 유출 걱정 없이, 졸업 요건 분석부터 과목 추천, 학사 정보 응답까지 한 번에!

---

## 🌟 프로젝트 소개 (Introduction)
학생들이 겪는 학업 관리의 불편함을 해소하기 위해 개발된 로컬 AI 기반 학업 조교 챗봇입니다.  
- **졸업 요건 자동 분석**  
- **개인 수강 이력 기반 과목 추천**  
- **실시간 학사 정보 응답**  
- **로컬 PC 환경에서 동작하여 강력한 개인정보 보호**  

> “정확하고 똑똑한 학업 파트너, AI 조교 챗봇”

---

## ✨ 주요 기능 (Features)

| 기능                     | 설명                                                                                       | 핵심 기술         |
|------------------------|------------------------------------------------------------------------------------------|----------------|
| 개인 맞춤형 추천         | 학생별 수강 내역을 분석하여 졸업까지 부족한 학점과 과목을 자동 계산하고<br>다음 학기 추천 과목 안내 | Python, MySQL  |
| 빠른 정보 제공           | “기계학습 과목이 뭐예요?” 등 학사 관련 질문에 대해<br>미리 구축된 지식 베이스로 즉시 답변            | RAG, LangChain |
| 행정 부담 감소           | 반복적인 학사 문의에 챗봇이 자동 응답하여<br>학과 조교·교직원 업무 부담 경감                          | LLM, Streamlit |
| 강력한 개인정보 보호      | 모든 분석·질의응답이 로컬 Ollama LLM으로 처리되어<br>데이터 외부 유출 방지                        | Ollama, Local LLM |

---

## 🚀 사용자 이용 시나리오 (User Scenario)

1. **학생 인증**  
   웹 UI에 학번·이름 입력 → 간편 인증  
2. **맞춤형 수강 추천**  
   > “졸업하려면 뭐 들어야 해?”  
   챗봇이 졸업 요건 충족 현황과 추천 과목 목록 안내  
3. **대화형 정보 응답**  
   > “소프트웨어원리 과목에 대해 알려줘”  
   RAG 파이프라인으로 정확한 규정·과목 정보 제공  
4. **데모 동작 예시**  
   <img width="740" alt="image" src="https://github.com/user-attachments/assets/074b2358-2849-40f8-aad4-e68bf94cad36" />

   <img width="739" alt="image" src="https://github.com/user-attachments/assets/11e6e0f2-d572-46c2-aa2f-65936a858eea" />

   <img width="746" alt="image" src="https://github.com/user-attachments/assets/0108addf-52a5-46d9-9cd0-04176fe7788d" />

   <img width="746" alt="image" src="https://github.com/user-attachments/assets/2cb5dd8a-12df-4d80-97d3-57f60a334d15" />

   <img width="743" alt="image" src="https://github.com/user-attachments/assets/22ea6ebf-0acb-47dc-8e59-803dc5ab1e3f" />

   <img width="748" alt="image" src="https://github.com/user-attachments/assets/ca6a666c-7748-43d8-955f-8857571b2470" />



---

## 🛠️ 시스템 구성 (System Architecture)

<img width="264" alt="image" src="https://github.com/user-attachments/assets/77322c1b-765f-4dfd-b5c3-b2bc622ea938" />




1. **Streamlit (Web UI)**  
   - 사용자 입력(학번·이름, 질의)  
2. **졸업 조건 분석 (Rule-Based Engine)**  
   - `requirements_rule.py` 기반 4단계 검증  
     1. 총 이수 학점 계산  
     2. 영역별 학점 분석  
     3. 필수 과목 이수 여부 확인  
     4. 세부 규칙 검증  
3. **RAG 기반 질의응답**  
   1. Multi-Query 생성  
   2. FAISS로 문서 검색 (최대 7개)  
   3. Cohere Rerank로 상위 3개 압축  
   4. LLM 답변 생성 (근거 기반)  
4. **결과 출력**  
   - Streamlit 챗봇 인터페이스로 실시간 제공  

---

## ⚙️ 서비스 구현 방법 (Implementation Details)

1. **규칙 기반 분석 (신뢰도 확보)**  
   - 100% 코드 처리: 졸업 요건 판단  
   - 단계별 검증 후 `분석 리포트` · `추천 과목 목록` 생성  

2. **RAG 기반 질의응답 (환각 방지)**  
   - 질문 확장 → 문서 검색 → 재순위 → 근거 기반 생성  

3. **로컬 AI 연동**  
   - Ollama Local LLM으로 모든 AI 연산 처리  
   - 외부 서버 불필요, 강력한 개인정보 보호  

---

## 🏁 결론 및 기대효과 (Conclusion & Impact)

- 학생들은 **간편하게 졸업 요건**을 확인하고  
- **맞춤형 과목 추천**으로 학업 계획을 최적화하며  
- **행정 문의 자동화**로 조교·교직원의 업무 부담을 대폭 경감합니다.  
- **로컬 환경 처리**로 개인정보 유출 없이 안심하고 사용 가능  

> **정확하고 똑똑한 학업 파트너, Local AI Academic Advisor Chatbot**

---
