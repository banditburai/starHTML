"""Debug theme toggle initialization"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from starhtml import *
from components.ui import Button, IconifyIcon

app, rt = star_app(title="Theme Debug Test")

@rt('/')
def home():
    return Div(
        # Theme initialization
        Script("""
            console.log('Theme init script running...');
            const saved = localStorage.getItem('theme');
            const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const isDark = saved === 'dark' || (!saved && systemDark);
            console.log('Saved theme:', saved);
            console.log('System dark:', systemDark);
            console.log('Should be dark:', isDark);
            
            if (isDark) {
                document.documentElement.classList.add('dark');
                console.log('Added dark class');
            }
            console.log('Has dark class after init:', document.documentElement.classList.contains('dark'));
        """),
        
        # Theme toggle with debugging
        Div(
            Button(
                IconifyIcon("ph:sun-bold", ds_show="!$isDark", cls="h-[1.2rem] w-[1.2rem]"),
                IconifyIcon("ph:moon-bold", ds_show="$isDark", cls="h-[1.2rem] w-[1.2rem]"),
                ds_on_click="""
                    console.log('Button clicked. Current $isDark:', $isDark);
                    console.log('Current DOM dark class:', document.documentElement.classList.contains('dark'));
                    $isDark = !$isDark;
                    console.log('New $isDark:', $isDark);
                    document.documentElement.classList.toggle('dark');
                    console.log('New DOM dark class:', document.documentElement.classList.contains('dark'));
                    localStorage.setItem('theme', $isDark ? 'dark' : 'light');
                """,
                size="icon",
                variant="outline",
                aria_label="Toggle theme"
            ),
            ds_signals={"isDark": "document.documentElement.classList.contains('dark')"},
            ds_init="""
                console.log('Datastar init running...');
                console.log('DOM has dark class:', document.documentElement.classList.contains('dark'));
                console.log('Initial $isDark will be:', document.documentElement.classList.contains('dark'));
            """,
            cls="fixed top-4 right-4"
        ),
        
        H1("Theme Debug Test"),
        P("Check console logs and test the theme toggle."),
        P("Current theme state: ", Span(ds_text="$isDark ? 'Dark' : 'Light'")),
        
        cls="p-8"
    )

if __name__ == "__main__":
    print("Theme Debug Test running on http://localhost:5005")
    serve(port=5005)