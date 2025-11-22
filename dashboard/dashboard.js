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

  // 유효성 검사
  if (
    !blankFile ||
    !rubricFile ||
    scoreFiles.length === 0 ||
    studentFiles.length === 0
  ) {
    alert("모든 파일을 업로드해주세요.");
    return;
  }

  // UI 전환: 로딩 표시
  document.getElementById("upload-section").classList.add("hidden");
  document.getElementById("loading-section").classList.remove("hidden");

  try {
    // ---------------------------------------------------------
    // [STEP 1] 문제지, 기준표, 점수표 전송 (/question-papers/upload)
    // ---------------------------------------------------------
    const qFormData = new FormData();
    qFormData.append("file", blankFile);
    qFormData.append("rubric", rubricFile);
    for (let i = 0; i < scoreFiles.length; i++) {
      qFormData.append("scoreFiles", scoreFiles[i]);
    }

    console.log("📤 1단계: 문제지/점수표 전송 중...");
    const qRes = await fetch("/question-papers/upload", {
      method: "POST",
      body: qFormData,
    });

    if (!qRes.ok) throw new Error(`1단계 업로드 실패: ${qRes.status}`);
    console.log("✅ 1단계 완료");

    // ---------------------------------------------------------
    // [STEP 2] 답안지 전송 및 분석 요청 (/answer-sheets/upload)
    // ---------------------------------------------------------
    const aFormData = new FormData();
    for (let i = 0; i < studentFiles.length; i++) {
      aFormData.append("files", studentFiles[i]);
    }

    console.log("📤 2단계: 답안지 전송 및 분석 시작...");
    const aRes = await fetch("/answer-sheets/upload", {
      method: "POST",
      body: aFormData,
    });

    if (!aRes.ok) throw new Error(`2단계 분석 요청 실패: ${aRes.status}`);

    const rawServerData = await aRes.json();
    console.log("📥 서버 응답 데이터:", rawServerData);

    // [중요] 서버 데이터(DB 구조)를 프론트엔드 형식으로 변환
    const processedData = processServerData(rawServerData);

    console.log("✅ 데이터 변환 완료:", processedData);
    renderDashboard(processedData);
  } catch (error) {
    console.error("Analysis Failed:", error);
    alert("분석 중 오류가 발생했습니다.\n콘솔을 확인해주세요.");

    // 에러 발생 시 초기 화면으로 복귀
    document.getElementById("loading-section").classList.add("hidden");
    document.getElementById("upload-section").classList.remove("hidden");
  }
}

// ============================================================
// [핵심] 백엔드 데이터(DB구조) -> 프론트엔드 데이터(View구조) 변환기
// ============================================================
function processServerData(rawData) {
  console.log("🔍 [Debug] 서버 데이터 확인:", rawData);

  // 1. 에러 메시지가 왔는지 확인
  if (rawData.error) {
    alert(`서버 오류: ${rawData.error}`);
    return { totalStudents: 0, questions: [] };
  }

  // [중요 수정] 이미 포맷이 완성된 데이터인지 확인
  // rawData 안에 'questions'와 'totalStudents'가 이미 있다면 변환 없이 그대로 반환!
  if (rawData.questions && typeof rawData.totalStudents !== "undefined") {
    console.log("✅ 이미 완성된 대시보드 데이터입니다. 변환을 건너뜁니다.");
    return rawData;
  }

  // ---------------------------------------------------------
  // 아래는 DB 형식(statistics 포함)으로 왔을 때만 실행되는 변환 로직
  // ---------------------------------------------------------

  const data = Array.isArray(rawData) ? rawData[0] : rawData;

  // 데이터 유효성 검사
  if (!data || !data.statistics) {
    console.error("❌ 데이터 형식을 알 수 없습니다:", rawData);
    alert("데이터 형식이 올바르지 않습니다. (콘솔 확인)");
    return { totalStudents: 0, questions: [] };
  }

  // DB 형식 -> 대시보드 형식 변환
  const total = data.statistics.total_answers;
  const correctCount = data.statistics.correct_answers;
  const wrongList = data.wrong_answers || [];
  const maxScore = data.max_score || 10;

  const scoreCounts = [0, 0, 0, 0, 0];

  wrongList.forEach((w) => {
    const s = w.score || 0;
    if (s === 0) scoreCounts[0]++;
    else if (s < 4) scoreCounts[1]++;
    else if (s < 7) scoreCounts[2]++;
    else if (s < 10) scoreCounts[3]++;
    else scoreCounts[4]++;
  });

  scoreCounts[4] += correctCount;

  let sum = 0;
  wrongList.forEach((w) => (sum += w.score || 0));
  sum += correctCount * maxScore;
  const avg = total > 0 ? (sum / total).toFixed(1) : 0;

  const clusters = data.analysis_result?.cluster_data || [];

  return {
    totalStudents: total,
    questions: [
      {
        qNum: data.question_number || 1,
        maxScore: maxScore,
        qText: data.question_text || "문제 내용 없음",
        avgScore: avg,
        scoreLabels: ["0점", "1-3점", "4-6점", "7-9점", "10점"],
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
