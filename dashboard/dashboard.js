document.addEventListener("DOMContentLoaded", () => {
  setupDragAndDrop("blank-drop-zone", "blankFile", handleBlankFileSelect);
  setupDragAndDrop(
    "student-drop-zone",
    "studentFiles",
    handleStudentFileSelect
  );

  document
    .getElementById("blankFile")
    .addEventListener("change", (e) => handleBlankFileSelect(e.target.files));
  document
    .getElementById("studentFiles")
    .addEventListener("change", (e) => handleStudentFileSelect(e.target.files));
  document
    .getElementById("analyze-btn")
    .addEventListener("click", startFinalAnalysis);

  // 모달 닫기 버튼 이벤트
  document
    .getElementById("close-modal-btn")
    .addEventListener("click", closeModal);
  // 모달 배경 클릭 시 닫기
  document.getElementById("report-modal").addEventListener("click", (e) => {
    if (e.target.id === "report-modal") closeModal();
  });

  // [추가됨] 과목 추가 모달 배경 클릭 닫기
  document
    .getElementById("add-subject-modal")
    .addEventListener("click", (e) => {
      if (e.target.id === "add-subject-modal") closeAddSubjectModal();
    });

  // [추가됨] 엔터키로 과목 추가
  document
    .getElementById("new-subject-input")
    .addEventListener("keypress", (e) => {
      if (e.key === "Enter") handleAddSubject();
    });
});

// 1. 드래그 앤 드롭
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

function handleStudentFileSelect(files) {
  if (files.length > 0) {
    document.getElementById("file-count-badge").innerText = files.length;
    document.getElementById("file-count-badge").classList.remove("hidden");
    document.getElementById(
      "student-label"
    ).innerHTML = `<span class="text-blue-600 font-bold">${files.length}개</span> 파일 선택됨`;
  }
}

// 2. 분석 시작
async function startFinalAnalysis() {
  const blank = document.getElementById("blankFile").files.length;
  const students = document.getElementById("studentFiles").files.length;

  if (blank === 0 || students === 0) {
    alert("파일을 모두 업로드해주세요.");
    return;
  }

  document.getElementById("upload-section").classList.add("hidden");
  document.getElementById("loading-section").classList.remove("hidden");

  setTimeout(() => {
    const mockData = generateMockData();
    renderDashboard(mockData);
  }, 1500);
}

// 3. Mock Data
function generateMockData() {
  const studentCount = 30;
  const commonClusterData = [
    {
      cluster_index: 1,
      cognitive_diagnosis: {
        misconceptions: ["다항식의 방정식 해 이해 부족", "부등식 해석의 혼동"],
        logical_gaps: ["가장 기본적 해를 구하는 단계 생략"],
        missing_keywords: ["해 구하기", "부등식 변환", "다항식 성질"],
      },
      pattern_characteristics: {
        specificity: "구체적",
        approach: "정석 풀이",
        error_type: "개념 오류 위주",
      },
      quantitative_metrics: {
        num_students: 8,
        percentage: 27.7,
        relative_length: "평균 문자 수가 중간 정도",
        expected_score_level: "중~하",
      },
      overall_summary:
        "이 클러스터의 학생들은 다항식 방정식과 부등식에 대한 이해가 부족하며, 기본적인 해 구하는 과정에서 논리적 비약이 관찰된다.",
    },
    {
      cluster_index: 2,
      cognitive_diagnosis: {
        misconceptions: [
          "다항식의 근 판별법에 대한 이해 부족",
          "함수의 성질에 대한 혼동",
        ],
        logical_gaps: [
          "근의 개수에 대한 검토 부족",
          "부등식 적용에 대한 명확한 설명 결여",
        ],
        missing_keywords: ["근 판별식", "부등식 해석", "p의 값에 대한 조건"],
      },
      pattern_characteristics: {
        specificity: "구체적",
        approach: "정석 풀이",
        error_type: "개념 오류 위주",
      },
      quantitative_metrics: {
        num_students: 12,
        percentage: 40.4,
        relative_length: "평균적으로 적정한 길이를 유지하나 중복이 있음",
        expected_score_level: "20~30점대에 머무를 가능성이 큼",
      },
      overall_summary:
        "클러스터 2의 학생들은 정석적 접근 방식으로 문제를 해결하려 했으나, 개념적 혼동과 논리적 결손으로 인해 일부 답안에서 충분한 깊이를 가지지 못하였습니다.",
    },
    {
      cluster_index: 3,
      cognitive_diagnosis: {
        misconceptions: [
          "다항식의 근에 대한 이해 부족",
          "f(x)와 x의 관계 해석 오류",
        ],
        logical_gaps: ["함수의 성질을 설명하는 단계 부재"],
        missing_keywords: ["함수의 연속성", "극한 개념"],
      },
      pattern_characteristics: {
        specificity: "구체적",
        approach: "정석 풀이",
        error_type: "개념 오류",
      },
      quantitative_metrics: {
        num_students: 8,
        percentage: 29.8,
        relative_length: "다른 클러스터 대비 보통 수준",
        expected_score_level: "중~하",
      },
      overall_summary:
        "이 클러스터는 다항식의 근을 다루면서 개념적 이해 부족과 특정 단계의 논리적 결손이 나타나며, 정석적인 접근을 따르지만 오류가 빈번하게 발생하는 모습을 보인다.",
    },
    {
      cluster_index: 4,
      cognitive_diagnosis: {
        misconceptions: [
          "함수의 정의역과 치역 개념 혼동",
          "직선의 방정식에 대한 이해 부족",
        ],
        logical_gaps: ["구간 설정 후 함수의 성질을 활용한 설명 단계가 부족"],
        missing_keywords: ["함수의 연속성", "극한", "대수적 조작"],
      },
      pattern_characteristics: {
        specificity: "보통",
        approach: "직관적 접근",
        error_type: "개념 오류 위주",
      },
      quantitative_metrics: {
        num_students: 2,
        percentage: 2.1,
        relative_length: "다른 클러스터에 비해 짧은 편",
        expected_score_level: "대략 상/중",
      },
      overall_summary:
        "클러스터 4의 학생들은 함수에 대한 개념적 오해와 논리적 비약이 있으며, 답안이 구체적이지 않고 간결해 전반적으로 중간 정도의 점수를 예상하게 된다.",
    },
  ];

  return {
    totalStudents: studentCount,
    questions: [
      {
        qNum: 1,
        maxScore: 10,
        qText:
          "이차방정식 x² - 5x + 6 = 0 의 두 근을 구하고 과정을 서술하시오.",
        avgScore: 8.5,
        scoreLabels: ["0점", "1-3점", "4-6점", "7-9점", "10점"],
        scoreData: [2, 1, 3, 4, 20],
        clusters: commonClusterData,
      },
      {
        qNum: 2,
        maxScore: 15,
        qText: "행렬 A = [[1, 2], [3, 4]] 의 역행렬을 구하시오.",
        avgScore: 7.2,
        scoreLabels: ["0점", "1-5점", "6-10점", "11-14점", "15점"],
        scoreData: [5, 8, 4, 3, 10],
        clusters: commonClusterData,
      },
      {
        qNum: 3,
        maxScore: 20,
        qText: "함수 f(x) = sin(x)cos(x) 를 0에서 π까지 적분하시오.",
        avgScore: 5.5,
        scoreLabels: ["0점", "1-7점", "8-14점", "15-19점", "20점"],
        scoreData: [10, 8, 5, 4, 3],
        clusters: commonClusterData,
      },
    ],
  };
}

