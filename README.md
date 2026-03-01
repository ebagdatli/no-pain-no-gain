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

Camera demo (real-time pose detection, rep counter, skeleton overlay):

```bash
cd ExercisePrediction && venv\Scripts\python -m src.camera_demo
# Or from repo root: python -m ExercisePrediction.src.camera_demo
# Press 'q' to quit. Requires trained model (metadata.json, scaler.pkl, etc.)
```
