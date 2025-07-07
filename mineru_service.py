# -*- coding: utf-8 -*-
import os
import uuid
import shutil
import time
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from fastapi.responses import FileResponse, JSONResponse
import markdown
import uvicorn
import mimetypes
import subprocess
from tempfile import NamedTemporaryFile

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mineru")

# 创建 FastAPI 应用
app = FastAPI()

# 临时输出目录
TEMP_BASE_DIR = Path("./temp_output")
TEMP_BASE_DIR.mkdir(exist_ok=True)

# 启动清理任务（清除超过 1 小时的目录）
async def clean_temp_dirs():
    while True:
        try:
            for dir in TEMP_BASE_DIR.iterdir():
                if dir.is_dir() and (time.time() - dir.stat().st_mtime) > 3600:
                    shutil.rmtree(dir, ignore_errors=True)
                    logger.info(f"清理目录: {dir}")
        except Exception as e:
            logger.exception(f"清理任务异常: {e}")
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(clean_temp_dirs())

# 请求体模型
class ParseRequest(BaseModel):
    file_paths: Optional[List[str]] = None
    lang: Optional[str] = "ch"
    backend: Optional[str] = "pipeline"
    method: Optional[str] = "auto"
    output_format: Optional[str] = "md"

# 转换常见办公文档为 PDF
def convert_to_pdf(input_path: Path) -> Path:
    suffix = input_path.suffix.lower()
    if suffix in ['.doc', '.docx', '.xls', '.xlsx']:
        output_path = input_path.with_suffix('.pdf')
        cmd = [
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(input_path.parent),
            str(input_path)
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0 or not output_path.exists():
            logger.error(
                f"❌ 文档转 PDF 失败: {input_path}\n"
                f"➡️ 命令: {' '.join(cmd)}\n"
                f"📄 stdout: {result.stdout}\n"
                f"📄 stderr: {result.stderr}"
            )
            # 可以选择返回原文件而不是报错中断（根据业务需要）
            # return input_path
            raise RuntimeError(f"文档转 PDF 失败: {input_path}")
        else:
            logger.info(f"✅ 转换成功: {input_path} -> {output_path}")
            return output_path
    else:
        return input_path
    
# 调用 mineru 命令行接口
def run_mineru_cli(input_path: str, output_path: str, lang: str = "ch", backend: str = "pipeline", method: str = "auto"):
    os.environ['MINERU_MODEL_SOURCE'] = "modelscope"
    cmd = f"mineru -p {input_path} -o {output_path} --source local"
    logger.info(f"运行命令: {cmd}")
    code = os.system(cmd)
    if code != 0:
        raise RuntimeError(f"mineru 命令执行失败，退出码 {code}")
@app.post("/parse")
async def parse_from_path(req: ParseRequest):
    result = {}
    for path in req.file_paths:
        name = Path(path).stem
        task_id = uuid.uuid4().hex[:8]
        task_output_dir = TEMP_BASE_DIR / task_id
        task_output_dir.mkdir(exist_ok=True)

        input_path = convert_to_pdf(Path(path)) 
        run_mineru_cli(input_path, str(task_output_dir), lang=req.lang, backend=req.backend, method=req.method)

        output_md_path = task_output_dir / name / f"auto"
        output_md_path = output_md_path / f"{name}.md"
        if req.output_format == "html":
            md_content = output_md_path.read_text(encoding="utf-8")
            result[name] = convert_md_to_html(md_content)
        else:
            result[name] = output_md_path.read_text(encoding="utf-8")
    return JSONResponse(content=result)
@app.post("/upload")
async def parse_from_upload(
    file: UploadFile = File(...),
    lang: str = Form("ch"),
    backend: str = Form("pipeline"),
    method: str = Form("auto"),
    output_format: str = Form("md")
):
    content = await file.read()
    name = Path(file.filename).stem
    task_id = uuid.uuid4().hex[:8]
    task_dir = TEMP_BASE_DIR / task_id
    task_dir.mkdir(exist_ok=True)

    input_path = task_dir / file.filename

    with open(input_path, "wb") as f:
        f.write(content)

    input_path = convert_to_pdf(input_path)
    run_mineru_cli(str(input_path), str(task_dir), lang=lang, backend=backend, method=method)

    output_md_path = task_dir / name / f"auto"
    output_md_path = output_md_path / f"{name}.md"
    if output_format == "html":
        md_content = output_md_path.read_text(encoding="utf-8")
        html_content = convert_md_to_html(md_content)
        return html_content
    else:
        return output_md_path.read_text(encoding="utf-8")

def convert_md_to_html(md_text: str) -> str:
    html = markdown.markdown(md_text, extensions=['extra', 'tables', 'nl2br'])
    html = html.replace("\n", "")  # 可选：去除残余换行符
    return html

# 启动服务
if __name__ == '__main__':
    uvicorn.run("__main__:app", host="0.0.0.0", port=5002, reload=False)
