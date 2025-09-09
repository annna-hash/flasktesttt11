# Anonymous Viewer (TikTok) — Vercel Ready (FastAPI)

## Local dev
```
pip install -r requirements.txt
uvicorn api.index:app --reload
```
Open http://127.0.0.1:8000

## Deploy to Vercel
```
npm i -g vercel
vercel
vercel --prod
```

This project rewrites all routes to the FastAPI app in `api/index.py`. Static files live under `/api/static`, templates in `/api/templates`.