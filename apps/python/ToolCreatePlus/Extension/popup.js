document.addEventListener("DOMContentLoaded", function () {
  const fillButton = document.getElementById("fillButton");
  const statusDiv = document.getElementById("status");

  // Load and display profile info
  chrome.storage.local.get(["paymentData"], function (result) {
    if (result.paymentData && result.paymentData.profiles[0]) {
      const profile = result.paymentData.profiles[0];
      document.getElementById("profileName").textContent = profile.name;
      document.getElementById(
        "profileAddress"
      ).textContent = `${profile.street}, ${profile.district}`;
      document.getElementById(
        "profileCity"
      ).textContent = `${profile.city}, ${profile.postalCode}`;
      document.getElementById("profileCountry").textContent = profile.country;
      document.getElementById("profileCard").textContent =
        profile.cardNumber.slice(-4);
    }
  });

  fillButton.addEventListener("click", function () {
    fillButton.disabled = true;
    fillButton.textContent = "Filling...";
    statusDiv.className = "status";
    statusDiv.style.display = "none";

    // Get current active tab
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      // Send message to content script
      chrome.tabs.sendMessage(
        tabs[0].id,
        { action: "fillForm" },
        function (response) {
          fillButton.disabled = false;
          fillButton.textContent = "Fill Payment Form";

          if (chrome.runtime.lastError) {
            statusDiv.className = "status error";
            statusDiv.textContent =
              "Error: " + chrome.runtime.lastError.message;
          } else if (response && response.success) {
            statusDiv.className = "status success";
            statusDiv.textContent = "Payment form filled successfully!";
          } else {
            statusDiv.className = "status error";
            statusDiv.textContent =
              "Failed to fill form. Make sure you are on a payment page.";
          }

          // Hide status after 3 seconds
          setTimeout(() => {
            statusDiv.style.display = "none";
          }, 3000);
        }
      );
    });
  });
});
