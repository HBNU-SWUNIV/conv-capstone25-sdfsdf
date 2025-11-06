# 파일명: ocr_utils.py (학번 추출 전용 버전)

import fitz
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
import io

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 학번 패턴: 20으로 시작하는 8자리 숫자
STUDENT_ID_PATTERN = re.compile(r'\b(20\d{6})\b')

def correct_and_validate_student_id(text_chunk):
    """흔한 OCR 오류를 교정하고 유효한 학번인지 검사합니다."""
    corrected_text = text_chunk.upper().replace('O', '0').replace('L', '1').replace('I', '1') \
                               .replace('S', '5').replace('B', '8').replace('Z', '2')
    
    match = STUDENT_ID_PATTERN.search(corrected_text)
    return match.group(1) if match else None

def extract_student_id_from_pdf(pdf_bytes):
    """PDF에서 학번을 OCR로 추출하고 교정하여 반환합니다."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if not doc: return None
        
        page = doc.load_page(0) # 첫 페이지만 검사
        
        # 페이지 상단 30% 영역만 잘라서 처리 (성능 향상)
        rect = fitz.Rect(0, 0, page.rect.width, page.rect.height * 0.3)
        pix = page.get_pixmap(dpi=300, clip=rect)
        
        nparr = np.frombuffer(pix.tobytes(), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        text = pytesseract.image_to_string(Image.fromarray(thresh), lang='kor+eng', config='--psm 6')
        print(f"[디버그] OCR 텍스트: {text.strip()}")
        
        # 숫자와 오류 가능성이 있는 문자로 이루어진 모든 덩어리를 찾음
        potential_chunks = re.findall(r'[\dOISBZLI]{6,}', text)
        for chunk in potential_chunks:
            student_id = correct_and_validate_student_id(chunk)
            if student_id:
                print(f"[디버그] 학번 찾음 (원본: {chunk} -> 교정: {student_id})")
                return student_id
        
        print("[디버그] 유효한 학번을 찾지 못했습니다.")
        return None

    except Exception as e:
        print(f"학번 추출 중 오류: {e}")
        return None