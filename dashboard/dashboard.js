document.addEventListener("DOMContentLoaded", () => {
  // 1. 문제 원본 (PDF)
  setupDragAndDrop("blank-drop-zone", "blankFile", handleBlankFileSelect);
  document
    .getElementById("blankFile")
    .addEventListener("change", (e) => handleBlankFileSelect(e.target.files));

  // 2. 채점 기준표 (PNG)
  setupDragAndDrop("rubric-drop-zone", "rubricFile", handleRubricFileSelect);
  document
    .getElementById("rubricFile")
    .addEventListener("change", (e) => handleRubricFileSelect(e.target.files));

  // 3. 점수표 (PNG - Multiple)
  setupDragAndDrop("score-drop-zone", "scoreFile", handleScoreFileSelect);
  document
    .getElementById("scoreFile")
    .addEventListener("change", (e) => handleScoreFileSelect(e.target.files));

  // 4. 학생 답안지 (PNG - Multiple)
  setupDragAndDrop(
    "student-drop-zone",
    "studentFiles",
    handleStudentFileSelect
  );
  document
    .getElementById("studentFiles")
    .addEventListener("change", (e) => handleStudentFileSelect(e.target.files));

  // 분석 시작 버튼
  document
    .getElementById("analyze-btn")
    .addEventListener("click", startFinalAnalysis);

  // 모달 관련 이벤트
  document
    .getElementById("close-modal-btn")
    .addEventListener("click", closeModal);
  document.getElementById("report-modal").addEventListener("click", (e) => {
    if (e.target.id === "report-modal") closeModal();
  });

  // 과목 추가 모달 이벤트
  document
    .getElementById("add-subject-modal")
    .addEventListener("click", (e) => {
      if (e.target.id === "add-subject-modal") closeAddSubjectModal();
    });
  document
    .getElementById("new-subject-input")
    .addEventListener("keypress", (e) => {
      if (e.key === "Enter") handleAddSubject();
    });
});

// ==========================================
// 1. 드래그 앤 드롭 유틸리티
// ==========================================
function setupDragAndDrop(zoneId, inputId, callback) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  zone.addEventListener("dragover", (e) => {
    e.preventDefault();
    zone.classList.add("drag-over");
  });
  zone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
  });
  zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("drag-over");
    if (e.dataTransfer.files.length > 0) {
      input.files = e.dataTransfer.files;
      callback(e.dataTransfer.files);
    }
  });
}

// 개별 파일 핸들러
function handleBlankFileSelect(files) {
  if (files.length > 0) {
    document.getElementById(
      "blank-label"
    ).innerHTML = `<span class="text-green-600 font-bold">${files[0].name}</span><br>준비 완료`;
    document.getElementById("blank-check").classList.remove("hidden");
    document.getElementById("blank-drop-zone").style.borderColor = "#22c55e";
    document.getElementById("blank-drop-zone").style.backgroundColor =
      "#f0fdf4";
  }
}

function handleRubricFileSelect(files) {
  if (files.length > 0) {
    document.getElementById(
      "rubric-label"
    ).innerHTML = `<span class="text-green-600 font-bold">${files[0].name}</span><br>준비 완료`;
    document.getElementById("rubric-check").classList.remove("hidden");
    document.getElementById("rubric-drop-zone").style.borderColor = "#22c55e";
    document.getElementById("rubric-drop-zone").style.backgroundColor =
      "#f0fdf4";
  }
}

function handleScoreFileSelect(files) {
  if (files.length > 0) {
    document.getElementById("score-file-count-badge").innerText = files.length;
    document
      .getElementById("score-file-count-badge")
      .classList.remove("hidden");
    document.getElementById(
      "score-label"
    ).innerHTML = `<span class="text-blue-600 font-bold">${files.length}개</span> 파일 선택됨`;
    const dropZone = document.getElementById("score-drop-zone");
    dropZone.style.borderColor = "#3b82f6";
    dropZone.style.backgroundColor = "#eff6ff";
    dropZone
      .querySelector("i")
      .classList.replace("text-slate-300", "text-blue-200");
  }
}

function handleStudentFileSelect(files) {
  if (files.length > 0) {
    document.getElementById("file-count-badge").innerText = files.length;
    document.getElementById("file-count-badge").classList.remove("hidden");
    document.getElementById(
      "student-label"
    ).innerHTML = `<span class="text-blue-600 font-bold">${files.length}개</span> 파일 선택됨`;
  }
}

