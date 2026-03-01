---
title: BecomeAPro Exercise Tracker
emoji: "\U0001F3CB"
colorFrom: green
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# BecomeAPro - AI-Powered Exercise Tracker

Yapay zeka destekli gercek zamanli egzersiz takip uygulamasi.

## Ozellikler

- Tarayici icinden kamera erisimi (WebRTC)
- MediaPipe ile 33 vucut noktasi takibi
- XGBoost / PyTorch ile hareket siniflandirma
- 5 egzersiz destegi: Sinav, Mekik, Squat, Barfiks, Ziplama
- Anlik hareket tespiti ve guven orani gosterimi

## Kullanim

1. "START" butonuna tiklayin ve kamera izni verin
2. Tam vucut gorunumunde, iyi aydinlatilmis ortamda durun
3. Egzersizinizi yapmaya baslayin - AI hareketlerinizi anlik tanir

## Teknik Detaylar

- **Pose Detection**: MediaPipe Pose Landmarker (33 landmark x 3 eksen)
- **Classification**: XGBoost / PyTorch MLP (10 sinif: 5 egzersiz x 2 pozisyon)
- **Smoothing**: Son 12 frame uzerinden mode filtresi + guven esigi (%65)
- **Frontend**: Streamlit + streamlit-webrtc
