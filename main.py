from fastapi import FastAPI, HTTPException
import requests
import os
import zipfile
import uuid
from fastapi.responses import JSONResponse

app = FastAPI()

BASE_DIR = "/app/unzipped"
os.makedirs(BASE_DIR, exist_ok=True)

@app.post("/zip_to_image_files")
def zip_to_image_files(payload: dict):
    if "zip_url" not in payload:
        raise HTTPException(status_code=400, detail="zip_url missing")

    zip_url = payload["zip_url"]

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(BASE_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    zip_path = os.path.join(job_dir, "input.zip")

    # 1️⃣ 下载 ZIP
    try:
        r = requests.get(zip_url, timeout=120)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download zip: {str(e)}")

    # 2️⃣ 解压 ZIP
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(job_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to unzip: {str(e)}")

    # 3️⃣ 扫描解压后的图片文件
    image_files = []
    for root, dirs, files in os.walk(job_dir):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                full_path = os.path.join(root, file)
                image_files.append({
                    "path": full_path,
                    "media_type": "image/jpeg"
                })

    if len(image_files) == 0:
        raise HTTPException(status_code=400, detail="No image files found in zip")

    # ✅ 4️⃣ 必须返回 JSON（不能返回 FileResponse！）
    return JSONResponse({
        "job_id": job_id,
        "total_files": len(image_files),
        "files": image_files   # ✅ Dify 可识别为 Array[File]
    })
