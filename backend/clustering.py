import json
import numpy as np
from openai import OpenAI
import base64
import mimetypes
import os
import time
from openai import RateLimitError
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()

# OpenAI API 키를 환경변수에서 읽어오기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# ---------- 설정 ----------
QUESTION_IMAGE_PATH = "문제지.png"   # 문제지 이미지
RUBRIC_IMAGE_PATH = "채점기준.png"   # 채점 기준 이미지

SIM_THRESHOLD = 0.90               # 클러스터링 기준 유사도
EMBED_MODEL = "text-embedding-3-large"
CLUSTER_SUMMARY_MODEL = "gpt-4o-mini"
MAX_SAMPLES_PER_CLUSTER = 10       # 클러스터당 요약에 쓸 최대 샘플 수

# 클러스터링을 수행할 문제 번호들 (파일명: problem{n}_answers.json)
PROBLEM_NUMS = [1, 2, 3]
# --------------------------

client = OpenAI(api_key=OPENAI_API_KEY)


def encode_image_to_data_url(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def exam_to_text(exam: dict) -> str:
    """
    한 exam(한 학생 답안)을 하나의 텍스트로 합치는 함수.
    problems -> subparts -> contents 를 순회하며
    text / equation 내용을 전부 이어붙인다.
    """
    pieces = [f"exam_id: {exam.get('exam_id', '')}"]

    for problem in exam.get("problems", []):
        p_no = problem.get("problem_number")
        pieces.append(f"\n[Problem {p_no}]")

        for sub in problem.get("subparts", []):
            for c in sub.get("contents", []):
                if c.get("type") == "text":
                    pieces.append(c.get("value", ""))
                elif c.get("type") == "equation":
                    pieces.append(c.get("latex") or c.get("raw", ""))

    return "\n".join(pieces)


def load_exams(json_path: str, problem_num: int):
    """
    problem{n}_answers.json 구조:
    {
      "answers": [
        {
          "student_id": "...",
          "problem_{n}_answer": { ... }
        },
        ...
      ]
    }
    또는
    [
      { "exam_id": "...", "problems": [...] },
      ...
    ]
    둘 다 처리.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # {"answers": [...]} 형태
    if isinstance(data, dict) and "answers" in data:
        answers = data["answers"]
        exam_ids = [ans["student_id"] for ans in answers]
        exams = []
        problem_key = f"problem_{problem_num}_answer"
        for ans in answers:
            exam = {
                "exam_id": ans["student_id"],
                "problems": [ans[problem_key]],
            }
            exams.append(exam)
        texts = [exam_to_text(exam) for exam in exams]
    else:
        # 기존 배열 형태
        exam_ids = [d["exam_id"] for d in data]
        texts = [exam_to_text(d) for d in data]

    return exam_ids, texts


def get_embeddings(texts):
    resp = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    vectors = np.array([item.embedding for item in resp.data])
    return vectors


def cosine_similarity_matrix(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-10
    normalized = vectors / norms
    return normalized @ normalized.T


def cluster_by_threshold(exam_ids, sim_matrix, threshold: float):
    n = len(exam_ids)
    visited = [False] * n
    clusters = []

    for i in range(n):
        if visited[i]:
            continue
        cluster = [exam_ids[i]]
        visited[i] = True

        for j in range(i + 1, n):
            if not visited[j] and sim_matrix[i, j] >= threshold:
                visited[j] = True
                cluster.append(exam_ids[j])

        clusters.append(cluster)

    return clusters


def compute_cluster_stats(exam_ids, texts, clusters, sim_mat):
    """
    각 클러스터에 대해 통계량 계산:
    - size (학생 수)
    - ratio (전체 대비 비율)
    - 답안 길이(문자수): 평균/최소/최대
    - 클러스터 내 유사도: 평균/최소/최대 (자기 자신 제외)
    """
    total_n = len(exam_ids)
    id_to_index = {eid: i for i, eid in enumerate(exam_ids)}
    id_to_text = dict(zip(exam_ids, texts))

    stats_per_cluster = []

    for idx, cluster in enumerate(clusters, start=1):
        size = len(cluster)
        ratio = size / total_n if total_n > 0 else 0.0
        indices = [id_to_index[eid] for eid in cluster]

        lengths = [len(id_to_text[eid]) for eid in cluster]
        avg_len = float(np.mean(lengths))
        min_len = int(np.min(lengths))
        max_len = int(np.max(lengths))

        sub_mat = sim_mat[np.ix_(indices, indices)]
        m = sub_mat.shape[0]
        if m > 1:
            tri_i, tri_j = np.triu_indices(m, k=1)
            sims = sub_mat[tri_i, tri_j]
            avg_sim = float(np.mean(sims))
            min_sim = float(np.min(sims))
            max_sim = float(np.max(sims))
        else:
            avg_sim = min_sim = max_sim = 1.0

        stats = {
            "cluster_index": idx,
            "size": size,
            "ratio": ratio,
            "length": {
                "avg_chars": avg_len,
                "min_chars": min_len,
                "max_chars": max_len,
            },
            "similarity": {
                "avg_intra_cosine": avg_sim,
                "min_intra_cosine": min_sim,
                "max_intra_cosine": max_sim,
            },
        }
        stats_per_cluster.append(stats)

    return stats_per_cluster


def describe_clusters_with_openai(
    exam_ids,
    texts,
    clusters,
    stats_per_cluster,
    question_image_path,
    rubric_image_path,
    model=CLUSTER_SUMMARY_MODEL,
    max_samples_per_cluster=MAX_SAMPLES_PER_CLUSTER,
):
    """
    각 클러스터에 대해:
    - 통계(stats_per_cluster)
    - 일부 예시 답안
    - 문제 이미지, 채점기준 이미지
    를 함께 넘기고,
    인지적 진단/패턴/정량 분포를 포함한 JSON 분석을 받는다.
    """
    id_to_text = dict(zip(exam_ids, texts))
    stats_by_index = {s["cluster_index"]: s for s in stats_per_cluster}

    # 문제/채점기준 이미지는 모든 클러스터에서 공통으로 사용
    question_data_url = encode_image_to_data_url(question_image_path)
    rubric_data_url = encode_image_to_data_url(rubric_image_path)

    cluster_summaries = []

    for idx, cluster in enumerate(clusters, start=1):
        stats = stats_by_index[idx]
        size = stats["size"]

        sample_ids = cluster[:max_samples_per_cluster]
        samples = []
        for sid in sample_ids:
            t = id_to_text.get(sid, "")
            t_short = t[:1500]
            samples.append(f"학생 {sid} 답안:\n{t_short}")

        samples_text = "\n\n".join(samples)
        stats_json = json.dumps(stats, ensure_ascii=False, indent=2)

        system_msg = """
당신은 수학 서술형 시험 답안을 분석하는 평가 전문가입니다.
문제지와 채점 기준, 그리고 클러스터별 답안/통계를 보고
인지적 진단, 답안 패턴, 정량적 분포를 해석해야 합니다.
"""

        # ⚠️ 요구사항: 답안 생성 로직 프롬프트(user_text)는 수정하지 않음
        user_text = f"""
다음은 1번 문제에 대한 답안을 임베딩 유사도로 클러스터링한 결과 중,
클러스터 {idx}에 대한 정보입니다.

[클러스터 {idx} 통계 JSON]
{stats_json}

- ratio: 전체 학생 중 이 클러스터에 속한 비율입니다 (0~1 사이).
- length.avg_chars: 한 학생 당 답안 평균 문자 수입니다.
- similarity.avg_intra_cosine: 클러스터 내부 코사인 유사도 평균입니다.

또한, 이 클러스터에 속한 학생들의 일부 답안을 예시로 제공합니다.

[클러스터 {idx} 예시 답안 (총 {size}명 중 최대 {len(sample_ids)}명)]
{samples_text}
[예시 끝]

위 통계와 예시, 그리고 첨부된 "문제+채점 기준" 이미지를 모두 참고하여,
이 클러스터에 대해 다음 세 관점으로 분석해 주세요.

1. 인지적 진단 (cognitive_diagnosis)
   - 왜 이런 답을 쓰게 되었는지, 사고 과정/오개념을 분석합니다.
   - 포함해야 할 항목:
     * misconceptions: 공통된 오개념/개념 혼동 (리스트)
     * logical_gaps: 논리적 비약/결손 (어느 단계가 비어 있는지)
     * missing_keywords: 사용하지 않은 핵심 용어/개념

2. 답안 패턴의 특징 (pattern_characteristics)
   - 답안을 '어떻게' 쓰는지에 대한 구조적 특징입니다.
   - 포함해야 할 항목:
     * specificity: 서술의 구체성 수준(추상적/보통/구체적 등 묘사)
     * approach: 접근 방식 요약 (정석 풀이/직관적 접근/우회적 풀이 등)
     * error_type: 오류의 일관성 (계산 실수 위주인지, 개념 오류 위주인지 등)

3. 정량적 분포 (quantitative_metrics)
   - 이 유형이 학급 전체에서 어느 정도 비율을 차지하는지,
     통계적 관점에서 요약합니다.
   - 포함해야 할 항목:
     * num_students: 이 클러스터의 학생 수 (size)
     * percentage: 전체 학생 대비 비율 (ratio * 100, 소수점 1자리 정도)
     * relative_length: 답안 길이가 다른 그룹에 비해 대략 어떤 수준인지에 대한 서술
     * expected_score_level: 채점 기준을 참고했을 때 예상되는 평균 점수 수준
       (예: "부분점수 위주로 40점 만점 중 10~20점 대에 머무를 가능성이 큼"처럼
        '정확한 숫자'가 아니라 범위/경향만 추정합니다. 새로운 구체 점수를 만들지 마세요.)

마지막으로, 위 세 관점을 종합해
이 클러스터를 한두 문장으로 요약하는 overall_summary 도 작성해 주세요.

반환 형식은 반드시 아래 JSON 구조를 따라야 합니다 (키 이름을 바꾸지 마세요):

{{
  "cluster_index": {idx},
  "cognitive_diagnosis": {{
    "misconceptions": ["..."],
    "logical_gaps": ["..."],
    "missing_keywords": ["..."]
  }},
  "pattern_characteristics": {{
    "specificity": "...",
    "approach": "...",
    "error_type": "..."
  }},
  "quantitative_metrics": {{
    "num_students": {size},
    "percentage": {stats["ratio"] * 100},
    "relative_length": "...",
    "expected_score_level": "..."
  }},
  "overall_summary": "..."
}}

주의:
- 통계값(num_students, percentage)은 위에서 제공된 값을 그대로 사용하고,
  새 숫자를 임의로 만들지 마세요.
- expected_score_level 은 "대략 상/중/하" 또는 "10~20점" 같은 범위 표현만 사용하고,
  새로운 정확한 점수(예: 13.4점)는 만들지 마세요.
- 개별 학생 답안을 길게 인용하지 말고, 공통 패턴과 통계에 기반해 요약하세요.
- JSON 이외의 다른 텍스트는 절대 출력하지 마세요.
"""

        # Rate Limit 대응: 재시도 로직
        max_retries = 5
        retry_delay = 2  # 초
        
        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_msg},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_text},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": question_data_url},
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": rubric_data_url},
                                },
                            ],
                        },
                    ],
                    max_tokens=900,
                )

                content = resp.choices[0].message.content
                summary_obj = json.loads(content)
                cluster_summaries.append(summary_obj)

                print(f"\n[Cluster {idx}] 특징 요약 완료")
                
                # 다음 클러스터 처리 전 짧은 대기 (Rate Limit 방지)
                if idx < len(clusters):
                    time.sleep(1)
                
                break  # 성공하면 재시도 루프 탈출
                
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"\n⚠️  Rate Limit 도달. {wait_time}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"\n❌ [Cluster {idx}] Rate Limit 에러: 최대 재시도 횟수 초과")
                    raise  # 최대 재시도 후에도 실패하면 에러 발생

    return cluster_summaries


def run_for_problem(problem_num: int):
    json_path = f"problem{problem_num}_answers.json"
    if not os.path.exists(json_path):
        print(f"[문제 {problem_num}] 파일 없음: {json_path} (건너뜀)")
        return

    print(f"\n========== 문제 {problem_num} ({json_path}) ==========")

    # 1) JSON 로드 + 텍스트 만들기
    exam_ids, texts = load_exams(json_path, problem_num)
    print(f"{len(exam_ids)}개 exam 로드 완료")

    # 2) 임베딩
    embeddings = get_embeddings(texts)
    print("임베딩 완료, shape =", embeddings.shape)

    # 3) 유사도 행렬
    sim_mat = cosine_similarity_matrix(embeddings)

    # 4) 클러스터링
    clusters = cluster_by_threshold(exam_ids, sim_mat, SIM_THRESHOLD)

    print(f"\n유사도 {SIM_THRESHOLD} 이상 클러스터 수: {len(clusters)}개\n")
    for idx, cluster in enumerate(clusters, start=1):
        print(f"[Cluster {idx}] ({len(cluster)}명)")
        print("  ", ", ".join(cluster))

    # 5) 통계 계산
    stats_per_cluster = compute_cluster_stats(exam_ids, texts, clusters, sim_mat)

    # 6) OpenAI로 인지적 진단 + 패턴 + 정량 분석
    print("\n=== OpenAI로 클러스터 진단/분석 중... ===")
    cluster_summaries = describe_clusters_with_openai(
        exam_ids,
        texts,
        clusters,
        stats_per_cluster,
        QUESTION_IMAGE_PATH,
        RUBRIC_IMAGE_PATH,
    )

    # 7) 결과 저장
    summary_path = f"cluster_analysis_problem{problem_num}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(cluster_summaries, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 문제 {problem_num} 클러스터 분석을 '{summary_path}' 파일에 저장했습니다.\n")


def main():
    for p in PROBLEM_NUMS:
        run_for_problem(p)


if __name__ == "__main__":
    main()