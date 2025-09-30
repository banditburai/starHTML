"""Routing Patterns - Dynamic routes and parameters"""

from starhtml import *

app, rt = star_app(
    title="Routing Patterns",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
            .route-active { background: #f3f4f6; border-left: 4px solid #3b82f6; }
        """),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return Div(
        # Main container
        Div(
            # Header
            Div(
                H1("08", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Routing Patterns", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P("Dynamic routes, parameters, and navigation", cls="text-lg text-gray-600 mt-4"),
                cls="mb-16",
            ),
            # === 1. BASIC NAVIGATION ===
            Div(
                H3("Basic Navigation", cls="text-2xl font-bold text-black mb-6"),
                # Navigation menu
                Div(
                    Button(
                        "Home",
                        data_on_click=get("page/home"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    Button(
                        "About",
                        data_on_click=get("page/about"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    Button(
                        "Contact",
                        data_on_click=get("page/contact"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    cls="flex gap-2 mb-6",
                ),
                # Page content area
                Div(
                    Div(
                        P("Welcome to the home page", cls="text-lg"),
                    ),
                    id="page-content",
                    cls="p-6 bg-white border border-gray-200 min-h-[150px]",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # === 2. DYNAMIC ROUTES ===
            Div(
                H3("Dynamic Routes", cls="text-2xl font-bold text-black mb-6"),
                P("Load user profiles dynamically:", cls="mb-4 text-gray-600"),
                # User list
                Div(
                    Button(
                        Icon("material-symbols:person", width="20", height="20", cls="inline mr-2"),
                        "Alice (ID: 1)",
                        data_on_click=get("user/1"),
                        cls="px-4 py-2 bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors",
                    ),
                    Button(
                        Icon("material-symbols:person", width="20", height="20", cls="inline mr-2"),
                        "Bob (ID: 2)",
                        data_on_click=get("user/2"),
                        cls="px-4 py-2 bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors",
                    ),
                    Button(
                        Icon("material-symbols:person", width="20", height="20", cls="inline mr-2"),
                        "Charlie (ID: 3)",
                        data_on_click=get("user/3"),
                        cls="px-4 py-2 bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors",
                    ),
                    cls="flex gap-2 mb-6",
                ),
                # User profile area
                Div(
                    Div(
                        P("Select a user to view their profile", cls="text-gray-500"),
                    ),
                    id="user-profile",
                    cls="p-6 bg-white border border-gray-200",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # === 3. QUERY PARAMETERS ===
            Div(
                (search_term := Signal("search_term", "")),
                (search_category := Signal("search_category", "all")),
                H3("Query Parameters", cls="text-2xl font-bold text-black mb-6"),
                P("Search with different filters:", cls="mb-4 text-gray-600"),
                # Search controls
                Div(
                    Input(
                        type="text",
                        placeholder="Enter search term...",
                        data_bind=search_term,
                        cls="w-full px-3 py-2 border border-gray-300 focus:outline-none focus:border-gray-500 mb-2 sm:mb-0 sm:rounded-l-lg sm:border-r-0",
                    ),
                    Select(
                        Option("All", value="all"),
                        Option("Products", value="products"),
                        Option("Users", value="users"),
                        Option("Posts", value="posts"),
                        data_bind=search_category,
                        cls="w-full px-3 py-2 border border-gray-300 focus:outline-none mb-2 sm:mb-0 sm:w-auto sm:border-t sm:border-b",
                    ),
                    Button(
                        "Search",
                        data_on_click=post("search"),
                        cls="w-full px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors sm:w-auto sm:rounded-r-lg",
                    ),
                    cls="flex flex-col sm:flex-row mb-6",
                ),
                # Search results area
                Div(
                    Div(
                        P("Enter a search query above", cls="text-gray-500"),
                    ),
                    id="search-results",
                    cls="p-6 bg-gray-50 border border-gray-200",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # === 4. NESTED ROUTES ===
            Div(
                H3("Nested Routes", cls="text-2xl font-bold text-black mb-6"),
                P("Navigate through nested content:", cls="mb-4 text-gray-600"),
                # Main navigation
                Div(
                    Button(
                        "Dashboard",
                        data_on_click=get("dashboard"),
                        cls="px-4 py-2 bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors",
                    ),
                    Button(
                        "Settings",
                        data_on_click=get("settings"),
                        cls="px-4 py-2 bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors",
                    ),
                    cls="flex gap-2 mb-4",
                ),
                # Nested content area with sub-navigation
                Div(
                    Div(
                        P("Select Dashboard or Settings to see nested content", cls="text-gray-500 p-4"),
                    ),
                    id="nested-content",
                    cls="bg-white border border-gray-200",
                ),
                cls="mb-12 p-8 bg-purple-50",
            ),
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen overflow-y-auto",
    )


# === ROUTE HANDLERS ===


@rt("/page/{page_name}")
@sse
def load_page(req, page_name: str):
    """Load different page content"""
    pages = {
        "home": Div(
            H2("Welcome Home", cls="text-2xl font-bold mb-4"),
            P("This is the home page content.", cls="mb-2"),
            P("Navigate using the buttons above to see different pages.", cls="text-gray-600"),
        ),
        "about": Div(
            H2("About Us", cls="text-2xl font-bold mb-4"),
            P("Learn more about our application.", cls="mb-2"),
            P("We build amazing web experiences with StarHTML!", cls="text-gray-600"),
        ),
        "contact": Div(
            H2("Contact", cls="text-2xl font-bold mb-4"),
            P("Get in touch with us.", cls="mb-2"),
            P("Email: hello@example.com", cls="text-gray-600"),
        ),
    }

    content = pages.get(page_name, Div(P("Page not found", cls="text-red-600")))
    yield elements(content, "#page-content", "inner")


@rt("/user/{user_id}")
@sse
def load_user(req, user_id: int):
    """Load user profile by ID"""
    users = {
        1: {"name": "Alice Johnson", "role": "Developer", "joined": "2023-01-15", "projects": 12},
        2: {"name": "Bob Smith", "role": "Designer", "joined": "2023-03-22", "projects": 8},
        3: {"name": "Charlie Brown", "role": "Manager", "joined": "2022-11-08", "projects": 15},
    }

    user = users.get(user_id)
    if user:
        profile = Div(
            Div(Icon("material-symbols:account-circle", width="64", height="64", cls="text-blue-600"), cls="mb-4"),
            H3(user["name"], cls="text-xl font-bold mb-2"),
            P(f"Role: {user['role']}", cls="text-gray-600 mb-1"),
            P(f"Joined: {user['joined']}", cls="text-gray-600 mb-1"),
            P(f"Projects: {user['projects']}", cls="text-gray-600"),
            cls="text-center",
        )
    else:
        profile = P("User not found", cls="text-red-600")

    yield elements(profile, "#user-profile", "inner")


@rt("/search")
@sse
def search(req, search_term: str = "", search_category: str = "all"):
    """Search with query parameters"""
    if not search_term:
        yield elements(P("Please enter a search term", cls="text-gray-500"), "#search-results", "inner")
        return

    # Simulate search results
    results = Div(
        H3("Search Results", cls="text-lg font-bold mb-4"),
        P(f"Query: '{search_term}'", cls="mb-2"),
        P(f"Category: {search_category}", cls="mb-4 text-gray-600"),
        Div(
            Div(f"Result 1 for '{search_term}'", cls="p-3 bg-white border-b border-gray-200 hover:bg-gray-50"),
            Div(f"Result 2 for '{search_term}'", cls="p-3 bg-white border-b border-gray-200 hover:bg-gray-50"),
            Div(f"Result 3 for '{search_term}'", cls="p-3 bg-white border-b border-gray-200 hover:bg-gray-50"),
            cls="border border-gray-300 rounded",
        ),
    )

    yield elements(results, "#search-results", "inner")


@rt("/dashboard")
@sse
def dashboard(req):
    """Load dashboard with sub-navigation"""
    content = Div(
        # Sub-navigation
        Div(
            Button(
                "Overview",
                data_on_click=get("dashboard/overview"),
                cls="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 transition-colors",
            ),
            Button(
                "Analytics",
                data_on_click=get("dashboard/analytics"),
                cls="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 transition-colors",
            ),
            Button(
                "Reports",
                data_on_click=get("dashboard/reports"),
                cls="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 transition-colors",
            ),
            cls="flex gap-2 p-4 border-b border-gray-200",
        ),
        # Sub-content area
        Div(
            P("Dashboard Overview", cls="font-semibold"),
            P("View your dashboard metrics here", cls="text-gray-600 mt-2"),
            id="sub-content",
            cls="p-4",
        ),
    )

    yield elements(content, "#nested-content", "inner")


@rt("/settings")
@sse
def settings(req):
    """Load settings with sub-navigation"""
    content = Div(
        # Sub-navigation
        Div(
            Button(
                "Profile",
                data_on_click=get("settings/profile"),
                cls="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 transition-colors",
            ),
            Button(
                "Security",
                data_on_click=get("settings/security"),
                cls="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 transition-colors",
            ),
            Button(
                "Preferences",
                data_on_click=get("settings/preferences"),
                cls="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 transition-colors",
            ),
            cls="flex gap-2 p-4 border-b border-gray-200",
        ),
        # Sub-content area
        Div(
            P("Profile Settings", cls="font-semibold"),
            P("Manage your profile information", cls="text-gray-600 mt-2"),
            id="sub-content",
            cls="p-4",
        ),
    )

    yield elements(content, "#nested-content", "inner")


@rt("/dashboard/{section}")
@sse
def dashboard_section(req, section: str):
    """Load dashboard sub-sections"""
    sections = {
        "overview": ("Dashboard Overview", "Key metrics and summary"),
        "analytics": ("Analytics Dashboard", "Detailed analytics and insights"),
        "reports": ("Reports Center", "Generate and view reports"),
    }

    title, desc = sections.get(section, ("Unknown", "Section not found"))
    content = Div(
        P(title, cls="font-semibold"),
        P(desc, cls="text-gray-600 mt-2"),
    )

    yield elements(content, "#sub-content", "inner")


@rt("/settings/{section}")
@sse
def settings_section(req, section: str):
    """Load settings sub-sections"""
    sections = {
        "profile": ("Profile Settings", "Update your name, email, and avatar"),
        "security": ("Security Settings", "Manage passwords and 2FA"),
        "preferences": ("Preferences", "Customize your experience"),
    }

    title, desc = sections.get(section, ("Unknown", "Section not found"))
    content = Div(
        P(title, cls="font-semibold"),
        P(desc, cls="text-gray-600 mt-2"),
    )

    yield elements(content, "#sub-content", "inner")


if __name__ == "__main__":
    serve(port=5018)
