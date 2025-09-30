"""Hero Section - Interactive Demo (Refactored)

The main hero section for StarHTML documentation with animated stars,
typewriter effect, and interactive controls.
"""

from starhtml import *


def hero_animations():
    """Rainbow and star animation styles."""
    return Style("""
        @keyframes rainbow-gradient {
            0%, 100% { color: #fbbf24; }
            14% { color: #facc15; } 28% { color: #a3e635; }
            42% { color: #4ade80; } 57% { color: #38bdf8; }
            71% { color: #a78bfa; } 85% { color: #e879f9; }
        }
        @keyframes rainbow-bg {
            0%, 100% { background-color: #fbbf24; }
            14% { background-color: #facc15; } 28% { background-color: #a3e635; }
            42% { background-color: #4ade80; } 57% { background-color: #38bdf8; }
            71% { background-color: #a78bfa; } 85% { background-color: #e879f9; }
        }
        @keyframes star-pulse { from { opacity: 0.4; } to { opacity: 1; } }
        @keyframes chevron-bounce-inline {
            0%, 20%, 53%, 80%, 100% { transform: translateY(0); }
            40%, 43% { transform: translateY(-6px); }
            70% { transform: translateY(-3px); }
        }
        .rainbow-sync { animation: rainbow-gradient 8s ease-in-out infinite; }
        .rainbow-sync-bg { animation: rainbow-bg 8s ease-in-out infinite; }
        .star-particle {
            position: absolute; pointer-events: none; z-index: 100;
            animation: rainbow-gradient 8s ease-in-out infinite, star-pulse 2s ease-in-out infinite alternate;
            transition: opacity 0.3s ease-out;
        }
    """)


def star_field(stars):
    """Dynamic star field that responds to stars signal."""
    return Div(
        data_effect="""
            const diff = $stars.length - el.children.length;
            if (diff > 0) {
                for (let i = el.children.length; i < $stars.length; i++) {
                    const {x, y} = $stars[i];
                    const star = Object.assign(document.createElement('div'), {
                        className: 'star-particle',
                        innerHTML: '✦'
                    });
                    Object.assign(star.style, {
                        left: `${x * 100}%`,
                        top: `${y * 100}%`,
                        fontSize: `${0.8 + Math.random() * 1.5}rem`,
                        animationDelay: `${Math.random() * 8}s`,
                        opacity: '0',
                        color: '#fbbf24'
                    });
                    el.appendChild(star);
                    requestAnimationFrame(() => {
                        star.classList.add('rainbow-sync');
                        star.style.opacity = '1';
                    });
                }
            } else if (diff < 0) {
                Array.from(el.children).slice($stars.length).forEach(star => star.remove());
            }
        """,
        id="star-field",
        cls="absolute inset-0 pointer-events-none overflow-hidden z-[100]",
    )


def hero_title(show_rainbow):
    return H1(
        Span(
            "star",
            cls="text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-black leading-[0.85] tracking-tight",
            data_class_rainbow_sync=show_rainbow,
        ),
        Span(
            "html",
            cls="text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-black text-black leading-[0.85] tracking-tight",
        ),
        Icon(
            "vaadin:asterisk",
            cls="ml-1 pb-1 sm:pb-2 text-4xl md:text-5xl lg:text-6xl",
            data_class_rainbow_sync=show_rainbow,
            id="title-asterisk",
        ),
        cls="mb-4 flex items-baseline",
    )


def typewriter_tagline(show_rainbow):
    return P(
        Icon(
            "vaadin:asterisk",
            id="asterisk",
            cls="rainbow-sync sm:pb-2 text-4xl md:text-5xl lg:text-6xl opacity-0",
            data_class_rainbow_sync=show_rainbow,
        ),
        Span(" ", id="space", cls="opacity-0 text-gray-300"),
        Span(
            data_on_load="""
                if (window.typewriterInitialized) return;
                window.typewriterInitialized = true;
                
                const texts = ['Write Python', 'Build anything', 'Stay brilliant'];
                let index = 0, isAnimating = false;
                const [asterisk, space, titleAsterisk] = ['asterisk', 'space', 'title-asterisk'].map(id => document.getElementById(id));
                const { animate } = window.Motion || {};
                
                const typewriter = async (text) => {
                    if (!animate || isAnimating) return;
                    isAnimating = true;
                    
                    await Promise.all([asterisk, space, el, titleAsterisk].map(elem => animate(elem, { opacity: 0 }, { duration: 0.2 })));
                    el.textContent = '';
                                        
                    await Promise.all([
                        animate(asterisk, { opacity: 1 }, { duration: 0.2 }),
                        animate(titleAsterisk, { opacity: 1 }, { duration: 0.2 })
                    ]);
                    await new Promise(r => setTimeout(r, 80));
                    await animate(space, { opacity: 1 }, { duration: 0.2 });
                    await new Promise(r => setTimeout(r, 80));
                    await animate(el, { opacity: 1 }, { duration: 0.2 });
                    
                    for (const char of text) {
                        el.textContent += char;
                        await new Promise(r => setTimeout(r, 80));
                    }
                    
                    isAnimating = false;
                    setTimeout(() => !isAnimating && typewriter(texts[++index % texts.length]), 2500);
                };
                
                setTimeout(() => typewriter(texts[0]), 500);
            """,
            id="typewriter-text",
            cls="ml-1 pb-0.5 sm:pb-2",
        ),
        cls="flex items-center text-4xl md:text-5xl lg:text-6xl xl:text-7xl font-black text-gray-300 leading-[1.0] mb-4 min-h-[1.2em]",
    )


