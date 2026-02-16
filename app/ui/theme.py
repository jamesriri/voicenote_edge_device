PRIMARY_BG = "#0F172A"
SECONDARY_BG = "#1E293B"
ACCENT = "#38BDF8"
TEXT_PRIMARY = "#E2E8F0"
TEXT_MUTED = "#94A3B8"

#  f0f2ef smoke white
RADIUS = "16px"
PADDING = "14px"

def app_stylesheet():
    """Application's stylesheet."""
    
    return f"""
    QWidget {{
        background-color: {PRIMARY_BG};
        color: {TEXT_PRIMARY};
        font-family: 'Inter', sans-serif;
        font-size: 18px;
    }}

    QLabel#title {{
        font-size: 42px;
        font-weight: 600;
        color: {TEXT_PRIMARY};
    }}

    QLabel#subtitle {{
        font-size: 20px;
        color: {TEXT_MUTED};
    }}

    QPushButton {{
        background-color: {SECONDARY_BG};
        border-radius: {RADIUS};
        padding: {PADDING};
        border: 1px solid transparent;
        min-height: 50px;
    }}

    QPushButton:hover {{
        border: 1px solid {ACCENT};
    }}

    QPushButton:pressed {{
        background-color: {ACCENT};
        color: #0F172A;
    }}
    """
