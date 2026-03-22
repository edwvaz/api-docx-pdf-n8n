from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
import subprocess, tempfile, os

app = FastAPI()

def verify_api_key(x_api_key: str = Header(None)):
    expected_key = os.getenv("API_KEY")
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return x_api_key

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/convert-to-pdf")
async def convert_docx_to_pdf(
    docx_file: UploadFile = File(...),
    filename: str = Form(default="documento.pdf"),
    api_key: str = Depends(verify_api_key)
):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Guardar DOCX
        docx_path = os.path.join(tmpdir, "input.docx")
        with open(docx_path, "wb") as f:
            f.write(await docx_file.read())

        # Convertir con LibreOffice (mejor compatibilidad con Word)
        subprocess.run(
            [
                "libreoffice", "--headless",
                "--convert-to", "pdf:writer_pdf_Export",
                "--outdir", tmpdir,
                docx_path
            ],
            check=True,
            capture_output=True
        )

        # Leer PDF generado
        pdf_path = os.path.join(tmpdir, "input.pdf")
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()

    if not filename.endswith(".pdf"):
        filename = filename.replace(".docx", ".pdf")
        if not filename.endswith(".pdf"):
            filename += ".pdf"

    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
