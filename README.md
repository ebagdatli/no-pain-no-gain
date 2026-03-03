# NoPainNoGain

[![Hugging Face Space](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-ActiMetric--AI-blue)](https://huggingface.co/spaces/bagdatli/ActiMetric-AI)

> **Live Demo:** [https://huggingface.co/spaces/bagdatli/ActiMetric-AI](https://huggingface.co/spaces/bagdatli/ActiMetric-AI)

AI-powered real-time exercise recognition and tracking platform. Detects your body movements through camera in real-time, counts repetitions and estimates calories burned.

## Features

- [x] **Exercise Recognition** -- Real-time detection of push-ups, sit-ups, squats, pull-ups and jumping jacks via camera
- [x] **Rep Counter** -- Automatic repetition counting with state machine (down -> up transition detection + debounce)
- [x] **Center Counter Animation** -- Large fading rep number appears in the center of the screen on each completed rep
- [x] **Workout Summary** -- Session summary popup showing exercise counts, duration and estimated calories when camera stops
- [x] **Calorie Estimation** -- Default per-exercise calorie rates (logic to be refined in future versions)
- [x] **Performance Optimized** -- Frame skipping, 480p resolution, simplified landmark drawing (33 -> 14 body points)

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Pose Detection | MediaPipe Pose Landmarker (33 landmarks x 3 axes) |
| Classification | XGBoost / PyTorch MLP (10 classes: 5 exercises x 2 positions) |
| Prediction Smoothing | Mode filter over last 12 frames + 65% confidence threshold |
| Local UI | Streamlit + OpenCV (CV2 window) |
| Cloud UI | Streamlit + streamlit-webrtc (in-browser camera) |
| Deployment | Docker on Hugging Face Spaces |

## Project Structure

```
NoPainNoGain/
├── app/
│   └── streamlit_app.py       # Local Streamlit UI (launches CV2 camera)
├── src/
│   ├── camera_demo.py         # Real-time pose detection + rep counter
│   ├── data_loader.py         # Load training data
│   ├── preprocessing.py       # LabelEncoder, MinMaxScaler, train/test split
│   ├── train.py               # XGBoost + PyTorch training
│   └── predict.py             # Model save/load utilities
├── notebooks/
│   └── main.ipynb             # Training pipeline: load -> train -> save best
├── hf_space/                  # Hugging Face Space deployment
│   ├── app.py                 # Combined UI + WebRTC camera + all logic
│   ├── Dockerfile
│   ├── README.md              # HF Space metadata (sdk: docker)
│   ├── requirements.txt
│   └── models/                # Copy trained model files here before deploy
├── data/
│   ├── raw/                   # train.csv (download from Kaggle)
│   └── processed/             # Generated artifacts
├── models/                    # Trained model files (.pkl, .json)
└── requirements.txt
```

## Setup

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

## Usage

**Local camera demo** (real-time pose detection with CV2 window):

```bash
venv\Scripts\python -m src.camera_demo
```

Press `q` to quit. A workout summary will be printed to the terminal.

**Streamlit UI** (local web interface):

```bash
venv\Scripts\python -m streamlit run app/streamlit_app.py
```

## Training

Download [Multi-Class Exercise Poses](https://www.kaggle.com/datasets/dp5995/gym-exercise-mediapipe-33-landmarks) dataset from Kaggle and place `train.csv` in `data/raw/`. Then run the training notebook or:

```bash
venv\Scripts\python -m src.train
```

## Hugging Face Deployment

The `hf_space/` directory contains everything needed for deployment. See the [deployment guide](hf_space/README.md) or visit the [live demo](https://huggingface.co/spaces/bagdatli/ActiMetric-AI).

## Data Source

| Dataset | Description | Link |
|---------|-------------|------|
| Multi-Class Exercise Poses | 10 exercise poses (5 exercises x 2 positions) with MediaPipe 33 landmarks | [Kaggle](https://www.kaggle.com/datasets/dp5995/gym-exercise-mediapipe-33-landmarks) |
