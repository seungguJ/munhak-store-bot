from alert.grading import base_grade, crowd_per_day, final_grade


def test_crowd_per_day_rounds():
    assert crowd_per_day(49000, 1.0) == 49000
    assert crowd_per_day(4000, 0.7) == 2800


def test_base_grade_thresholds():
    assert base_grade(30000) == "S"
    assert base_grade(29999) == "A"
    assert base_grade(10000) == "A"
    assert base_grade(9999) == "B"
    assert base_grade(3000) == "B"
    assert base_grade(2999) == "C"


def test_base_grade_applies_distance_weight():
    # 원거리(0.5) 4만 명 → 보정 2만 → A
    assert base_grade(40000, weight=0.5) == "A"


def test_final_grade_adjust_and_clamp():
    assert final_grade("A", 1) == "S"
    assert final_grade("A", -1) == "B"
    assert final_grade("S", 1) == "S"
    assert final_grade("C", -1) == "C"
    assert final_grade("B", 0) == "B"
