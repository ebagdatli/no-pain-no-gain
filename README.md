# Exercise Prediction

**Kaggle**: [Multi-Class Exercise Poses for Human Skeleton](https://www.kaggle.com/datasets/dp5995/gym-exercise-mediapipe-33-landmarks)

Classification: 10 pose classes (5 exercises × 2 positions: up/down). Push-up, Pull-up, Sit-up, Jumping Jack, Squat. MediaPipe 33 landmarks (x,y,z). Metric: Accuracy.

## Getting the data

Data is not in the repo. Download from Kaggle and place in `data/raw/`:

- `train.csv` – pose_id, pose, 99 landmark columns (33 × 3)

Kaggle dataset path: `/kaggle/input/exercise-recognition/train.csv` (when running on Kaggle) or download from the link above and place locally.

## Project structure

```
ExercisePrediction/
├── data/
│   ├── raw/          # train.csv
│   └── processed/    # cleaned/transformed artifacts
├── models/           # final_model.pkl or .pt, encoder, scaler, meta
├── notebooks/
│   └── main.ipynb    # pipeline: load → train (XGBoost + PyTorch) → save best
├── src/
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── train.py
│   └── predict.py
├── app/
│   └── streamlit_app.py
├── hf_space/         # Hugging Face Space deployment files
│   ├── Dockerfile
│   ├── README.md
│   ├── requirements.txt
│   ├── app.py        # Combined UI + WebRTC camera
│   └── models/       # Copy trained model files here before deploy
└── requirements.txt
```

## Setup

```bash
cd ExercisePrediction
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\pip install ipykernel
venv\Scripts\python -m ipykernel install --user --name=exercise-prediction --display-name="Python (ExercisePrediction)"
```

For Jupyter/notebook: select kernel **"Python (ExercisePrediction)"** so xgboost and other deps are found.

## Run

```bash
# From repo root
python run_competition.py ExercisePrediction
```

Streamlit (upload CSV with landmark rows to predict). **ExercisePrediction venv kullanin** (xgboost vb. bu venv'de):

```bash
cd ExercisePrediction
venv\Scripts\python -m streamlit run app/streamlit_app.py
# veya: run_streamlit.bat (Windows)
```

Camera demo (real-time pose detection, skeleton overlay):

```bash
cd ExercisePrediction && venv\Scripts\python -m src.camera_demo
# Or from repo root: python -m ExercisePrediction.src.camera_demo
# Press 'q' to quit. Requires trained model (metadata.json, scaler.pkl, etc.)
```

## Hugging Face Space Deploy

Uygulamayi Hugging Face Spaces uzerinde yayinlamak icin `hf_space/` klasoru hazir dosyalar icerir. Docker SDK + streamlit-webrtc ile tarayici icinden kamera erisimi saglanir.

### Adimlar

1. [huggingface.co/new-space](https://huggingface.co/new-space) adresinden yeni Space olusturun:
   - **SDK**: Docker
   - **Hardware**: CPU Basic (ucretsiz)

2. Space reposunu klonlayin:
   ```bash
   git clone https://huggingface.co/spaces/KULLANICI_ADI/SPACE_ADI
   cd SPACE_ADI
   ```

3. `hf_space/` icerigini klonlanan repoya kopyalayin:
   ```bash
   cp -r /path/to/ExercisePrediction/hf_space/* .
   ```

4. Egitilmis model dosyalarini `models/` klasorune kopyalayin:
   ```bash
   cp /path/to/ExercisePrediction/models/*.pkl models/
   cp /path/to/ExercisePrediction/models/*.json models/
   ```

5. Buyuk dosyalar icin Git LFS ayarlayin:
   ```bash
   git lfs install
   git lfs track "*.pkl"
   git lfs track "*.pt"
   git add .gitattributes
   ```

6. Push edin:
   ```bash
   git add . && git commit -m "Initial deployment" && git push
   ```

HF Spaces otomatik olarak Docker image'i build edip deploy edecektir. `pose_landmarker_lite.task` dosyasi calisma zamaninda otomatik indirilir.

## Roadmap (v2)

Asagidaki ozellikler v2 surumunde eklenecektir:

- **Tekrar Sayaci** - Egzersiz tekrarlarinin otomatik sayimi (down → up gecis algilama ile). Mevcut model pozisyonlari (orn. `pushups_down`, `pushups_up`) zaten taniyor; v2'de bu gecisler guvenilir sekilde izlenip tekrar olarak sayilacak.
- **Kalori Hesaplama** - Yapilan egzersiz turune ve tekrar sayisina bagli olarak tahmini kalori yakimi hesaplanacak. Her egzersiz icin MET (Metabolic Equivalent of Task) degerleri kullanilarak kullaniciya anlik kalori bilgisi sunulacak.
- **Antrenman Ozeti** - Seans sonunda toplam tekrar, sure ve yakilan kalori bilgisini iceren bir ozet ekrani.
