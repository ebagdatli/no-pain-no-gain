# Fitness AI — Design Handoff Kit

Tasarım dosyalarının tam kılavuzu. Figma kurulumu, React entegrasyonu ve token kullanımı.

---

## 📁 Dosya Yapısı

```
fitness-ai/
├── tokens/
│   ├── tokens.json        ← Figma Token Studio plugin için (W3C format)
│   └── variables.css      ← Vanilla CSS / plain HTML projeleri için
├── tailwind.config.js     ← Tailwind CSS projeleri için
└── components/
    ├── LandingScreen.tsx       ← Ekran 1: Karşılama
    ├── LiveTrackingScreen.tsx  ← Ekran 2: Canlı Takip
    └── SummaryAndProfile.tsx   ← Ekran 3 & 4: Özet + Profil
```

---

## 🎨 Figma Kurulumu

### Adım 1 — Font Kurulumu
Figma'da kullanılan fontları yükle:
- **Bebas Neue** → Google Fonts: https://fonts.google.com/specimen/Bebas+Neue
- **DM Sans** → Google Fonts: https://fonts.google.com/specimen/DM+Sans

### Adım 2 — Design Tokens (Token Studio Plugin)
1. Figma → Plugins → "Tokens Studio for Figma" yükle
2. Plugin'i aç → "Load from file" seç
3. `tokens/tokens.json` dosyasını yükle
4. Token'lar otomatik olarak Figma'ya aktarılır

### Adım 3 — Renk Paletiyle Çalışma
Figma'da bu renk stillerini oluştur:

| İsim                    | Hex              | Kullanım              |
|-------------------------|------------------|-----------------------|
| brand/neon-green        | #2ecc71          | Sayaç, iskelet, başarı|
| brand/blue              | #3498db          | Squat, ikincil aksent |
| brand/orange            | #e67e22          | Accuracy uyarı (<80%) |
| brand/red               | #e74c3c          | Durdurma butonu       |
| brand/gold              | #f39c12          | XP, kupa              |
| brand/purple            | #9b9bff          | Lig rozeti            |
| bg/base                 | #0a0a0a          | Ana arka plan         |
| bg/surface-1            | #0d0d0d          | Ekran arka planı      |
| bg/surface-2            | #141414          | Modal, kart           |
| bg/surface-3            | #1a1a1a          | İç bileşenler         |

### Adım 4 — Text Stilleri
Figma'da bu metin stillerini oluştur:

| İsim              | Font        | Size | Weight | Tracking |
|-------------------|-------------|------|--------|----------|
| Display/Counter   | Bebas Neue  | 64px | 400    | 0        |
| Display/Title     | Bebas Neue  | 20px | 400    | 0        |
| Display/Screen    | Bebas Neue  | 18px | 400    | 0        |
| Body/Card Name    | DM Sans     | 15px | 600    | 0        |
| Body/Default      | DM Sans     | 11px | 500    | 0        |
| Label/Uppercase   | DM Sans     | 9px  | 500    | 1.5px    |
| Label/Tiny        | DM Sans     | 8px  | 400    | 2px      |

---

## ⚛️ React Entegrasyonu

### Kurulum

```bash
npm install
# Fontları index.html ya da global CSS'e ekle:
# @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600;700&display=swap');
```

### Kullanım Örneği

```tsx
import { LandingScreen } from './components/LandingScreen'
import { LiveTrackingScreen } from './components/LiveTrackingScreen'
import { SummaryModal, ProfileScreen } from './components/SummaryAndProfile'

function App() {
  const [screen, setScreen] = useState<'landing' | 'tracking' | 'summary' | 'profile'>('landing')

  return (
    <div style={{ width: 260, height: 520, borderRadius: 32, overflow: 'hidden', position: 'relative' }}>
      {screen === 'landing' && (
        <LandingScreen onSelectExercise={(type) => setScreen('tracking')} />
      )}
      {screen === 'tracking' && (
        <LiveTrackingScreen
          repCount={12}
          accuracy={78}
          onStop={() => setScreen('summary')}
        />
      )}
      {screen === 'summary' && (
        <div style={{ position: 'relative', width: '100%', height: '100%' }}>
          <LiveTrackingScreen repCount={42} accuracy={92} />
          <SummaryModal
            result={{
              reps: 42,
              xp: 850,
              speed: 1.2,
              feedback: 'Sırtın biraz fazla kavisliydi. Bir sonraki antrenmanda belini düz tutmaya odaklan.',
            }}
            onSave={() => setScreen('profile')}
          />
        </div>
      )}
      {screen === 'profile' && (
        <ProfileScreen
          userName="Pro-Developer"
          leagueName="Gümüş Lig"
        />
      )}
    </div>
  )
}
```

---

## 🎨 Vanilla CSS Kullanımı

```html
<link rel="stylesheet" href="tokens/variables.css">

<style>
  .counter {
    font-family: var(--font-display);
    font-size: var(--text-display-counter);
    color: var(--color-brand-green);
    box-shadow: var(--shadow-neon-green);
  }

  .screen {
    width: var(--phone-width);
    height: var(--phone-height);
    background: var(--color-bg-s1);
    border-radius: var(--phone-radius);
  }
</style>
```

---

## 🖌️ Ekran Bileşen Özeti

### Ekran 1 — LandingScreen
- Props: `onSelectExercise(type: 'pushup' | 'squat')`
- Bağımlılık: Bebas Neue font, SVG skeleton figürü

### Ekran 2 — LiveTrackingScreen
- Props: `repCount`, `accuracy` (0-100), `onStop`
- `accuracy < 80` → bar turuncu olur

### Ekran 3 — SummaryModal
- Props: `result { reps, xp, speed, feedback }`, `onSave`
- Overlay olarak çalışır, LiveTrackingScreen üzerine konumlandırılır

### Ekran 4 — ProfileScreen
- Props: `userName`, `leagueName`, `chartData` (7 değer), `activities[]`
- `MiniLineChart` bağımlılığı yok (SVG ile çizilir)
