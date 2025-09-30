import inspect
import json

from starlighter import CodeBlock, StarlighterStyles

from starhtml import *
from starhtml.datastar import collect, js, match, value
from starhtml.handlers import split_handler

# ============================================================================
# VANILLA JAVASCRIPT COMPARISON (For code display only)
# ============================================================================

VANILLA_JS_CODE = """// ==================== VANILLA JAVASCRIPT DATA TABLE ====================
// State management
let state = {
    employees: [
        { id: '1', name: "Sarah Chen", role: "Senior Engineer", department: "Engineering", status: "active" },
        { id: '2', name: "Marcus Johnson", role: "Product Manager", department: "Product", status: "active" },
        { id: '3', name: "Elena Rodriguez", role: "UX Designer", department: "Design", status: "active" },
        { id: '4', name: "David Kim", role: "DevOps Engineer", department: "Engineering", status: "on_leave" },
        { id: '5', name: "Rachel Thompson", role: "Marketing Director", department: "Marketing", status: "active" },
        { id: '6', name: "Ahmed Hassan", role: "Frontend Developer", department: "Engineering", status: "active" }
    ],
    search: '',
    selected: [],
    employeeStatus: {
        '1': 'active', '2': 'active', '3': 'active',
        '4': 'on_leave', '5': 'active', '6': 'active'
    }
};

// DOM elements cache
const elements = {
    searchInput: null,
    selectAllCheckbox: null,
    tableBody: null,
    selectedCount: null,
    exportBtn: null,
    clearBtn: null
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    elements.searchInput = document.getElementById('search-input');
    elements.selectAllCheckbox = document.getElementById('select-all');
    elements.tableBody = document.getElementById('employee-rows');
    elements.selectedCount = document.getElementById('selected-count');
    elements.exportBtn = document.getElementById('export-btn');
    elements.clearBtn = document.getElementById('clear-btn');

    attachEventListeners();
    render();
});

function attachEventListeners() {
    // Search
    elements.searchInput.addEventListener('input', (e) => {
        state.search = e.target.value;
        render();
    });

    // Select all
    elements.selectAllCheckbox.addEventListener('change', (e) => {
        const visibleIds = getVisibleIds();
        if (e.target.checked) {
            const hiddenSelected = state.selected.filter(id => !visibleIds.includes(id));
            state.selected = [...hiddenSelected, ...visibleIds];
        } else {
            state.selected = state.selected.filter(id => !visibleIds.includes(id));
        }
        render();
    });

    // Export
    elements.exportBtn.addEventListener('click', () => {
        alert(`Exporting ${state.selected.length} employees`);
    });

    // Clear
    elements.clearBtn.addEventListener('click', () => {
        state.selected = [];
        render();
    });
}

function getVisibleIds() {
    if (!state.search) return state.employees.map(e => e.id);
    const query = state.search.toLowerCase();
    return state.employees
        .filter(emp =>
            emp.name.toLowerCase().includes(query) ||
            emp.role.toLowerCase().includes(query) ||
            emp.department.toLowerCase().includes(query)
        )
        .map(e => e.id);
}

function render() {
    renderTable();
    renderCheckboxes();
    renderButtons();
    updateSelectedCount();
    updateSelectAllCheckbox();
}

function renderTable() {
    const query = state.search.toLowerCase();
    elements.tableBody.innerHTML = '';

    state.employees.forEach(emp => {
        const isVisible = !query ||
            emp.name.toLowerCase().includes(query) ||
            emp.role.toLowerCase().includes(query) ||
            emp.department.toLowerCase().includes(query);

        if (!isVisible) return;

        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="checkbox" value="${emp.id}" id="cb-${emp.id}"></td>
            <td>${emp.name}</td>
            <td>${emp.role}</td>
            <td>${emp.department}</td>
            <td><span class="status-badge" id="status-${emp.id}"></span></td>
        `;

        const checkbox = row.querySelector('input');
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                state.selected = [...state.selected, emp.id];
            } else {
                state.selected = state.selected.filter(id => id !== emp.id);
            }
            render();
        });

        const statusBadge = row.querySelector('.status-badge');
        statusBadge.addEventListener('click', () => {
            const current = state.employeeStatus[emp.id];
            state.employeeStatus[emp.id] =
                current === 'active' ? 'on_leave' :
                current === 'on_leave' ? 'inactive' : 'active';
            render();
        });

        elements.tableBody.appendChild(row);
    });
}

function renderCheckboxes() {
    state.employees.forEach(emp => {
        const cb = document.getElementById(`cb-${emp.id}`);
        if (cb) cb.checked = state.selected.includes(emp.id);
    });
}

function renderButtons() {
    const hasSelection = state.selected.length > 0;
    elements.exportBtn.style.display = hasSelection ? 'inline-flex' : 'none';
    elements.clearBtn.style.display = hasSelection ? 'inline-flex' : 'none';
}

function updateSelectedCount() {
    elements.selectedCount.textContent = state.selected.length;
}

function updateSelectAllCheckbox() {
    const visibleIds = getVisibleIds();
    elements.selectAllCheckbox.checked =
        visibleIds.length > 0 && visibleIds.every(id => state.selected.includes(id));
}

// Status badge rendering
function renderStatusBadges() {
    state.employees.forEach(emp => {
        const badge = document.getElementById(`status-${emp.id}`);
        if (!badge) return;

        const status = state.employeeStatus[emp.id];
        badge.textContent =
            status === 'active' ? 'Active' :
            status === 'on_leave' ? 'On Leave' : 'Inactive';
        badge.className = `status-badge status-${status}`;
    });
}

// Call status rendering in main render
const originalRender = render;
render = function() {
    originalRender();
    renderStatusBadges();
};

// Total: ~180 lines vs ~50 lines of Python
"""


