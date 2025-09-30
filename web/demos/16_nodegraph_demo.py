"""Demo: Interactive Workflow Builder
A practical demo showing canvas + drag to build visual workflows with real-time state tracking
"""

import json

from starhtml import *

# ===== REUSABLE STYLES =====

WORKFLOW_STYLES = """
    body {
        margin: 0;
        padding: 0;
        overflow: hidden;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .canvas-viewport.fullpage {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        background: #2a2a2a;
        cursor: grab;
        touch-action: none;
        user-select: none;
        -webkit-user-select: none;
        overscroll-behavior: none;
    }
    
    .canvas-viewport.fullpage:active {
        cursor: grabbing;
    }
    
    .canvas-container {
        position: relative;
        width: 100%;
        height: 100%;
        transform-origin: 0 0;
        will-change: transform;
    }
"""

NODE_STYLES = """
    /* Workflow Node Styles */
    .workflow-node {
        position: absolute;
        background: #2a2a3a;
        border: 2px solid #3a3a4a;
        border-radius: 12px;
        padding: 16px;
        min-width: 140px;
        max-width: 200px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        user-select: none;
        cursor: grab;
        transition: box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
        z-index: 1;
        pointer-events: auto;
        display: flex;
        flex-direction: column;
        gap: 8px;
        will-change: transform;
        contain: layout style;
    }
    
    /* Status dot */
    .status-dot {
        position: absolute;
        top: 8px;
        right: 8px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        font-size: 12px;
        line-height: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: color 0.2s ease;
    }
    
    .status-dot.status-ready { color: #10B981; }
    .status-dot.status-running {
        color: #F59E0B;
        animation: pulse 1s infinite;
    }
    .status-dot.status-complete { color: #10B981; }
    .status-dot.status-pending { color: #6B7280; }
    
    .workflow-node:hover {
        border-color: #4a4a5a;
        box-shadow: 0 6px 16px rgba(0,0,0,0.5);
    }
    
    .workflow-node:active {
        cursor: grabbing;
    }
    
    /* CRITICAL: Disable ALL transitions when dragging */
    .is-dragging,
    .is-dragging *,
    body.is-drag-active .workflow-node,
    body.is-drag-active .workflow-node * {
        transition: none !important;
    }
    
    .workflow-node.selected {
        border-color: #4A90E2;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.4), 0 6px 20px rgba(74, 144, 226, 0.2);
    }
    
    /* Node state styles */
    .workflow-node.node_running {
        border-color: #F59E0B;
        box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.3), 0 6px 16px rgba(245, 158, 11, 0.2);
        animation: nodeGlow 2s infinite;
    }
    
    .workflow-node.node_complete {
        border-color: #10B981;
        background: linear-gradient(135deg, #2a3a2a, #2a2a3a);
    }
    
    @keyframes nodeGlow {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.85; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
"""

NODE_TYPE_STYLES = """
    /* Node Type Variations */
    .workflow-node.node-start {
        border-color: #10B981;
        background: linear-gradient(135deg, #2a3a2a, #2a2a3a);
    }
    
    .workflow-node.node-process {
        border-color: #3B82F6;
        background: linear-gradient(135deg, #2a2a3a, #3a3a4a);
    }
    
    .workflow-node.node-action {
        border-color: #F59E0B;
        background: linear-gradient(135deg, #3a2a2a, #2a2a3a);
    }
    
    .workflow-node.node-end {
        border-color: #EF4444;
        background: linear-gradient(135deg, #3a2a2a, #2a2a3a);
    }
    
    .node-title {
        font-weight: 600;
        color: #ffffff;
        font-size: 13px;
        flex: 1;
    }
    
    .node-type-badge {
        font-size: 9px;
        padding: 2px 6px;
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        display: inline-block;
    }
"""

TOOLBAR_STYLES = """
    /* Toolbar Styles */
    .modern-toolbar {
        position: fixed;
        bottom: 1rem;
        right: 1rem;
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 12px;
        background: rgba(30, 30, 30, 0.95);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        z-index: 1000;
        min-width: 140px;
    }
    
    .toolbar-btn {
        width: 32px;
        height: 32px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #e5e7eb;
        background: rgba(255, 255, 255, 0.08);
    }
    
    .toolbar-btn:hover {
        background: rgba(255, 255, 255, 0.15);
        color: #ffffff;
        transform: translateY(-1px);
    }
    
    .reset-btn {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
    }
    
    .reset-btn:hover {
        background: rgba(59, 130, 246, 0.3);
        color: #93c5fd;
    }
    
    .workflow-btn {
        padding: 8px 12px;
        background: #10B981;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        transition: background 0.2s;
    }
    
    .workflow-btn:hover:not(:disabled) {
        background: #059669;
    }
    
    .workflow-btn:disabled {
        background: #374151;
        color: #6B7280;
        cursor: not-allowed;
    }
    
    .reset-workflow-btn {
        padding: 6px 12px;
        background: #374151;
        color: #9ca3af;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 11px;
        transition: background 0.2s;
    }
    
    .reset-workflow-btn:hover {
        background: #4B5563;
        color: #D1D5DB;
    }
    
    .status-display {
        padding: 0 8px;
        border-top: 1px solid rgba(255, 255, 255, 0.15);
        padding-top: 8px;
    }
    
    .zoom-indicator {
        font-family: 'SF Mono', 'Monaco', monospace;
        font-size: 12px;
        font-weight: 500;
        color: #9ca3af;
        white-space: nowrap;
    }
"""

