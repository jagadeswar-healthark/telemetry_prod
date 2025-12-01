
/* -------------------------
   Element refs
   ------------------------- */
const toggleButton = document.getElementById("toggle-upload");
const uploadForm = document.getElementById("upload-form");
const fileUpload = document.getElementById("file-upload");
const fileInfo = document.getElementById("file-info");
const fileName = document.getElementById("file-name");
const fileSize = document.getElementById("file-size");
const successMsg = document.getElementById("success-msg");
const processing = document.getElementById("processing");
const countdownElement = document.getElementById("countdown"); // uses <span id="countdown">
const resultsContainer = document.getElementById("results-container");
const dropArea = document.getElementById("drop-area");
const homepageImage = document.getElementById("homepage-image");
const pageTitle = document.getElementById("page-title");
const scrollToTopBtn = document.getElementById("scroll-to-top");

let countdownInterval = null; // used for countdown
let remainingSecondsDefault = 180; // default 3 minutes

/* -------------------------
   Dropdown Toggle Functionality - Native Details Element
   ------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  // Handle arrow rotation for details/summary elements
  const detailsElements = document.querySelectorAll('details');
  
  detailsElements.forEach(details => {
    details.addEventListener('toggle', function() {
      const arrow = this.querySelector('.summary-arrow');
      if (arrow) {
        if (this.open) {
          arrow.style.transform = 'rotate(180deg)';
        } else {
          arrow.style.transform = 'rotate(0deg)';
        }
      }
    });
  });
});

/* -------------------------
   Scroll to Top Button
   ------------------------- */
if (scrollToTopBtn) {
  window.addEventListener('scroll', () => {
    if (window.pageYOffset > 300) {
      scrollToTopBtn.style.opacity = '1';
      scrollToTopBtn.style.pointerEvents = 'auto';
    } else {
      scrollToTopBtn.style.opacity = '0';
      scrollToTopBtn.style.pointerEvents = 'none';
    }
  });

  scrollToTopBtn.addEventListener('click', () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });
}

/* -------------------------
   Drag and Drop functionality
   ------------------------- */
if (dropArea) {
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
  });

  function highlight(e) {
    const label = dropArea.querySelector('label');
    if (label) {
      label.classList.add('bg-red-50');
      label.style.borderColor = 'rgb(239, 68, 68)';
    }
  }

  function unhighlight(e) {
    const label = dropArea.querySelector('label');
    if (label) {
      label.classList.remove('bg-red-50');
      label.style.borderColor = 'rgba(248, 113, 113, 0.6)';
    }
  }

  dropArea.addEventListener('drop', handleDrop, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
      fileUpload.files = files;
      handleFiles(files);
    }
  }

  function handleFiles(files) {
    const file = files[0];
    if (file) {
      if (fileName) fileName.textContent = file.name;
      if (fileSize) fileSize.textContent = (file.size / (1024 * 1024)).toFixed(1) + " MB";
      if (fileInfo) fileInfo.classList.remove("hidden");
      if (successMsg) successMsg.classList.remove("hidden");
    }
  }
}

/* -------------------------
   Helpers: toggle panel & file selection
   ------------------------- */
if (toggleButton) {
  toggleButton.addEventListener("click", () => {
    uploadForm.classList.toggle("hidden");

    // Hide homepage image and show title when menu is opened
    if (!uploadForm.classList.contains("hidden")) {
      if (homepageImage) homepageImage.classList.add("hidden");
      if (pageTitle) pageTitle.classList.remove("hidden");
      // smooth scroll into view
      uploadForm.scrollIntoView({ behavior: "smooth" });
    }
  });
}

if (fileUpload) {
  fileUpload.addEventListener("change", () => {
    const file = fileUpload.files[0];

    if (file) {
      if (fileName) fileName.textContent = file.name;
      if (fileSize) fileSize.textContent = (file.size / (1024 * 1024)).toFixed(1) + " MB";
      if (fileInfo) fileInfo.classList.remove("hidden");
      if (successMsg) successMsg.classList.remove("hidden");
    }
  });
}