// 4. 메인 대시보드 렌더링
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

// 5. 모달 상세 보고서 로직
let histogramChart = null;
let pieChart = null;
let currentClusters = [];

function openModal(qData) {
  const modal = document.getElementById("report-modal");
  currentClusters = qData.clusters;

  document.getElementById("modal-q-num").innerText = `Q${qData.qNum}`;
  document.getElementById("modal-q-text").innerText = qData.qText;
  document.getElementById(
    "modal-avg-score"
  ).innerText = `평균: ${qData.avgScore}점 / ${qData.maxScore}점`;

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
    (c) => c.quantitative_metrics.num_students
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

  document.getElementById("cluster-placeholder").classList.add("hidden");
  document.getElementById("cluster-content").classList.remove("hidden");

  const badge = document.getElementById("selected-cluster-badge");
  badge.innerText = `Cluster ${data.cluster_index}`;
  badge.className =
    "bg-blue-600 text-white text-xs px-2 py-1 rounded font-bold transition-colors";

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

  fillList("detail-misconceptions", data.cognitive_diagnosis.misconceptions);
  fillList("detail-gaps", data.cognitive_diagnosis.logical_gaps);
  fillList("detail-keywords", data.cognitive_diagnosis.missing_keywords);

  document.getElementById("detail-summary").innerText = data.overall_summary;
}

function closeModal() {
  const modal = document.getElementById("report-modal");
  modal.classList.remove("open");
  setTimeout(() => {
    modal.classList.add("hidden");
    document.body.style.overflow = "auto";
  }, 300);
}

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

// [추가됨] 과목 추가 관련 함수들
function openAddSubjectModal() {
  const modal = document.getElementById("add-subject-modal");
  const input = document.getElementById("new-subject-input");

  input.value = ""; // 초기화
  modal.classList.remove("hidden");

  // 약간의 지연 후 애니메이션 적용 및 포커스
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

  // 메뉴 컨테이너 찾기
  const menuContainer = document.getElementById("subject-menu-container");
  // 구분선 찾기 (이 앞에 추가하기 위함)
  const divider = document.getElementById("subject-divider");

  // 새 과목 요소 생성 (기존 스타일 그대로 복사)
  const newLink = document.createElement("a");
  newLink.href = "#";
  newLink.className =
    "subject-item block px-4 py-3 text-sm text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-colors flex justify-between items-center group/item";
  newLink.onclick = () => changeSubject(subjectName);
  newLink.innerHTML = `
    ${subjectName}
    <i class="fas fa-check text-blue-600 text-xs opacity-0 check-icon" data-subject="${subjectName}"></i>
  `;

  // DOM에 추가 (구분선 바로 앞에)
  menuContainer.insertBefore(newLink, divider);

  // 추가 후 바로 선택
  changeSubject(subjectName);

  // 모달 닫기
  closeAddSubjectModal();
}