def get_styles():
    return Style("""
        /* Modern table styling - clean and minimal */
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }

        .data-table th {
            padding: 0.75rem;
            font-size: 0.75rem;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid #e5e7eb;
            background: transparent;
        }

        .data-table th:not(:first-child) {
            text-align: left;
        }

        .data-table td {
            padding: 0.75rem;
            font-size: 0.875rem;
            color: #1f2937;
            border-bottom: 1px solid #f3f4f6;
        }

        .data-table tbody tr:hover {
            background: #fafafa;
        }

        /* Checkbox styling */
        input[type="checkbox"] {
            width: 16px;
            height: 16px;
            accent-color: #000;
            cursor: pointer;
        }

        /* Status badges - clean pill design */
        .bold-status-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.375rem 0.875rem;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s ease;
            min-width: 90px;
            text-align: center;
            letter-spacing: 0.025em;
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
        }

        .status-active {
            background: #dcfce7;
            color: #15803d;
            border: 1px solid #86efac;
        }

        .status-on_leave {
            background: #fef3c7;
            color: #a16207;
            border: 1px solid #fde68a;
        }

        .status-inactive {
            background: #f3f4f6;
            color: #4b5563;
            border: 1px solid #e5e7eb;
        }

        .bold-status-badge:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Split panels for code */
        .code-split {
            height: 600px;
            overflow: hidden;
        }
        
        .code-panel {
            padding: 1rem;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.75rem;
            line-height: 1.5;
            overflow: auto;
            height: 100%;
            background: white;
        }
        
        /* Override Starlighter container borders */
        .code-panel > div {
            border: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        .code-panel pre {
            border: none !important;
            margin: 0 !important;
        }
        
        .python-header {
            background: #3776ab;
            color: white;
            padding: 0.5rem 1rem;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .js-header {
            background: #f7df1e;
            color: #323330;
            padding: 0.5rem 1rem;
            font-size: 0.75rem;
            font-weight: 600;
        }
    """)


def create_hero():
    return Div(
        H1("Python First", cls="text-2xl font-bold text-black mb-2"),
        P(
            "Write Python and build anything. JavaScript available as an escape hatch when needed.",
            cls="text-gray-600 mb-4",
        ),
        Div(
            Span(
                Icon("material-symbols:code", width="16", height="16", cls="mr-1 text-blue-600"),
                "Python → HTML",
                cls="inline-flex items-center text-sm text-gray-700 mr-6",
            ),
            Span(
                Icon("material-symbols:dns", width="16", height="16", cls="mr-1 text-purple-600"),
                "Server-Side First",
                cls="inline-flex items-center text-sm text-gray-700 mr-6",
            ),
            Span(
                Icon("material-symbols:data-object", width="16", height="16", cls="mr-1 text-green-600"),
                "Declarative Attributes",
                cls="inline-flex items-center text-sm text-gray-700 mr-6",
            ),
            Span(
                Icon("material-symbols:bolt", width="16", height="16", cls="mr-1 text-yellow-600"),
                "Sprinkle Reactivity",
                cls="inline-flex items-center text-sm text-gray-700",
            ),
            cls="mb-6 pb-4 border-b border-gray-200",
        ),
    )


def get_sample_employees():
    return [
        {"id": 1, "name": "Sarah Chen", "role": "Senior Engineer", "department": "Engineering", "status": "active"},
        {"id": 2, "name": "Marcus Johnson", "role": "Product Manager", "department": "Product", "status": "active"},
        {"id": 3, "name": "Elena Rodriguez", "role": "UX Designer", "department": "Design", "status": "active"},
        {"id": 4, "name": "David Kim", "role": "DevOps Engineer", "department": "Engineering", "status": "on_leave"},
        {
            "id": 5,
            "name": "Rachel Thompson",
            "role": "Marketing Director",
            "department": "Marketing",
            "status": "active",
        },
        {
            "id": 6,
            "name": "Ahmed Hassan",
            "role": "Frontend Developer",
            "department": "Engineering",
            "status": "active",
        },
    ]


