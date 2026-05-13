import streamlit as st
from langchain_community.document_loaders import (
        PyPDFLoader,
        TextLoader,
        Docx2txtLoader
    )
st.title("PDF Tutor !!")
st.write("Upload ur documents and ask questions about it !!")

uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "txt"])
if uploaded_file is not None:
    st.write("File uploaded successfully!")
    

    with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())
    
    

    file_extension = uploaded_file.name.split(".")[-1]

    if file_extension == "pdf":
        loader = PyPDFLoader(uploaded_file.name)
    elif file_extension == "txt":
        loader = TextLoader(uploaded_file.name)
    elif file_extension == "docx":
        loader = Docx2txtLoader(uploaded_file.name)

    docs = loader.load()

    st.write(docs[0].page_content)