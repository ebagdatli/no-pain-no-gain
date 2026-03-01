"""
BecomeAPro - AI-Powered Exercise Tracker
Modern Streamlit UI for real-time exercise pose detection and rep counting.
"""
import subprocess
import sys
from pathlib import Path

import streamlit as st
from joblib import load

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODELS_DIR = ROOT / "models"

EXERCISES = [
    {
        "name": "Sinav",
        "en": "Push-ups",
        "icon": "💪",
        "desc": "Gogus, omuz ve triceps kaslari icin temel egzersiz.",
        "color": "#00d4aa",
    },
    {
        "name": "Mekik",
        "en": "Sit-ups",
        "icon": "🔄",
        "desc": "Karin kaslari icin etkili bir core egzersizi.",
        "color": "#7c3aed",
    },
    {
        "name": "Squat",
        "en": "Squats",
        "icon": "🦵",
        "desc": "Bacak ve kalca kaslari icin en etkili hareket.",
        "color": "#f59e0b",
    },
    {
        "name": "Barfiks",
        "en": "Pull-ups",
        "icon": "🧗",
        "desc": "Sirt ve biceps kaslarini guclendiren egzersiz.",
        "color": "#ef4444",
    },
    {
        "name": "Ziplama",
        "en": "Jumping Jacks",
        "icon": "🤸",
        "desc": "Tam vucut kardiyo ve koordinasyon egzersizi.",
        "color": "#3b82f6",
    },
]

