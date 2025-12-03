# VLM ZIP Frame Processor (Dify + Railway)

This service prepares image frames for vision-based VLM processing in Dify.

## Features
- Accepts ZIP file containing JPG/PNG frames
- Unzips and converts frames into Array[File]
- Outputs files in a Dify-compatible format for VLM
- Designed for Railway deployment

## Endpoints
POST /zip_to_image_files  
Input: ZIP file  
Output: Array[File] images

## Usage Flow
1. Video → Frame Extraction Service
2. Frames → ZIP
3. ZIP → zip_to_image_files
4. Output → VLM Vision Model

## Environment
- Python 3.11
- FastAPI
- Railway
- Dify Workflow Compatible
