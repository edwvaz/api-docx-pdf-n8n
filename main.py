from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import subprocess
import tempfile
import os
from io import BytesIO
from pathlib import Path

app = FastAPI(
    title="DOCX to PDF Converter",
    version="1.0.0"
)

# ============= VALIDACIÓN API KEY =============
def verify_api_key(x_api_key: str = Header(None)):
    """Valida API key desde header X-API-Key"""
    expected_key = os.getenv("API_KEY")
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header requerido")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="API Key inválida")
    return x_api_key

@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    try:
        # Verificar que Pandoc esté instalado
        result = subprocess.run(
            ["pandoc", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "status": "healthy",
            "pandoc_version": result.stdout.split('\n')[0]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# ============= ENDPOINT DE CONVERSIÓN =============
@app.post("/convert-to-pdf")
async def convert_docx_to_pdf(
    docx_file: UploadFile = File(...),
    filename: str = Form(default="documento.pdf"),
    api_key: str = Depends(verify_api_key)
):
    """
    Convierte DOCX a PDF usando Pandoc
    
    - **docx_file**: Archivo DOCX a convertir
    - **filename**: Nombre del archivo PDF de salida (opcional)
    """
    try:
        # Validar extensión del archivo de entrada
        if not docx_file.filename.endswith('.docx'):
            raise HTTPException(
                status_code=400, 
                detail="El archivo debe ser .docx"
            )
        
        # Asegurar que filename termine en .pdf
        if not filename.endswith('.pdf'):
            filename = filename.replace('.docx', '.pdf') if '.docx' in filename else f"{filename}.pdf"
        
        # Crear archivos temporales
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_docx:
            # Guardar DOCX subido
            content = await docx_file.read()
            tmp_docx.write(content)
            tmp_docx_path = tmp_docx.name
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            tmp_pdf_path = tmp_pdf.name
        
        # Ejecutar Pandoc: DOCX → PDF
        subprocess.run(
            [
            "pandoc", tmp_docx_path, "-o", tmp_pdf_path, "--pdf-engine=weasyprint"
            ],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Leer PDF generado
        with open(tmp_pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Limpiar archivos temporales
        os.unlink(tmp_docx_path)
        os.unlink(tmp_pdf_path)
        
        # Retornar PDF
        return StreamingResponse(
            iter([pdf_content]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error en conversión Pandoc: {e.stderr}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