function clearFile() {
  if (fileUpload) fileUpload.value = "";
  if (fileInfo) fileInfo.classList.add("hidden");
  if (successMsg) successMsg.classList.add("hidden");
}

/* -------------------------
   Countdown logic
   ------------------------- */
function formatMMSS(totalSeconds) {
  const mins = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const secs = String(totalSeconds % 60).padStart(2, "0");
  return `${mins}:${secs}`;
}

function setCountdownStyle(totalSeconds) {
  // default style
  if (!countdownElement) return;
  countdownElement.classList.remove("text-yellow-600", "text-red-600", "blink");
  countdownElement.style.transition = "color 0.2s ease";

  if (totalSeconds <= 10) {
    // critical - blinking red text
    countdownElement.classList.add("text-red-600", "blink");
    // we will implement blink via CSS class below
  } else if (totalSeconds <= 30) {
    // warning
    countdownElement.classList.add("text-yellow-600");
  } else {
    // normal (red-ish default from your HTML)
    countdownElement.classList.remove("text-yellow-600", "text-red-600", "blink");
  }
}

// Add blink CSS dynamically (so drop-in works)
(function addBlinkCSS() {
  const style = document.createElement("style");
  style.textContent = `
    .blink {
      animation: blinkAnim 1s steps(1, start) infinite;
    }
    @keyframes blinkAnim {
      50% { opacity: 0; }
    }
  `;
  document.head.appendChild(style);
})();

function startCountdown(seconds = remainingSecondsDefault) {
  // clear previous if any
  stopCountdown();

  let remaining = Math.max(0, Math.floor(seconds));
  if (!countdownElement) return;

  countdownElement.textContent = formatMMSS(remaining);
  setCountdownStyle(remaining);

  // Start stage animations
  animateProcessingStages();

  countdownInterval = setInterval(() => {
    remaining = remaining - 1;
    if (remaining < 0) remaining = 0;

    countdownElement.textContent = formatMMSS(remaining);
    setCountdownStyle(remaining);

    if (remaining <= 0) {
      // time's up — stop countdown and optionally take action
      stopCountdown();
      // leave spinner visible unless you prefer to auto-hide
      // you could show a message here if needed
    }
  }, 1000);
}

function stopCountdown() {
  if (countdownInterval) {
    clearInterval(countdownInterval);
    countdownInterval = null;
  }
  // Reset stage animations
  resetProcessingStages();
}

/* -------------------------
   Processing Stages Animation
   ------------------------- */
function animateProcessingStages() {
  const stages = [
    { box: 'stage-1', arrow: 'arrow-1', delay: 500 },
    { box: 'stage-2', arrow: 'arrow-2', delay: 1000 },
    { box: 'stage-3', arrow: 'arrow-3', delay: 1500 },
    { box: 'stage-4', arrow: 'arrow-4', delay: 2000 },
    { box: 'stage-5', arrow: null, delay: 2500 }
  ];

  stages.forEach(stage => {
    setTimeout(() => {
      const boxElement = document.getElementById(stage.box);
      if (boxElement) {
        boxElement.classList.add('show');
      }
      if (stage.arrow) {
        setTimeout(() => {
          const arrowElement = document.getElementById(stage.arrow);
          if (arrowElement) {
            arrowElement.classList.add('show');
          }
        }, 200);
      }
    }, stage.delay);
  });
}

function resetProcessingStages() {
  for (let i = 1; i <= 5; i++) {
    const boxElement = document.getElementById(`stage-${i}`);
    if (boxElement) {
      boxElement.classList.remove('show');
    }
    if (i < 5) {
      const arrowElement = document.getElementById(`arrow-${i}`);
      if (arrowElement) {
        arrowElement.classList.remove('show');
      }
    }
  }
}

/* -------------------------
   Table population helper (kept from your code)
   ------------------------- */
