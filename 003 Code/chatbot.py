# 파일명: chatbot.py (RAG 기능 통합 버전)

import os
from langchain_community.llms import Ollama
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from db_utils import authenticate_student
from academic_advisor import analyze_graduation_progress, suggest_courses

# --- 설정 (자신의 환경에 맞게 수정) ---
LLM_MODEL = "gemma3:12b" 
EMBEDDING_MODEL = "nomic-embed-text" # 임베딩에 사용할 모델
FAISS_INDEX_PATH = "faiss_course_index"  # RAG 인덱스가 저장된 폴더
# ----------------------------------------

def format_report_for_llm(student_name, analysis, suggestions):
    # 이 함수는 이전과 동일합니다.
    report = f"--- {student_name}님 학업 분석 보고서 ---\n\n"
    summary = analysis['summary']
    report += f"**[졸업까지 남은 학점]**\n- 총 필요 학점: {summary['total_required']} / 현재 이수 학점: {summary['total_completed']} (남은 학점: {summary['total_missing']})\n\n"
    report += "**[영역별 부족 학점]** (부족한 부분만 표시)\n"
    missing_areas = [area for area in analysis['by_classification'] if area['missing'] > 0]
    if not missing_areas:
        report += "- 모든 영역별 최소 학점을 충족했습니다. 훌륭해요!\n"
    else:
        for area in missing_areas:
            report += f"- {area['classification']}: {area['missing']}학점 부족\n"
    if analysis['missing_required_courses']:
        report += "\n**[아직 듣지 않은 필수 과목]**\n"
        for course in analysis['missing_required_courses']:
            report += f"- {course}\n"
    report += "\n--- 다음 학기 추천 과목 목록 (실제 개설 과목 기반) ---\n"
    if not suggestions:
        report += "현재 기준으로 추천할 수 있는 과목이 없습니다.\n"
    else:
        for category, courses in suggestions.items():
            report += f"\n**[{category}]**\n"
            if not courses:
                report += "- 추천할 개설 과목을 찾지 못했습니다.\n"
            for course in courses:
                credits = f" ({int(course['credits'])}학점)" if course.get('credits') is not None else ""
                report += f"- {course['course_name']}{credits}\n"
    return report

def run_chatbot():
    print("="*50)
    print("AI 학업 조교 챗봇 (RAG 탑재 버전)에 오신 것을 환영합니다!")
    print("="*50)
    
    # --- LLM 및 RAG 구성 요소 로딩 ---
    try:
        llm = Ollama(model=LLM_MODEL)
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        print(f"✅ LLM ({LLM_MODEL}) 및 임베딩 모델 ({EMBEDDING_MODEL})에 성공적으로 연결되었습니다.")
    except Exception as e:
        print(f"❌ LLM 또는 임베딩 모델 연결 실패: {e}\nOllama가 실행 중인지, 모델들이 다운로드되었는지 확인해주세요.")
        return

    if not os.path.exists(FAISS_INDEX_PATH):
        print(f"❌ RAG 인덱스 파일을 찾을 수 없습니다. '{FAISS_INDEX_PATH}'")
        print("먼저 `rag_setup.py` 스크립트를 실행하여 인덱스를 생성해주세요.")
        return
        
    print("RAG 인덱스 로딩 중...")
    vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = vector_store.as_retriever()
    print("✅ RAG 인덱스 로딩 완료.")
    # ---------------------------------

    student_info = None
    while not student_info:
        student_id = input("학번을 입력하세요: ")
        student_name = input("이름을 입력하세요: ")
        student_info = authenticate_student(student_id, student_name)
        if student_info:
            print(f"\n✅ {student_name}님, 반갑습니다! 무엇을 도와드릴까요?")
            print("   - 졸업 요건 분석: '졸업', '학점', '추천' 등 입력")
            print("   - 특정 과목 정보: '과목명'에 대해 알려줘 등 입력")
        else:
            print("\n❌ 학생 정보가 일치하지 않습니다. 다시 시도해주세요.")

    # RAG 체인 생성
    rag_prompt = ChatPromptTemplate.from_template(
        """당신은 과목 정보를 상세히 설명해주는 AI 조교입니다.
        아래에 주어진 '참고 자료'를 바탕으로 사용자의 '질문'에 대해 아는 만큼만 상세하게 답변해주세요.
        만약 참고 자료에 없는 내용이라면, "해당 과목에 대한 상세 정보를 PDF에서 찾을 수 없습니다."라고 솔직하게 답변하세요.

        [참고 자료]
        {context}

        [질문]
        {question}
        """
    )
    rag_chain = {"context": retriever, "question": RunnablePassthrough()} | rag_prompt | llm | StrOutputParser()
    
    while True:
        query = input(f"\n[{student_info['student_name']}님] >> ")
        if query.lower() in ['exit', 'quit', '종료', '그만']:
            print("\n[AI 조교] 챗봇을 종료합니다. 언제든 다시 찾아주세요!")
            break

        # --- 질문 유형에 따라 다른 기능 호출 (라우팅) ---
        if any(keyword in query for keyword in ['졸업', '요건', '학점', '추천']):
            # 1. 졸업 요건 분석 기능
            print("\n[AI 조교] ⏳ 학업 현황을 분석하고 맞춤형 조언을 생성 중입니다...")
            analysis = analyze_graduation_progress(student_info)
            suggestions = suggest_courses(student_info, analysis)
            report_for_llm = format_report_for_llm(student_info['student_name'], analysis, suggestions)
            
            # 졸업 요건 분석용 프롬프트는 기존과 동일
            advisor_prompt = ChatPromptTemplate.from_template(...) # 이전 답변의 프롬프트 복사
            advisor_chain = advisor_prompt | llm | StrOutputParser()
            
            print("\n[AI 조교] ", end="")
            for chunk in advisor_chain.stream({"report": report_for_llm}):
                print(chunk, end="", flush=True)
            print()
            
        else:
            # 2. RAG를 이용한 과목 정보 검색 기능 (기본값)
            print("\n[AI 조교] ⏳ 과목 정보를 PDF에서 검색 중입니다...")
            print("\n[AI 조교] ", end="")
            for chunk in rag_chain.stream(query):
                print(chunk, end="", flush=True)
            print()

if __name__ == '__main__':
    run_chatbot()