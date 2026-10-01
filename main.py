from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import yt_dlp
import os
import uuid

app = FastAPI()

# إنشاء مجلد مؤقت للتنزيلات داخل الخادم
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

templates = Jinja2Templates(directory="templates")

def cleanup_file(file_path: str):
    """دالة لحذف الملف الموقت من الخادم بعد إرساله للمستخدم"""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/get-formats")
async def get_formats(url: str = Form(...)):
    info_opts = {'quiet': True}
    try:
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            unique_resolutions = {}
            for f in formats:
                vcodec = f.get('vcodec', 'none')
                height = f.get('height')
                f_id = f.get('format_id')

                if vcodec != 'none' and height:
                    if height not in unique_resolutions:
                        unique_resolutions[height] = f_id

            sorted_heights = sorted(unique_resolutions.keys(), reverse=True)
            
            return {
                "status": "success",
                "title": info.get('title', 'Video'),
                "resolutions": sorted_heights,
                "thumbnail": info.get('thumbnail', '')
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/download")
async def download_video(background_tasks: BackgroundTasks, url: str = Form(...), quality: str = Form(...)):
    # توليد معرّف فريد لتفادي تداخل الملفات عند التنزيل المتزامن
    file_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}_%(title)s.%(ext)s")

    if quality == "mp3":
        ydl_opts = {
            'outtmpl': output_template,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        ydl_opts = {
            'outtmpl': output_template,
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
            'merge_output_format': 'mp4',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if quality == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"

        # إضافة مهمة خلفية لحذف الملف من السيرفر فور انتهاء التنزيل للمستخدم
        background_tasks.add_task(cleanup_file, filename)

        return FileResponse(
            path=filename,
            filename=os.path.basename(filename).replace(f"{file_id}_", ""),
            media_type='application/octet-stream'
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}