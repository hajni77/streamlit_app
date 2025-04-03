import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
if not firebase_admin._apps:  # Avoid reinitialization error
    cred = credentials.Certificate("your-firebase-credentials.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()
reviews_ref = db.collection("reviews")

st.title("🌍 Global Review System")

# User Input
user_review = st.text_area("Write your review here:")
if st.button("Submit Review"):
    if user_review:
        reviews_ref.add({"review": user_review})
        st.success("✅ Review submitted!")

# Display Reviews from Global Users
st.subheader("🌎 Reviews from Around the World")
docs = reviews_ref.stream()
for doc in docs:
    st.write(f"- {doc.to_dict()['review']}")
