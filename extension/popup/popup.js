document.addEventListener("DOMContentLoaded", async () => {
  const tabPromptBtn = document.getElementById("tab-prompt-btn");
  const tabTextBtn = document.getElementById("tab-text-btn");
  const tabPrompt = document.getElementById("tab-prompt");
  const tabText = document.getElementById("tab-text");

  const promptInput = document.getElementById("prompt-input");
  const textInput = document.getElementById("text-input");
  const runPromptBtn = document.getElementById("run-prompt-btn");
  const runTextBtn = document.getElementById("run-text-btn");

  const loadingDiv = document.getElementById("loading");
  const errorDiv = document.getElementById("error-msg");
  const resultsDiv = document.getElementById("results");

  const aiResponseBox = document.getElementById("ai-response-box");
  const aiResponseText = document.getElementById("ai-response-text");
  const claimsList = document.getElementById("claims-list");

  const metricTotal = document.getElementById("metric-total");
  const metricSupported = document.getElementById("metric-supported");
  const metricHallucinated = document.getElementById("metric-hallucinated");
  const metricUncertain = document.getElementById("metric-uncertain");

  // Tab switching
  tabPromptBtn.addEventListener("click", () => {
    tabPromptBtn.classList.add("active");
    tabTextBtn.classList.remove("active");
    tabPrompt.classList.add("active");
    tabText.classList.remove("active");
  });

  tabTextBtn.addEventListener("click", () => {
    tabTextBtn.classList.add("active");
    tabPromptBtn.classList.remove("active");
    tabText.classList.add("active");
    tabPrompt.classList.remove("active");
  });

  // Check context menu storage
  const storageData = await chrome.storage.local.get("latest_report");
  if (storageData.latest_report) {
    const reportObj = storageData.latest_report;
    if (reportObj.loading) {
      showLoading("Processing context menu selection...");
    } else if (reportObj.error) {
      showError(reportObj.error);
    } else if (reportObj.data) {
      renderReport(reportObj.data);
    }
  }

  // Handle Prompt Submission
  runPromptBtn.addEventListener("click", () => {
    const prompt = promptInput.value.trim();
    if (!prompt) {
      showError("Please enter a prompt.");
      return;
    }

    hideError();
    showLoading("Generating response & verifying Wikipedia evidence...");
    resultsDiv.classList.add("hidden");

    chrome.runtime.sendMessage({ action: "verify_prompt", prompt }, (response) => {
      hideLoading();
      if (!response || !response.success) {
        showError(response?.error || "Failed to connect to backend server. Make sure server.py is running on http://localhost:8000.");
        return;
      }
      renderReport(response.data, true);
    });
  });

  // Handle Text Audit Submission
  runTextBtn.addEventListener("click", () => {
    const text = textInput.value.trim();
    if (!text) {
      showError("Please enter text to audit.");
      return;
    }

    hideError();
    showLoading("Resolving atomic claims & searching Wikipedia...");
    resultsDiv.classList.add("hidden");

    chrome.runtime.sendMessage({ action: "verify_text", text }, (response) => {
      hideLoading();
      if (!response || !response.success) {
        showError(response?.error || "Failed to connect to backend server. Make sure server.py is running on http://localhost:8000.");
        return;
      }
      renderReport(response.data, false);
    });
  });

  function showLoading(msg) {
    loadingDiv.classList.remove("hidden");
    document.getElementById("loading-text").innerText = msg;
  }

  function hideLoading() {
    loadingDiv.classList.add("hidden");
  }

  function showError(msg) {
    errorDiv.innerText = msg;
    errorDiv.classList.remove("hidden");
  }

  function hideError() {
    errorDiv.classList.add("hidden");
  }

  function renderReport(report, isPromptMode = false) {
    resultsDiv.classList.remove("hidden");

    if (isPromptMode && (report.verified_answer || report.text)) {
      aiResponseBox.classList.remove("hidden");
      aiResponseText.innerText = report.verified_answer || report.corrected_text || report.text;
    } else {
      aiResponseBox.classList.add("hidden");
    }


    const summary = report.summary || { supported: 0, hallucinated: 0, uncertain: 0 };
    metricTotal.innerText = report.claims_count || (report.results ? report.results.length : 0);
    metricSupported.innerText = summary.supported || 0;
    metricHallucinated.innerText = summary.hallucinated || 0;
    metricUncertain.innerText = summary.uncertain || 0;

    claimsList.innerHTML = "";
    if (!report.results || report.results.length === 0) {
      claimsList.innerHTML = "<p style='font-size:12px; color:#5f6368;'>No factual claims found to verify.</p>";
      return;
    }

    report.results.forEach((item, index) => {
      const card = document.createElement("div");
      card.className = "claim-card";

      const verdictClass = item.verdict || "UNCERTAIN";
      
      let sourceLinkHtml = "";
      if (item.source_url) {
        sourceLinkHtml = `<div class="source-link">🔗 <a href="${escapeHtml(item.source_url)}" target="_blank" rel="noopener">${escapeHtml(item.source_title || 'Wikipedia Article')}</a></div>`;
      }

      let quoteHtml = "";
      if (item.quoted_evidence) {
        quoteHtml = `<div class="evidence-box"><strong>Quote:</strong> "${escapeHtml(item.quoted_evidence)}"</div>`;
      }

      card.innerHTML = `
        <div class="claim-title">${index + 1}. ${escapeHtml(item.claim)}</div>
        <span class="badge ${verdictClass}">${verdictClass}</span>
        <div class="claim-explanation">${escapeHtml(item.explanation)}</div>
        ${quoteHtml}
        ${sourceLinkHtml}
      `;
      claimsList.appendChild(card);
    });
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
});