function populateTable(data, tableId) {
  const tableContainer = document.getElementById(`${tableId}-container`);
  const tableHeader = document.getElementById(`${tableId}-header`);
  const tableBody = document.getElementById(`${tableId}-body`);

  if (!tableContainer || !tableHeader || !tableBody) return;

  tableHeader.innerHTML = "";
  tableBody.innerHTML = "";

  if (!Array.isArray(data) || data.length === 0) {
    tableContainer.classList.add("hidden");
    return;
  }

  tableContainer.classList.remove("hidden");

  const headers = Object.keys(data[0] || {});

  // header row
  headers.forEach(header => {
    const th = document.createElement("th");
    th.className = "border border-gray-300 px-4 py-2 text-left";
    th.textContent = header;
    tableHeader.appendChild(th);
  });

  const groupByDate = (arr, dateField) => {
    const grouped = {};
    arr.forEach(row => {
      const date = row[dateField];
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(row);
    });
    return grouped;
  };

  // Handle grouped tables
  if (tableId === "door-table" || tableId === "power-table") {
    const dateField = "Date of Event";
    const totalField = tableId === "door-table" ? "No of Door Openings" : "Total Events in Day";
    const grouped = groupByDate(data, dateField);

    for (const date in grouped) {
      const rows = grouped[date];
      // assume last row contains summary 'total' field
      const total = rows[rows.length - 1] ? rows[rows.length - 1][totalField] : "";

      rows.forEach((row, index) => {
        const tr = document.createElement("tr");
        headers.forEach(header => {
          const td = document.createElement("td");
          td.className = "border border-gray-300 px-4 py-2";

          if (header === dateField) {
            td.textContent = index === 0 ? row[header] : "";
          } else if (header === totalField) {
            td.textContent = index === 0 ? total : "";
          } else {
            td.textContent = row[header] === undefined ? "" : row[header];
          }

          tr.appendChild(td);
        });
        tableBody.appendChild(tr);
      });
    }
  } else {
    // Default table
    data.forEach(row => {
      const tr = document.createElement("tr");
      headers.forEach(header => {
        const td = document.createElement("td");
        td.className = "border border-gray-300 px-4 py-2";
        td.textContent = row[header] === undefined ? "" : row[header];
        tr.appendChild(td);
      });
      tableBody.appendChild(tr);
    });
  }
}

/* -------------------------
   UI: display results (kept and slightly hardened)
   ------------------------- */
