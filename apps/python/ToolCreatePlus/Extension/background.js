// Background service worker
chrome.runtime.onInstalled.addListener(() => {
  console.log("Auto Payment Filler Extension installed");

  // Load payment data from file
  fetch(chrome.runtime.getURL("payment_data.json"))
    .then((response) => response.json())
    .then((data) => {
      chrome.storage.local.set({ paymentData: data });
      console.log("Payment data loaded");
    })
    .catch((error) => {
      console.error("Error loading payment data:", error);
    });
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getPaymentData") {
    chrome.storage.local.get(["paymentData"], (result) => {
      sendResponse({ data: result.paymentData });
    });
    return true; // Keep message channel open for async response
  }

  if (request.action === "fillForm") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(tabs[0].id, { action: "fillPaymentForm" });
    });
  }
});
