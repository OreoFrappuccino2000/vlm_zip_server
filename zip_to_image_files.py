from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import requests
import os
import zipfile
import uuid
import shutil

app = FastAPI()

BASE_DIR = "/app/unzipped"
os.makedirs(BASE_DIR, exist_ok=True)

@app.post("/zip_to_image_files")
def zip_to_image_files(payload: dict):

    zip_url = None

    # ✅ 1️⃣ 支持两种输入格式
    if "zip_url" in payload and payload["zip_url"]:
        zip_url = payload["zip_url"].strip()

    elif "files" in payload and len(payload["files"]) > 0:
        file_obj = payload["files"][0]
        if "url" in file_obj and file_obj["url"]:
           zip_url = file_obj["url"].strip()

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

    # ✅ 3️⃣ 下载 ZIP
    try:
        r = requests.get(zip_url, timeout=180)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            f.write(r.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download zip: {str(e)}")

    # ✅ 4️⃣ 安全解压 ZIP
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                member_path = os.path.join(job_dir, member)
                if not os.path.abspath(member_path).startswith(os.path.abspath(job_dir)):
                    raise HTTPException(status_code=400, detail="Unsafe zip content detected")
            zip_ref.extractall(job_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to unzip: {str(e)}")

    # ✅ 5️⃣ 重新打包为 Dify 可接收的 ZIP
    output_zip = os.path.join(job_dir, "output_images.zip")

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zout:
        for root, _, files in os.walk(job_dir):
            for file in files:
                if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    full_path = os.path.join(root, file)
                    zout.write(full_path, arcname=file)

    if not os.path.exists(output_zip):
        raise HTTPException(status_code=400, detail="Repack failed")

    # ✅ ✅ ✅ 6️⃣ 关键修复：返回“真实二进制文件”，不是 JSON
    return FileResponse(
        path=output_zip,
        media_type="application/zip",
        filename="frames.zip"
    )
