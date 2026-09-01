// Setup Context Menu on Install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "verify-hallucination",
    title: "🔍 Verify with Hallucination Detector",
    contexts: ["selection"]
  });
  console.log("AI Hallucination Detector extension installed.");
});

// Handle Context Menu Item Click
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "verify-hallucination" && info.selectionText) {
    const selectedText = info.selectionText.trim();
    if (!selectedText) return;

    try {
      // Save pending status
      await chrome.storage.local.set({
        latest_report: {
          loading: true,
          text: selectedText
        }
      });

      const response = await fetch("http://localhost:8000/api/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: selectedText })
      });

      if (!response.ok) {
        throw new Error(`Server status ${response.status}`);
      }

      const report = await response.json();
      await chrome.storage.local.set({
        latest_report: {
          loading: false,
          data: report
        }
      });
      console.log("Verification complete for selected text.");

    } catch (err) {
      console.error("Verification failed:", err);
      await chrome.storage.local.set({
        latest_report: {
          loading: false,
          error: "Failed to connect to backend server. Make sure server.py is running on http://localhost:8000."
        }
      });
    }
  }
});

// Handle messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "verify_prompt") {
    (async () => {
      try {
        const res = await fetch("http://localhost:8000/api/generate-and-verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: message.prompt })
        });
        const data = await res.json();
        sendResponse({ success: true, data });
      } catch (err) {
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true; // Keep message channel open for async response
  } else if (message.action === "verify_text") {
    (async () => {
      try {
        const res = await fetch("http://localhost:8000/api/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: message.text })
        });
        const data = await res.json();
        sendResponse({ success: true, data });
      } catch (err) {
        sendResponse({ success: false, error: err.message });
      }
    })();
    return true;
  }
});
