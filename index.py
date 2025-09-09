from pathlib import Path
from typing import Optional
import re
import httpx
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Anonymous Viewer (TikTok) - Vercel Ready", version="1.0.0")

# resolve template/static dirs relative to this file so it works in Vercel
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

TIKTOK_OEMBED = "https://www.tiktok.com/oembed"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def clean_input(s: str) -> str:
    return s.strip()

@app.post("/view", response_class=HTMLResponse)
async def view(request: Request, tiktok_input: str = Form(...)):
    raw = clean_input(tiktok_input)
    # allow either a full post URL or a @handle
    if raw.startswith("@"):
        # For profiles, TikTok doesn't provide oEmbed. We show a simple hint & link.
        profile_url = f"https://www.tiktok.com/{raw}"
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "kind": "profile",
                "display_url": profile_url,
                "embed_html": None,
            },
        )

    # otherwise try to treat it as a post URL and use oEmbed
    # basic sanity check
    if not re.match(r"^https?://", raw):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Please paste a full TikTok post URL (or @username)."},
        )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(TIKTOK_OEMBED, params={"url": raw})
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"TikTok didn't return an embed for this URL (HTTP {e.response.status_code}). Make sure the post is public."},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": f"Unexpected error: {e}"},
        )

    embed_html = data.get("html")
    if not embed_html:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "Could not render embed code for this URL."},
        )

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "kind": "post",
            "display_url": raw,
            "embed_html": embed_html,
        },
    )

@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    return "ok"

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nDisallow: /healthz\n"