import sys
import os
import json
import argparse
from pathlib import Path
from decimal import Decimal

sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 1. 백엔드 스크립트 경로 설정
# ==========================================
# analysis_wrapper.py가 backend 폴더에 있으므로 현재 디렉토리를 사용
CURRENT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = CURRENT_DIR

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(BACKEND_DIR))

# dotenv를 먼저 import (다른 모듈들이 사용할 수 있도록)
from dotenv import load_dotenv
load_dotenv()

# 백엔드 모듈 import
try:
    from test_parse import parse_exam
    from score import parse_sheet
    from parse2 import parse_student_answer_handwriting
    import clustering
    from clustering import (
        load_exams, get_embeddings, cosine_similarity_matrix, 
        cluster_by_threshold, compute_cluster_stats, describe_clusters_with_openai
    )
    # clustering 모듈에서 상수 가져오기
    SIM_THRESHOLD = getattr(clustering, 'SIM_THRESHOLD', 0.90)
    EMBED_MODEL = getattr(clustering, 'EMBED_MODEL', 'text-embedding-3-large')
    CLUSTER_SUMMARY_MODEL = getattr(clustering, 'CLUSTER_SUMMARY_MODEL', 'gpt-4o-mini')
    MAX_SAMPLES_PER_CLUSTER = getattr(clustering, 'MAX_SAMPLES_PER_CLUSTER', 10)
    CLUSTERING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 일부 모듈 import 실패: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    CLUSTERING_AVAILABLE = False
    # 기본값 설정
    SIM_THRESHOLD = 0.90
    EMBED_MODEL = "text-embedding-3-large"
    CLUSTER_SUMMARY_MODEL = "gpt-4o-mini"
    MAX_SAMPLES_PER_CLUSTER = 10

# ==========================================
# 2. 문제별 만점 설정 (extract_answers.py에서 가져옴)
# ==========================================
PROBLEM_MAX_SCORES = {
    1: 40,  # 1번 문제: 40점 만점
    2: 30,  # 2번 문제: 30점 만점
    3: 30   # 3번 문제: 30점 만점
}

# ==========================================
# 3. Helper Functions
# ==========================================
def extract_student_code_from_score(score_result: dict) -> str:
    """점수표 파싱 결과에서 학번 추출"""
    return score_result.get("student_code", "unknown")

def calculate_score_distribution(score_results: list, question_num: int, max_score: int) -> tuple:
    """
    점수 분포 계산
    Returns: (scoreLabels, scoreData, avgScore)
    """
    scores = []
    for score_result in score_results:
        for answer in score_result.get("answers", []):
            if answer.get("question_number") == question_num:
                scores.append(answer.get("score", 0))
                break
    
    if not scores:
        return (["0점", "1-3점", "4-6점", "7-9점", "만점"], [0, 0, 0, 0, 0], 0.0)
    
    # 점수 구간별 분류
    score_labels = ["0점", "1-3점", "4-6점", "7-9점", f"{max_score}점"]
    score_data = [0, 0, 0, 0, 0]
    
    for score in scores:
        if score == 0:
            score_data[0] += 1
        elif score < 4:
            score_data[1] += 1
        elif score < 7:
            score_data[2] += 1
        elif score < max_score:
            score_data[3] += 1
        else:  # 만점
            score_data[4] += 1
    
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    return (score_labels, score_data, round(avg_score, 1))

