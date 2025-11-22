import json

# 1) 100 samples.json에서 문제 "1"이 40점이 아닌 학생 ID들을 찾기
with open("100 samples.json", "r", encoding="utf-8") as f:
    scores_data = json.load(f)

# 문제 "1"의 점수가 40이 아닌 student_id들 필터링
non_perfect_students = []
for student in scores_data:
    student_id = student["student_id"]
    score_1 = student["scores"].get("3", 0)
    
    if score_1 != 40:
        non_perfect_students.append({
            "student_id": student_id,
            "score": score_1
        })

print(f"문제 1번 점수가 40점이 아닌 학생 수: {len(non_perfect_students)}명")

# 2) Samples(answers).json에서 해당 학생들의 문제 "1" 답안 추출
with open("Samples(answers).json", "r", encoding="utf-8") as f:
    answers_data = json.load(f)

# student_id를 키로 하는 딕셔너리로 변환 (빠른 검색을 위해)
non_perfect_ids = {item["student_id"] for item in non_perfect_students}

# 결과 저장할 리스트
extracted_answers = []

for answer_entry in answers_data:
    student_id = answer_entry.get("exam_id")  # Samples(answers).json에서는 exam_id가 학번
    
    if student_id in non_perfect_ids:
        # 해당 학생의 점수 찾기
        score = next((s["score"] for s in non_perfect_students if s["student_id"] == student_id), None)
        
        # 문제 1번 답안만 추출
        problem_1_data = None
        for problem in answer_entry.get("problems", []):
            if problem.get("problem_number") == 1:
                problem_1_data = problem
                break
        
        if problem_1_data:
            extracted_answers.append({
                "student_id": student_id,
                "score": score,
                "problem_1_answer": problem_1_data
            })

# 3) 결과를 JSON 파일로 저장
output_data = {
    "total_count": len(extracted_answers),
    "description": "문제 1번 점수가 40점이 아닌 학생들의 답안",
    "answers": extracted_answers
}

output_filename = "problem_2_non_perfect_answers.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"\n✅ 결과 저장 완료: {output_filename}")
print(f"추출된 답안 수: {len(extracted_answers)}개")

# 간단한 통계 출력
if extracted_answers:
    scores = [item["score"] for item in extracted_answers if item["score"] is not None]
    if scores:
        print(f"\n점수 통계:")
        print(f"  - 최고점: {max(scores)}점")
        print(f"  - 최저점: {min(scores)}점")
        print(f"  - 평균: {sum(scores)/len(scores):.1f}점")

