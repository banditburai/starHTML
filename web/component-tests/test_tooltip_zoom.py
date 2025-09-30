#!/usr/bin/env python3
# Mock tooltip component based on the provided code
from typing import Any, Literal
from uuid import uuid4

from starhtml import *
from starhtml import FT, Div


def cn(*classes: str, **conditionals: Any) -> str:
    """Simple class name helper"""
    result = " ".join(classes)
    for cls, condition in conditionals.items():
        if condition:
            result += f" {cls}"
    return result


def Tooltip(*children, cls: str = "relative inline-block", **attrs: Any) -> FT:
    tooltip_id = f"tooltip_{uuid4().hex[:8]}"
    return Div(
        *[child(tooltip_id) if callable(child) else child for child in children],
        data_signals={f"{tooltip_id}_open": False},
        cls=cls,
        **attrs,
    )


def TooltipTrigger(
    *children,
    delay_duration: int = 700,
    hide_delay: int = 0,
    class_name: str = "",
    cls: str = "",
    **attrs: Any,
):
    def create(tooltip_id: str) -> FT:
        return Div(
            *children,
            data_ref=f"{tooltip_id}Trigger",
            data_on_mouseenter=f"""
                clearTimeout(window.tooltipTimer_{tooltip_id});
                window.tooltipTimer_{tooltip_id} = setTimeout(() => {{
                    ${tooltip_id}_open = true;
                }}, {delay_duration});
            """,
            data_on_mouseleave=(
                f"""
                clearTimeout(window.tooltipTimer_{tooltip_id});
                window.tooltipTimer_{tooltip_id} = setTimeout(() => {{
                    ${tooltip_id}_open = false;
                }}, {hide_delay});
                """
                if hide_delay > 0
                else f"""
                clearTimeout(window.tooltipTimer_{tooltip_id});
                ${tooltip_id}_open = false;
                """
            ),
            data_on_focus=f"""
                clearTimeout(window.tooltipTimer_{tooltip_id});
                window.tooltipTimer_{tooltip_id} = setTimeout(() => {{
                    ${tooltip_id}_open = true;
                }}, {delay_duration});
            """,
            data_on_blur=f"""
                clearTimeout(window.tooltipTimer_{tooltip_id});
                ${tooltip_id}_open = false;
            """,
            data_on_keydown=f"event.key === 'Escape' && (clearTimeout(window.tooltipTimer_{tooltip_id}), ${tooltip_id}_open = false)",
            id=f"{tooltip_id}-trigger",
            tabindex="0",
            aria_describedby=f"{tooltip_id}-content",
            **{"aria-expanded": f"${tooltip_id}_open"},
            cls=cn("inline-block outline-none", class_name, cls),
            **attrs,
        )

    return create


def TooltipContent(
    *children,
    side: Literal["top", "right", "bottom", "left"] = "top",
    align: Literal["start", "center", "end"] = "center",
    side_offset: int = 8,
    class_name: str = "",
    cls: str = "",
    **attrs: Any,
):
    def create_content(tooltip_id: str) -> FT:
        placement = f"{side}-{align}" if align != "center" else side
        return Div(
            *children,
            data_ref=f"{tooltip_id}Content",
            data_show=f"${tooltip_id}_open",
            data_position=(
                f"{tooltip_id}-trigger",
                dict(placement=placement, offset=side_offset, flip=True, shift=True),
            ),
            id=f"{tooltip_id}-content",
            role="tooltip",
            **{"data-state": f"${tooltip_id}_open ? 'open' : 'closed'"},
            **{"data-side": side},
            cls=cn(
                "absolute z-50 rounded-md px-3 py-1.5",
                "bg-gray-900 text-white text-xs",
                "pointer-events-none",
                "transition-opacity duration-150",
                class_name,
                cls,
            ),
            **attrs,
        )

    return create_content


def TooltipProvider(*children, **attrs: Any) -> FT:
    return Div(*children, **attrs)


# Create the test app
app, rt = star_app(
    live=True,
    hdrs=(
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/tailwindcss@2/dist/tailwind.min.css"),
        position_handler(),
    ),
)


