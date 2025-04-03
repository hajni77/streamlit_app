import streamlit as st
import pandas as pd
import requests
import json
import base64

# GitHub Repository Details
GITHUB_TOKEN = "your_github_personal_access_token"
GITHUB_REPO = "your_username/your_repo"
FILE_PATH = "data/reviews.csv"

# GitHub API URL
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"

st.title("📢 User Reviews")

# Load existing CSV or create a new DataFrame
try:
    df = pd.read_csv(FILE_PATH)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Name", "Review"])

# Collect user input
user_name = st.text_input("Your Name")
user_review = st.text_area("Write your review here:")

if st.button("Submit Review"):
    if user_name and user_review:
        # Append new review
        new_data = pd.DataFrame([[user_name, user_review]], columns=["Name", "Review"])
        df = pd.concat([df, new_data], ignore_index=True)

        # Save to CSV locally
        df.to_csv(FILE_PATH, index=False)
        
        # Read file content and encode in Base64 for GitHub API
        with open(FILE_PATH, "rb") as file:
            file_content = file.read()
        encoded_content = base64.b64encode(file_content).decode("utf-8")

        # Prepare API request payload
        message = "Updated reviews file"
        payload = {
            "message": message,
            "content": encoded_content,
            "branch": "main"
        }

        # Get the file SHA if it exists (required for updating)
        response = requests.get(GITHUB_API_URL, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        if response.status_code == 200:
            payload["sha"] = response.json()["sha"]

        # Upload to GitHub
        response = requests.put(GITHUB_API_URL, headers={"Authorization": f"token {GITHUB_TOKEN}"}, data=json.dumps(payload))

        if response.status_code in [200, 201]:
            st.success("✅ Review uploaded to GitHub!")
        else:
            st.error(f"❌ Failed to upload: {response.json()}")

# Display reviews
st.subheader("🌎 Global Reviews")
st.dataframe(df)
