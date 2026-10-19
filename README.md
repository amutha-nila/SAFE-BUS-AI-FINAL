# SAFE-BUS AI — Full VS Code Project

A full-stack academic prototype for predictive public-bus crowding safety using an Artificial Neural Network.

## Implemented

Real APC data -> preprocessing -> chronological train/validation/test -> train-only historical statistics -> ANN -> saved model -> real inference.

ETM/GPS event -> saved ANN -> next 1/2/3 observed route-event load prediction -> safety engine -> Tamil/English dynamic alert -> Tamil neural TTS -> Traffic Officer escalation message.

No CNN, YOLO, fake MP3, hard-coded ANN prediction, automatic bus stopping, or fake claim of live Tamil Nadu MTC telemetry.

## Dataset

The project downloads real AC Transit APC records from the public Hugging Face dataset. It contains stop-level boardings, alightings, passenger load, route/stop, timestamps and coordinates. The full dataset is hundreds of millions of rows, so the acquisition script downloads a configurable monthly slice for local training.

Important limitation: the public APC dataset does not expose a vehicle identifier. The training target is therefore the next 1/2/3 observed events within route + service day, not a claim that the public dataset identifies the exact physical bus. The bus-specific UI is an integration layer where an authorized ETM feed would provide actual vehicle state.

## Windows + VS Code

1. Open this folder in VS Code.
2. Double-click `setup_windows.bat`.
3. Download real data and train:

```powershell
.\.venv\Scripts\Activate.ps1
python scripts/acquire_apc.py --rows 100000 --out backend/data/raw/ac_transit_apc.csv
python -m backend.app.train
```

4. Terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

5. Terminal 2:

```powershell
cd frontend
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

## Tamil voice

Primary voice: `ta-IN-PallaviNeural`.

Azure Speech can synthesize Tamil neural speech. Configure:

```powershell
$env:SPEECH_KEY="YOUR_KEY"
$env:SPEECH_REGION="centralindia"
```

If Azure credentials are absent, the backend tries `edge-tts` with the same Tamil voice. This generates a fresh MP3 at runtime; no static recording is used.

## Severe Tamil alert

சாமி, பஸ் ஓவர்லோடு ஆச்சு. இப்போ ... பேர் இருக்காங்க. கொள்ளளவு ... பேர். அடுத்த ஸ்டாப்களிலும் கூட்டம் அதிகரிக்க வாய்ப்பு இருக்கு. கூட்டம் குறையும் வரை யாரையும் உள்ளே ஏத்தாதீங்க. யாராவது கீழே இறங்கினால் மட்டும் புதிய பயணிகளை அனுமதிக்கவும். பஸ்ஸை தானாக நிறுத்த வேண்டாம். Traffic Officer-க்கு தகவல் தெரிவிக்கப்படுகிறது.

English:

Attention. The bus is overloaded. Do not allow new passengers to board until the crowd decreases. Allow boarding only when passengers get down. Do not stop the bus automatically. The Traffic Officer is being alerted.

Passenger numbers are inserted dynamically from the current event and ANN prediction.

## Safety states

SAFE < 80%; WARNING 80%-<100%; CRITICAL >=100%; SEVERE = CRITICAL + persistent overload + HIGH_RISK doorway input.

These are project-defined operating thresholds, not legal passenger limits.

## ANN

Input -> Dense(64, ReLU) -> Dense(32, ReLU) -> Dense(16, ReLU) -> Dense(3, Linear)

Outputs: next observed event, next 2 observed events, next 3 observed events.

Evaluation: MAE, RMSE, R2, Accuracy, Precision, Recall, F1, confusion matrix.

Baselines: Persistence and Linear Regression.

## Structure

```text
SAFE-BUS-AI-FINAL/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── train.py
│   │   ├── data_pipeline.py
│   │   ├── safety.py
│   │   ├── alerts.py
│   │   └── tts.py
│   ├── data/
│   ├── models/
│   └── results/
├── frontend/
│   ├── src/main.jsx
│   ├── src/styles.css
│   └── package.json
├── scripts/
├── setup_windows.bat
├── start_backend.bat
└── start_frontend.bat
```