@rt("/")
def index():
    return Body(
        Div(
            # Zoom indicator
            Div(
                H2("Zoom Level Test", cls="text-2xl font-bold mb-2"),
                Div(
                    "Current Zoom: ",
                    Span(id="zoom-level", cls="font-mono font-bold"),
                    " | Device Pixel Ratio: ",
                    Span(id="pixel-ratio", cls="font-mono"),
                    cls="bg-gray-100 p-3 rounded mb-6",
                ),
                cls="mb-8",
            ),
            # Instructions
            Div(
                H3("Testing Instructions:", cls="text-lg font-semibold mb-2"),
                Ul(
                    Li("Test at different zoom levels: 100%, 125%, 150%, 175%, 200%"),
                    Li("Use Ctrl/Cmd + Plus/Minus to change zoom"),
                    Li("Hover over buttons to trigger tooltips"),
                    Li("Watch for flickering or incorrect positioning"),
                    Li("Test rapid hover in/out to check for race conditions"),
                    cls="list-disc list-inside space-y-1 text-gray-700",
                ),
                cls="bg-yellow-50 border border-yellow-200 p-4 rounded mb-8",
            ),
            # Test grid with tooltips
            Div(
                H3("Tooltip Position Tests", cls="text-lg font-semibold mb-4"),
                Div(
                    # Top tooltip
                    TooltipProvider(
                        Tooltip(
                            TooltipTrigger(
                                Button(
                                    "Hover for Top",
                                    cls="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600",
                                ),
                                delay_duration=200,
                            ),
                            TooltipContent(
                                "Top positioned tooltip",
                                side="top",
                            ),
                        ),
                    ),
                    # Bottom tooltip
                    TooltipProvider(
                        Tooltip(
                            TooltipTrigger(
                                Button(
                                    "Hover for Bottom",
                                    cls="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600",
                                ),
                                delay_duration=200,
                            ),
                            TooltipContent(
                                "Bottom positioned tooltip",
                                side="bottom",
                            ),
                        ),
                    ),
                    # Left tooltip
                    TooltipProvider(
                        Tooltip(
                            TooltipTrigger(
                                Button(
                                    "Hover for Left",
                                    cls="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600",
                                ),
                                delay_duration=200,
                            ),
                            TooltipContent(
                                "Left positioned tooltip",
                                side="left",
                            ),
                        ),
                    ),
                    # Right tooltip
                    TooltipProvider(
                        Tooltip(
                            TooltipTrigger(
                                Button(
                                    "Hover for Right",
                                    cls="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600",
                                ),
                                delay_duration=200,
                            ),
                            TooltipContent(
                                "Right positioned tooltip",
                                side="right",
                            ),
                        ),
                    ),
                    cls="grid grid-cols-2 gap-8 max-w-md",
                ),
                cls="mb-8",
            ),
            # Multiple tooltips in close proximity
            Div(
                H3("Adjacent Tooltips Test", cls="text-lg font-semibold mb-4"),
                P("Test multiple tooltips close together - they should not interfere", cls="text-gray-600 mb-2"),
                Div(
                    TooltipProvider(
                        Tooltip(
                            TooltipTrigger(
                                Span("Item 1", cls="px-3 py-1 bg-gray-200 rounded cursor-pointer hover:bg-gray-300"),
                                delay_duration=100,
                            ),
                            TooltipContent("First tooltip", side="top"),
                        ),
                    ),
                    TooltipProvider(
                        Tooltip(
                            TooltipTrigger(
                                Span("Item 2", cls="px-3 py-1 bg-gray-200 rounded cursor-pointer hover:bg-gray-300"),
                                delay_duration=100,
                            ),
                            TooltipContent("Second tooltip", side="top"),
                        ),
                    ),
                    TooltipProvider(
                        Tooltip(
                            TooltipTrigger(
                                Span("Item 3", cls="px-3 py-1 bg-gray-200 rounded cursor-pointer hover:bg-gray-300"),
                                delay_duration=100,
                            ),
                            TooltipContent("Third tooltip", side="top"),
                        ),
                    ),
                    cls="flex gap-2",
                ),
                cls="mb-8",
            ),
            # Automated test section
            Div(
                H3("Automated Test", cls="text-lg font-semibold mb-4"),
                Div(
                    Button(
                        "Run Automated Tests",
                        id="run-tests",
                        cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 mr-4",
                    ),
                    Span("Status: ", cls="text-gray-600"),
                    Span(id="test-status", cls="font-semibold"),
                    cls="mb-4",
                ),
                Div(
                    id="test-results",
                    cls="bg-gray-100 p-4 rounded mb-4 hidden",
                ),
                cls="mb-8",
            ),
            # Debug output
            Div(
                H3("Debug Log", cls="text-lg font-semibold mb-2"),
                Div(
                    id="debug-log",
                    cls="bg-gray-900 text-green-400 p-4 rounded font-mono text-xs h-48 overflow-y-auto",
                ),
            ),
            cls="container mx-auto p-8",
        ),
        # Zoom monitoring script
        Script("""
            function updateZoomIndicators() {
                const zoom = Math.round(window.devicePixelRatio * 100);
                document.getElementById('zoom-level').textContent = zoom + '%';
                document.getElementById('pixel-ratio').textContent = window.devicePixelRatio.toFixed(3);
            }
            
            function addDebugLog(message) {
                const log = document.getElementById('debug-log');
                const entry = document.createElement('div');
                entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
                log.insertBefore(entry, log.firstChild);
                while (log.children.length > 20) {
                    log.removeChild(log.lastChild);
                }
            }
            
            let lastZoom = window.devicePixelRatio;
            setInterval(() => {
                if (Math.abs(window.devicePixelRatio - lastZoom) > 0.001) {
                    addDebugLog(`Zoom changed: ${Math.round(lastZoom * 100)}% → ${Math.round(window.devicePixelRatio * 100)}%`);
                    lastZoom = window.devicePixelRatio;
                    updateZoomIndicators();
                }
            }, 100);
            
            updateZoomIndicators();
            addDebugLog('Test page loaded - Ready for testing');
            
            // Add keyboard shortcut for testing
            document.addEventListener('keydown', (e) => {
                if (e.key === 't' && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault();
                    runAutomatedTests();
                }
            });
            
            // Monitor tooltip visibility and position changes
            const tooltipObserver = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    if (mutation.target.id && mutation.target.id.includes('tooltip') && mutation.target.id.includes('content')) {
                        const el = mutation.target;
                        const style = window.getComputedStyle(el);
                        const isVisible = style.display !== 'none' && style.visibility !== 'hidden';
                        
                        if (isVisible) {
                            const rect = el.getBoundingClientRect();
                            const placement = el.getAttribute('data-side') || 'unknown';
                            
                            // Check for position issues
                            const issues = [];
                            if (rect.left < 0) issues.push('cut-off-left');
                            if (rect.right > window.innerWidth) issues.push('cut-off-right');
                            if (rect.top < 0) issues.push('cut-off-top');
                            if (rect.bottom > window.innerHeight) issues.push('cut-off-bottom');
                            
                            const posInfo = `pos:(${Math.round(rect.left)},${Math.round(rect.top)}) ${placement}`;
                            const issueInfo = issues.length ? ` ISSUES: ${issues.join(', ')}` : '';
                            addDebugLog(`Tooltip shown: ${el.id} ${posInfo}${issueInfo}`);
                        }
                    }
                });
            });
            
            tooltipObserver.observe(document.body, {
                attributes: true,
                subtree: true,
                attributeFilter: ['style', 'class']
            });
            
            // Automated testing functionality
            const runAutomatedTests = async () => {
                const statusEl = document.getElementById('test-status');
                const resultsEl = document.getElementById('test-results');
                
                statusEl.textContent = 'Running...';
                statusEl.className = 'font-semibold text-yellow-600';
                resultsEl.classList.remove('hidden');
                resultsEl.innerHTML = '';
                
                const testResults = [];
                const tooltipButtons = [
                    { id: 'tooltip_', label: 'Top', expectedSide: 'top' },
                    { id: 'tooltip_', label: 'Bottom', expectedSide: 'bottom' },
                    { id: 'tooltip_', label: 'Left', expectedSide: 'left' },
                    { id: 'tooltip_', label: 'Right', expectedSide: 'right' }
                ];
                
                // Test at different zoom levels
                const zoomLevels = [100, 125, 150, 175, 200];
                
                for (const zoom of zoomLevels) {
                    // Note: Can't programmatically change zoom, but can simulate different positions
                    const zoomResults = { zoom, tests: [] };
                    
                    for (const btn of tooltipButtons) {
                        // Find the trigger button
                        const triggers = Array.from(document.querySelectorAll('[id^="' + btn.id + '"][id$="-trigger"]'));
                        const trigger = triggers.find(t => t.textContent.includes(btn.label));
                        
                        if (!trigger) continue;
                        
                        // Trigger tooltip
                        const mouseEnter = new MouseEvent('mouseenter', { bubbles: true });
                        trigger.dispatchEvent(mouseEnter);
                        
                        // Wait for tooltip to position
                        await new Promise(resolve => setTimeout(resolve, 300));
                        
                        // Check tooltip position
                        const tooltipId = trigger.id.replace('-trigger', '-content');
                        const tooltip = document.getElementById(tooltipId);
                        
                        if (tooltip) {
                            const rect = tooltip.getBoundingClientRect();
                            const style = window.getComputedStyle(tooltip);
                            const isVisible = style.display !== 'none' && style.visibility !== 'hidden';
                            
                            const result = {
                                button: btn.label,
                                visible: isVisible,
                                position: { x: Math.round(rect.left), y: Math.round(rect.top) },
                                cutOffLeft: rect.left < 0,
                                cutOffRight: rect.right > window.innerWidth,
                                cutOffTop: rect.top < 0,
                                cutOffBottom: rect.bottom > window.innerHeight,
                                actualSide: tooltip.getAttribute('data-side') || 'unknown'
                            };
                            
                            result.hasIssues = result.cutOffLeft || result.cutOffRight || result.cutOffTop || result.cutOffBottom;
                            zoomResults.tests.push(result);
                        }
                        
                        // Hide tooltip
                        const mouseLeave = new MouseEvent('mouseleave', { bubbles: true });
                        trigger.dispatchEvent(mouseLeave);
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }
                    
                    testResults.push(zoomResults);
                }
                
                // Display results
                let hasAnyIssues = false;
                let html = '<div class="space-y-4">';
                
                for (const zoomResult of testResults) {
                    const zoomIssues = zoomResult.tests.filter(t => t.hasIssues);
                    hasAnyIssues = hasAnyIssues || zoomIssues.length > 0;
                    
                    html += `<div class="border rounded p-3">`;
                    html += `<h4 class="font-semibold mb-2">Current Zoom (${Math.round(window.devicePixelRatio * 100)}%)</h4>`;
                    html += '<ul class="space-y-1 text-sm">';
                    
                    for (const test of zoomResult.tests) {
                        const icon = test.hasIssues ? '❌' : '✅';
                        const issues = [];
                        if (test.cutOffLeft) issues.push('left');
                        if (test.cutOffRight) issues.push('right');
                        if (test.cutOffTop) issues.push('top');
                        if (test.cutOffBottom) issues.push('bottom');
                        
                        const issueText = issues.length ? ` (cut-off: ${issues.join(', ')})` : '';
                        html += `<li>${icon} ${test.button}: ${test.actualSide}${issueText}</li>`;
                    }
                    
                    html += '</ul></div>';
                }
                
                html += '</div>';
                resultsEl.innerHTML = html;
                
                // Update status
                if (hasAnyIssues) {
                    statusEl.textContent = 'Issues Found';
                    statusEl.className = 'font-semibold text-red-600';
                } else {
                    statusEl.textContent = 'All Tests Passed';
                    statusEl.className = 'font-semibold text-green-600';
                }
            };
            
            document.getElementById('run-tests').addEventListener('click', runAutomatedTests);
        """),
    )


if __name__ == "__main__":
    serve(port=5005)
