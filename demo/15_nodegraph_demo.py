"""Demo: Interactive Workflow Builder
A practical demo showing canvas + drag to build visual workflows with real-time state tracking
"""

from starhtml import *

app, rt = star_app(
    title="Composable Node Graph Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        # Canvas handler for pan/zoom/grid
        canvas_handler(grid_color="rgba(255,255,255,0.1)", minor_grid_color="rgba(255,255,255,0.05)"),
        # Single drag handler for all nodes (best practice)
        drag_handler(
            signal="node_drag",
            mode="freeform",
            constrain_to_parent=False,
        ),
        # Override viewport background for dark theme
        Style("[data-canvas-viewport] { background: #2a2a2a !important; }"),
    ],
)


def workflow_node(node_id, title, node_type, x, y):
    """Create a workflow node with consistent structure."""
    node_state = f"$node_states.{node_id}"

    return Div(
        # Status indicator
        Div(
            "●",
            ds_class(
                ready=equals(node_state, "ready"),
                running=equals(node_state, "running"),
                complete=equals(node_state, "complete"),
                pending=equals(node_state, "pending"),
            ),
            cls="status-dot",
        ),
        # Node title and type
        Div(title, cls="node-title"),
        Div(node_type.upper(), cls="node-type-badge"),
        # Interactive behaviors
        ds_on_click(f"$selected_node = ($selected_node === '{node_id}' ? null : '{node_id}')"),
        ds_class(
            selected=equals("$selected_node", node_id),
            node_ready=equals(node_state, "ready"),
            node_running=equals(node_state, "running"),
            node_complete=equals(node_state, "complete"),
            **{f"node_{node_type}": True},
        ),
        ds_draggable(),
        # Element properties
        id=f"node-{node_id}",
        cls="workflow-node",
        style=f"left: {x}px; top: {y}px;",
        data_node_id=node_id,
    )


