// Content script - Auto fill OpenAI/Stripe payment forms
(function () {
  "use strict";

  let paymentData = null;

  console.log("✓ Content script loaded");

  // Load payment data from background
  chrome.runtime.sendMessage({ action: "getPaymentData" }, (response) => {
    if (response && response.data) {
      paymentData = response.data;
      console.log("✓ Payment data loaded:", paymentData);
    } else {
      console.log("✗ Failed to load payment data");
    }
  });

  // Listen for fill command from popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "fillForm") {
      console.log("Fill form requested via message");
      fillPaymentForm();
      sendResponse({ success: true });
    }
  });

  // Listen for custom event from Python/Selenium
  window.addEventListener("triggerPaymentFill", () => {
    console.log("✓ Payment fill triggered by custom event");
    console.log("Email from window:", window.chatgptEmail);
    console.log("Payment data status:", paymentData ? "loaded" : "not loaded");

    if (!paymentData) {
      console.log("⚠️  Waiting for payment data to load...");
      setTimeout(() => {
        fillPaymentForm();
      }, 3000);
    } else {
      setTimeout(() => {
        fillPaymentForm();
      }, 2000);
    }
  });

  // Main fill function
  async function fillPaymentForm() {
    if (
      !paymentData ||
      !paymentData.profiles ||
      paymentData.profiles.length === 0
    ) {
      console.log("✗ No payment data available");
      return;
    }

    const profile = paymentData.profiles[0];
    console.log("🚀 Starting payment form fill...");

    // Helper: Set input value with native setter (React/Stripe compatible)
    function setNativeValue(element, value) {
      if (!element || !value) return false;

      try {
        const valueSetter = Object.getOwnPropertyDescriptor(
          element,
          "value"
        )?.set;
        const prototype = Object.getPrototypeOf(element);
        const prototypeValueSetter = Object.getOwnPropertyDescriptor(
          prototype,
          "value"
        )?.set;

        if (valueSetter && valueSetter !== prototypeValueSetter) {
          prototypeValueSetter.call(element, value);
        } else if (valueSetter) {
          valueSetter.call(element, value);
        }

        element.dispatchEvent(new Event("input", { bubbles: true }));
        element.dispatchEvent(new Event("change", { bubbles: true }));
        element.dispatchEvent(new Event("blur", { bubbles: true }));
        return true;
      } catch (e) {
        console.warn("Error setting value:", e);
        return false;
      }
    }

    // Helper: Fill input by ID or selector
    function fillInput(selector, value, label = "") {
      const input = document.querySelector(selector);
      if (input && value) {
        input.focus();
        if (setNativeValue(input, value)) {
          console.log(`✅ ${label || selector}: ${value}`);
          return true;
        }
      } else {
        console.warn(`❌ Not found: ${selector}`);
      }
      return false;
    }

    // Helper: Select dropdown option
    function selectOption(selector, value, label = "") {
      const select = document.querySelector(selector);
      if (select && value) {
        select.value = value;
        select.dispatchEvent(new Event("change", { bubbles: true }));
        console.log(`✅ ${label || selector}: ${value}`);
        return true;
      } else {
        console.warn(`❌ Dropdown not found: ${selector}`);
      }
      return false;
    }

    // Helper: Toggle checkbox
    function toggleCheckbox(selector, shouldCheck = true) {
      const checkbox = document.querySelector(selector);
      if (checkbox) {
        if (checkbox.checked !== shouldCheck) {
          checkbox.click();
          console.log(`✅ Checkbox ${selector}: ${shouldCheck}`);
          return true;
        }
      }
      return false;
    }

    // Step 0: Wait a bit for page to be ready
    await new Promise((r) => setTimeout(r, 500));

    // Step 1: Fill Email
    const email = window.chatgptEmail || profile.contact.email;
    fillInput("input#email", email, "Email");

    // Step 2: Fill Card Information
    // Note: These might be in Stripe iframe and blocked for security
    fillInput("input#cardNumber", profile.payment.cardNumber, "Card Number");
    const expiry = `${
      profile.payment.expireMonth
    } / ${profile.payment.expireYear.slice(-2)}`;
    fillInput("input#cardExpiry", expiry, "Expiry");
    fillInput("input#cardCvc", profile.payment.cvv, "CVC");

    // Step 3: Fill Cardholder Name
    fillInput("input#billingName", profile.contact.fullName, "Cardholder Name");

    await new Promise((r) => setTimeout(r, 300));

    // Step 4: Select Country (this may trigger form reload)
    selectOption("select#billingCountry", "KR", "Country"); // Korea

    // Wait for form to update based on country selection
    await new Promise((r) => setTimeout(r, 800));

    // Step 5: Select Administrative Area (Province/Do Si - Dropdown)
    // For Korea, this is typically a dropdown
    selectOption(
      "select#billingAdministrativeArea",
      "서울특별시",
      "Province/Do Si"
    );

    await new Promise((r) => setTimeout(r, 300));

    // Step 6: Fill Address Details
    fillInput(
      "input#billingAddressLine1",
      profile.billing.street,
      "Address Line 1"
    );
    fillInput("input#billingAddressLine2", "", "Address Line 2"); // Usually empty

    // Step 7: Fill City/Locality
    fillInput("input#billingLocality", profile.billing.city, "City");

    // Step 8: Fill District/Dependent Locality
    fillInput(
      "input#billingDependentLocality",
      profile.billing.district,
      "District"
    );

    // Step 9: Fill Postal Code
    fillInput(
      "input#billingPostalCode",
      profile.billing.postalCode,
      "Postal Code"
    );

    await new Promise((r) => setTimeout(r, 500));

    // Step 10: Handle Checkboxes
    // "I'm purchasing as a business" - usually leave unchecked
    toggleCheckbox("input#purchasingAsBusinessCheckbox", false);

    // Terms of Service - check it
    toggleCheckbox("input#termsOfServiceConsentCheckbox", true);

    // Also try generic checkbox selectors as fallback
    const allCheckboxes = document.querySelectorAll(
      'input[type="checkbox"]:not(#purchasingAsBusinessCheckbox)'
    );
    allCheckboxes.forEach((checkbox) => {
      if (!checkbox.checked && checkbox.id !== "purchasingAsBusinessCheckbox") {
        checkbox.click();
        console.log(`✅ Checked: ${checkbox.id || "checkbox"}`);
      }
    });

    await new Promise((r) => setTimeout(r, 500));

    console.log("✅ Payment form filled successfully!");

    // Step 11: Submit form (optional - uncomment if you want auto-submit)
    // await new Promise(r => setTimeout(r, 1000));
    // const submitButton = document.querySelector('button[type="submit"]');
    // if (submitButton) {
    //   console.log("🎯 Clicking submit button...");
    //   submitButton.click();
    // }
  }
})();
