import { useMemo } from 'react';

/**
 * Hook to dynamically read OKLCH chart colors from CSS variables
 * Supports all 3 themes: light, dark, drilling-slate
 */
export const useChartColors = () => {
  return useMemo(() => {
    const getColor = (varName: string) => {
      return getComputedStyle(document.documentElement)
        .getPropertyValue(varName)
        .trim();
    };

    return {
      // Chart accent colors (6-color palette)
      accent1: getColor('--color-chart-accent-1'),
      accent2: getColor('--color-chart-accent-2'),
      accent3: getColor('--color-chart-accent-3'),
      accent4: getColor('--color-chart-accent-4'),
      accent5: getColor('--color-chart-accent-5'),
      accent6: getColor('--color-chart-accent-6'),

      // Semantic colors
      brand: getColor('--color-brand'),
      surface: getColor('--color-surface'),
      surfaceElevated: getColor('--color-surface-elevated'),
      text: getColor('--color-text'),
      textMuted: getColor('--color-text-muted'),
      border: getColor('--color-border'),
      borderSubtle: getColor('--color-border-subtle'),

      // Status colors
      success: getColor('--color-success'),
      warning: getColor('--color-warning'),
      error: getColor('--color-error'),
      info: getColor('--color-info'),

      // Helper: Get all accent colors as array
      accents: [
        getColor('--color-chart-accent-1'),
        getColor('--color-chart-accent-2'),
        getColor('--color-chart-accent-3'),
        getColor('--color-chart-accent-4'),
        getColor('--color-chart-accent-5'),
        getColor('--color-chart-accent-6'),
      ],
    };
  }, []); // Empty deps - colors update via CSS, not React state
};
