# Debug Plan: Fix Persistence & Theming

## Issue 1: Thinking Process Persistence
- **Symptom**: "Thinking..." toggle disappears after refresh.
- **Hypothesis**: `fetchMessages` in `App.tsx` is not correctly extracting `thoughts` from `msg.meta.thoughts` or the backend is not saving it (though backend logic looked correct).
- **Check**: Inspect `fetchMessages` logic in `App.tsx`.
- **Action**: Ensure `meta` is properly accessed and `thoughts` are mapped.

## Issue 2: Theme Awareness
- **Symptom**: Plotly charts (specifically Choropleth) don't update background instantly.
- **Hypothesis**: Plotly's internal `layout` state might not react to CSS variable changes unless forces a redraw.
- **Check**: `PlotlyVisualizer.tsx`.
- **Action**: Add a `key={theme}` prop to the `Plot` component to force a complete re-mount and re-calculation of styles when theme changes.

## Issue 3: Alignment
- **Symptom**: Chat content is wider/misaligned with Input Bar.
- **Hypothesis**: Padding mismatch.
- **Action**: Adjust `ChatInterface` containers to strictly match `InputBar` (likely `max-w-4xl mx-auto px-4`).

## Updated Plan
1. **Frontend Persistence**: Debug `App.tsx` -> `fetchMessages`.
2. **Frontend Theming**: Add `key={theme}` to `Plot` in `PlotlyVisualizer.tsx`.
3. **Alignment**: Creating a dedicated `LayoutWrapper` component or strictly enforcing classes.
