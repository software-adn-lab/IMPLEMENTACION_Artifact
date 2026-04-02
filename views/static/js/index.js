// ========================================
// DOM ELEMENT REFERENCES
// ========================================
const form = document.getElementById("connectionForm");
const messageBox = document.getElementById("message");
const isPrivateCheckbox = document.getElementById("isPrivate");
const tokenField = document.getElementById("tokenField");
const tokenInput = document.getElementById("token");
const toggleHint = document.getElementById("toggleHint");


// ========================================
// TOGGLE: SHOW / HIDE TOKEN FIELD
// ========================================
isPrivateCheckbox.addEventListener("change", function () {

    const isPrivate = this.checked;

    tokenField.classList.toggle("is-hidden", !isPrivate);
    tokenInput.required = isPrivate;

    toggleHint.textContent = isPrivate
        ? "Private repository — authorization token is required"
        : "Public repository — only the project name is required";

});


// ========================================
// FORM SUBMISSION
// ========================================
form.addEventListener("submit", async function (event) {

    event.preventDefault();

    // Get values
    const project_key = document.getElementById("project_key").value.trim();
    const isPrivate = isPrivateCheckbox.checked;
    const token = isPrivate ? tokenInput.value.trim() : "";

    // Loading message
    messageBox.classList.remove("is-hidden");
    messageBox.className = "msg";
    messageBox.textContent = "Checking SonarCloud connection...";

    try {

        // Backend request
        const response = await fetch("/api/test-connection", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                project_key: project_key,
                token: token,
                language: "python"
            })
        });

        const data = await response.json();

        // Show server message
        messageBox.classList.remove("is-hidden");
        messageBox.className = `msg ${data.success ? "ok" : "error"}`;
        messageBox.textContent = data.message || "Invalid server response.";

        // If analysis was successful
        if (data.success && data.antipattern_result) {

            // Save results for the charts page
            sessionStorage.setItem(
                "antipatternResult",
                JSON.stringify(data.antipattern_result)
            );
            // Save project name and language for the results page
            sessionStorage.setItem("projectName", project_key);
            sessionStorage.setItem("language", "python"); // Or use a variable if you define it dynamically
            sessionStorage.setItem("isRepoPrivate", isPrivate);
            // Redirect to the results page
            setTimeout(() => {
                window.location.href = "/general-report";
            }, 500);
        }

    } catch (error) {

        console.error("Connection error:", error);

        messageBox.classList.remove("is-hidden");
        messageBox.className = "msg error";
        messageBox.textContent =
            "Could not connect to the server. Make sure you are accessing from http://127.0.0.1:5000";

    }

});