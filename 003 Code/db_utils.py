# 파일명: db_utils.py (최종 수정본)

import mysql.connector

# --- DB 설정 ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'hanjaewoong1',
    'database': 'subject_list',
    'port': 3306
}

def get_db_connection():
    """DB 커넥션을 생성하고 반환합니다."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"DB 연결 오류: {err}")
        return None

# ★★★ 원래의 간단한 인증 함수만 사용 ★★★
def authenticate_student(student_id, student_name):
    """학생 ID와 이름으로 학생 정보를 조회하여 인증합니다."""
    conn = get_db_connection()
    if not conn: return None
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM students WHERE student_id = %s AND student_name = %s"
        cursor.execute(query, (student_id, student_name))
        student_info = cursor.fetchone()
        return student_info
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_student_enrollments(student_id):
    """특정 학생의 전체 수강 내역을 조회합니다 (P/F 포함, F/W 제외)."""
    conn = get_db_connection()
    if not conn: return []
        
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM enrollments WHERE student_id = %s AND grade NOT IN ('F', 'W', 'NP')"
        cursor.execute(query, (student_id,))
        enrollments = cursor.fetchall()
        return enrollments
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def get_available_courses(taken_course_names, target_departments=None):
    """수강 가능한 과목 목록을 조회합니다."""
    conn = get_db_connection()
    if not conn: return []

    try:
        cursor = conn.cursor(dictionary=True)
        
        base_query = "SELECT course_name, course_classification, credits, lecture_number, department FROM courses WHERE is_폐강 = FALSE"
        params = []

        if target_departments:
            dept_placeholders = ','.join(['%s'] * len(target_departments))
            base_query += f" AND department IN ({dept_placeholders})"
            params.extend(target_departments)

        if taken_course_names:
            taken_placeholders = ','.join(['%s'] * len(taken_course_names))
            base_query += f" AND course_name NOT IN ({taken_placeholders})"
            params.extend(list(taken_course_names))
            
        cursor.execute(base_query, tuple(params))
        courses = cursor.fetchall()
        return courses
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()