def extract_non_perfect_answers(score_results: list, student_answers: list, problem_num: int, max_score: int) -> list:
    """
    만점이 아닌 학생들의 답안 추출 (extract_answers.py 로직)
    Returns: problem{n}_answers.json 형식의 데이터
    """
    non_perfect_students = []
    
    # 만점이 아닌 학생 찾기
    for score_result in score_results:
        student_code = score_result.get("student_code")
        for answer in score_result.get("answers", []):
            if answer.get("question_number") == problem_num:
                score = answer.get("score", 0)
                if score != max_score:
                    non_perfect_students.append({
                        "student_code": student_code,
                        "score": score
                    })
                break
    
    # 해당 학생들의 답안 추출
    extracted = []
    non_perfect_codes = {s["student_code"] for s in non_perfect_students}
    
    for answer_data in student_answers:
        student_code = answer_data.get("student_code") or answer_data.get("exam_id", "")
        if student_code in non_perfect_codes:
            # parse2.py 결과 형식: {"student_code": ..., "answers": [...]}
            # clustering.py가 기대하는 형식: {"exam_id": ..., "problems": [{"problem_number": ..., "subparts": [...]}]}
            # 변환 필요
            
            # 해당 문제의 답안 찾기
            answer_item = None
            for ans in answer_data.get("answers", []):
                if ans.get("question_number") == problem_num:
                    answer_item = ans
                    break
            
            if answer_item:
                score = next((s["score"] for s in non_perfect_students if s["student_code"] == student_code), 0)
                
                # clustering.py가 기대하는 형식으로 변환
                # answer_item을 problem 형식으로 변환
                problem_answer = {
                    "problem_number": problem_num,
                    "subparts": [
                        {
                            "label": "a",
                            "is_blank": False,
                            "contents": [
                                {
                                    "index": 0,
                                    "type": "text",
                                    "value": answer_item.get("answer_text", "")
                                }
                            ]
                        }
                    ]
                }
                
                extracted.append({
                    "student_code": student_code,
                    "score": score,
                    f"problem_{problem_num}_answer": problem_answer
                })
    
    return extracted