def _get_visible_ids_js(employees):
    search_map = {str(emp["id"]): f"{emp['name']} {emp['role']} {emp['department']}".lower() for emp in employees}
    return f"""
        const searchMap = {json.dumps(search_map)};
        const visibleIds = Object.keys(searchMap).filter(id =>
            !$search || searchMap[id].includes($search.toLowerCase())
        );
    """


def _search_input(search):
    return Input(placeholder="Search employees...", data_bind=search, cls="w-full p-3 border rounded-lg mb-4")


def _employee_stats(employees, selected):
    return Div(
        P(f"Showing {len(employees)} of {len(employees)} employees"),
        P("Selected ", Span(data_text=selected.length, cls="font-bold"), " employees"),
        cls="flex justify-between text-sm text-gray-600 mb-4",
    )


def _checkbox_sync_effect():
    # Browsers ignore checked attribute after user interaction - must update .checked property
    return Div(
        data_effect=js("""
            document.querySelectorAll('[id^=emp-]').forEach(cb =>
                cb.checked = $selected.includes(cb.value)
            );
        """),
        style="display: none",
    )


def _table_header(employees):
    return Thead(
        Tr(
            Th(
                Input(
                    type="checkbox",
                    id="select-all",
                    data_attr_checked=Signal("all_selected", _ref_only=True),
                    data_on_change=js(f"""
                        {_get_visible_ids_js(employees)}
                        $selected = evt.target.checked
                            ? [...$selected.filter(id => !visibleIds.includes(id)), ...visibleIds]
                            : $selected.filter(id => !visibleIds.includes(id));
                    """),
                    cls="cursor-pointer",
                ),
                cls="p-3 text-center",
            ),
            Th("Name", cls="p-3 text-left"),
            Th("Role", cls="p-3 text-left"),
            Th("Department", cls="p-3 text-left"),
            Th("Status", cls="p-3 text-left"),
        )
    )


def _action_buttons(selected):
    return Div(
        Button(
            Icon("material-symbols:download", width="16", height="16", cls="mr-1.5"),
            "Export ",
            Span(data_text=selected.length, cls="mx-1"),
            " selected",
            style="display: none",
            data_show=selected.length > 0,
            data_on_click=js("alert(`Exporting ${$selected.length} employees`)"),
            cls="inline-flex items-center bg-black text-white px-4 py-2 rounded-lg font-medium text-sm hover:bg-gray-800 transition-colors mr-2",
        ),
        Button(
            Icon("material-symbols:close", width="16", height="16", cls="mr-1.5"),
            "Clear selection",
            style="display: none",
            data_on_click=selected.set([]),
            data_show=selected.length > 0,
            cls="inline-flex items-center bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium text-sm hover:bg-gray-200 transition-colors border border-gray-200",
        ),
        cls="mt-4 flex gap-2",
    )


def minimal_reactive_table():
    employees = get_sample_employees()

    return Div(
        (search := Signal("search", "")),
        (selected := Signal("selected", [])),
        (employee_status := Signal("employee_status", {str(emp["id"]): emp["status"] for emp in employees})),
        Signal(
            "all_selected",
            js(f"""
            {_get_visible_ids_js(employees)}
            return visibleIds.length && visibleIds.every(id => $selected.includes(id));
        """),
        ),
        _search_input(search),
        _employee_stats(employees, selected),
        _checkbox_sync_effect(),
        Div(
            Table(
                _table_header(employees),
                Tbody(*[employee_row(emp, search, selected, employee_status) for emp in employees]),
                cls="w-full border-collapse bg-white rounded-lg overflow-hidden data-table",
            ),
            cls="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0",
        ),
        _action_buttons(selected),
    )


def employee_row(emp, search, selected, employee_status):
    emp_id = str(emp["id"])
    status_ref = js(f"$employee_status['{emp_id}']")

    return Tr(
        Td(
            Input(
                type="checkbox",
                value=emp_id,
                id=f"emp-{emp_id}",
                data_on_change=js(f"""
                    $selected = evt.target.checked
                        ? [...$selected, '{emp_id}']
                        : $selected.filter(id => id !== '{emp_id}');
                """),
                cls="cursor-pointer",
            ),
            cls="p-3 text-center",
        ),
        Td(emp["name"], cls="p-3 font-medium text-gray-900"),
        Td(emp["role"], cls="p-3 text-gray-600"),
        Td(emp["department"], cls="p-3 text-gray-600"),
        Td(
            Span(
                data_text=match(
                    status_ref, active="Active", on_leave="On Leave", inactive="Inactive", default="Unknown"
                ),
                data_on_click=employee_status[emp_id].toggle("active", "on_leave", "inactive"),
                data_attr_class=collect(
                    [
                        (value(True), "bold-status-badge"),
                        (status_ref == "active", "status-active"),
                        (status_ref == "on_leave", "status-on_leave"),
                        (status_ref == "inactive", "status-inactive"),
                    ]
                ),
                title="Click to cycle status",
            ),
            cls="p-3",
        ),
        data_show=(search == "")
        | value(emp["name"]).lower().contains(search.lower())
        | value(emp["role"]).lower().contains(search.lower())
        | value(emp["department"]).lower().contains(search.lower()),
        cls="transition-colors",
    )


