#!/usr/bin/env python
"""
Demo: Position Handler Debug - Testing Virtual Anchor for Context Menu
"""

from starhtml import *

def app():
    return Body(
        Div(
            Header(
                H1("🎯 Position Handler Debug", cls="text-3xl font-bold mb-2"),
                P("Testing virtual anchor for context menu", cls="text-muted-foreground"),
                cls="text-center py-8 border-b bg-background sticky top-0 z-10",
            ),
            
            Main(
                # Context Menu with Debug
                Section(
                    H2("📋 Context Menu Debug", cls="text-2xl font-semibold mb-4"),
                    Div(
                        Div(
                            "Right-click in this area",
                            ds_on_contextmenu("""
                                event.preventDefault();
                                console.log('Right-click at:', event.clientX, event.clientY);
                                
                                // Create virtual element at cursor position
                                const virtualEl = {
                                    getBoundingClientRect: () => {
                                        const rect = {
                                            x: event.clientX,
                                            y: event.clientY,
                                            width: 0,
                                            height: 0,
                                            top: event.clientY,
                                            right: event.clientX,
                                            bottom: event.clientY,
                                            left: event.clientX
                                        };
                                        console.log('Virtual element rect:', rect);
                                        return rect;
                                    }
                                };
                                
                                // Store virtual anchor using convention: [elementId]VirtualAnchor
                                window.contextMenuVirtualAnchor = virtualEl;
                                console.log('Set window.contextMenuVirtualAnchor');
                                
                                // Also log what's in window
                                console.log('Window keys with "Virtual":', 
                                    Object.keys(window).filter(k => k.includes('Virtual'))
                                );
                                
                                $context_open = true;
                            """),
                            ds_on_click("""
                                console.log('Closing context menu');
                                window.contextMenuVirtualAnchor = null;
                                $context_open = false;
                            """),
                            id="contextArea",
                            cls="h-32 bg-gray-100 border-2 border-dashed border-gray-400 rounded flex items-center justify-center cursor-context-menu",
                        ),
                        
                        Div(
                            Div("Cut", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                            Div("Copy", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                            Div("Paste", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                            Hr(cls="my-1"),
                            Div("Delete", cls="px-4 py-2 hover:bg-red-50 text-red-600 cursor-pointer"),
                            
                            ds_position(
                                anchor="contextArea",
                                placement="bottom-start",
                                strategy="fixed"
                            ),
                            ds_show("$context_open"),
                            ds_on_click("""
                                console.log('Menu item clicked');
                                window.contextMenuVirtualAnchor = null;
                                $context_open = false;
                            """),
                            id="contextMenu",
                            cls="bg-white border border-gray-300 rounded-lg shadow-xl min-w-[150px] py-1",
                        ),
                        
                        ds_signals(context_open=False),
                        cls="mb-8",
                    ),
                    cls="mb-12",
                ),
                
                # Debug Output
                Section(
                    H2("Debug Output", cls="text-2xl font-semibold mb-4"),
                    P("Open browser console to see debug logs", cls="text-muted-foreground mb-4"),
                    Div(
                        Button(
                            "Test Virtual Anchor Manually",
                            ds_on_click("""
                                console.log('Testing manual virtual anchor');
                                
                                // Create virtual element at (200, 200)
                                const virtualEl = {
                                    getBoundingClientRect: () => ({
                                        x: 200, y: 200, width: 0, height: 0,
                                        top: 200, right: 200, bottom: 200, left: 200
                                    })
                                };
                                
                                window.contextMenuVirtualAnchor = virtualEl;
                                console.log('Set virtual anchor at (200, 200)');
                                
                                $context_open = true;
                                
                                setTimeout(() => {
                                    console.log('Checking if menu moved to (200, 200)');
                                    const menu = document.getElementById('contextMenu');
                                    console.log('Menu position:', menu.style.left, menu.style.top);
                                }, 100);
                            """),
                            cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700",
                        ),
                        cls="mb-4",
                    ),
                    cls="mb-12",
                ),
                
                # Also add a script to monitor position updates
                Script("""
                    // Monitor position updates
                    document.addEventListener('DOMContentLoaded', () => {
                        const menu = document.getElementById('contextMenu');
                        if (menu) {
                            menu.addEventListener('position-update', (e) => {
                                console.log('Position update event:', e.detail);
                            });
                        }
                    });
                    
                    // Periodically check virtual anchor
                    setInterval(() => {
                        if (window.contextMenuVirtualAnchor) {
                            console.log('Virtual anchor exists:', 
                                window.contextMenuVirtualAnchor.getBoundingClientRect());
                        }
                    }, 2000);
                """),
                
                cls="container mx-auto px-4 py-8 max-w-4xl",
            ),
            cls="min-h-screen bg-background text-foreground",
        )
    )

if __name__ == "__main__":
    print("Position Handler Debug running on http://localhost:5001")
    serve(port=5001)