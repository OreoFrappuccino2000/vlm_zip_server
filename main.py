from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import zipfile
import os
import uuid
import shutil

app = FastAPI()

TMP_ROOT = "/app/tmp_zip"
OUT_ROOT = "/app/unzipped_images"

os.makedirs(TMP_ROOT, exist_ok=True)
os.makedirs(OUT_ROOT, exist_ok=True)


@app.post("/zip_to_image_files")
async def zip_to_image_files(file: UploadFile = File(...)):

    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only ZIP files are supported")

    job_id = str(uuid.uuid4())
    zip_path = os.path.join(TMP_ROOT, f"{job_id}.zip")
    extract_dir = os.path.join(OUT_ROOT, job_id)

    os.makedirs(extract_dir, exist_ok=True)

    # 1️⃣ 保存 ZIP 到本地
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 2️⃣ 解压 ZIP
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
    except Exception as e:
        raise HTTPException(500, f"Unzip failed: {e}")

    # 3️⃣ 收集图片文件
    image_paths = []
    for root, _, files in os.walk(extract_dir):
        for fname in sorted(files):
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                image_paths.append(os.path.join(root, fname))

    if not image_paths:
        raise HTTPException(400, "No images found in ZIP")

    # 4️⃣ ✅ 关键：直接返回 Array[File]（不要包 JSON）
    return [FileResponse(p, media_type="image/jpeg") for p in image_paths]
