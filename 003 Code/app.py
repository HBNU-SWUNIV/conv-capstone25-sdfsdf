# 파일명: 1_🎓_AI_학업_조교_챗봇.py (최종 간결 버전)

import streamlit as st
import time
from collections import defaultdict
import pandas as pd

# --- 필요한 모듈 임포트 (RAG/OCR 관련 모두 제거) ---
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from db_utils import authenticate_student, get_student_enrollments
from academic_advisor import analyze_graduation_progress, suggest_courses

# --- 설정 ---
LLM_MODEL = "gemma3:12b"

# --- Streamlit 캐싱: LLM 모델 로딩 ---
@st.cache_resource
def load_llm():
    """LLM 모델을 로드하고 캐시에 저장합니다."""
    try:
        llm = Ollama(model=LLM_MODEL)
        llm.invoke("test") # 간단한 호출로 연결 테스트
        print("LLM 모델 로딩 성공.")
        return llm
    except Exception as e:
        st.error(f"LLM 모델 로딩 중 오류 발생: {e}")
        st.info("Ollama 서버가 실행 중인지, 모델이 다운로드되었는지 확인해주세요.")
        return None

# --- 분석 결과를 LLM 프롬프트용 텍스트로 변환하는 함수 ---
def format_report_for_llm(student_name, analysis, suggestions):
    """분석 및 추천 결과를 LLM이 이해하기 좋은 텍스트로 변환합니다."""
    report = f"--- {student_name}님 학업 분석 보고서 ---\n\n"
    summary = analysis['summary']
    report += f"**[졸업까지 남은 학점]**\n- 총 필요 학점: {summary['total_required']} / 현재 이수 학점: {summary['total_completed']} (남은 학점: {summary['total_missing']})\n"
    
    missing_areas = [area for area in analysis['by_classification'] if area['missing'] > 0]
    if not missing_areas:
        report += "\n**[영역별 이수 현황]**\n- 모든 영역별 최소 학점을 충족했습니다.\n"
    else:
        report += "\n**[부족한 영역별 학점]**\n"
        for area in missing_areas:
            report += f"- {area['classification']}: {area['missing']}학점 부족\n"

    if analysis.get('detailed_analysis'):
        report += "\n**[세부 졸업요건 충족 현황]**\n"
        for detail in analysis['detailed_analysis']:
            status = "✅ 충족" if detail['is_satisfied'] else "❌ 미충족"
            report += f"- **{detail['name']}**: {status}\n"
            if not detail['is_satisfied']:
                report += f"  - 내용: {detail['description']}\n"
                if detail.get('missing_items'):
                    report += f"  - **미이수 과목:** {', '.join(detail['missing_items'])}\n"
                if detail.get('missing_areas'):
                    report += f"  - **남은 영역:** {', '.join(detail['missing_areas'])}\n"
                if detail.get('details'):
                     report += f"  - 현황: {detail['details']}\n"

    if analysis['missing_required_courses']:
        report += "\n**[아직 듣지 않은 필수 과목 목록 (전공/대학특화)]**\n"
        for course in analysis['missing_required_courses']:
            report += f"- {course}\n"
    
    report += "\n--- 다음 학기 추천 과목 목록 (실제 개설 과목 기반) ---\n"
    if not suggestions:
        report += "현재 추천할 수 있는 개설 과목이 없습니다.\n"
    else:
        for category, courses in suggestions.items():
            report += f"\n**[{category}]**\n"
            if not courses:
                report += "- 추천할 개설 과목을 찾지 못했습니다.\n"
            for course in courses:
                credits = f" ({int(course['credits'])}학점)" if course.get('credits') is not None else ""
                report += f"- {course['course_name']}{credits}\n"
                
    return report

# --- 메인 애플리케이션 ---
def main():
    st.set_page_config(page_title="AI 학업 조교 챗봇", page_icon="🎓", layout="wide")
    st.title("🎓 AI 학업 조교 챗봇")

    llm = load_llm()

    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.clear()
        st.session_state.messages = []
        st.session_state.authenticated = False
        st.session_state.student_info = None

    # --- 1. 학생 인증 UI ---
    if not st.session_state.authenticated:
        st.subheader("학생 인증")
        with st.form("auth_form"):
            student_id = st.text_input("학번", value="20231081")
            student_name = st.text_input("이름", value="한재웅")
            submitted = st.form_submit_button("인증하기")

            if submitted:
                if not llm:
                    st.error("챗봇 시스템이 아직 준비되지 않았습니다. Ollama 서버를 확인해주세요.")
                else:
                    student_info = authenticate_student(student_id, student_name)
                    if student_info:
                        st.session_state.authenticated = True
                        st.session_state.student_info = student_info
                        st.session_state.messages.append({"role": "assistant", "content": f"**{student_name}**님, 반갑습니다! 무엇을 도와드릴까요?"})
                        st.rerun()
                    else:
                        st.error("학번 또는 이름이 일치하지 않습니다.")
    else:
        # --- 2. 챗봇 UI ---
        st.sidebar.header(f"👋 {st.session_state.student_info['student_name']}님")
        st.sidebar.markdown(f"**학번:** {st.session_state.student_info['student_id']}")
        st.sidebar.markdown(f"**학과:** {st.session_state.student_info['department_major']}")
        if st.sidebar.button("로그아웃", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

        # 이전 대화 내용 표시
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 사용자 입력 처리
        if prompt := st.chat_input("질문을 입력하세요..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                response_container = st.empty()
                
                # RAG 기능이 없으므로, 모든 질문을 졸업요건 분석으로 처리
                with st.spinner("학업 현황 분석 및 답변을 생성 중입니다..."):
                    analysis = analyze_graduation_progress(st.session_state.student_info)
                    suggestions = suggest_courses(st.session_state.student_info, analysis)
                    report_for_llm = format_report_for_llm(st.session_state.student_info['student_name'], analysis, suggestions)

                    advisor_prompt = ChatPromptTemplate.from_template(
                        """당신은 대학교의 친절하고 유능한 AI 학업 조교입니다.
                        아래에 주어진 학생의 '학업 분석 및 추천 리포트'를 바탕으로 학생의 질문에 답변해주세요.
                        먼저, 학생의 현재 학점 현황(총학점, 부족한 영역)을 요약해서 설명해주세요.
                        그 다음, 리포트에 있는 '세부 졸업요건 충족 현황'을 바탕으로 학생이 놓치고 있는 중요한 규칙이 있다면 강조해서 설명해주세요.
                        마지막으로 '다음 학기 추천 과목 목록'을 카테고리별로 명확하게 제시하며, 왜 이 과목들을 들어야 하는지 간단히 설명하고 격려하며 대화를 마무리해주세요.
                        
                        --- 학업 분석 및 추천 리포트 ---
                        {report}
                        --------------------------------
                        
                        이제 위 리포트를 바탕으로 학생에게 자연스럽게 설명해주세요."""
                    )
                    advisor_chain = advisor_prompt | llm | StrOutputParser()
                    stream = advisor_chain.stream({"report": report_for_llm})
                
                full_response = "".join(list(stream))
                response_container.markdown(full_response)
                
            st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
# python rag_setup.py
# streamlit run app.py        