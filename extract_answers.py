import json

# ========== 설정 ==========
# 문제별 만점
PROBLEM_MAX_SCORES = {
    1: 40,  # 1번 문제: 40점 만점
    2: 30,  # 2번 문제: 30점 만점
    3: 30   # 3번 문제: 30점 만점
}
# ========================

# 1) 100 samples.json 로드
with open("100 samples.json", "r", encoding="utf-8") as f:
    scores_data = json.load(f)

# 2) Samples(answers).json 로드
with open("Samples(answers).json", "r", encoding="utf-8") as f:
    answers_data = json.load(f)

print("="*80)
print("문제별 만점이 아닌 학생 답안 추출")
print("="*80)

# 각 문제에 대해 처리
for problem_num in [1, 2, 3]:
    print(f"\n{'='*80}")
    print(f"문제 {problem_num}번 처리 중... (만점: {PROBLEM_MAX_SCORES[problem_num]}점)")
    print(f"{'='*80}")
    
    max_score = PROBLEM_MAX_SCORES[problem_num]
    
    # 만점이 아닌 student_id들 필터링
    non_perfect_students = []
    for student in scores_data:
        student_id = student["student_id"]
        score = student["scores"].get(str(problem_num), 0)
        
        if score != max_score:
            non_perfect_students.append({
                "student_id": student_id,
                "score": score
            })
    
    print(f"만점이 아닌 학생 수: {len(non_perfect_students)}명")
    
    # student_id를 키로 하는 딕셔너리로 변환 (빠른 검색을 위해)
    non_perfect_ids = {item["student_id"] for item in non_perfect_students}
    
    # 결과 저장할 리스트
    extracted_answers = []
    
    for answer_entry in answers_data:
        student_id = answer_entry.get("exam_id")  # Samples(answers).json에서는 exam_id가 학번
        
        if student_id in non_perfect_ids:
            # 해당 학생의 점수 찾기
            score = next((s["score"] for s in non_perfect_students if s["student_id"] == student_id), None)
            
            # 해당 문제 답안만 추출
            problem_data = None
            for problem in answer_entry.get("problems", []):
                if problem.get("problem_number") == problem_num:
                    problem_data = problem
                    break
            
            if problem_data:
                extracted_answers.append({
                    "student_id": student_id,
                    "score": score,
                    f"problem_{problem_num}_answer": problem_data
                })
    
    # 결과를 JSON 파일로 저장
    output_data = {
        "total_count": len(extracted_answers),
        "problem_number": problem_num,
        "max_score": max_score,
        "description": f"문제 {problem_num}번 점수가 {max_score}점(만점)이 아닌 학생들의 답안",
        "answers": extracted_answers
    }
    
    output_filename = f"problem{problem_num}_answers.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"파일 저장: {output_filename}")
    print(f"추출된 답안 수: {len(extracted_answers)}개")
    
    # 간단한 통계 출력
    if extracted_answers:
        scores = [item["score"] for item in extracted_answers if item["score"] is not None]
        if scores:
            print(f"\n점수 통계:")
            print(f"  - 최고점: {max(scores)}점")
            print(f"  - 최저점: {min(scores)}점")
            print(f"  - 평균: {sum(scores)/len(scores):.1f}점")
            print(f"  - 만점자 제외: {len(non_perfect_students)}명 / 전체 {len(scores_data)}명")

print(f"\n{'='*80}")
print(f"{'='*80}")
print("\n생성된 파일:")
for problem_num in [1, 2, 3]:
    print(f"  - problem_{problem_num}_answers.json")

