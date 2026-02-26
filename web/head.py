"""Global <head> elements for star_app(hdrs=...)."""

from starhtml import JsonLd, Link, Meta, Script, Socials, Style

SITE_URL = "https://starhtml.com"

SITE_TITLE = "StarHTML — Python-First Hypermedia Framework"
SITE_DESCRIPTION = (
    "Build reactive web UIs entirely in Python. StarHTML combines "
    "Datastar's reactive signals with server-sent events for real-time, "
    "type-safe hypermedia applications — no JavaScript required."
)

_JSONLD_DICT = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "StarHTML",
    "applicationCategory": "DeveloperApplication",
    "operatingSystem": "Any",
    "description": SITE_DESCRIPTION,
    "url": SITE_URL,
    "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD",
        "description": "Open source, Apache 2.0 license",
    },
    "publisher": {
        "@type": "Organization",
        "name": "StarHTML",
        "url": SITE_URL,
    },
}

_INLINE_CSS = """\
* { box-sizing: border-box; }

:root {
    --split-handle-size: 8px;
    --split-handle-color: rgba(0, 0, 0, 0.15);
    --split-handle-hover-color: rgba(0, 123, 255, 0.3);
    --split-handle-active-color: rgba(0, 123, 255, 0.5);
}

body, html { margin: 0; padding: 0; width: 100%; overflow-x: hidden; }

.docs-section { min-height: 100vh; scroll-margin-top: 80px; }

.docs-nav-item {
    transition: all 0.2s ease-out;
    border-left: 3px solid transparent;
}
.docs-nav-item.active {
    border-left-color: #000;
    background: rgba(0, 0, 0, 0.05);
}

.code-example {
    background: #1a1a1a;
    border-radius: 12px;
    overflow: hidden;
    transition: transform 0.2s ease-out;
}
.code-example:hover { transform: translateY(-2px); }

.mini-demo {
    background: white;
    border: 2px solid #f3f4f6;
    border-radius: 16px;
    transition: all 0.2s ease-out;
}
.mini-demo:hover {
    border-color: #d1d5db;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
}

.scroll-progress-container {
    position: fixed;
    top: 60px;
    left: 0;
    width: 100%;
    height: 4px;
    background: rgba(0, 0, 0, 0.1);
    z-index: 40;
}
.scroll-progress-fill {
    height: 100%;
    background-color: #fbbf24;
    transition: width 0.1s ease;
    width: 0%;
    animation: rainbow-bg 8s ease-in-out infinite;
}

.fade-in-up {
    opacity: 1;
    transform: translateY(0);
    transition: all 0.6s ease-out;
}

.navigation-unselectable {
    user-select: none;
    -webkit-user-select: none;
}

#markdown-content-container {
    user-select: text;
    -webkit-user-select: text;
}

@media (max-width: 640px) {
    .desktop-only { display: none !important; }
    .mobile-only { display: flex !important; }
}
@media (min-width: 641px) {
    .desktop-only { display: flex !important; }
    .mobile-only { display: none !important; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
"""


def _build_hdrs() -> tuple:
    return (
        Link(rel="preconnect", href="https://cdn.jsdelivr.net", crossorigin=""),
        Link(
            rel="icon",
            href='data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<text y=".9em" font-size="90">⭐</text></svg>',
        ),
        Meta(name="theme-color", content="#000000"),
        *Socials(
            title=SITE_TITLE,
            site_name="StarHTML",
            description=SITE_DESCRIPTION,
            image="/static/images/og/starhtml.jpg",
            url=SITE_URL,
            w=1200,
            h=630,
            card="summary_large_image",
        ),
        JsonLd(_JSONLD_DICT),
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Script(src="https://cdn.jsdelivr.net/npm/motion@11.11.13/dist/motion.js"),
        Style(_INLINE_CSS),
    )


hdrs = _build_hdrs()