app, rt = star_app(
    title="Composable Node Graph Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4", iconify=True),
        # Canvas handler for pan/zoom/grid
        (
            canvas := canvas_handler(
                background_color="#2a2a2a",
                grid_color="rgba(255,255,255,0.1)",
                minor_grid_color="rgba(255,255,255,0.05)",
            )
        ),
        # Single drag handler for all nodes (best practice)
        (
            drag := drag_handler(
                signal="node_drag",
                mode="freeform",
                constrain_to_parent=False,
            )
        ),
    ],
    iconify=True,
    compression=False,
)


def workflow_node(node_id, title, node_type, x, y, node_states, selected_node):
    """Create a workflow node with reactive positioning and state using Pythonic syntax."""
    node_state = node_states[node_id]

    return Div(
        # Status indicator - programmatically generated conditional classes
        Span(
            "●",
            cls="status-dot",  # Base class always present
            data_class={
                f"status-{state}": node_state == state for state in ["ready", "running", "complete", "pending"]
            },
        ),
        Div(title, cls="node-title"),
        Div(node_type.upper(), cls="node-type-badge"),
        # Interactive behaviors and positioning
        data_on_click=selected_node.toggle(node_id, None),
        data_draggable=True,
        # Static and dynamic classes
        cls=f"workflow-node node-{node_type}",
        data_class_selected=selected_node == node_id,
        data_class_node_running=node_state == "running",
        data_class_node_complete=node_state == "complete",
        # Element properties
        id=f"node-{node_id}",
        style=f"left: {x}px; top: {y}px;",
        data_node_id=node_id,
    )


