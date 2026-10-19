from pathlib import Path
import asyncio,requests
from .config import RESULTS,SPEECH_KEY,SPEECH_REGION
VOICE='ta-IN-PallaviNeural'

def synthesize(text,filename):
    out=RESULTS/filename
    if SPEECH_KEY and SPEECH_REGION:
        url=f'https://{SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1'
        headers={'Ocp-Apim-Subscription-Key':SPEECH_KEY,'Content-Type':'application/ssml+xml','X-Microsoft-OutputFormat':'audio-24khz-48kbitrate-mono-mp3','User-Agent':'SAFE-BUS-AI'}
        ssml=f'<speak version="1.0" xml:lang="ta-IN"><voice name="{VOICE}">{text}</voice></speak>'
        r=requests.post(url,headers=headers,data=ssml.encode('utf-8'),timeout=30);r.raise_for_status();out.write_bytes(r.content);return {'status':'generated','filename':filename,'provider':'azure'}
    try:
        import edge_tts
        async def make(): await edge_tts.Communicate(text,VOICE).save(str(out))
        asyncio.run(make());return {'status':'generated','filename':filename,'provider':'edge-tts'}
    except Exception as e:return {'status':'unavailable','reason':str(e)}