def create_data_table():
    return Div(
        H4("Live Demo: Reactive Data Table", cls="font-semibold mb-2"),
        P(
            "Search, select, and toggle status - all built in Python with full reactive power",
            cls="text-sm text-gray-600 mb-4",
        ),
        minimal_reactive_table(),
        cls="p-4 bg-white border border-gray-200 col-span-full",
    )


def get_python_implementation_source():
    sources = [
        "from starhtml import *",
        "import json\n",
        inspect.getsource(get_sample_employees),
        inspect.getsource(_get_visible_ids_js),
        inspect.getsource(_search_input),
        inspect.getsource(_employee_stats),
        inspect.getsource(_checkbox_sync_effect),
        inspect.getsource(_table_header),
        inspect.getsource(_action_buttons),
        inspect.getsource(minimal_reactive_table),
        inspect.getsource(employee_row),
    ]
    return "\n".join(sources)


def create_code_comparison():
    python_code = get_python_implementation_source()

    python_panel = Div(
        Div("Python (~145 lines)", cls="python-header"), Div(CodeBlock(python_code, lang="python"), cls="code-panel")
    )

    js_panel = Div(
        Div("JavaScript (~180 lines)", cls="js-header"),
        Pre(Code(VANILLA_JS_CODE, cls="language-javascript"), cls="code-panel"),
    )

    return Div(
        H4("Code Comparison", cls="font-semibold mb-2"),
        P("Drag the divider to compare Python vs JavaScript implementations", cls="text-sm text-gray-600 mb-3"),
        Div(
            Div(
                Div(python_panel, cls="panel left"),
                Div(data_split="code_split:horizontal:50,50"),
                Div(js_panel, cls="panel right"),
                cls="split-container flex h-full",
            ),
            cls="code-split border border-gray-200 rounded-lg overflow-hidden",
        ),
        cls="col-span-full mb-8",
    )


def create_examples():
    examples = [
        (
            "Search Filtering",
            "value(emp['name']).lower()\n  .contains(search.lower())",
            "emp.name.toLowerCase()\n  .includes(search.toLowerCase())",
            "blue",
        ),
        (
            "State Management",
            "selected = Signal('selected', [])",
            "let selected = []\n// + 50 lines of boilerplate",
            "green",
        ),
        ("Reactivity", "data_show=count > 0", "el.style.display =\n  count > 0 ? 'block' : 'none'", "purple"),
    ]

    return Div(
        H4("Key Transformations", cls="font-semibold mb-4"),
        Div(
            *[
                Div(
                    H5(title, cls="font-semibold text-sm mb-3"),
                    Div("Python:", cls="text-xs font-semibold text-gray-600 mb-1"),
                    Pre(
                        Code(py, cls="text-xs"),
                        cls=f"bg-{color}-50 p-2 rounded mb-2 text-{color}-900",
                        style="white-space: pre-wrap; word-break: break-word;",
                    ),
                    Div("JavaScript:", cls="text-xs font-semibold text-gray-600 mb-1"),
                    Pre(
                        Code(js, cls="text-xs"),
                        cls="bg-red-50 p-2 rounded text-red-900",
                        style="white-space: pre-wrap; word-break: break-word;",
                    ),
                    cls="p-4 bg-white border border-gray-200",
                )
                for title, py, js, color in examples
            ],
            cls="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-3 gap-4",
        ),
    )


def python_first_section():
    return Div(
        get_styles(),
        StarlighterStyles("github-light"),
        create_hero(),
        Div(
            Div(create_data_table(), create_code_comparison(), cls="grid grid-cols-1 gap-4 mb-4"),
            create_examples(),
            cls="p-2 sm:p-4 bg-gray-50",
        ),
    )


# Standalone app
app, rt = star_app(
    title="Python First Philosophy",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        StarlighterStyles("github-light"),
        split_handler(signal="code_split", responsive=False),
        Style("body { background: white; font-family: system-ui, sans-serif; }"),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return python_first_section(embedded=False)


if __name__ == "__main__":
    serve(port=5001)
