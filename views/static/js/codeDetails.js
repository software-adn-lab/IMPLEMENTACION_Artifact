document.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);
    const component = params.get("component");
    const startLine = parseInt(params.get("startLine"), 10);
    // Ensure endLine has a value, using startLine as fallback.
    const endLine = parseInt(params.get("endLine"), 10) || startLine;
    
    const projectName = params.get("projectName");
    const codeContentEl = document.getElementById("codeContent");
    const fileNameEl = document.getElementById("fileName");

    if (!component || !projectName) {
        codeContentEl.textContent = "Error: Component or project name was not provided.";
        return;
    }

    const repoPath = projectName.replace("_", "/");

    // Try to fetch code from GitHub, first with 'main' and then with 'master'.
    async function fetchCodeWithBranchFallback(branches = ['main', 'master']) {
        let lastError = null;
        let brokeLoop = false;
        for (const branch of branches) {
            const githubRawUrl = `https://raw.githubusercontent.com/${repoPath}/${branch}/${component}`;
            try {
                const response = await fetch(githubRawUrl);
                if (response.ok) {
                    return await response.text(); // Success, return the code.
                }
                lastError = new Error(`Unsuccessful response (status ${response.status}) from branch '${branch}'`);
                if (response.status !== 404) {
                    brokeLoop = true;
                    break; // If it is not a 404, stop retrying.
                }
            } catch (error) {
                lastError = error; // Network error, etc.
                console.warn(`Failed to fetch from branch '${branch}':`, error.message);
                brokeLoop = true;
                break; // Stop on network error.
            }
        }
        // If the loop broke early, throw the specific error that caused it.
        if (brokeLoop) {
            throw lastError;
        }
        // If loop finished, all branches returned 404.
        throw new Error(`Could not find the file on GitHub. Tried branches '${branches.join("' and '")}'. Verify repository name, file path, and branch name.`);
    }

    fileNameEl.textContent = component.split("/").pop();

    try {
        const code = await fetchCodeWithBranchFallback();

        const lines = code.split('\n');
        let formattedCode = '';

        lines.forEach((line, index) => {
            const lineNumber = index + 1;
            const isHighlighted = lineNumber >= startLine && lineNumber <= endLine;
            
            const lineClass = isHighlighted ? 'highlight' : '';

            // Wrap each line in a span with 'line-wrapper' for better style control.
            formattedCode += `<span class="line-wrapper ${lineClass}"><span class="line-number">${lineNumber}</span>${escapeHtml(line)}</span>\n`;
        });

        codeContentEl.innerHTML = formattedCode;

    } catch (error) {
        console.error("Error loading code:", error);
        codeContentEl.textContent = `Error loading code: ${error.message}`;
    }
});

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}