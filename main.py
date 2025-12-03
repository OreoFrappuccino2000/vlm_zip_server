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

    zip_url = None

    # ✅ 1️⃣ 支持两种输入格式：
    # A) { "zip_url": "https://xxx.zip" }
    # B) Dify Tool File 自动注入 { "files": [ { "url": "https://upload.dify.ai/....zip" } ] }

    if "zip_url" in payload and payload["zip_url"]:
        zip_url = payload["zip_url"]

    elif "files" in payload and len(payload["files"]) > 0:
        file_obj = payload["files"][0]
        if "url" in file_obj and file_obj["url"]:
            zip_url = file_obj["url"]

    if not zip_url:
        raise HTTPException(
            status_code=400,
            detail="zip_url missing or Dify files[0].url missing"
        )

    # ✅ 2️⃣ 创建任务目录
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(BASE_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    zip_path = os.path.join(job_dir, "input.zip")

    # ✅ 3️⃣ 下载 ZIP（支持 Dify Signed URL）
    try:
        r = requests.get(zip_url, timeout=180)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download zip: {str(e)}")

    # ✅ 4️⃣ 安全解压 ZIP（防路径穿越）
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                member_path = os.path.join(job_dir, member)
                if not os.path.abspath(member_path).startswith(os.path.abspath(job_dir)):
                    raise HTTPException(status_code=400, detail="Unsafe zip content detected")
            zip_ref.extractall(job_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to unzip: {str(e)}")

    # ✅ 5️⃣ 扫描图片文件（递归）
    image_files = []
    for root, _, files in os.walk(job_dir):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                full_path = os.path.join(root, file)

                ext = os.path.splitext(file)[1].lower()
                media_type = "image/png" if ext == ".png" else "image/jpeg"

                image_files.append({
                    "path": full_path,
                    "media_type": media_type
                })

    if not image_files:
        raise HTTPException(status_code=400, detail="No image files found in zip")

    # ✅ 6️⃣ 返回 Dify 识别的标准 JSON
    return JSONResponse({
        "job_id": job_id,
        "total_files": len(image_files),
        "files": image_files
    })
