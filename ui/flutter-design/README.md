# Fitness AI — Flutter Handoff Kit

React/Tailwind dosyaları Flutter'a dönüştürüldü. Tüm tasarım kararları korundu.

---

## 📁 Proje Yapısı

```
fitness_ai/
├── pubspec.yaml                      ← Bağımlılıklar
├── lib/
│   ├── main.dart                     ← App entry + GoRouter navigation
│   ├── core/
│   │   └── app_tokens.dart           ← Tüm design tokens (renkler, tipografi, spacing)
│   └── screens/
│       ├── landing_screen.dart       ← Ekran 1: Karşılama
│       ├── live_tracking_screen.dart ← Ekran 2: Canlı Takip
│       └── summary_profile_screen.dart ← Ekran 3 & 4: Özet + Profil
└── assets/
    └── fonts/
        └── BebasNeue-Regular.ttf     ← Manuel indir (bkz. kurulum)
```

---

## 🚀 Kurulum

### 1. Bebas Neue fontunu indir
```
https://fonts.google.com/specimen/Bebas+Neue
→ "Download family" → BebasNeue-Regular.ttf dosyasını assets/fonts/ klasörüne koy
```

### 2. Bağımlılıkları yükle
```bash
flutter pub get
```

### 3. Çalıştır
```bash
flutter run
```

---

## 🎨 Figma → Flutter Token Karşılığı

| Figma Token                  | Flutter Karşılığı                        |
|------------------------------|------------------------------------------|
| `brand/neon-green` #2ECC71   | `AppColors.brandGreen`                   |
| `brand/blue` #3498DB         | `AppColors.brandBlue`                    |
| `brand/orange` #E67E22       | `AppColors.brandOrange`                  |
| `brand/red` #E74C3C          | `AppColors.brandRed`                     |
| `brand/gold` #F39C12         | `AppColors.brandGold`                    |
| `brand/purple` #9B9BFF       | `AppColors.brandPurple`                  |
| `bg/base` #0A0A0A            | `AppColors.bgBase`                       |
| `bg/surface-2` #141414       | `AppColors.bgSurface2`                   |
| `Display/Counter` 64px       | `AppTypography.counter`                  |
| `Display/Title` 20px         | `AppTypography.displayMd`                |
| `Label/Uppercase` 9px        | `AppTypography.labelSm`                  |
| `radius/lg` 14px             | `AppRadius.lg_`                          |
| `radius/xl` 20px             | `AppRadius.xl_`                          |

---

## 📦 Paket Açıklamaları

| Paket                          | Kullanım                              |
|--------------------------------|---------------------------------------|
| `camera`                       | Ekran 2'de kamera feed'i              |
| `google_mlkit_pose_detection`  | İskelet noktaları tespiti (AI katmanı)|
| `flutter_riverpod`             | repCount ve accuracy state yönetimi   |
| `google_fonts`                 | DM Sans (body font)                   |
| `fl_chart`                     | Profil ekranı 7 günlük çizgi grafik   |
| `go_router`                    | Ekranlar arası navigasyon             |
| `shared_preferences`           | Kullanıcı XP ve geçmiş kalıcılığı     |

---

## 🏗️ Gerçek Kamera Entegrasyonu (Ekran 2)

`LiveTrackingScreen`'deki `_CameraBackground` widget'ını gerçek kamerayla değiştir:

```dart
// live_tracking_screen.dart içinde _CameraBackground yerine:
class _CameraBackground extends StatelessWidget {
  final CameraController controller;
  const _CameraBackground({required this.controller});

  @override
  Widget build(BuildContext context) => CameraPreview(controller);
}
```

Pose detection için `google_mlkit_pose_detection` ile `_FullSkeletonPainter`'a gerçek
`PoseLandmark` koordinatları beslenebilir:

```dart
// PoseLandmark noktalarını painter'a ver
class _FullSkeletonPainter extends CustomPainter {
  final List<PoseLandmark>? landmarks; // gerçek koordinatlar
  // ...
}
```

---

## 📊 State Yönetimi (Riverpod)

```dart
// providers/workout_provider.dart
@riverpod
class WorkoutNotifier extends _$WorkoutNotifier {
  @override
  WorkoutState build() => const WorkoutState(repCount: 0, accuracy: 100);

  void incrementRep() => state = state.copyWith(repCount: state.repCount + 1);
  void updateAccuracy(double acc) => state = state.copyWith(accuracy: acc);
}
```

---

## ✅ Önemli Notlar

- `CustomPainter` — İskelet çizimi için kullanıldı. SVG'nin Flutter karşılığı budur.
- `fl_chart` — Profil ekranındaki çizgi grafik için. Gerçek veri `List<double>` ile beslenir.
- `AnimatedContainer` — Accuracy barı animasyonlu (500ms ease-out).
- `GestureDetector` — Tüm özel butonlarda `InkWell` yerine kullanıldı (daha fazla kontrol).
- Tüm renkler `AppColors.*`, tüm stil `AppTypography.*` üzerinden gider — sabit renk yok.
