import streamlit as st
import re
import os
import tempfile
from io import BytesIO

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
)
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract
from pytesseract import TesseractNotFoundError

try:
    from pdf2image import convert_from_bytes
    from pdf2image.exceptions import PDFInfoNotInstalledError
except ImportError:
    convert_from_bytes = None
    PDFInfoNotInstalledError = Exception


def preprocess_image(image: Image.Image) -> Image.Image:
    if image.mode != "L":
        image = image.convert("L")

    image = ImageOps.autocontrast(image, cutoff=1)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    width, height = image.size
    if width < 2000 or height < 2000:
        image = image.resize((min(3000, width * 2), min(3000, height * 2)), Image.LANCZOS)

    if image.getextrema()[1] - image.getextrema()[0] < 100:
        image = ImageOps.equalize(image)

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    return image


def try_image_ocr(image, psm: int = 6, lang: str = "eng"):
    try:
        processed = preprocess_image(image)
        config = f"--oem 3 --psm {psm}"
        return pytesseract.image_to_string(processed, config=config, lang=lang).strip()
    except TesseractNotFoundError:
        st.error(
            "Tesseract is not installed or not found in PATH. "
            "Install Tesseract from https://github.com/tesseract-ocr/tesseract and restart Streamlit."
        )
        return None

st.title("PDF Tutor !!")
st.write("Upload your documents and ask questions about them !!")

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["pdf", "txt", "docx", "jpg", "jpeg", "png"],
)

ocr_mode = st.selectbox(
    "OCR page segmentation mode",
    [
        (3, "Automatic page segmentation"),
        (4, "Single column of text"),
        (6, "Single uniform block of text"),
        (7, "Single text line"),
        (11, "Sparse text"),
    ],
    format_func=lambda item: item[1],
)
ocr_psm = ocr_mode[0]

ocr_language = st.text_input("Tesseract language code", value="eng")

if uploaded_file is not None:
    st.success("File uploaded successfully!")

    file_extension = uploaded_file.name.lower().split(".")[-1]
    temp_path = None

    if file_extension in ["pdf", "txt", "docx"]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
            tmp.write(uploaded_file.getbuffer())
            temp_path = tmp.name

        if file_extension == "pdf":
            loader = PyPDFLoader(temp_path)
        elif file_extension == "txt":
            loader = TextLoader(temp_path)
        else:
            loader = Docx2txtLoader(temp_path)

        docs = loader.load()
        if docs:
            st.subheader("Document content")
            for i, doc in enumerate(docs, start=1):
                st.markdown(f"**Page {i}**")
                st.write(doc.page_content)
        else:
            st.warning("No text content was extracted from the document.")

        if file_extension == "pdf":
            if convert_from_bytes is None:
                st.warning("PDF image OCR requires pdf2image. Install it to extract text from images inside PDFs.")
            else:
                try:
                    pages = convert_from_bytes(uploaded_file.getvalue(), dpi=300)
                except PDFInfoNotInstalledError:
                    st.error(
                        "Poppler is not installed or not found in PATH. "
                        "Please install Poppler:\n\n"
                        "**Option 1 (Recommended):** Install via pip\n"
                        "`pip install poppler-windows`\n\n"
                        "**Option 2:** Download from GitHub\n"
                        "https://github.com/oschwartz10612/poppler-windows/releases/\n"
                        "Extract and add the bin folder to your PATH.\n\n"
                        "**Option 3:** Use Chocolatey (if installed)\n"
                        "`choco install poppler`"
                    )
                else:
                    ocr_texts = []
                    ocr_error = False
                    for page in pages:
                        page_text = try_image_ocr(page)
                        if page_text is None:
                            ocr_error = True
                            break
                        if page_text:
                            ocr_texts.append(page_text)

                    if ocr_texts:
                        st.subheader("PDF image OCR")
                        st.write("\n\n".join(ocr_texts))
                    elif not ocr_error:
                        st.info("No text was detected in PDF images.")

    elif file_extension in ["jpg", "jpeg", "png"]:
        image = Image.open(BytesIO(uploaded_file.getvalue()))
        text = try_image_ocr(image)

        st.subheader("OCR Result")
        if text is None:
            st.error("OCR failed. Check that Tesseract is installed and the image is readable.")
        elif text:
            st.write(text)
        else:
            st.warning("No text was detected in the image.")

    else:
        st.error("Unsupported file type. Please upload PDF, TXT, DOCX, JPG, JPEG, or PNG.")

    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)

    cleaned_file_name = re.sub(r"[^\w\s-]", "", uploaded_file.name)
    st.write(f"Cleaned file name: {cleaned_file_name}")






    


