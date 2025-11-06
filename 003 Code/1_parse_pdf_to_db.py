# 파일명: 1_parse_pdf_to_db.py

import PyPDF2
import mysql.connector
import re

# ---!!! 중요: 자신의 환경에 맞게 수정하세요 !!!---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hanjaewoong1', # 본인의 MySQL 비밀번호로 변경
    'database': 'subject_list',  # 사용할 데이터베이스 이름
    'port': 3306  
}
PDF_PATH = r'C:\Users\user\Desktop\과목.pdf'  # PDF 파일의 절대 경로로 변경
# ---------------------------------------------------

def extract_text_from_pdf(pdf_path):
    """PDF에서 페이지별 텍스트를 추출합니다."""
    text_by_page = []
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            print(f"PDF 총 페이지 수: {len(reader.pages)}")
            for page in reader.pages:
                text_by_page.append(page.extract_text())
        return text_by_page
    except FileNotFoundError:
        print(f"오류: PDF 파일을 찾을 수 없습니다. 경로를 확인하세요: {pdf_path}")
        return []
    except Exception as e:
        print(f"PDF 텍스트 추출 중 오류 발생: {e}")
        return []

def parse_course_data(text_pages):
    """추출된 텍스트에서 정규식을 이용해 과목 정보를 파싱합니다."""
    parsed_courses = []
    # PDF 텍스트 구조에 맞는 정규식 (공백, 줄바꿈 등에 유연하게 대처)
    course_pattern = re.compile(
        r"^(?P<process_type>일반|교직|계약|학석사통합|학석박사통합|계약\(DSC\))\s*"
        r"(?P<폐강여부>폐강)?\s*"
        r"(?P<course_code_full>[A-Z0-9]+)\s+"
        r"(?P<lecture_number>\d{10})\s+"
        r"(?P<course_name>.+?)\s+"
        r"(?P<department>.+?)\s+"
        r"(?P<contact_info>\S+)$",
        re.MULTILINE
    )

    for page_text in text_pages:
        if not page_text:
            continue
        
        for match in course_pattern.finditer(page_text):
            data = match.groupdict()
            
            # 학수번호와 분반 파싱
            full_code = data['course_code_full']
            # 학수번호 뒤에 붙은 숫자(최대 3자리)를 분반으로 가정
            match_suffix = re.search(r'(\d{1,3})$', full_code)
            if match_suffix and len(full_code) > len(match_suffix.group(1)):
                class_number = match_suffix.group(1)
                course_code = full_code[:-len(class_number)]
            else:
                class_number = ""
                course_code = full_code

            parsed_courses.append({
                'process_type': data['process_type'].strip(),
                'course_code': course_code.strip(),
                'class_number': class_number.strip(),
                'lecture_number': data['lecture_number'].strip(),
                'course_name': data['course_name'].strip(),
                'department': data['department'].strip(),
                'contact_info': data['contact_info'].strip(),
                'is_폐강': bool(data.get('폐강여부'))
            })
    print(f"정규식 매칭 성공: 총 {len(parsed_courses)}개 과목 발견")
    return parsed_courses

def setup_database_and_insert_courses(course_list):
    """DB에 연결하여 테이블을 생성하고, 과목 리스트를 삽입/업데이트합니다."""
    if not course_list:
        print("DB에 삽입할 데이터가 없습니다.")
        return

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("`courses` 테이블 생성 또는 확인 중...")
        # `courses` 테이블 생성 (이미 있으면 넘어감)
        # 챗봇에 필요한 최소한의 컬럼만 정의
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                lecture_number VARCHAR(20) UNIQUE NOT NULL,
                course_name VARCHAR(255) NOT NULL,
                course_code VARCHAR(30),
                class_number VARCHAR(10),
                department VARCHAR(100),
                process_type VARCHAR(20),
                is_폐강 BOOLEAN DEFAULT FALSE,
                credits FLOAT,
                course_classification VARCHAR(20)
            );
        """)

        # INSERT ... ON DUPLICATE KEY UPDATE 쿼리
        sql = """
        INSERT INTO courses (lecture_number, course_name, course_code, class_number, department, process_type, is_폐강)
        VALUES (%(lecture_number)s, %(course_name)s, %(course_code)s, %(class_number)s, %(department)s, %(process_type)s, %(is_폐강)s)
        ON DUPLICATE KEY UPDATE
            course_name = VALUES(course_name),
            course_code = VALUES(course_code),
            class_number = VALUES(class_number),
            department = VALUES(department),
            process_type = VALUES(process_type),
            is_폐강 = VALUES(is_폐강);
        """
        
        for course in course_list:
            cursor.execute(sql, course)
        
        conn.commit()
        print(f"데이터 처리 완료: 총 {cursor.rowcount}개 행이 영향을 받았습니다.")
        
    except mysql.connector.Error as err:
        print(f"MySQL 오류: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    print("--- 1. PDF에서 텍스트 추출 시작 ---")
    all_pages_text = extract_text_from_pdf(PDF_PATH)
    
    if all_pages_text:
        print("\n--- 2. 텍스트에서 과목 정보 파싱 시작 ---")
        parsed_courses = parse_course_data(all_pages_text)
        
        if parsed_courses:
            print("\n--- 3. MySQL에 데이터 삽입 시작 ---")
            setup_database_and_insert_courses(parsed_courses)
            print("\n--- 모든 작업 완료 ---")