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

## Run

```bash
# From repo root
python run_competition.py ExercisePrediction
```

Streamlit (upload CSV with landmark rows to predict):

```bash
streamlit run ExercisePrediction/app/streamlit_app.py
```