@rt("/")
def home():
    """Composable node graph using canvas + custom drag logic."""
    return Div(
        # Initialize workflow state
        ds_signals(
            selected_node=None,
            workflow_status="ready",
            execution_progress=0,
            last_executed=None,
            node_states={
                "start": "ready",
                "validate": "pending",
                "transform": "pending",
                "notify": "pending",
                "complete": "pending",
            },
        ),
        # Canvas viewport with connections container
        Div(
            # Canvas container with nodes and connections
            Div(
                # Workflow nodes in a logical layout from center origin
                workflow_node("start", "Start", "start", -300, -100),
                workflow_node("validate", "Validate Data", "process", -100, -150),
                workflow_node("transform", "Transform", "process", 100, -50),
                workflow_node("notify", "Send Notification", "action", -100, 100),
                workflow_node("complete", "Complete", "end", 300, -100),
                ds_canvas_container(),
                cls="canvas-container",
            ),
            ds_canvas_viewport(),
            ds_on_canvas(
                "console.log(`Canvas interaction: pan=(${$canvas_pan_x},${$canvas_pan_y}) zoom=${$canvas_zoom}`)"
            ),
            ds_on_load("setTimeout(() => $canvas_reset_view(), 100)"),
            cls="canvas-viewport fullpage",
        ),
        # Controls (based on demo 13 toolbar)
        Div(
            H3("⚡ Workflow Builder", style="margin: 0 0 8px 0; font-size: 14px; color: #e5e7eb;"),
            Div(
                Button("R", ds_on_click("$canvas_reset_view()"), cls="toolbar-btn reset-btn", title="Reset View"),
                Button("−", ds_on_click("$canvas_zoom_out()"), cls="toolbar-btn zoom-btn", title="Zoom Out"),
                Button("+", ds_on_click("$canvas_zoom_in()"), cls="toolbar-btn zoom-btn", title="Zoom In"),
                Div(
                    Span(ds_text("Math.round(($canvas_zoom || 1) * 100) + '%'"), cls="zoom-indicator"),
                    cls="status-display",
                ),
                style="display: flex; align-items: center; gap: 4px;",
            ),
            Div(
                P(
                    ds_text("'Selected: ' + ($selected_node || 'none')"),
                    style="margin: 8px 0 4px 0; font-size: 12px; color: #e5e7eb;",
                ),
                P(
                    ds_text("'Status: ' + $workflow_status"),
                    style="margin: 4px 0 2px 0; font-size: 11px; color: #e5e7eb;",
                ),
                P(
                    ds_text("'Progress: ' + $execution_progress + '%'"),
                    style="margin: 2px 0 2px 0; font-size: 11px; color: #e5e7eb;",
                ),
                P(
                    ds_text("'Last: ' + ($last_executed || 'none')"),
                    style="margin: 2px 0 2px 0; font-size: 11px; color: #e5e7eb;",
                ),
                Button(
                    "Run Workflow",
                    ds_on_click("""
                        if ($workflow_status === 'running') return;
                        
                        $workflow_status = 'running';
                        $execution_progress = 0;
                        
                        const steps = [
                            {id: 'start', progress: 20},
                            {id: 'validate', progress: 40},
                            {id: 'transform', progress: 60},
                            {id: 'notify', progress: 80},
                            {id: 'complete', progress: 100}
                        ];
                        
                        function executeStep(index) {
                            if (index >= steps.length) {
                                $workflow_status = 'complete';
                                return;
                            }
                            
                            const step = steps[index];
                            $node_states = {...$node_states, [step.id]: 'running'};
                            $last_executed = step.id;
                            
                            setTimeout(() => {
                                $node_states = {...$node_states, [step.id]: 'complete'};
                                $execution_progress = step.progress;
                                
                                setTimeout(() => executeStep(index + 1), 300);
                            }, 600);
                        }
                        
                        executeStep(0);
                    """),
                    ds_disabled("$workflow_status === 'running'"),
                    cls="workflow-btn",
                    style="margin-top: 8px; width: 100%;",
                ),
                Button(
                    "Reset",
                    ds_on_click("""
                        $node_states = {
                            start: 'ready',
                            validate: 'pending',
                            transform: 'pending',
                            notify: 'pending',
                            complete: 'pending'
                        };
                        $workflow_status = 'ready';
                        $execution_progress = 0;
                        $last_executed = null;
                        $selected_node = null;
                    """),
                    cls="reset-workflow-btn",
                    style="margin-top: 4px; width: 100%;",
                ),
            ),
            cls="modern-toolbar",
        ),
        # CSS Styles (based on demo 13 + node styles)
        Style("""
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
            }
            
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
                transition: all 0.3s ease;
                z-index: 1;
                pointer-events: auto;
                display: flex;
                flex-direction: column;
                gap: 8px;
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
                transition: all 0.3s ease;
            }
            
            .status-dot.ready { color: #10B981; }
            .status-dot.running {
                color: #F59E0B;
                animation: pulse 1s infinite;
                transform: scale(1.2);
            }
            .status-dot.complete { color: #10B981; }
            .status-dot.pending { color: #6B7280; }
            
            .workflow-node:hover {
                border-color: #4a4a5a;
                box-shadow: 0 6px 16px rgba(0,0,0,0.5);
                transform: translateY(-2px);
            }
            
            .workflow-node:active {
                cursor: grabbing;
            }
            
            .workflow-node.selected {
                border-color: #4A90E2;
                box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.4), 0 6px 20px rgba(74, 144, 226, 0.2);
                transform: translateY(-2px);
            }
            
            /* Node state styles */
            .workflow-node.node_running {
                border-color: #F59E0B;
                box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.3), 0 6px 16px rgba(245, 158, 11, 0.2);
                animation: nodeRunning 2s infinite;
            }
            
            .workflow-node.node_complete {
                border-color: #10B981;
                background: linear-gradient(135deg, #2a3a2a, #2a2a3a);
            }
            
            @keyframes nodeRunning {
                0%, 100% {
                    box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.3), 0 6px 16px rgba(245, 158, 11, 0.2);
                }
                50% {
                    box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.6), 0 8px 20px rgba(245, 158, 11, 0.4);
                }
            }
            
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
            
            .node-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }
            
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                font-size: 8px;
                line-height: 1;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .status-indicator.status-ready { color: #10B981; }
            .status-indicator.status-running { color: #F59E0B; animation: pulse 1s infinite; }
            .status-indicator.status-complete { color: #10B981; }
            .status-indicator.status-pending { color: #6B7280; }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
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
            
            .execute-btn {
                padding: 4px 8px;
                font-size: 10px;
                background: #4A90E2;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .execute-btn:hover {
                background: #357ABD;
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
            
            
            /* Toolbar (from demo 13) */
            .modern-toolbar {
                position: fixed;
                top: 1rem;
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
        """),
        # Auto-focus
        ds_on_load("el.focus()"),
        ds_on_keydown("""
            if (evt.target.tagName === 'INPUT') return;
            
            switch(evt.key) {
                case 'r':
                case 'R':
                    $canvas_reset_view();
                    evt.preventDefault();
                    break;
                case '+':
                case '=':
                    $canvas_zoom_in();
                    evt.preventDefault();
                    break;
                case '-':
                case '_':
                    $canvas_zoom_out();
                    evt.preventDefault();
                    break;
                case 'Enter':
                    if ($workflow_status !== 'running') {
                        $workflow_status = 'running';
                        $execution_progress = 0;
                        
                        const steps = [
                            {id: 'start', progress: 20},
                            {id: 'validate', progress: 40},
                            {id: 'transform', progress: 60},
                            {id: 'notify', progress: 80},
                            {id: 'complete', progress: 100}
                        ];
                        
                        function executeStep(index) {
                            if (index >= steps.length) {
                                $workflow_status = 'complete';
                                return;
                            }
                            
                            const step = steps[index];
                            $node_states = {...$node_states, [step.id]: 'running'};
                            $last_executed = step.id;
                            
                            setTimeout(() => {
                                $node_states = {...$node_states, [step.id]: 'complete'};
                                $execution_progress = step.progress;
                                
                                setTimeout(() => executeStep(index + 1), 300);
                            }, 600);
                        }
                        
                        executeStep(0);
                    }
                    evt.preventDefault();
                    break;
            }
        """),
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
