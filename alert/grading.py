"""예상 인파와 등급 계산 (spec §6). 기준값은 운영 후 보정."""
GRADES = ["S", "A", "B", "C"]  # 높은 순
THRESHOLDS = [("S", 30000), ("A", 10000), ("B", 3000)]


def crowd_per_day(capacity, fill_rate):
    return int(round(capacity * fill_rate))


def base_grade(crowd, weight=1.0):
    adjusted = crowd * weight
    for grade, minimum in THRESHOLDS:
        if adjusted >= minimum:
            return grade
    return "C"


def final_grade(base, adjust):
    """Claude의 정성 판단으로 최대 한 단계 조정 (S/C 경계에서 멈춤)."""
    i = GRADES.index(base) - adjust
    return GRADES[min(max(i, 0), len(GRADES) - 1)]


def rank(grade):
    """비교용: 높을수록 큰 값."""
    return len(GRADES) - GRADES.index(grade)