# ==========================================
# 4. Clustering 연동
# ==========================================
def run_clustering_for_problem(problem_num: int, rubric_path: str, question_image_path: str, non_perfect_answers: list):
    """
    clustering.py를 사용하여 클러스터링 분석 수행
    """
    if not CLUSTERING_AVAILABLE or not non_perfect_answers:
        return []
    
    try:
        # problem{n}_answers.json 형식으로 임시 파일 생성
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        json_path = temp_dir / f"problem{problem_num}_answers.json"
        
        # extract_answers.py 형식으로 데이터 저장
        output_data = {
            "total_count": len(non_perfect_answers),
            "problem_number": problem_num,
            "max_score": PROBLEM_MAX_SCORES.get(problem_num, 10),
            "description": f"문제 {problem_num}번 만점이 아닌 학생들의 답안",
            "answers": non_perfect_answers
        }
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # clustering.py의 함수들을 직접 호출
        exam_ids, texts = load_exams(str(json_path), problem_num)
        
        print(f"    📊 문제 {problem_num}번: {len(exam_ids)}명의 학생 답안 로드됨", file=sys.stderr)
        
        if len(exam_ids) < 2:
            # 학생이 2명 미만이면 클러스터링 불가
            print(f"    ⚠️ 문제 {problem_num}번: 학생이 {len(exam_ids)}명뿐이라 클러스터링 불가", file=sys.stderr)
            return []
        
        # 임베딩 생성
        print(f"    🔄 문제 {problem_num}번: 임베딩 생성 중...", file=sys.stderr)
        embeddings = get_embeddings(texts)
        
        # 유사도 행렬 계산
        print(f"    🔄 문제 {problem_num}번: 유사도 행렬 계산 중...", file=sys.stderr)
        sim_mat = cosine_similarity_matrix(embeddings)
        
        # 클러스터링 (유사도 임계값 이상)
        print(f"    🔄 문제 {problem_num}번: 클러스터링 중...", file=sys.stderr)
        clusters = cluster_by_threshold(exam_ids, sim_mat, SIM_THRESHOLD)
        print(f"    ✅ 문제 {problem_num}번: {len(clusters)}개 클러스터 생성됨", file=sys.stderr)
        
        if not clusters:
            print(f"    ⚠️ 문제 {problem_num}번: 클러스터가 생성되지 않음 (유사도 임계값: {SIM_THRESHOLD})", file=sys.stderr)
            return []
        
        # 통계 계산
        stats_per_cluster = compute_cluster_stats(exam_ids, texts, clusters, sim_mat)
        
        # OpenAI로 클러스터 분석
        print(f"    🤖 문제 {problem_num}번: OpenAI로 클러스터 분석 중...", file=sys.stderr)
        cluster_summaries = describe_clusters_with_openai(
            exam_ids,
            texts,
            clusters,
            stats_per_cluster,
            question_image_path,
            rubric_path,
            problem_num=problem_num,  # 문제 번호 전달
            model=CLUSTER_SUMMARY_MODEL,
            max_samples_per_cluster=MAX_SAMPLES_PER_CLUSTER
        )
        
        print(f"    ✅ 문제 {problem_num}번: {len(cluster_summaries)}개 클러스터 분석 완료", file=sys.stderr)
        
        # 임시 파일 삭제
        if json_path.exists():
            json_path.unlink()
        
        return cluster_summaries
        
    except Exception as e:
        print(f"⚠️ 클러스터링 실패 (문제 {problem_num}): {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return []

# ==========================================
# 5. Main Analysis Function
# ==========================================
def perform_analysis(blank_path, rubric_path, score_path, student_paths):
    """
    전체 분석 파이프라인 실행
    
    Args:
        blank_path: 문제 원본 파일 경로 (문제지.pdf) → test_parse.py의 parse_exam() 사용
        rubric_path: 채점 기준표 이미지 경로 → clustering.py의 describe_clusters_with_openai() 사용
        score_path: 점수표 이미지 경로 → score.py의 parse_sheet() 사용
        student_paths: 학생 답안지 이미지 경로 리스트 → parse2.py의 parse_student_answer_handwriting() 사용
    """
    print("🚀 분석 시작...", file=sys.stderr)
    
    # 1. 문제지 파싱 (test_parse.py) - 문제 원본 처리
    print("📝 [1단계] 문제지 파싱 중 (test_parse.py)...", file=sys.stderr)
    try:
        problem_data = parse_exam(blank_path)  # test_parse.py의 parse_exam() 사용
        questions = problem_data.get("problems", [])
        print(f"✅ 문제 {len(questions)}개 파싱 완료", file=sys.stderr)
    except Exception as e:
        print(f"❌ 문제지 파싱 실패: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        questions = []
    
    # 2. 점수표 파싱 (score.py) - 점수표 처리 (여러 개 가능)
    print("📊 [2단계] 점수표 파싱 중 (score.py)...", file=sys.stderr)
    score_results = []
    # score_path는 이미 리스트로 받음 (nargs='+')
    score_paths = score_path if isinstance(score_path, list) else [score_path]
    
    print(f"  📊 점수표 {len(score_paths)}개 처리 예정", file=sys.stderr)
    for sp in score_paths:
        try:
            result = parse_sheet(sp)  # score.py의 parse_sheet() 사용
            score_results.append(result)
        except Exception as e:
            print(f"⚠️ 점수표 파싱 실패 ({sp}): {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    total_students = len(score_results)
    print(f"✅ 점수표 {total_students}개 파싱 완료", file=sys.stderr)
    
    # 3. 학생 답안 파싱 (parse2.py) - 학생 답안지 처리
    print("✍️ [3단계] 학생 답안 파싱 중 (parse2.py)...", file=sys.stderr)
    student_answers = []
    
    for idx, student_path in enumerate(student_paths):
        try:
            # 점수표에서 학번 찾기
            student_code = None
            if idx < len(score_results):
                student_code = score_results[idx].get("student_code")
            
            answer_data = parse_student_answer_handwriting(student_path, student_code)  # parse2.py 사용
            student_answers.append(answer_data)
        except Exception as e:
            print(f"⚠️ 답안 파싱 실패 ({student_path}): {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    
    print(f"✅ 답안 {len(student_answers)}개 파싱 완료", file=sys.stderr)
    
    # 4. 문제별 분석 및 클러스터링 (clustering.py) - 채점 기준표 사용
    print("📈 [4단계] 문제별 분석 중 (clustering.py)...", file=sys.stderr)
    questions_result = []
    
    for problem in questions:
        problem_num = problem.get("problem_index")
        max_score = problem.get("score", PROBLEM_MAX_SCORES.get(problem_num, 10))
        
        # 점수 분포 계산
        score_labels, score_data, avg_score = calculate_score_distribution(
            score_results, problem_num, max_score
        )
        
        # 만점이 아닌 학생 답안 추출
        non_perfect_answers = extract_non_perfect_answers(
            score_results, student_answers, problem_num, max_score
        )
        
        print(f"  📊 문제 {problem_num}번: 만점이 아닌 학생 {len(non_perfect_answers)}명", file=sys.stderr)
        
        # 클러스터링 실행 (clustering.py 사용, rubric_path와 blank_path 전달)
        print(f"  📊 문제 {problem_num}번 클러스터링 중 (clustering.py, 채점 기준표 사용)...", file=sys.stderr)
        clusters = run_clustering_for_problem(problem_num, rubric_path, blank_path, non_perfect_answers)
        
        print(f"  📊 문제 {problem_num}번: 클러스터링 결과 {len(clusters) if clusters else 0}개", file=sys.stderr)
        
        # 클러스터가 없으면 기본값 제공
        if not clusters:
            clusters = [
                {
                    "cluster_index": 1,
                    "cognitive_diagnosis": {
                        "misconceptions": ["분석 데이터 부족"],
                        "logical_gaps": ["분석 데이터 부족"],
                        "missing_keywords": ["분석 데이터 부족"]
                    },
                    "pattern_characteristics": {
                        "specificity": "분석 데이터 부족",
                        "approach": "분석 데이터 부족",
                        "error_type": "분석 데이터 부족"
                    },
                    "quantitative_metrics": {
                        "num_students": len(non_perfect_answers),
                        "percentage": round((len(non_perfect_answers) / total_students * 100) if total_students > 0 else 0, 1),
                        "relative_length": "분석 데이터 부족",
                        "expected_score_level": "분석 데이터 부족"
                    },
                    "overall_summary": "클러스터링을 수행할 충분한 데이터가 없습니다."
                }
            ]
        
        # 프론트엔드 형식으로 변환
        question_result = {
            "qNum": problem_num,
            "maxScore": max_score,
            "qText": problem.get("raw_text", ""),
            "avgScore": avg_score,
            "scoreLabels": score_labels,
            "scoreData": score_data,
            "clusters": clusters
        }
        
        questions_result.append(question_result)
    
    # 최종 결과 반환
    return {
        "totalStudents": total_students,
        "questions": questions_result
    }

# ==========================================
# 6. Main Orchestrator
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--blank", required=True, help="문제 원본 PDF/IMG 경로")
    parser.add_argument("--rubric", required=True, help="채점 기준표 IMG 경로")
    parser.add_argument("--score", nargs='+', required=True, help="점수표 IMG 경로 (여러 개 가능)")
    parser.add_argument("--students", nargs='+', required=True, help="학생 답안 IMG 경로 리스트")
    args = parser.parse_args()

    try:
        # 분석 실행 (여러 점수표 처리)
        final_data = perform_analysis(args.blank, args.rubric, args.score, args.students)
        
        # 결과를 JSON 문자열로 출력 (Node.js가 읽는 부분)
        print(json.dumps(final_data, ensure_ascii=False))
        
    except Exception as e:
        # 에러 발생 시 stderr로 출력
        import traceback
        sys.stderr.write(f"Error in analysis_wrapper.py: {str(e)}\n")
        sys.stderr.write(traceback.format_exc())
        sys.exit(1)

