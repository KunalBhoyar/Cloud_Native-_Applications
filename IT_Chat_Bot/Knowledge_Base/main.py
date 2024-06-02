from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer
import os
import fitz  # PyMuPDF
from docx import Document
from typing import List

# Initialize FastAPI application
app = FastAPI()

# Load a pre-trained language model for question answering from Hugging Face
model_name = "distilbert-base-uncased-distilled-squad"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForQuestionAnswering.from_pretrained(model_name)
nlp = pipeline("question-answering", model=model, tokenizer=tokenizer)



UPLOAD_DIRECTORY = "uploaded_documents"



# Create the upload directory if it doesn't exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)




# Function to load and preprocess documents
def load_documents(directory):
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            with open(os.path.join(directory, filename), 'r') as file:
                documents.append(file.read())
        elif filename.endswith(".pdf"):
            documents.append(load_pdf(os.path.join(directory, filename)))
        elif filename.endswith(".docx"):
            documents.append(load_docx(os.path.join(directory, filename)))
    return " ".join(documents)

# Function to load text from PDF files
def load_pdf(filepath):
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()
    return text

# Function to load text from Word files
def load_docx(filepath):
    doc = Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])



# Endpoint to serve the HTML frontend
@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("index.html") as f:
        return f.read()


# Endpoint to handle file uploads
@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    for file in files:
        file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    return {"message": "Files successfully uploaded"}




# Load and preprocess documents
documents_context = load_documents("uploaded_documents")
print(documents_context)

# Define the request body structure using pydantic
class QueryRequest(BaseModel):
    question: str

# Define an endpoint to handle POST requests
@app.post("/query")
async def query_kb(request: QueryRequest):
    prompt = request.question

    try:
        result = nlp(question=prompt, context=documents_context)
        answer = result['answer']
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