function displayResults(data) {
  const container = document.createElement('div');

  // Title
  if (data.title) {
    const titleSection = document.createElement('div');
    titleSection.className = "mb-6";
    titleSection.innerHTML = `<h2 class="text-2xl font-bold text-red-700 mb-4">${data.title}</h2>`;
    container.appendChild(titleSection);
  }

  // File Type
  if (data.file_type) {
    const ft = document.createElement('div');
    ft.className = "mb-6";
    ft.innerHTML = `<h3 class="text-xl font-semibold text-red-600 mb-2">File Type</h3>${String(data.file_type).replace(/\n/g, '<br>')}<p class="text-gray-800"></p>`;
    container.appendChild(ft);
  }

  // Note
  if (data.note) {
    const ns = document.createElement('div');
    ns.className = "mb-6";
    ns.innerHTML = `<h3 class="text-xl font-semibold text-red-600 mb-2">Note</h3>${String(data.note).replace(/\n/g, '<br>')}<p class="text-gray-800"></p>`;
    container.appendChild(ns);
  }

  // Observation
  if (data.observation) {
    const obs = document.createElement('div');
    obs.className = "mb-6";
    obs.innerHTML = `<h3 class="text-xl font-semibold text-red-600 mb-2">Observation</h3>${String(data.observation).replace(/\n/g, '<br>')}<p class="text-gray-800"></p>`;
    container.appendChild(obs);
  }

  // Charts wrapper
  const chartsWrapper = document.createElement('div');
  chartsWrapper.className = "mt-8";

  // Images-based charts you returned as base64/url
  if (data.sensor_values) {
    const h = document.createElement('h3'); h.className = "text-xl font-bold mb-2 text-red-700"; h.textContent = "Sensor Values";
    const d = document.createElement('div');
    const img = document.createElement('img'); img.src = data.sensor_values; img.alt = "Sensor Values Plot"; img.style.maxWidth = "100%";
    d.appendChild(img); chartsWrapper.appendChild(h); chartsWrapper.appendChild(d);
  }

  if (data.sensor_trends) {
    const h = document.createElement('h3'); h.className = "text-xl font-bold mb-2 text-red-700"; h.textContent = "Sensor Trends";
    const d = document.createElement('div');
    const img = document.createElement('img'); img.src = data.sensor_trends; img.alt = "Sensor Trends Plot"; img.style.maxWidth = "100%";
    d.appendChild(img); chartsWrapper.appendChild(h); chartsWrapper.appendChild(d);
  }

  if (data.trend_issues) {
    const h = document.createElement('h3'); h.className = "text-xl font-bold mb-2 text-red-700"; h.textContent = "Trend Issues";
    const d = document.createElement('div');
    const img = document.createElement('img'); img.src = data.trend_issues; img.alt = "Trend Issues Plot"; img.style.maxWidth = "100%";
    d.appendChild(img); chartsWrapper.appendChild(h); chartsWrapper.appendChild(d);
  }

  // Vega charts (if provided)
  try {
    if (data.door_events) {
      const h = document.createElement('h3'); h.className = "text-xl font-bold mb-2 text-red-700"; h.textContent = "Door Openings";
      const d = document.createElement('div');
      chartsWrapper.appendChild(h); chartsWrapper.appendChild(d);
      if (typeof vegaEmbed === "function") vegaEmbed(d, data.door_events, { width: 400, height: 250 });
    }
    if (data.trend_issues_altair) {
      const h = document.createElement('h3'); h.className = "text-xl font-bold mb-2 text-red-700"; h.textContent = "Trend Issues";
      const d = document.createElement('div');
      chartsWrapper.appendChild(h); chartsWrapper.appendChild(d);
      if (typeof vegaEmbed === "function") vegaEmbed(d, data.trend_issues_altair, { width: 400, height: 250 });
    }
    if (data.tc10_chart) {
      const h = document.createElement('h3'); h.className = "text-xl font-bold mb-2 text-red-700"; h.textContent = "TC10 Plot";
      const d = document.createElement('div'); d.id = "tc10-chart-div";
      chartsWrapper.appendChild(h); chartsWrapper.appendChild(d);
      if (typeof vegaEmbed === "function") vegaEmbed(d, data.tc10_chart, { width: 400, height: 250 });
    }
    if (data.tc1_tc6_chart) {
      const h = document.createElement('h3'); h.className = "text-xl font-bold mb-2 text-red-700"; h.textContent = "TC1 and TC6 Plot";
      const d = document.createElement('div'); d.id = "tc1-tc6-chart-div";
      chartsWrapper.appendChild(h); chartsWrapper.appendChild(d);
      if (typeof vegaEmbed === "function") vegaEmbed(d, data.tc1_tc6_chart, { width: 400, height: 250 });
    }
  } catch (err) {
    console.warn("Vega embed failed: ", err);
  }

  container.appendChild(chartsWrapper);

  // Additional summary sections (if present)
  const otherKeys = ['Summary: Events', '🧠 Root Cause Explanation:'];
  otherKeys.forEach((key, idx) => {
    if (!data[key]) return;
    const section = document.createElement('div');
    section.className = "mb-6";
    const sectionTitle = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

    if (typeof data[key] === 'string') {
      section.innerHTML = `<h3 class="text-xl font-semibold text-red-600 mb-2">${sectionTitle}</h3><p class="text-gray-800">${data[key].replace(/\n/g, '<br>')}</p>`;
    } else if (Array.isArray(data[key])) {
      section.innerHTML = `<h3 class="text-xl font-semibold text-red-600 mb-2">${sectionTitle}</h3><ul class="list-disc pl-6">${data[key].map(item => `<li>${item}</li>`).join('')}</ul>`;
    } else {
      section.innerHTML = `<h3 class="text-xl font-semibold text-red-600 mb-2">${sectionTitle}</h3><pre class="text-gray-800">${JSON.stringify(data[key], null, 2)}</pre>`;
    }

    container.appendChild(section);

    if (idx < otherKeys.length - 1) {
      const divider = document.createElement('hr');
      divider.className = "my-8 border-t border-gray-300 mx-4";
      container.appendChild(divider);
    }
  });

  // Replace results container
  resultsContainer.innerHTML = '';
  resultsContainer.appendChild(container);

  // Download button
  const downloadWordButton = document.createElement('button');
  downloadWordButton.className = "bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-full mt-6";
  downloadWordButton.textContent = "Download Results";
  downloadWordButton.addEventListener('click', () => downloadResultsWord(data));
  resultsContainer.appendChild(downloadWordButton);

  resultsContainer.classList.remove("hidden");
  resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

/* -------------------------
   Download results as Word
   ------------------------- */
function downloadResultsWord(data) {
  fetch('/download_word', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  .then(response => {
    if (!response.ok) throw new Error('Failed to generate Word file');
    return response.blob();
  })
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `telemetry_results_${new Date().toISOString().split('T')[0]}.docx`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  })
  .catch(error => {
    alert('Error downloading Word file.');
    console.error(error);
  });
}

