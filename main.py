from typing import List, Optional
from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI(title="Spec Score API")

# ──────────────────────────
# 1) Pydantic 모델 정의
# ──────────────────────────
class University(BaseModel):
    school_name: str
    degree: Optional[str]
    major: Optional[str]
    gpa: Optional[float]
    gpa_max: Optional[float]

class Career(BaseModel):
    company: str
    role: Optional[str]

class Language(BaseModel):
    test: str
    score_or_grade: str

class Activity(BaseModel):
    name: str
    role: Optional[str]
    award: Optional[str]

class SpecV1(BaseModel):
    nickname: str
    final_edu: str
    final_status: str
    desired_job: str
    universities: Optional[List[University]] = []
    careers: Optional[List[Career]] = []
    certificates: Optional[List[str]] = []
    languages: Optional[List[Language]] = []
    activities: Optional[List[Activity]] = []

# ──────────────────────────
# 2) 카테고리별 점수 함수
# ──────────────────────────
def score_education(final_edu: str) -> float:
    mapping = {
        "고등학교": 20,
        "전문학사": 40,
        "학사": 60,
        "석사": 80,
        "박사": 100
    }
    return mapping.get(final_edu, 0.0)

def score_universities(unis: List[University]) -> float:
    if not unis:
        return 0.0
    
    scores = []
    for u in unis:
        # GPA가 있고 gpa_max가 0이 아닌 경우만 계산
        if u.gpa is not None and u.gpa_max is not None and u.gpa_max > 0:
            scores.append((u.gpa / u.gpa_max) * 100)
    
    return sum(scores) / len(scores) if scores else 0.0

def score_careers(careers: List[Career]) -> float:
    if not careers:
        return 0.0
    return min(len(careers) * 20.0, 100.0)

def score_certificates(certs: List[str]) -> float:
    if not certs:
        return 0.0
    return min(len(certs) * 10.0, 100.0)

def score_languages(langs: List[Language]) -> float:
    if not langs:
        return 0.0
    
    total = 0.0
    count = 0
    
    for lang in langs:
        test_upper = lang.test.upper()
        if test_upper == "TOEIC":
            try:
                s = float(lang.score_or_grade)
                if s >= 0 and s <= 990:
                    total += (s / 990.0) * 100.0
                    count += 1
            except ValueError:
                continue
        elif test_upper == "TOEFL":
            try:
                s = float(lang.score_or_grade)
                if s >= 0 and s <= 120:
                    total += (s / 120.0) * 100.0
                    count += 1
            except ValueError:
                continue
        elif test_upper == "IELTS":
            try:
                s = float(lang.score_or_grade)
                if s >= 0 and s <= 9:
                    total += (s / 9.0) * 100.0
                    count += 1
            except ValueError:
                continue
        elif test_upper == "OPIC" or test_upper == "OPIC":
            grade_mapping = {
                "NL": 10.0, "NM": 20.0, "NH": 30.0,
                "IL": 40.0, "IM": 50.0, "IH": 60.0,
                "AL": 80.0, "AM": 90.0, "AH": 100.0
            }
            score = grade_mapping.get(lang.score_or_grade.upper(), 0.0)
            if score > 0:
                total += score
                count += 1
    
    return (total / count) if count else 0.0

def score_activities(acts: List[Activity]) -> float:
    if not acts:
        return 0.0
    
    total = 0.0
    for a in acts:
        total += 10.0
        if a.award:
            total += 10.0
    return min(total, 100.0)

# ──────────────────────────
# 3) 가중치 설정
# ──────────────────────────
WEIGHTS = {
    "education":    0.20,
    "university":   0.20,
    "careers":      0.15,
    "certificates": 0.10,
    "languages":    0.20,
    "activities":   0.15,
}

# ──────────────────────────
# 4) V1 엔드포인트
# ──────────────────────────
@app.post("/spec/v1/post")
def spec_v1_post(spec: SpecV1):
    # 각 카테고리 점수 계산
    edu  = score_education(spec.final_edu)
    uni  = score_universities(spec.universities)
    car  = score_careers(spec.careers)
    cert = score_certificates(spec.certificates)
    lang = score_languages(spec.languages)
    act  = score_activities(spec.activities)
    
    # 디버깅을 위한 개별 점수 출력 (실제 API에서는 제거 가능)
    scores = {
        "education": edu,
        "university": uni,
        "careers": car,
        "certificates": cert,
        "languages": lang,
        "activities": act
    }
    
    # 가중치 합산 (0~100)
    weighted_total = (
        edu  * WEIGHTS["education"] +
        uni  * WEIGHTS["university"] +
        car  * WEIGHTS["careers"] +
        cert * WEIGHTS["certificates"] +
        lang * WEIGHTS["languages"] +
        act  * WEIGHTS["activities"]
    )
    
    # 반올림
    total = round(weighted_total, 2)
    
    # 최소 20점, 최대 100점으로 보정
    if total < 20.0:
        total = 20.0
    elif total > 100.0:
        total = 100.0
    
    return {
        "nickname": spec.nickname,
        "totalScore": total,
        # "categoryScores": scores  # 필요시 개별 점수 표시 (디버깅용)
    }

# ──────────────────────────
# 5) 서버 실행
# ──────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)