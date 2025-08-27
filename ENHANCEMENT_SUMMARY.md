# Scroll Handler Enhancement: Anchored Positioning

## Summary

Successfully implemented automatic anchored positioning for floating UI elements in the scroll handler, reducing boilerplate code by ~95% while maintaining backwards compatibility.

## What Was Implemented

### 1. TypeScript Handler Enhancement (`typescript/handlers/scroll.ts`)
- Added `AnchoredElementState` interface for tracking anchored elements
- Implemented `detectAnchoredElements()` to auto-detect configuration
- Added `updateAnchoredPosition()` for automatic scroll delta tracking
- Smart visibility checking with 100px intervals to prevent off-screen elements
- Auto-detection of signal prefixes from element IDs
- Support for native popover API and custom hide actions

### 2. Python API Enhancement (`src/starhtml/datastar.py`)
- Enhanced `ds_on_scroll()` with new parameters:
  - `anchor_to`: Element ID to anchor to
  - `signal_prefix`: Explicit or auto-detected prefix
  - `hide_when_offscreen`: Auto-hide behavior
  - `hide_action`: Custom hide JavaScript
- Maintained backwards compatibility with existing API

### 3. Comprehensive Demos

#### Demo 16: Problem Demonstration
Shows the current complexity of manual scroll tracking:
- 20+ lines of boilerplate per component
- Manual delta calculations
- Visibility checking logic
- Multiple signals to track scroll state

#### Demo 17: Solution Demonstration
Shows the enhanced solution:
- Single line configuration
- Automatic delta tracking
- Built-in visibility management
- 95% code reduction

#### Demo 18: Components Gallery
Real-world UI patterns:
- Context menus
- Dropdown menus
- Autocomplete
- Hover cards
- All using the simplified API

### 4. Test Coverage
Created comprehensive test suite covering:
- Basic scroll handlers
- Anchored positioning configurations
- Backwards compatibility
- Parameter combinations
- Integration with HTML elements

## Key Benefits

1. **Developer Experience**
   - From 20+ lines to 1 line per floating element
   - Auto-detection reduces configuration
   - Consistent behavior across components

2. **Performance**
   - Smart throttling (configurable)
   - Visibility checks only every 100px
   - Batch DOM updates via startBatch/endBatch

3. **Flexibility**
   - Works with native popover API
   - Custom hide actions
   - Combine with custom scroll logic
   - Explicit overrides when needed

## Usage Examples

### Before (20+ lines)
```python
ds_on_scroll("""
    if ($popover_open) {
        const deltaY = window.scrollY - $popover_initialScrollY;
        const deltaX = window.scrollX - $popover_initialScrollX;
        $popover_top = $popover_top - deltaY;
        $popover_left = $popover_left - deltaX;
        $popover_initialScrollY = window.scrollY;
        $popover_initialScrollX = window.scrollX;
        
        if (Math.floor(window.scrollY / 100) !== 
            Math.floor((window.scrollY - deltaY) / 100)) {
            const tr = popoverTrigger.getBoundingClientRect();
            const triggerVisible = tr.bottom > 0 && 
                                 tr.top < window.innerHeight;
            if (!triggerVisible) {
                $popover_open = false;
            }
        }
    }
""", throttle="16")
```

### After (1 line)
```python
ds_on_scroll("", anchor_to="popoverTrigger", throttle="16")
```

## Migration Guide

1. Remove manual scroll tracking code
2. Add `anchor_to` parameter pointing to trigger element
3. Remove `_initialScrollY/X` signals
4. Optionally specify `hide_action` for custom behavior

## Files Modified

- `typescript/handlers/scroll.ts` - Core implementation
- `src/starhtml/datastar.py` - Python API
- `demo/16_anchored_popover_problem.py` - Problem demo
- `demo/17_anchored_popover_solution.py` - Solution demo
- `demo/18_anchored_components.py` - Components gallery
- `demo/app.py` - Added new demos to hub
- `tests/unit/test_scroll_anchored.py` - Test coverage

## Next Steps

Potential future enhancements:
1. Support for nested scrollable containers
2. Automatic positioning adjustment (flip when near edges)
3. Virtual scrolling support
4. Animation options for show/hide
5. Collision detection with viewport edges

## Backwards Compatibility

✅ Fully backwards compatible
- Existing scroll handlers work unchanged
- New features are opt-in via parameters
- No breaking changes to API