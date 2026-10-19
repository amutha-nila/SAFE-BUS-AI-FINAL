from fastapi import FastAPI,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from pathlib import Path
import pandas as pd,time
from .config import MODELS,RESULTS,ROOT,DEFAULT_CAPACITY
from .safety import SafetyEngine
from .alerts import alerts,officer
from .tts import synthesize
app=FastAPI(title='SAFE-BUS AI')
FRONT=ROOT/'frontend'
app.mount('/audio',StaticFiles(directory=RESULTS),name='audio')
class Event(BaseModel):
 bus_id:str;route_id:str;stop_id:str;timestamp:str;current_load:int=Field(ge=0);capacity:int=Field(ge=1);boarding:int=Field(ge=0);alighting:int=Field(ge=0);doorway_risk:str='NORMAL'
_engines={};_predictor=None

def predictor():
 global _predictor
 if _predictor is None:
  if not (MODELS/'ann_model.keras').exists():raise RuntimeError('ANN model not found. Run: python -m backend.app.train')
  import tensorflow as tf,joblib,json
  _predictor=(tf.keras.models.load_model(MODELS/'ann_model.keras'),joblib.load(MODELS/'scaler.joblib'),json.loads((MODELS/'feature_config.json').read_text()),json.loads((MODELS/'historical_stats.json').read_text()))
 return _predictor

def infer(e):
 from .data_pipeline import contextualize,attach_history,matrix
 model,sc,config,stats=predictor();ts=pd.Timestamp(e.timestamp)
 frame=pd.DataFrame([{'route_id':e.route_id,'stop_id':e.stop_id,'event_timestamp':ts,'boardings':e.boarding,'alightings':e.alighting,'passenger_load':e.current_load}]);frame['service_date']=ts.date().isoformat();x=contextualize(frame);x=attach_history(x,stats);return model.predict(sc.transform(matrix(x)),verbose=0)[0].tolist()
@app.get('/')
def root(): return FileResponse(FRONT/'index.html')
@app.get('/api/health')
def health():return {'status':'ok','model_ready':(MODELS/'ann_model.keras').exists(),'frontend':'react-vite'}
@app.post('/api/analyze')
def analyze(e:Event):
 try:
  preds=infer(e);engine=_engines.setdefault(e.bus_id,SafetyEngine(e.capacity));s=engine.evaluate(e.current_load,preds,e.doorway_risk);ta,en=alerts(e.bus_id,s);off=officer(e.bus_id,s) if s['state']=='SEVERE' else None;tts=synthesize(ta,f'{e.bus_id}_{int(time.time())}.mp3') if s['state'] in ('CRITICAL','SEVERE') else {'status':'not_requested'}
  if off:(RESULTS/'traffic_officer_alerts.log').open('a',encoding='utf-8').write(off+'\n')
  return {'safety':s,'alert':{'tamil':ta,'english':en},'officer_alert':off,'tts':tts}
 except Exception as ex:raise HTTPException(500,str(ex))