/* -------------------------
   Upload form submit handler
   ------------------------- */
const uploadFormElement = document.getElementById("upload-form");
if (uploadFormElement) {
  uploadFormElement.addEventListener("submit", function (e) {
    e.preventDefault();
    const file = fileUpload ? fileUpload.files[0] : null;

    if (!file) {
      alert("Please upload a file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    // Show spinner and start countdown
    if (processing) processing.classList.remove("hidden");
    if (resultsContainer) resultsContainer.classList.add("hidden");

    // start 3-min countdown (or use different seconds by passing param)
    startCountdown(remainingSecondsDefault);

    fetch('/process', {
      method: 'POST',
      body: formData
    })
    .then(async response => {
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || "Failed to process file");
      }
      return data;
    })
    .then(data => {
      // when main processing done - stop countdown
      stopCountdown();
      if (processing) processing.classList.add("hidden");

      // Fetch and merge visualizations before displaying results
      fetch('/visualizations')
        .then(response => response.json())
        .then(charts => {
          // Merge chart data into summary data
          if (charts.sensor_values) data.sensor_values = charts.sensor_values;
          if (charts.sensor_trends) data.sensor_trends = charts.sensor_trends;
          if (charts.trend_issues) data.trend_issues = charts.trend_issues;
          if (charts['door events']) data.door_events = charts['door events'];
          if (charts['trend_issues_altair']) data.trend_issues_altair = charts['trend_issues_altair'];
          if (charts['tc10_chart']) data.tc10_chart = charts['tc10_chart'];
          if (charts['tc1_tc6_chart']) data.tc1_tc6_chart = charts['tc1_tc6_chart'];

          // Display
          displayResults(data);

          // Populate tables (if present)
          try { if (data.absolute_df) populateTable(data.absolute_df, "absolute-table"); } catch(e){console.warn(e);}
          try { if (data.trend_df) populateTable(data.trend_df, "trend-table"); } catch(e){console.warn(e);}
          try { if (data.door_df) populateTable(data.door_df, "door-table"); } catch(e){console.warn(e);}
          try { if (data.power_df) populateTable(data.power_df, "power-table"); } catch(e){console.warn(e);}
          try { if (data.ref_df) populateTable(data.ref_df, "ref-table"); } catch(e){console.warn(e);}

        })
        .catch(error => {
          // If chart fetch fails, just show summary
          displayResults(data);
          console.warn("Failed to fetch visualizations:", error);
        });
    })
    .catch(error => {
      stopCountdown();
      if (processing) processing.classList.add("hidden");
      alert(error.message || "Processing failed");
      console.error(error);
    });
  });
}

/* -------------------------
   Optional: ensure countdown stops when user navigates away from page
   ------------------------- */
window.addEventListener("beforeunload", () => {
  stopCountdown();
});