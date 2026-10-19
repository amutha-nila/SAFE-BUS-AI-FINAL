from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[2]
DATA_RAW=ROOT/'backend'/'data'/'raw'; MODELS=ROOT/'backend'/'models'; RESULTS=ROOT/'backend'/'results'
for p in (DATA_RAW,MODELS,RESULTS): p.mkdir(parents=True,exist_ok=True)
DEFAULT_CAPACITY=int(os.getenv('DEFAULT_BUS_CAPACITY','50'))
SPEECH_KEY=os.getenv('SPEECH_KEY',''); SPEECH_REGION=os.getenv('SPEECH_REGION','')