def code_example():
    return Div(
        Pre(
            Code(
                """from starhtml import *

# Create reactive state
(stars := Signal('stars', 0))

# Build reactive UI
Button("Add", data_on_click=stars.add(1))
Span(data_text="Stars in the sky: " + stars)""",
                cls="text-gray-800 font-mono text-sm lg:text-base leading-relaxed",
            ),
            cls="m-0 p-0",
        ),
        cls="bg-gray-50 border border-gray-200 rounded-xl p-6 lg:p-8 w-full",
    )


def star_controls(stars, star_count, show_rainbow):
    return Div(
        Div(
            Span("Stars in the sky:", cls="text-gray-600 text-2xl mr-3"),
            Span(data_text=star_count, cls="text-5xl font-black leading-none", data_class_rainbow_sync=show_rainbow),
            cls="mb-6 flex items-baseline",
        ),
        Div(
            Button(
                Icon("tabler:star-filled", width="18", height="18", cls="inline-block mr-1"),
                "Add",
                data_on_click="$stars = [...$stars, {id: Date.now(), x: Math.random(), y: Math.random()}]; $star_count = $stars.length",
                cls="flex items-center justify-center px-4 py-2 text-white font-semibold rounded-lg hover:scale-105 transition-transform duration-200",
                data_class_rainbow_sync_bg=show_rainbow,
            ),
            Button(
                Icon("tabler:star-off", width="18", height="18", cls="inline-block mr-1"),
                "Remove",
                data_on_click="$stars = $stars.slice(0, -1); $star_count = $stars.length",
                cls="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-700 font-semibold rounded-lg hover:bg-gray-300 transition-colors duration-200",
            ),
            Button(
                Icon("tabler:cloud-off", width="18", height="18", cls="inline-block mr-1"),
                "Clear the Sky",
                data_on_click="$stars = []; $star_count = 0",
                cls="flex items-center justify-center px-4 py-2 border-2 border-gray-300 text-gray-700 font-semibold rounded-lg hover:bg-gray-50 transition-colors duration-200",
            ),
            cls="flex items-center gap-2 flex-wrap",
        ),
        Div(
            Div(
                Icon("tabler:sparkles", width="20", height="20", cls="text-amber-500 mr-2"),
                Span("New!", cls="text-amber-600 font-bold text-sm"),
                Span(" ", cls="mx-1"),
                A(
                    "Explore Interactive Demos",
                    href="/demos/",
                    cls="text-black font-semibold underline decoration-2 decoration-amber-400 hover:decoration-amber-500",
                ),
                Icon("tabler:arrow-right", width="18", height="18", cls="ml-2 inline-block"),
                cls="flex items-center justify-center",
            ),
            cls="mt-6 p-3 bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-lg",
        ),
    )


def scroll_indicator():
    return Div(
        Div(
            P("Explore more below", cls="text-sm text-gray-400 mb-2 font-medium"),
            Icon(
                "tabler:chevron-down",
                width="28",
                height="28",
                cls="inline-block relative z-[1] animate-[chevron-bounce-inline_2s_ease-in-out_infinite]",
            ),
            cls="text-gray-300 flex flex-col items-center",
        ),
        cls="mt-10 sm:mt-12 md:mt-16 flex justify-center",
    )


def hero_section():
    """Clean, composable hero section for docs integration."""
    return Section(
        (stars := Signal("stars", [])),
        (star_count := Signal("star_count", 0)),
        (show_rainbow := Signal("show_rainbow", True)),
        hero_animations(),
        star_field(stars),
        hero_title(show_rainbow),
        typewriter_tagline(show_rainbow),
        Div(
            Div(code_example(), cls="w-full lg:w-1/2 xl:w-3/5"),
            Div(star_controls(stars, star_count, show_rainbow), cls="w-full lg:w-1/2 xl:w-2/5 mt-6 lg:mt-0"),
            cls="flex flex-col lg:flex-row gap-8 lg:gap-12 items-start",
        ),
        scroll_indicator(),
        cls="docs-section relative min-h-screen bg-white overflow-hidden flex flex-col justify-start px-6 sm:px-8 lg:px-12 pt-20 md:pt-24 lg:pt-32 pb-16 sm:pb-20 md:pb-24",
        id="hero",
    )


app, rt = star_app(
    title="Hero Section - StarHTML Documentation (Dev Mode)",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Script(src="https://cdn.jsdelivr.net/npm/motion@11.11.13/dist/motion.js"),
    ],
    iconify=True,
)


@rt("/")
def dev_home():
    return Div(
        Div("⚠️ Development Mode - Hero Section", cls="bg-yellow-100 p-4 mb-4 text-center font-mono text-sm"),
        hero_section(),
    )


if __name__ == "__main__":
    print("🚀 Hero Section - Development Mode")
    print("Visit: http://localhost:5090/")

    serve(port=5090)