st.set_page_config(
    page_title="BecomeAPro | AI Exercise Tracker",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "sessions_started" not in st.session_state:
    st.session_state.sessions_started = 0
if "camera_active" not in st.session_state:
    st.session_state.camera_active = False


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """\
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 0 !important; max-width: 1200px; margin: 0 auto;}

.stApp {
    background: linear-gradient(180deg, #080810 0%, #0d0d1a 40%, #080810 100%);
    color: #e0e0e8;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hero */
.hero {
    text-align: center;
    padding: 4.5rem 1rem 2.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60%; left: -30%; width: 160%; height: 220%;
    background:
        radial-gradient(ellipse at 30% 50%, rgba(0,212,170,0.07) 0%, transparent 50%),
        radial-gradient(ellipse at 70% 50%, rgba(124,58,237,0.07) 0%, transparent 50%);
    animation: drift 10s ease-in-out infinite alternate;
    pointer-events: none;
}
@keyframes drift {
    from { transform: translate(0,0) rotate(0deg); }
    to   { transform: translate(-3%,2%) rotate(1deg); }
}

.hero-badge {
    display: inline-block;
    background: rgba(0,212,170,0.08);
    border: 1px solid rgba(0,212,170,0.25);
    border-radius: 50px;
    padding: 6px 20px;
    font-size: 0.82rem;
    color: #00d4aa;
    font-weight: 600;
    margin-bottom: 1.6rem;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}

.hero h1 {
    font-size: clamp(2.2rem, 5vw, 3.8rem);
    font-weight: 800;
    line-height: 1.08;
    margin: 0 0 1.1rem;
    color: #ffffff;
    position: relative;
}
.hero h1 .grad {
    background: linear-gradient(135deg, #00d4aa 0%, #7c3aed 55%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 1.12rem;
    color: #7a7a95;
    max-width: 580px;
    margin: 0 auto;
    line-height: 1.7;
    position: relative;
}

/* Section Titles */
.sec-title {
    font-size: 1.85rem;
    font-weight: 700;
    text-align: center;
    margin: 3.5rem 0 0.4rem;
    color: #fff;
}
.sec-sub {
    text-align: center;
    color: #7a7a95;
    font-size: 0.95rem;
    margin-bottom: 2rem;
}

/* Glass Card */
.g-card {
    background: rgba(18,18,30,0.65);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.055);
    border-radius: 16px;
    padding: 1.8rem 1.5rem;
    transition: all 0.35s cubic-bezier(.4,0,.2,1);
    position: relative;
    overflow: hidden;
    height: 100%;
}
.g-card:hover {
    border-color: rgba(0,212,170,0.18);
    transform: translateY(-4px);
    box-shadow: 0 16px 48px rgba(0,0,0,0.25);
}

/* Step Cards */
.step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 46px; height: 46px;
    border-radius: 12px;
    background: linear-gradient(135deg, #00d4aa, #7c3aed);
    color: #fff;
    font-weight: 700;
    font-size: 1.15rem;
    margin-bottom: 1rem;
}
.step-t {
    font-size: 1.1rem;
    font-weight: 600;
    color: #fff;
    margin-bottom: 0.45rem;
}
.step-d {
    font-size: 0.88rem;
    color: #7a7a95;
    line-height: 1.6;
}

/* Exercise Cards */
.accent-top {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
    opacity: 0.7;
    transition: opacity 0.3s;
}
.g-card:hover .accent-top { opacity: 1; }

.ex-icon  { font-size: 2.5rem; margin-bottom: 0.7rem; display: block; }
.ex-name  { font-size: 1.05rem; font-weight: 600; color: #fff; margin-bottom: 0.15rem; }
.ex-en    { font-size: 0.78rem; color: #5a5a7a; margin-bottom: 0.5rem; }
.ex-desc  { font-size: 0.82rem; color: #7a7a95; line-height: 1.5; }

/* CTA Section */
.cta-box {
    text-align: center;
    padding: 3rem 2rem 1.5rem;
    background: linear-gradient(135deg, rgba(0,212,170,0.04), rgba(124,58,237,0.04));
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 24px;
    margin: 2.5rem 0 0;
    position: relative;
    overflow: hidden;
}
.cta-box::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 24px;
    background: linear-gradient(135deg, rgba(0,212,170,0.12), transparent 40%, rgba(124,58,237,0.12));
    z-index: 0;
    pointer-events: none;
}
.cta-t {
    font-size: 1.75rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 0.5rem;
    position: relative;
}
.cta-d {
    color: #7a7a95;
    margin-bottom: 0.2rem;
    font-size: 0.95rem;
    position: relative;
}

/* Metric Card */
.m-val {
    font-size: 2.1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00d4aa, #7c3aed);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.m-lbl {
    font-size: 0.82rem;
    color: #7a7a95;
    font-weight: 500;
    margin-top: 4px;
}

/* Primary Button */
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #00d4aa 0%, #00b894 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.85rem 2.8rem !important;
    font-size: 1.08rem !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    color: #080810 !important;
    box-shadow: 0 4px 24px rgba(0,212,170,0.22) !important;
    transition: all 0.3s cubic-bezier(.4,0,.2,1) !important;
    letter-spacing: 0.3px !important;
    min-height: 56px !important;
}
div.stButton > button[kind="primary"]:hover,
div.stButton > button[data-testid="stBaseButton-primary"]:hover {
    box-shadow: 0 8px 36px rgba(0,212,170,0.38) !important;
    transform: translateY(-2px) !important;
}
div.stButton > button[kind="primary"]:active,
div.stButton > button[data-testid="stBaseButton-primary"]:active {
    transform: translateY(0) !important;
}

/* Secondary Button */
div.stButton > button[kind="secondary"],
div.stButton > button[data-testid="stBaseButton-secondary"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 14px !important;
    padding: 0.8rem 2rem !important;
    color: #d0d0e0 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.3s !important;
    min-height: 54px !important;
}
div.stButton > button[kind="secondary"]:hover,
div.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(0,212,170,0.25) !important;
}

/* Status Pill */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(0,212,170,0.08);
    border: 1px solid rgba(0,212,170,0.25);
    border-radius: 50px;
    padding: 8px 18px;
    color: #00d4aa;
    font-size: 0.88rem;
    font-weight: 500;
}
.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #00d4aa;
    animation: blink 1.5s ease-in-out infinite;
}
@keyframes blink {
    0%,100% { opacity:1; }
    50%     { opacity:0.2; }
}

/* Tip Box */
.tip-box {
    background: rgba(59,130,246,0.06);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 14px;
    padding: 1.1rem 1.4rem;
    color: #8ab4f8;
    font-size: 0.88rem;
    line-height: 1.6;
    margin: 1rem 0;
}
.tip-box strong { color: #a8ccff; }

/* Helpers */
.sep {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
    margin: 2.5rem 0;
}

/* Footer */
.foot {
    text-align: center;
    padding: 2rem 0 1.5rem;
    color: #444460;
    font-size: 0.82rem;
    margin-top: 3rem;
    border-top: 1px solid rgba(255,255,255,0.04);
}
.foot a { color: #00d4aa; text-decoration: none; }

/* Expander */
.streamlit-expanderHeader {
    background: rgba(18,18,30,0.5) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 14px !important;
    font-family: 'Inter', sans-serif !important;
}

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* Scrollbar */
::-webkit-scrollbar       { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3a3a52; }

/* Alert Overrides */
.stSuccess > div, .stInfo > div { border-radius: 12px !important; }

/* File Uploader */
[data-testid="stFileUploader"] section {
    border-radius: 14px !important;
    border: 1px dashed rgba(255,255,255,0.1) !important;
    background: rgba(18,18,30,0.4) !important;
}

/* Onboarding Card */
.onboard-card {
    background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(0,212,170,0.08));
    border: 1px solid rgba(124,58,237,0.15);
    border-radius: 16px;
    padding: 2rem;
    text-align: center;
}
.onboard-card h3 {
    color: #fff;
    font-size: 1.3rem;
    margin-bottom: 0.6rem;
}
.onboard-card p {
    color: #7a7a95;
    font-size: 0.92rem;
    line-height: 1.6;
}
.onboard-card code {
    background: rgba(0,212,170,0.12);
    color: #00d4aa;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.85rem;
}
</style>
"""


# ---------------------------------------------------------------------------
# Model loading & prediction
# ---------------------------------------------------------------------------


def load_model_and_artifacts():
    meta_path = MODELS_DIR / "meta.pkl"
    if not meta_path.exists():
        return None, None, None, None, None

    meta = load(meta_path)
    encoder = load(MODELS_DIR / "encoder.pkl")
    scaler = load(MODELS_DIR / "scaler.pkl")
    categories = meta.get("categories", load(MODELS_DIR / "categories.pkl"))
    model_type = meta.get("model_type", "xgboost")

    model_path = meta.get("model_path")
    if model_path and not Path(model_path).is_absolute():
        model_path = MODELS_DIR / Path(model_path).name

    if model_type == "xgboost":
        model = load(model_path)
    else:
        import torch
        from src.train import build_pytorch_model

        input_size = meta.get("input_size", 99)
        num_classes = meta.get("num_classes", len(categories))
        model = build_pytorch_model(input_size, num_classes)
        model.load_state_dict(torch.load(model_path))
        model.eval()

    return model, encoder, scaler, categories, model_type



# ---------------------------------------------------------------------------
# UI Sections
# ---------------------------------------------------------------------------


def render_hero():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">AI-Powered Fitness</div>
            <h1>
                Egzersizlerini<br>
                <span class="grad">Yapay Zeka ile Takip Et</span>
            </h1>
            <p class="hero-sub">
                Kamerani ac, egzersizini yap. Yapay zeka hareketlerini anlik olarak tanir,
                tekrarlarini sayar ve performansini takip eder.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stats():
    cols = st.columns(4)
    stats = [
        ("5", "Desteklenen Egzersiz"),
        ("10", "Hareket Pozisyonu"),
        ("33", "Vucut Noktasi Takibi"),
        (str(st.session_state.sessions_started), "Baslanan Antrenman"),
    ]
    for col, (val, label) in zip(cols, stats):
        with col:
            st.markdown(
                f"""
                <div class="g-card" style="text-align:center; padding:1.4rem 1rem;">
                    <div class="m-val">{val}</div>
                    <div class="m-lbl">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_how_it_works():
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sec-title">Nasil Calisir?</div>', unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sec-sub">Uc basit adimda antrenmanina basla</div>',
        unsafe_allow_html=True,
    )

    steps = [
        (
            "1",
            "Kamerayi Baslat",
            "Asagidaki butona tiklayarak webcam penceresini ac. "
            "Kameranin tam vucudunu gorecegi bir konumda dur.",
        ),
        (
            "2",
            "Egzersizini Yap",
            "Sinav, mekik, squat veya baska bir egzersiz yapmaya basla. "
            "AI modeli hareketlerini anlik olarak tanir.",
        ),
        (
            "3",
            "Sonuclarini Gor",
            "Tekrar sayilari, hareket tipi ve guven orani "
            "ekranda canli olarak gosterilir.",
        ),
    ]

    cols = st.columns(3)
    for col, (num, title, desc) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div class="g-card" style="text-align:center;">
                    <div class="step-num">{num}</div>
                    <div class="step-t">{title}</div>
                    <div class="step-d">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_exercises():
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sec-title">Desteklenen Egzersizler</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sec-sub">AI modelimiz asagidaki hareketleri taniyor</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    for col, ex in zip(cols, EXERCISES):
        with col:
            st.markdown(
                f"""
                <div class="g-card" style="text-align:center; padding:1.6rem 0.8rem;">
                    <div class="accent-top" style="background:{ex['color']};"></div>
                    <div class="ex-icon">{ex['icon']}</div>
                    <div class="ex-name">{ex['name']}</div>
                    <div class="ex-en">{ex['en']}</div>
                    <div class="ex-desc">{ex['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_workout_launcher():
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="cta-box">
            <div class="cta-t">Antrenmanina Basla</div>
            <div class="cta-d">
                Kamerani acarak yapay zeka destekli egzersiz takibine hemen basla
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _pad_l, col_center, _pad_r = st.columns([1, 2, 1])
    with col_center:
        if st.button("Kamerayi Baslat", type="primary", use_container_width=True):
            venv_python = (
                ROOT
                / "venv"
                / ("Scripts" if sys.platform == "win32" else "bin")
                / ("python.exe" if sys.platform == "win32" else "python")
            )
            python_exe = str(venv_python) if venv_python.exists() else sys.executable
            try:
                subprocess.Popen(
                    [python_exe, "-m", "src.camera_demo"],
                    cwd=str(ROOT),
                    creationflags=(
                        subprocess.CREATE_NEW_CONSOLE
                        if sys.platform == "win32"
                        else 0
                    ),
                )
                st.session_state.sessions_started += 1
                st.session_state.camera_active = True
            except Exception as e:
                st.error(f"Kamera baslatilamadi: {e}")

    if st.session_state.camera_active:
        _p1, col_status, _p2 = st.columns([1, 2, 1])
        with col_status:
            st.markdown(
                """
                <div style="text-align:center; margin-top:0.8rem;">
                    <div class="status-pill">
                        <span class="status-dot"></span>
                        Kamera penceresi acildi
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class="tip-box" style="margin-top:0.8rem; text-align:center;">
                    <strong>Ipucu:</strong> Gorev cubugunda acilan kamera penceresine tiklayin.
                    Cikmak icin <strong>Q</strong> tusuna basin. Iyi aydinlatilmis bir ortamda
                    tam vucut gorunumunde durmaniz en iyi sonuclari verir.
                </div>
                """,
                unsafe_allow_html=True,
            )



def render_footer():
    st.markdown(
        """
        <div class="foot">
            <strong>BecomeAPro</strong> &mdash; AI-Powered Exercise Tracker<br>
            <span style="font-size:0.78rem; margin-top:4px; display:inline-block;">
                MediaPipe &bull; XGBoost / PyTorch &bull; Streamlit
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_model_missing():
    """Friendly onboarding when models haven't been trained yet."""
    st.markdown('<div class="sep"></div>', unsafe_allow_html=True)
    _p1, col_c, _p2 = st.columns([1, 3, 1])
    with col_c:
        st.markdown(
            """
            <div class="onboard-card">
                <h3>Model Henuz Egitilmedi</h3>
                <p>
                    Uygulamayi kullanabilmek icin once modeli egitmeniz gerekiyor.
                    Asagidaki komutu calistirarak egitim surecini baslatin:
                </p>
                <p style="margin-top:1rem;">
                    <code>python run_competition.py ExercisePrediction</code>
                </p>
                <p style="margin-top:1rem; font-size:0.85rem; color:#5a5a7a;">
                    Egitim tamamlandiktan sonra bu sayfayi yenileyin.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    model, encoder, scaler, categories, model_type = load_model_and_artifacts()

    render_hero()

    if model is None:
        render_model_missing()
        render_footer()
        return

    render_stats()
    render_how_it_works()
    render_exercises()
    render_workout_launcher()
    render_footer()


if __name__ == "__main__":
    main()
