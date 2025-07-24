import os
import requests
from pathlib import Path
import mimetypes

API_BASE = "http://localhost:8000"
CV_DIR = r"C:\Users\DevX\specialProjects\mAIndScout\test_cvs"
JD_DIR = r"C:\Users\DevX\specialProjects\mAIndScout\test_jds"

# --- CONFIGURE THESE IF AUTH IS ENABLED ---
EMAIL = os.environ.get("TEST_USER_EMAIL", "testuser@example.com")
PASSWORD = os.environ.get("TEST_USER_PASSWORD", "testpassword123")


def find_first_file(folder):
    p = Path(folder)
    for f in p.iterdir():
        if f.is_file():
            return f
    return None

def authenticate():
    url = f"{API_BASE}/auth/login"
    try:
        resp = requests.post(url, json={"email": EMAIL, "password": PASSWORD})
        resp.raise_for_status()
        token = resp.json()["access_token"]
        print(f"[AUTH] Authenticated as {EMAIL}")
        return token
    except Exception as e:
        print(f"[AUTH] Authentication failed: {e}")
        return None

def upload_file(file_path, file_type, token=None):
    url = f"{API_BASE}/upload/upload"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Guess the content type (MIME type) of the file
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        # Provide a default if the type can't be guessed
        content_type = 'application/octet-stream'

    # The 'files' dictionary now includes filename, file object, and content type
    files = {"file": (os.path.basename(file_path), open(file_path, "rb"), content_type)}
    data = {"file_type": file_type}

    try:
        resp = requests.post(url, files=files, data=data, headers=headers)
        resp.raise_for_status()
        print(f"[UPLOAD] Uploaded {file_type} file: {file_path}")
        return resp.json()
    except Exception as e:
        print(f"[UPLOAD] Failed to upload {file_type} file: {e}")
        # It's helpful to print the response text on failure
        if 'resp' in locals() and resp is not None:
            print("Response text:", resp.text)
        return None
    finally:
        # Ensure the file handle in the tuple is closed
        if 'files' in locals() and files.get("file"):
            files["file"][1].close()

def match_candidates(job_data, token=None):
    url = f"{API_BASE}/candidates/match"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = requests.post(url, json=job_data, headers=headers)
        resp.raise_for_status()
        print("[MATCH] Matching triggered successfully.")
        return resp.json()
    except Exception as e:
        print(f"[MATCH] Failed to trigger matching: {e}")
        if 'resp' in locals() and resp is not None:
            print(resp.text)
        return None

def main():
    print("=== mAIndScout End-to-End Test ===")
    # 1. Authenticate (if needed)
    token = authenticate()

    # 2. Find files
    cv_file = find_first_file(CV_DIR)
    jd_file = find_first_file(JD_DIR)
    if not cv_file or not jd_file:
        print(f"[ERROR] Could not find test files. CV: {cv_file}, JD: {jd_file}")
        return
    print(f"[INFO] Using CV: {cv_file}")
    print(f"[INFO] Using JD: {jd_file}")

    # 3. Upload CV
    cv_result = upload_file(str(cv_file), "candidate_profile", token)
    print("\n=== Candidate Profile Output ===")
    print(cv_result)

    # 4. Upload JD
    jd_result = upload_file(str(jd_file), "job_description", token)
    print("\n=== Job Description Output ===")
    print(jd_result)

    # 5. Trigger matching (use job_data from JD upload)
    if jd_result and "job_data" in jd_result:
        match_result = match_candidates(jd_result["job_data"], token)
        print("\n=== Matching Results ===")
        print(match_result)
    else:
        print("[ERROR] No job_data found in JD upload response. Cannot trigger matching.")

if __name__ == "__main__":
    main()