@rt("/")
def home():
    """Composable node graph using canvas + custom drag logic."""
    # Define nodes as data for flexibility
    nodes = [
        {"id": "start", "title": "Start", "type": "start", "x": -300, "y": -100},
        {"id": "validate", "title": "Validate Data", "type": "process", "x": -100, "y": -150},
        {"id": "transform", "title": "Transform", "type": "process", "x": 100, "y": -50},
        {"id": "notify", "title": "Send Notification", "type": "action", "x": -100, "y": 100},
        {"id": "complete", "title": "Complete", "type": "end", "x": 300, "y": -100},
    ]

    # Prepare initial states for reuse
    initial_node_states = {node["id"]: "ready" if node["id"] == "start" else "pending" for node in nodes}
    initial_positions = {node["id"]: {"x": node["x"], "y": node["y"]} for node in nodes}

    steps = [{"id": node["id"], "progress": (i + 1) * 100 // len(nodes)} for i, node in enumerate(nodes)]

    reset_workflow_js = f"""
        $node_states = {json.dumps(initial_node_states)};
        $node_positions = {json.dumps(initial_positions)};
        $workflow_status = 'ready';
        $execution_progress = 0;
        $last_executed = null;
        $selected_node = null;
    """

    run_workflow_js = f"""
        if ($workflow_status === 'running') return;
        
        $workflow_status = 'running';
        $execution_progress = 0;
        
        const steps = {json.dumps(steps)};
        
        function executeStep(index) {{
            if (index >= steps.length) {{
                $workflow_status = 'complete';
                return;
            }}
            
            const step = steps[index];
            $node_states = {{...$node_states, [step.id]: 'running'}};
            $last_executed = step.id;
            
            setTimeout(() => {{
                $node_states = {{...$node_states, [step.id]: 'complete'}};
                $execution_progress = step.progress;
                setTimeout(() => executeStep(index + 1), 300);
            }}, 600);
        }}
        
        executeStep(0);
    """

    return Div(
        # Define all signals at the start using walrus operator
        (selected_node := Signal("selected_node", None)),
        (workflow_status := Signal("workflow_status", "ready")),
        (execution_progress := Signal("execution_progress", 0)),
        (last_executed := Signal("last_executed", None)),
        # Node states signal - initialize with proper states
        (node_states := Signal("node_states", initial_node_states)),
        # Node positions signal - initialize with positions from data
        (node_positions := Signal("node_positions", initial_positions)),
        # Canvas viewport with connections container
        Div(
            # Canvas container with nodes and connections
            Div(
                # Generate workflow nodes dynamically from data - pass signals for Pythonic syntax
                *[
                    workflow_node(
                        node["id"], node["title"], node["type"], node["x"], node["y"], node_states, selected_node
                    )
                    for node in nodes
                ],
                data_canvas_container=True,
                cls="canvas-container",
            ),
            data_canvas_viewport=True,
            data_on_canvas=console.log(
                f("Canvas interaction: pan=({x},{y}) zoom={z}", x=canvas.pan_x, y=canvas.pan_y, z=canvas.zoom)
            ),
            data_on_load=f"setTimeout(() => {canvas.reset_view()}, 100)",
            cls="canvas-viewport fullpage",
        ),
        # Controls (based on demo 13 toolbar)
        Div(
            H3("⚡ Workflow Builder", style="margin: 0 0 8px 0; font-size: 14px; color: #e5e7eb;"),
            Div(
                Button("R", data_on_click=canvas.reset_view(), cls="toolbar-btn reset-btn", title="Reset View"),
                Button("−", data_on_click=canvas.zoom_out(), cls="toolbar-btn zoom-btn", title="Zoom Out"),
                Button("+", data_on_click=canvas.zoom_in(), cls="toolbar-btn zoom-btn", title="Zoom In"),
                Div(
                    Span(data_text=(canvas.zoom * 100).round() + "%", cls="zoom-indicator"),
                    cls="status-display",
                ),
                style="display: flex; align-items: center; gap: 4px;",
            ),
            Div(
                P(
                    data_text="Selected: " + (selected_node | "none"),
                    style="margin: 8px 0 4px 0; font-size: 12px; color: #e5e7eb;",
                ),
                P(
                    data_text="Status: " + workflow_status,
                    style="margin: 4px 0 2px 0; font-size: 11px; color: #e5e7eb;",
                ),
                P(
                    data_text="Progress: " + execution_progress + "%",
                    style="margin: 2px 0 2px 0; font-size: 11px; color: #e5e7eb;",
                ),
                P(
                    data_text="Last: " + (last_executed | "none"),
                    style="margin: 2px 0 2px 0; font-size: 11px; color: #e5e7eb;",
                ),
                Button(
                    "Run Workflow",
                    data_on_click=run_workflow_js,
                    data_attr_disabled=workflow_status == "running",
                    cls="workflow-btn",
                    style="margin-top: 8px; width: 100%;",
                ),
                Button(
                    "Reset",
                    data_on_click=reset_workflow_js,
                    cls="reset-workflow-btn",
                    style="margin-top: 4px; width: 100%;",
                ),
            ),
            cls="modern-toolbar",
        ),
        # Organized styles using module constants
        Style(WORKFLOW_STYLES),
        Style(NODE_STYLES),
        Style(NODE_TYPE_STYLES),
        Style(TOOLBAR_STYLES),
        # Auto-focus
        data_on_load="el.focus()",
        data_on_keydown=f"""
            if (evt.target.tagName === 'INPUT') return;
            
            switch(evt.key) {{
                case 'r':
                case 'R':
                    {canvas.reset_view}();
                    evt.preventDefault();
                    break;
                case '+':
                case '=':
                    {canvas.zoom_in}();
                    evt.preventDefault();
                    break;
                case '-':
                case '_':
                    {canvas.zoom_out}();
                    evt.preventDefault();
                    break;
                case 'Enter':
                    {run_workflow_js}
                    evt.preventDefault();
                    break;
                case 'Escape':
                    {reset_workflow_js}
                    evt.preventDefault();
                    break;
            }}
        """,
        cls="composable-nodegraph-demo",
        tabindex="0",
        style="outline: none;",
    )


if __name__ == "__main__":
    print("=" * 60)
    print("⚡ INTERACTIVE WORKFLOW BUILDER")
    print("=" * 60)
    print("📍 Running on: http://localhost:5001")
    print("🛠️  Features:")
    print("   • Visual workflow creation with drag & drop")
    print("   • Real-time execution simulation")
    print("   • Node status tracking (ready/running/complete)")
    print("   • Canvas pan/zoom with grid background")
    print("   • Keyboard shortcuts (R, +, -, Enter)")
    print("   • Dynamic node styling based on type/status")
    print("📋 Usage:")
    print("   • Drag nodes to rearrange workflow")
    print("   • Click nodes to select and see execute button")
    print("   • Use 'Run Workflow' to simulate execution")
    print("   • Press Enter to run, R to reset view")
    print("=" * 60)
    serve(port=5001)
