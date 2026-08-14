from fastapi import FastAPI

app = FastAPI(title='Human Pathology Platform')

@app.get('/api/health')
def health():
    return {'status':'ok'}

@app.get('/api/status')
def status():
    return {'raw_data':'detected'}
