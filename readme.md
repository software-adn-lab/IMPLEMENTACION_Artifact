# Design Antipattern Detector Based on SonarCloud Code Smells

## 1. Overview

This tool is a web application that analyzes SonarCloud projects, identifies `Code Smells`, and detects high-level `Design Antipatterns` such as BLOB and Spaghetti Code.

It provides a clear and detailed visualization of results to help developers understand and improve code quality.

## 2. Key Features

- **SonarCloud integration:** Uses the SonarCloud API to fetch `Code Smells` from a specific project.
- **Public and private repository support:** Supports both open-source and private projects that require token authentication.
- **Smell mapping:** Translates SonarCloud `Code Smells` to an intermediate classification (`Moha Smells`) using an Excel configuration matrix (`Mapeo.xlsx`).
- **Antipattern detection:** Detects 4 antipattern types (BLOB, Swiss Army Knife, Functional Decomposition, Spaghetti Code) based on `Moha Smells` combinations.
- **Interactive dashboard:** Provides a general report with a visual summary of each antipattern status.
- **Detailed reports:** Generates individual views per antipattern with met conditions and related smells.
- **Dynamic filters:** Detail tables include Excel-style filters per column.
- **Code viewer:** Highlights source lines related to each smell (available only for public GitHub repositories).

## 3. Prerequisites

Before running the application, make sure you have:

- **Python 3.8 or higher**
- **`pip`** (Python package manager)
- **A project already analyzed in SonarCloud**
- **(Optional) A SonarCloud user token** for private repository analysis. You can generate it in SonarCloud under `My Account > Security > Generate Tokens`.

## 4. Installation and Run

1. **Clone the repository:**
   ```bash
   git clone <REPOSITORY_URL>
   cd ArtefactoImplementacionDEMO
   ```

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate

   pip install -r requirements.txt
   ```
   Ensure `requirements.txt` includes `Flask`, `requests`, and `openpyxl`.

3. **Run the Flask app:**
   ```bash
   flask run
   ```

4. **Open the app:**
   `http://127.0.0.1:5000`

## 5. User Guide

### Step 1: Home Page (Analysis)

1. **Project Name (Project Key):** Enter your SonarCloud project key. You can find it in your project URL (`.../summary?id=MY_PROJECT_KEY`) or project information panel.
2. **Private repository:** Enable this if your SonarCloud project is private.
3. **Authorization token:** If private, paste your SonarCloud user token.
4. Click **"Verify project"**. The app will display progress while connecting and processing data.

### Step 2: General Report

After analysis, you are redirected to the main dashboard.

- You will see one card per antipattern.
- Each card displays a **circular chart** showing how many conditions (`Moha Smells`) are met.
  - **Red:** All conditions met. Antipattern is **detected**.
  - **Yellow:** At least half the conditions met. Antipattern is **likely**.
  - **Green:** Fewer than half the conditions met. Antipattern is **not detected**.

### Step 3: Individual Report

This view provides a detailed analysis for one antipattern.

- A visual summary and text conclusion are shown at the top.
- A detailed table lists contributing `Code Smells`.
  - **Columns:** `Moha Smell`, `Sonar Rule`, `Line`, `Severity`, `Location`, `View in SonarCloud`.
  - **Filters:** Each column supports dropdown filtering.
  - **Links:**
    - `Location`: links to the code viewer for public repositories.
    - `View in SonarCloud`: opens the corresponding SonarCloud issue.

### Step 4: Code Viewer

- Opened from the `Location` column for public repositories.
- Displays the source file directly from GitHub.
- Highlights the lines associated with the `Code Smell`.

## 6. Architecture and Internal Logic

1. **Frontend:** HTML, CSS, and JavaScript capture user input (`index.js`), call backend APIs, and render reports (`results.js`, `individualReport.js`) using `sessionStorage` data.
2. **Backend (Flask):**
   - `controllers/main_controller.py`: Defines routes and orchestrates analysis via `/api/test-connection`.
   - `models/JSONReader.py`: Connects to SonarCloud API, handles authentication, and extracts `CODE_SMELL` issues.
   - `models/ExcelProcessor.py`: Reads `Mapeo.xlsx` and maps Sonar rules to `Moha Smells`.
   - `models/AntipatternDetector.py`: Applies core detection logic and returns final results.

## 7. Troubleshooting

- **Error: "Project not found in SonarCloud."**
  - Cause: Incorrect project key.
  - Fix: Verify the project key exactly as shown in SonarCloud.

- **Error: "The repository is private or the authorization token is invalid."**
  - Cause: Private project without token, or expired/invalid token.
  - Fix: Enable `Private repository` and provide a valid token.

- **Error: "Could not connect to the server."**
  - Cause: Flask server is not running.
  - Fix: Run `flask run` and verify app availability at `http://127.0.0.1:5000`.

- **Location column has no links.**
  - Cause: Private repository analysis.
  - Fix: This is expected behavior to avoid exposing non-public code paths.