// ==========================================
// 2. 분석 시작 (서버 통신 및 데이터 변환)
// ==========================================
async function startFinalAnalysis() {
  const blankFile = document.getElementById("blankFile").files[0];
  const rubricFile = document.getElementById("rubricFile").files[0];
  const scoreFiles = document.getElementById("scoreFile").files;
  const studentFiles = document.getElementById("studentFiles").files;

  if (
    !blankFile ||
    !rubricFile ||
    scoreFiles.length === 0 ||
    studentFiles.length === 0
  ) {
    alert("모든 파일을 업로드해주세요.");
    return;
  }

  document.getElementById("upload-section").classList.add("hidden");
  document.getElementById("loading-section").classList.remove("hidden");

  try {
    // 1단계: 문제지 업로드
    const blankFormData = new FormData();
    blankFormData.append("file", blankFile);
    const blankRes = await fetch("/question-papers/upload/blank", {
      method: "POST",
      body: blankFormData,
    });
    if (!blankRes.ok) {
      const error = await blankRes.json();
      throw new Error(error.error || "1단계(문제지) 업로드 실패");
    }

    // 2단계: 채점 기준표 업로드
    const rubricFormData = new FormData();
    rubricFormData.append("rubric", rubricFile);
    const rubricRes = await fetch("/question-papers/upload/rubric", {
      method: "POST",
      body: rubricFormData,
    });
    if (!rubricRes.ok) {
      const error = await rubricRes.json();
      throw new Error(error.error || "2단계(채점 기준표) 업로드 실패");
    }

    // 3단계: 점수표 업로드
    const scoreFormData = new FormData();
    for (let i = 0; i < scoreFiles.length; i++) {
      scoreFormData.append("scoreFiles", scoreFiles[i]);
    }
    const scoreRes = await fetch("/question-papers/upload/scores", {
      method: "POST",
      body: scoreFormData,
    });
    if (!scoreRes.ok) {
      const error = await scoreRes.json();
      throw new Error(error.error || "3단계(점수표) 업로드 실패");
    }

    // 4단계: 답안지 업로드 및 분석 요청
    const aFormData = new FormData();
    for (let i = 0; i < studentFiles.length; i++) {
      aFormData.append("files", studentFiles[i]);
    }

    const aRes = await fetch("/answer-sheets/upload", {
      method: "POST",
      body: aFormData,
    });
    if (!aRes.ok) {
      const error = await aRes.json();
      throw new Error(error.error || "4단계(답안지) 분석 요청 실패");
    }

    const rawData = await aRes.json();

    // [중요] 서버 데이터(analysis.py 형식)를 프론트엔드 형식으로 변환
    const processedData = processServerData(rawData);

    console.log("✅ 분석 데이터 처리 완료:", processedData);
    renderDashboard(processedData);
  } catch (error) {
    console.error("Error:", error);
    alert("오류가 발생했습니다. 콘솔을 확인해주세요.");
    document.getElementById("loading-section").classList.add("hidden");
    document.getElementById("upload-section").classList.remove("hidden");
  }
}

// [핵심] 서버 데이터를 대시보드용 데이터로 변환하는 함수
function processServerData(serverData) {
  // 만약 서버가 이미 dashboard 형식을 준다면 그대로 반환
  if (serverData.questions && serverData.totalStudents) return serverData;

  // analysis.py 형식이 단일 객체로 온다고 가정 (또는 배열일 수도 있음)
  // 여기서는 단일 문항 응답을 가정하고 배열로 감쌉니다.
  const inputItem = Array.isArray(serverData) ? serverData[0] : serverData;

  // 1. 기본 정보 추출
  const totalStudents = inputItem.statistics?.total_answers || 0;
  const correctCount = inputItem.statistics?.correct_answers || 0;
  const wrongList = inputItem.wrong_answers || [];
  const maxScore = inputItem.max_score || 10;

  // 2. 점수 히스토그램 계산 (Distribution)
  // 예: 10점 만점이면 [0점, 1-3점, 4-6점, 7-9점, 10점] 5개 구간으로 나눔
  const scoreLabels = ["0점", "1-3점", "4-6점", "7-9점", "10점(정답)"];
  const scoreCounts = [0, 0, 0, 0, 0]; // 각 구간별 인원 수

  // 오답자 점수 집계
  wrongList.forEach((item) => {
    const s = item.score || 0;
    if (s === 0) scoreCounts[0]++;
    else if (s < 4) scoreCounts[1]++;
    else if (s < 7) scoreCounts[2]++;
    else if (s < 10) scoreCounts[3]++;
    else scoreCounts[4]++; // 혹시 오답 리스트에 만점자가 있다면
  });

  // 정답자(만점자) 추가
  // analysis.py 로직상 정답자는 wrong_answers 리스트에 없으므로 따로 더해줍니다.
  scoreCounts[4] += correctCount;

  // 3. 평균 점수 계산
  let totalSum = 0;
  wrongList.forEach((w) => (totalSum += w.score || 0));
  totalSum += correctCount * maxScore;
  const avgScore =
    totalStudents > 0 ? (totalSum / totalStudents).toFixed(1) : 0;

  // 4. 클러스터 데이터 매핑
  // analysis_result.cluster_data 가 없으면 빈 배열
  const clusters = inputItem.analysis_result?.cluster_data || [];

  return {
    totalStudents: totalStudents,
    questions: [
      {
        qNum: inputItem.question_number || 1,
        maxScore: maxScore,
        qText: inputItem.question_text || "문제 내용을 불러올 수 없습니다.",
        avgScore: avgScore,
        scoreLabels: scoreLabels,
        scoreData: scoreCounts,
        clusters: clusters,
      },
    ],
  };
}

