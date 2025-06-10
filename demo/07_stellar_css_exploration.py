"""Demo: Exploring Stellar CSS with StarHTML"""

from starhtml import *

# Include stellar styles and component in the app setup
stellar_setup = [
    Link(rel="stylesheet", href="/static/css/styles.css"),
    Script(type="module", src="/static/js/stellar/stellar.js"),
]

app, rt = star_app(title="Stellar CSS Explorer", hdrs=stellar_setup)


@rt("/")
def home():
    """Stellar CSS Explorer"""
    return Div(
        # Add the sf-stellar component first in the body as per notes
        ft_datastar("sf-stellar", config="/static/css/stellar-config.json"),
        # Debug info with more details
        Div(
            "Theme: ",
            Span(ds_text="$theme"),
            " | BG: ",
            Span(ds_text="getComputedStyle(document.body).backgroundColor"),
            " | --surface-1: ",
            Span(ds_text="getComputedStyle(document.body).getPropertyValue('--surface-1')"),
            style="position: fixed; bottom: 20px; left: 20px; background: #333; color: #fff; padding: 10px; z-index: 9999; border-radius: 5px; font-size: 12px",
        ),
        # Theme toggle button
        Button(
            "🌙 Dark",  # Initial text
            ds_text="$theme === 'light' ? '🌙 Dark' : '☀️ Light'",
            ds_on_click="""
                $theme = ($theme === 'light') ? 'dark' : 'light';
                document.documentElement.setAttribute('data-theme', $theme);
                localStorage.setItem('stellar-theme', $theme);

                // Force style update
                document.body.style.backgroundColor = getComputedStyle(document.body).getPropertyValue('--background');
                document.body.style.color = getComputedStyle(document.body).getPropertyValue('--foreground');
            """,
            cls="theme-toggle",
        ),
        H1("Stellar CSS Explorer", style="text-align: center; font-size: var(--font-size-8); margin: var(--size-5)"),
        Main(
            # Color swatches
            Section(
                H2("Color Palette", style="font-size: var(--font-size-6)"),
                Div(
                    *[
                        Div(
                            f"{color}-{i}",
                            style=f"background: var(--{color}-{i}); padding: var(--size-3); color: var(--{color}-{12 if i < 6 else 0}); border-radius: var(--radius-2)",
                        )
                        for color in ["gray", "blue", "green", "red", "purple", "orange", "brown"]
                        for i in range(13)
                    ],
                    cls="color-grid",
                ),
            ),
            # Typography scale
            Section(
                H2("Typography Scale", style="font-size: var(--font-size-6); margin-top: var(--size-8)"),
                *[
                    Div(
                        f"Font Size {i}: The quick brown fox jumps over the lazy dog",
                        style=f"font-size: var(--font-size-{i}); margin-bottom: var(--size-2)",
                    )
                    for i in range(-2, 11)
                ],
            ),
            # Spacing scale
            Section(
                H2("Spacing Scale", style="font-size: var(--font-size-6); margin-top: var(--size-8)"),
                Div(
                    *[
                        Div(
                            f"size-{i}",
                            style=f"background: var(--blue-5); height: var(--size-{i}); margin-bottom: var(--size-2); display: flex; align-items: center; padding-left: var(--size-2); color: white",
                        )
                        for i in range(-2, 16)
                    ]
                ),
            ),
            # Border radius
            Section(
                H2("Border Radius", style="font-size: var(--font-size-6); margin-top: var(--size-8)"),
                Div(
                    *[
                        Div(
                            f"radius-{i}",
                            style=f"background: var(--purple-5); padding: var(--size-4); margin: var(--size-2); border-radius: var(--radius-{i}); color: white; display: inline-block",
                        )
                        for i in range(1, 7)
                    ]
                ),
            ),
            # Animations
            Section(
                H2("Animations (Click to trigger)", style="font-size: var(--font-size-6); margin-top: var(--size-8)"),
                Div(
                    *[
                        Button(
                            animation,
                            ds_on_click=f"$animations.{animation} = !$animations.{animation}",
                            ds_class=f"{{ 'animation-demo': $animations.{animation} }}",
                            style=f"animation-name: var(--{animation}); padding: var(--size-3); margin: var(--size-2); background: var(--surface-2); border: var(--border-size-1) solid var(--surface-3); border-radius: var(--radius-2)",
                        )
                        for animation in ["fadeIn", "slideInUp", "bounce", "pulse", "float", "spin", "shakeX", "ping"]
                    ],
                    style="display: flex; flex-wrap: wrap",
                ),
            ),
            # Shadows
            Section(
                H2("Shadows", style="font-size: var(--font-size-6); margin-top: var(--size-8)"),
                Div(
                    *[
                        Div(
                            f"shadow-{i}",
                            style=f"background: var(--surface-1); padding: var(--size-4); margin: var(--size-4); box-shadow: var(--shadow-{i}); border-radius: var(--radius-3)",
                        )
                        for i in range(1, 7)
                    ]
                ),
            ),
            # Gradients
            Section(
                H2("Gradients", style="font-size: var(--font-size-6); margin-top: var(--size-8)"),
                Div(
                    *[
                        Div(
                            f"{gradient_type} {color}",
                            style=f"background: var(--{gradient_type}-gradient-{color}{'-' + str(i) if gradient_type == 'linear' else ''}); height: var(--size-12); display: flex; align-items: center; justify-content: center; color: white; font-weight: var(--font-weight-7); border-radius: var(--radius-2)",
                        )
                        for gradient_type in ["radial", "linear"]
                        for color in ["blue", "green", "purple", "red"]
                        for i in ([0] if gradient_type == "radial" else [0, 2, 4])
                    ],
                    style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--size-3)",
                ),
            ),
            style="padding: var(--size-5); max-width: var(--size-content-3); margin: 0 auto",
        ),
        # Datastar signals
        ds_signals={
            "theme": "dark",
            "animations": {
                "fadeIn": False,
                "slideInUp": False,
                "bounce": False,
                "pulse": False,
                "float": False,
                "spin": False,
                "shakeX": False,
                "ping": False,
            },
        },
        # Initialize theme on mount
        ds_on_load="""
            const saved = localStorage.getItem('stellar-theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            $theme = saved || (prefersDark ? 'dark' : 'light');
            document.documentElement.setAttribute('data-theme', $theme);

            // Force a style recalculation
            document.body.style.backgroundColor = getComputedStyle(document.body).getPropertyValue('--background');
            document.body.style.color = getComputedStyle(document.body).getPropertyValue('--foreground');

            // Debug CSS variables
            const styles = getComputedStyle(document.documentElement);
            console.log('--surface-1:', styles.getPropertyValue('--surface-1'));
            console.log('--gray-0:', styles.getPropertyValue('--gray-0'));
            console.log('--gray-9:', styles.getPropertyValue('--gray-9'));
        """,
    )


if __name__ == "__main__":
    print("Stellar CSS Explorer running on http://localhost:5001")
    serve()
