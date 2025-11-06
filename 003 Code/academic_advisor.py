# 파일명: academic_advisor.py (DB 조회 최종 버전)

from collections import defaultdict
from requirements_rule import GRADUATION_REQUIREMENTS
from db_utils import get_student_enrollments, get_available_courses

def analyze_graduation_progress(student_info):
    """학생의 졸업 요건 충족 현황을 분석합니다. (DB 조회 기반)"""
    department = student_info['department_major']
    if department not in GRADUATION_REQUIREMENTS:
        return {"error": f"'{department}'의 졸업 요건 정보가 정의되지 않았습니다."}

    requirements = GRADUATION_REQUIREMENTS[department]
    enrollments = get_student_enrollments(student_info['student_id'])
    
    taken_courses_names_normalized = {e['course_name'].replace(" ", "") for e in enrollments}
    taken_courses_names = {e['course_name'] for e in enrollments}
    
    completed_credits_by_classification = defaultdict(int)
    total_completed_credits = 0

    for e in enrollments:
        if e.get('credits') and e.get('grade') not in ['F', 'W', 'NP']:
            total_completed_credits += e['credits']
            if e.get('course_classification'):
                completed_credits_by_classification[e['course_classification']] += e['credits']
    
    analysis = {
        'summary': {
            'total_required': requirements['total_credits'],
            'total_completed': int(total_completed_credits),
            'total_missing': max(0, requirements['total_credits'] - total_completed_credits)
        },
        'by_classification': [],
        'missing_required_courses': [],
        'detailed_analysis': [] 
    }

    for classification, required in requirements['classification_credits'].items():
        completed = completed_credits_by_classification[classification]
        analysis['by_classification'].append({
            'classification': classification, 'required': required,
            'completed': int(completed), 'missing': max(0, required - completed)
        })

    for required_course in requirements.get('required_courses', []):
        if required_course.replace(" ", "") not in taken_courses_names_normalized:
            analysis['missing_required_courses'].append(required_course)
    
    if 'detailed_requirements' in requirements:
        for req_name, req_details in requirements['detailed_requirements'].items():
            rule_type = req_details.get('type')
            result = {'name': req_name, 'description': req_details['description'], 'is_satisfied': False}

            if rule_type == 'credit_sum':
                sum_credits = sum(completed_credits_by_classification.get(c, 0) for c in req_details['classifications'])
                req_credits = req_details['required_credits']
                result['is_satisfied'] = sum_credits >= req_credits
                result['details'] = f"필요: {req_credits}학점, 현재: {sum_credits}학점"

            elif rule_type == 'take_all':
                missing = [c for c in req_details['courses'] if c.replace(" ", "") not in taken_courses_names_normalized]
                result['is_satisfied'] = not missing
                if missing: result['missing_items'] = missing

            elif rule_type == 'take_one_or_more':
                completed = any(c.replace(" ", "") in taken_courses_names_normalized for c in req_details['courses'])
                result['is_satisfied'] = completed
                if not completed: result['details'] = "아직 이수하지 않았습니다."

            elif rule_type == 'area_based':
                all_area_courses = {c.replace(" ", "") for courses in req_details['areas'].values() for c in courses}
                taken_in_category = taken_courses_names_normalized.intersection(all_area_courses)
                completed_areas = {area for area, courses in req_details['areas'].items() if not {c.replace(" ", "") for c in courses}.isdisjoint(taken_in_category)}
                num_completed = len(completed_areas)
                num_required = req_details['num_areas_required']
                result['is_satisfied'] = num_completed >= num_required
                if not result['is_satisfied']:
                    result['missing_areas'] = list(set(req_details['areas'].keys()) - completed_areas)

            analysis['detailed_analysis'].append(result)
            
    return analysis

def suggest_courses(student_info, analysis):
    """분석 결과를 바탕으로 courses 테이블을 조회하여 수강할 과목을 추천합니다."""
    if "error" in analysis: return {}

    student_department = student_info['department_major']
    enrollments = get_student_enrollments(student_info['student_id'])
    taken_course_names = {e['course_name'] for e in enrollments}
    
    suggestions = defaultdict(list)
    recommended_courses_set = set()

    available_major_courses = get_available_courses(taken_course_names, target_departments=[student_department])
    available_liberal_arts_courses = get_available_courses(taken_course_names, target_departments=None) 
    
    combined_courses = available_major_courses + available_liberal_arts_courses
    unique_courses = {course['lecture_number']: course for course in combined_courses}
    all_available_courses = list(unique_courses.values())

    if analysis.get('detailed_analysis'):
        requirements = GRADUATION_REQUIREMENTS.get(student_department, {})
        all_detailed_reqs = requirements.get('detailed_requirements', {})
        for detail in analysis['detailed_analysis']:
            if detail.get('is_satisfied'): continue
            rule_name = detail['name']
            rule_details = all_detailed_reqs.get(rule_name, {})
            if not rule_details: continue
            courses_for_rule = []
            category_name = f"필수 이수 필요: {rule_name}"
            if detail.get('missing_items'):
                for missing_course_name in detail['missing_items']:
                    for course in all_available_courses:
                        if course['course_name'].replace(" ", "") == missing_course_name.replace(" ", "") and course['course_name'] not in recommended_courses_set:
                            courses_for_rule.append(course)
            elif rule_details.get('type') == 'take_one_or_more':
                rule_courses = rule_details.get('courses', [])
                courses_for_rule = [c for c in all_available_courses if c['course_name'] in rule_courses and c['course_name'] not in recommended_courses_set]
            elif detail.get('missing_areas'):
                areas_to_check = rule_details.get('areas', {})
                for missing_area in detail['missing_areas']:
                    category_name_area = f"필수 영역: {missing_area}"
                    courses_in_area = areas_to_check.get(missing_area, [])
                    recommended_for_area = [c for c in all_available_courses if c['course_name'] in courses_in_area and c['course_name'] not in recommended_courses_set]
                    if recommended_for_area:
                        suggestions[category_name_area].extend(recommended_for_area[:2])
                        for c in recommended_for_area[:2]: recommended_courses_set.add(c['course_name'])
                continue
            if courses_for_rule:
                suggestions[category_name].extend(courses_for_rule[:2])
                for c in courses_for_rule[:2]: recommended_courses_set.add(c['course_name'])

    for required_course_name in analysis['missing_required_courses']:
        if required_course_name in recommended_courses_set: continue
        for course in all_available_courses:
            if course['course_name'] == required_course_name:
                suggestions['꼭 들어야 하는 필수 과목 (전공/특화)'].append(course)
                recommended_courses_set.add(required_course_name)
                break
    
    sorted_missing_areas = sorted(analysis['by_classification'], key=lambda x: x['missing'], reverse=True)
    for area in sorted_missing_areas:
        if area['missing'] <= 0: continue
        category_name = f"{area['classification']} 학점 보충 추천"
        source_for_search = []
        if area['classification'] in ['전선', '심선']:
             source_for_search = available_major_courses
        elif area['classification'] in ['교필', '교선', '일선']:
             source_for_search = available_liberal_arts_courses
        courses_to_recommend = [c for c in source_for_search if c.get('course_classification') == area['classification'] and c['course_name'] not in recommended_courses_set]
        if courses_to_recommend:
            num_to_recommend = min(len(courses_to_recommend), 2)
            recommended_for_area = courses_to_recommend[:num_to_recommend]
            suggestions[category_name].extend(recommended_for_area)
            for rec_course in recommended_for_area: recommended_courses_set.add(rec_course['course_name'])
                
    return suggestions

# streamlit run app.py