// ==========================================
// 3. 메인 대시보드 렌더링 (UI)
// ==========================================
function renderDashboard(data) {
  document.getElementById("loading-section").classList.add("hidden");
  document.getElementById("result-section").classList.remove("hidden");
  document.getElementById(
    "total-student-count"
  ).innerText = `${data.totalStudents}명`;

  const grid = document.getElementById("questions-grid");
  grid.innerHTML = "";

  data.questions.forEach((q) => {
    const card = document.createElement("div");
    card.className = "question-card group";
    card.onclick = () => openModal(q);

    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <span class="bg-blue-100 text-blue-700 font-bold px-2 py-1 rounded text-sm">Q${q.qNum}</span>
        </div>
        <p class="text-slate-800 font-bold text-lg mb-2 line-clamp-3 break-keep">
            ${q.qText}
        </p>
    `;
    grid.appendChild(card);
  });
}

// ==========================================
// 4. 모달 (상세 분석 및 차트)
// ==========================================
let histogramChart = null;
let pieChart = null;
let currentClusters = [];

function openModal(qData) {
  const modal = document.getElementById("report-modal");
  currentClusters = qData.clusters || []; // 클러스터 데이터 저장

  // 텍스트 정보
  document.getElementById("modal-q-num").innerText = `Q${qData.qNum}`;
  document.getElementById("modal-q-text").innerText = qData.qText;
  document.getElementById(
    "modal-avg-score"
  ).innerText = `평균: ${qData.avgScore}점 / ${qData.maxScore}점`;

  // 초기화
  resetClusterDetailPanel();

  // 1. 히스토그램 차트
  const ctxHist = document.getElementById("detail-chart").getContext("2d");
  if (histogramChart) histogramChart.destroy();

  histogramChart = new Chart(ctxHist, {
    type: "bar",
    data: {
      labels: qData.scoreLabels,
      datasets: [
        {
          label: "학생 수",
          data: qData.scoreData,
          backgroundColor: "#60a5fa",
          borderRadius: 4,
          barPercentage: 0.6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { stepSize: 1 } },
        x: { grid: { display: false } },
      },
    },
  });

  // 2. 클러스터 파이 차트
  const ctxPie = document.getElementById("cluster-pie-chart").getContext("2d");
  if (pieChart) pieChart.destroy();

  // 클러스터 데이터가 없으면 빈 차트 방지
  if (!currentClusters || currentClusters.length === 0) {
    // 데이터 없음 표시 처리 가능
  }

  const pieLabels = currentClusters.map((c) => `Cluster ${c.cluster_index}`);
  const pieData = currentClusters.map(
    (c) => c.quantitative_metrics?.num_students || 0
  );

  pieChart = new Chart(ctxPie, {
    type: "doughnut",
    data: {
      labels: pieLabels,
      datasets: [
        {
          data: pieData,
          backgroundColor: ["#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe"],
          borderWidth: 0,
          hoverOffset: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: function (context) {
              let label = context.label || "";
              let value = context.parsed || 0;
              return `${label}: ${value}명`;
            },
          },
        },
      },
      onClick: (evt, elements) => {
        if (elements.length > 0) {
          const index = elements[0].index;
          updateClusterDetailPanel(index);
        }
      },
    },
  });

  modal.classList.remove("hidden");
  setTimeout(() => modal.classList.add("open"), 10);
  document.body.style.overflow = "hidden";
}

function resetClusterDetailPanel() {
  document.getElementById("selected-cluster-badge").innerText = "선택 안됨";
  document.getElementById("selected-cluster-badge").className =
    "bg-slate-100 text-slate-500 text-xs px-2 py-1 rounded font-bold";
  document.getElementById("cluster-placeholder").classList.remove("hidden");
  document.getElementById("cluster-content").classList.add("hidden");
}

function updateClusterDetailPanel(index) {
  const data = currentClusters[index];
  if (!data) return;

  document.getElementById("cluster-placeholder").classList.add("hidden");
  document.getElementById("cluster-content").classList.remove("hidden");

  const badge = document.getElementById("selected-cluster-badge");
  badge.innerText = `Cluster ${data.cluster_index}`;
  badge.className =
    "bg-blue-600 text-white text-xs px-2 py-1 rounded font-bold transition-colors";

  // 진단 데이터 채우기
  const diag = data.cognitive_diagnosis || {};

  const fillList = (elementId, items) => {
    const list = document.getElementById(elementId);
    list.innerHTML = "";
    if (!items || items.length === 0) {
      list.innerHTML = "<li class='text-slate-400 italic'>해당 사항 없음</li>";
      return;
    }
    items.forEach((item) => {
      if (elementId === "detail-keywords") {
        const span = document.createElement("span");
        span.className =
          "bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs border border-blue-100";
        span.innerText = item;
        list.appendChild(span);
      } else {
        const li = document.createElement("li");
        li.innerText = item;
        list.appendChild(li);
      }
    });
  };

  fillList("detail-misconceptions", diag.misconceptions);
  fillList("detail-gaps", diag.logical_gaps);
  fillList("detail-keywords", diag.missing_keywords);

  document.getElementById("detail-summary").innerText =
    data.overall_summary || "요약 정보가 없습니다.";
}

function closeModal() {
  const modal = document.getElementById("report-modal");
  modal.classList.remove("open");
  setTimeout(() => {
    modal.classList.add("hidden");
    document.body.style.overflow = "auto";
  }, 300);
}

// ==========================================
// 5. 기타 기능 (과목 추가 등)
// ==========================================
function changeSubject(subjectName) {
  document.getElementById("current-subject").innerText = subjectName;
  const checkIcons = document.querySelectorAll(".check-icon");
  checkIcons.forEach((icon) => {
    if (icon.dataset.subject === subjectName) {
      icon.classList.remove("opacity-0");
      icon.classList.add("opacity-100");
    } else {
      icon.classList.remove("opacity-100");
      icon.classList.add("opacity-0");
    }
  });
}

function openAddSubjectModal() {
  const modal = document.getElementById("add-subject-modal");
  const input = document.getElementById("new-subject-input");
  input.value = "";
  modal.classList.remove("hidden");
  setTimeout(() => {
    modal.classList.add("opacity-100");
    modal.querySelector("div").classList.remove("scale-95");
    modal.querySelector("div").classList.add("scale-100");
    input.focus();
  }, 10);
}

function closeAddSubjectModal() {
  const modal = document.getElementById("add-subject-modal");
  modal.classList.remove("opacity-100");
  modal.querySelector("div").classList.remove("scale-100");
  modal.querySelector("div").classList.add("scale-95");
  setTimeout(() => {
    modal.classList.add("hidden");
  }, 300);
}

function handleAddSubject() {
  const input = document.getElementById("new-subject-input");
  const subjectName = input.value.trim();
  if (!subjectName) {
    alert("과목명을 입력해주세요.");
    return;
  }
  const menuContainer = document.getElementById("subject-menu-container");
  const divider = document.getElementById("subject-divider");
  const newLink = document.createElement("a");
  newLink.href = "#";
  newLink.className =
    "subject-item block px-4 py-3 text-sm text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-colors flex justify-between items-center group/item";
  newLink.onclick = () => changeSubject(subjectName);
  newLink.innerHTML = `
    ${subjectName}
    <i class="fas fa-check text-blue-600 text-xs opacity-0 check-icon" data-subject="${subjectName}"></i>
  `;
  menuContainer.insertBefore(newLink, divider);
  changeSubject(subjectName);
  closeAddSubjectModal();
}
