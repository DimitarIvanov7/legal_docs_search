from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import uuid

from starlette.responses import FileResponse

from search import tf_idf_search

app = FastAPI(title="TF-IDF Legal Search")

UPLOAD_DIR = Path("tmp")
UPLOAD_DIR.mkdir(exist_ok=True)

DOCUMENTS_DIR = Path("Data/Documents")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
)

@app.post("/search/pdf")
async def search_by_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save uploaded PDF temporarily
    tmp_filename = f"{uuid.uuid4()}.pdf"
    tmp_path = UPLOAD_DIR / tmp_filename

    with tmp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        results = tf_idf_search(tmp_path, top_k=5)
    finally:
        tmp_path.unlink(missing_ok=True)  # cleanup

    return {
        "results": [
            {
                "document": doc_id,
                "score": round(score, 4),
                "download_url": f"http://localhost:8000/documents/{doc_id}"
            }
            for doc_id, score in results
        ]
    }


@app.get("/documents/{filename}")
def get_document(filename: str):
    file_path = DOCUMENTS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )
