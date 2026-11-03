from __future__ import annotations
import os, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('KINETICASD_DB', ROOT / 'kineticasd_demo.db'))
app = FastAPI(title='KineticASD Demo API', version='0.1.0', description='HOSA educational prototype using synthetic data only. Not for real patient information.')
app.mount('/static', StaticFiles(directory=str(ROOT / 'static')), name='static')

@contextmanager
def db():
    # Create the parent directory when a host mounts persistent storage (e.g. /data).
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def initialize_database():
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS observations (
          id INTEGER PRIMARY KEY AUTOINCREMENT, observed_at TEXT NOT NULL, setting TEXT NOT NULL,
          discipline TEXT NOT NULL, antecedent TEXT NOT NULL, behavior TEXT NOT NULL,
          consequence TEXT NOT NULL, context_notes TEXT NOT NULL DEFAULT '',
          created_by TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, event_at TEXT NOT NULL,
          actor_role TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL);
        ''')
        if con.execute('SELECT COUNT(*) FROM observations').fetchone()[0] == 0:
            rows = [
              ('2026-10-26T16:30:00+00:00','Home','Caregiver','Transition from play to homework','Needed additional transition support','Caregiver used a visual schedule','Fictional example; no clinical inference.','Demo caregiver',1),
              ('2026-10-27T14:00:00+00:00','Speech therapy','Speech-language therapy','Activity changed','Paused and looked to therapist for help','Therapist offered a visual choice','Fictional example; timeline demonstration.','Demo therapist',1),
              ('2026-10-28T15:15:00+00:00','Occupational therapy','Occupational therapy','Room became noisier','Requested a quieter area','Therapist supported a move to a quieter area','Fictional example; context is not a causal claim.','Demo therapist',1),
              ('2026-10-29T17:10:00+00:00','Home','Caregiver','Started evening routine','Completed one step independently','Caregiver acknowledged participation','Positive observation; fictional example.','Demo caregiver',1),
              ('2026-10-30T13:30:00+00:00','Behavioral therapy','Behavioral therapy','Presented a familiar activity','Engaged with the activity','Therapist recorded the observation','Fictional example for product demo.','Demo therapist',1),
              ('2026-10-31T11:00:00+00:00','School','School support','Classroom activity changed','Used a visual schedule to transition','Staff noted the strategy used','Fictional example; synthetic data only.','Demo school staff',1),
            ]
            con.executemany('''INSERT INTO observations
              (observed_at,setting,discipline,antecedent,behavior,consequence,context_notes,created_by,is_demo)
              VALUES (?,?,?,?,?,?,?,?,?)''', rows)
        con.execute('INSERT INTO audit_events(event_at,actor_role,action,detail) VALUES(?,?,?,?)',
                    (now(),'system','database_initialized','Demo database initialized; synthetic records only.'))

@app.on_event('startup')
def startup(): initialize_database()

class ObservationCreate(BaseModel):
    observed_at: Optional[str] = None
    setting: str = Field(min_length=1, max_length=80)
    discipline: str = Field(min_length=1, max_length=100)
    antecedent: str = Field(min_length=1, max_length=500)
    behavior: str = Field(min_length=1, max_length=500)
    consequence: str = Field(min_length=1, max_length=500)
    context_notes: str = Field(default='', max_length=2000)
    created_by: str = Field(default='Demo caregiver', max_length=100)

def audit(actor, action, detail):
    with db() as con:
        con.execute('INSERT INTO audit_events(event_at,actor_role,action,detail) VALUES(?,?,?,?)',
                    (now(), actor, action, detail[:500]))

@app.get('/', response_class=HTMLResponse)
def home(): return (ROOT / 'static' / 'index.html').read_text(encoding='utf-8')

@app.get('/api/health')
def health(): return {'status':'ok','mode':'synthetic-demo-only','database':DB_PATH.name}

@app.get('/api/observations')
def observations(setting: Optional[str]=Query(None,max_length=80), discipline: Optional[str]=Query(None,max_length=100), search: Optional[str]=Query(None,max_length=200)):
    sql='SELECT * FROM observations WHERE is_demo=1'; params=[]
    if setting: sql += ' AND setting=?'; params.append(setting)
    if discipline: sql += ' AND discipline=?'; params.append(discipline)
    if search:
        sql += ' AND (antecedent LIKE ? OR behavior LIKE ? OR consequence LIKE ? OR context_notes LIKE ?)'
        params.extend([f'%{search}%']*4)
    sql += ' ORDER BY observed_at DESC,id DESC'
    with db() as con: return [dict(r) for r in con.execute(sql,params).fetchall()]

@app.post('/api/observations', status_code=201)
def create_observation(payload: ObservationCreate):
    with db() as con:
        cur=con.execute('''INSERT INTO observations(observed_at,setting,discipline,antecedent,behavior,consequence,context_notes,created_by,is_demo)
          VALUES(?,?,?,?,?,?,?,?,1)''',(payload.observed_at or now(),payload.setting,payload.discipline,payload.antecedent,payload.behavior,payload.consequence,payload.context_notes,payload.created_by))
        row=con.execute('SELECT * FROM observations WHERE id=?',(cur.lastrowid,)).fetchone()
    audit('demo-user','observation_created',f'Created synthetic observation ID {row["id"]}')
    return dict(row)

@app.get('/api/summary')
def summary():
    with db() as con:
        total=con.execute('SELECT COUNT(*) FROM observations WHERE is_demo=1').fetchone()[0]
        setting=con.execute('SELECT setting AS label,COUNT(*) AS count FROM observations WHERE is_demo=1 GROUP BY setting ORDER BY count DESC,label').fetchall()
        discipline=con.execute('SELECT discipline AS label,COUNT(*) AS count FROM observations WHERE is_demo=1 GROUP BY discipline ORDER BY count DESC,label').fetchall()
        days=con.execute("SELECT substr(observed_at,1,10) AS label,COUNT(*) AS count FROM observations WHERE is_demo=1 GROUP BY substr(observed_at,1,10) ORDER BY label").fetchall()
    return {'total_observations':total,'by_setting':[dict(r) for r in setting],'by_discipline':[dict(r) for r in discipline],'by_day':[dict(r) for r in days]}

@app.get('/api/audit')
def audit_events(limit: int=Query(20,ge=1,le=100)):
    with db() as con: return [dict(r) for r in con.execute('SELECT * FROM audit_events ORDER BY id DESC LIMIT ?',(limit,)).fetchall()]

@app.get('/api/demo-permissions')
def demo_permissions():
    return {'notice':'Illustrative permissions only; authentication is not implemented.','parent':['create synthetic observations','view demo observations'],'therapist':['view and filter demo observations','view summaries','view demo audit'],'admin':['review simulated therapist applications']}

@app.get('/api/therapist-applications')
def therapist_applications():
    return [
      {'id':'DEMO-001','name':'Jordan Taylor','profession':'Speech-language therapist','jurisdiction':'Pennsylvania','status':'Pending review','note':'Fictional application. Credentials have NOT been verified.'},
      {'id':'DEMO-002','name':'Morgan Lee','profession':'Occupational therapist','jurisdiction':'Pennsylvania','status':'Approved (simulation)','note':'Fictional application. Not a real credential check.'}
    ]

@app.post('/api/therapist-applications/{application_id}/decision')
def decide_application(application_id: str, decision: str=Query(...,pattern='^(approve|reject)$')):
    if application_id not in {'DEMO-001','DEMO-002'}: raise HTTPException(404,'Demo application not found')
    audit('demo-admin',f'therapist_application_{decision}',f'Simulated decision for {application_id}')
    return {'application_id':application_id,'decision':decision,'simulation_only':True,'warning':'This does not verify a real therapist or grant secure access.'}
