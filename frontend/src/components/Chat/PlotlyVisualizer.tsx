// @ts-nocheck
import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

interface PlotlyVisualizerProps {
  data: any;
  visualizationType: string;
  theme: 'light' | 'dark' | 'drilling-slate' | 'system';
}

// Helper function to determine compatible chart types based on data structure
const getCompatibleChartTypes = (columns: string[], rows: any[], rowCount: number): string[] => {
  const compatible: string[] = ['table']; // Table always works

  if (rowCount === 0) return compatible;

  // Helper to check if column is numeric
  const isNumeric = (col: string) => {
    try {
      return typeof rows[0][col] === 'number';
    } catch {
      return false;
    }
  };

  const numericCols = columns.filter(isNumeric);
  const categoricalCols = columns.filter(col => !isNumeric(col));

  // Heuristic: Is this a "Metric" (Count/Amount) or "Dimension" (Age/Year)?
  // If we only have "Dimension" style numbers, we might prefer charts that can handle Counts (like Bar/Pie) 
  // explicitly over those that require 3+ numbers.

  // Basic charts (need at least 2 columns)
  if (columns.length >= 2) {
    compatible.push('bar', 'scatter', 'area');

    // Pie/donut for categorical + numeric
    // OR just categorical (we can count)
    if (categoricalCols.length >= 1) {
      compatible.push('pie', 'donut');
    }
  }

  // Line chart (works with 2+ columns)
  if (columns.length >= 2) {
    compatible.push('line');
  }

  // Statistical charts (need numeric data)
  if (numericCols.length >= 1) {
    compatible.push('box', 'violin', 'histogram');
  }

  // Heatmap (need 2+ numeric columns)
  if (numericCols.length >= 2) {
    compatible.push('heatmap');
  }

  // 3D charts (need 3+ numeric columns)
  if (numericCols.length >= 3) {
    compatible.push('scatter3d', 'surface');
  }

  // Maps (need state/country column)
  if (columns.some(col => col.toLowerCase().includes('state') || col.toLowerCase().includes('country'))) {
    compatible.push('choropleth', 'scattergeo');
  }

  // Hierarchical (need 2+ categorical columns)
  if (categoricalCols.length >= 2) {
    compatible.push('sunburst', 'treemap');
  }

  // Specialized
  if (numericCols.length >= 1) {
    compatible.push('indicator', 'gauge');
  }

  if (numericCols.length >= 4) {
    compatible.push('parcoords', 'splom');
  }

  // Financial
  if (columns.length >= 2) {
    compatible.push('waterfall', 'funnel');
  }

  return compatible;
};

// Utils for smart column selection
const METRIC_KEYWORDS = ['count', 'total', 'sum', 'amount', 'revenue', 'profit', 'sales', 'val', 'cost', 'bill', 'avg', 'average', 'score', 'rating', 'rate', 'percent', 'min', 'max'];
const DIMENSION_KEYWORDS = ['age', 'year', 'month', 'day', 'id', 'zip', 'code', 'lat', 'lon'];

const isMetricColumn = (colName: string) => METRIC_KEYWORDS.some(kw => colName.toLowerCase().includes(kw));
const isDimensionColumn = (colName: string) => DIMENSION_KEYWORDS.some(kw => colName.toLowerCase().includes(kw));

const getBestValueColumn = (columns: string[], rows: any[]): string | null => {
  const numericCols = columns.filter(col => typeof rows[0][col] === 'number');
  if (numericCols.length === 0) return null;

  // 1. Prefer explicit metrics
  const explicitMetric = numericCols.find(isMetricColumn);
  if (explicitMetric) return explicitMetric;

  // 2. Avoid dimensions if possible
  const nonDimension = numericCols.find(col => !isDimensionColumn(col));
  if (nonDimension) return nonDimension;

  // 3. Fallback (but logic should handle "null" implies "Count rows")
  return numericCols[0];
};

const shouldUseRowCount = (valueCol: string | null): boolean => {
  if (!valueCol) return true;
  return isDimensionColumn(valueCol) && !isMetricColumn(valueCol);
};

const PlotlyVisualizer: React.FC<PlotlyVisualizerProps> = ({ data, visualizationType, theme }) => {
  const [selectedChartType, setSelectedChartType] = useState<string>(visualizationType);

  // Determine current theme for Plotly
  const isDark = useMemo(() => {
    if (theme === 'system') {
      return typeof window !== 'undefined' ? window.matchMedia('(prefers-color-scheme: dark)').matches : true;
    }
    return theme === 'dark';
  }, [theme]);

  // Determine compatible chart types based on data
  const compatibleChartTypes = useMemo(() => {
    if (!data || !data.columns || !data.data) return ['table'];
    return getCompatibleChartTypes(data.columns, data.data, data.data.length);
  }, [data]);

  // Update selected chart type when visualizationType prop changes
  React.useEffect(() => {
    setSelectedChartType(visualizationType);
  }, [visualizationType]);

  const { plotData, layout } = useMemo(() => {
    if (!data || !data.columns || !data.data || data.data.length === 0) {
      return { plotData: [], layout: {} };
    }

    const columns = data.columns;
    const rows = data.data;

    // Theme Palette (Centralized CSS Variables)
    // We use getComputedStyle if we need explicit hex for logic, but for simple assignment, var() works.
    // However, for consistency with 'palette' array which Plotly needs as explicit colors sometimes,
    // we might stick to a static palette for the series but theme-aware for the layout.
    // Actually, let's try strict var usage where possible.
    const themeColors = {
      primary: 'var(--chart-primary)',
      text: 'var(--chart-text)',
      bgPaper: 'var(--chart-bg-paper)',
      bgPlot: 'var(--chart-bg-plot)',
      grid: 'var(--chart-grid)',
      zeroLine: 'var(--chart-grid)', // Reuse grid color
      // Palette: We can't easily use var() in an array for 'colorway' without defining them all.
      // Use hardcoded theme-aware palette for data series if needed, OR relies on Plotly's default which is good.
      // But we promised 'Abyss'. Let's use a var-based palette if possible or keep the hex logic for data series only.
      // Given the requirement for "instant switch", CSS vars are best.
      palette: [
        'var(--chart-primary)',
        '#EF4444',
        '#10B981',
        '#F59E0B',
        '#EC4899',
        '#6366F1'
      ]
    };

    // Theme Configuration
    const baseLayout: any = {
      paper_bgcolor: themeColors.bgPaper,
      plot_bgcolor: themeColors.bgPlot,
      font: {
        color: themeColors.text,
        family: 'var(--font-heading)'
      },
      margin: { t: 40, r: 20, b: 60, l: 60 },
      hoverlabel: {
        bgcolor: themeColors.bgPaper,
        font: { color: themeColors.text, size: 12 },
        bordercolor: themeColors.grid
      },
      xaxis: {
        gridcolor: themeColors.grid,
        zerolinecolor: themeColors.zeroLine,
        tickcolor: themeColors.text
      },
      yaxis: {
        gridcolor: themeColors.grid,
        zerolinecolor: themeColors.zeroLine,
        tickcolor: themeColors.text
      }
    };

    // Helper to extract column data
    const getColumn = (colName: string) => rows.map((row: any) => row[colName]);

    // Determine chart type and generate appropriate data
    switch (selectedChartType) {
      // ===== BASIC CHARTS =====
      case 'bar': {
        const xCol = columns[0];
        const yCol = columns[1];

        // Smart Value Detection
        const bestValueCol = getBestValueColumn(columns, rows);
        const useCount = shouldUseRowCount(bestValueCol);

        // Aggregate if X is not unique implies grouping needed
        const uniqueX = new Set(getColumn(xCol));

        if (uniqueX.size < rows.length) {
          const aggMap = new Map<string, number>();
          rows.forEach((row: any) => {
            const key = String(row[xCol]);
            const val = useCount ? 1 : (Number(row[bestValueCol!]) || 0);
            aggMap.set(key, (aggMap.get(key) || 0) + val);
          });

          return {
            plotData: [{
              type: 'bar',
              x: Array.from(aggMap.keys()),
              y: Array.from(aggMap.values()),
              marker: { color: '#00F0FF', line: { color: '#00F0FF', width: 1 } }
            }],
            layout: { ...baseLayout, title: `Bar Chart (${useCount ? 'Count' : bestValueCol})`, xaxis: { ...baseLayout.xaxis, title: xCol }, yaxis: { ...baseLayout.yaxis, title: useCount ? 'Count' : bestValueCol } }
          };
        }

        return {
          plotData: [{
            type: 'bar',
            x: getColumn(xCol),
            y: getColumn(yCol),
            marker: { color: '#00F0FF', line: { color: '#00F0FF', width: 1 } }
          }],
          layout: { ...baseLayout, title: 'Bar Chart', xaxis: { ...baseLayout.xaxis, title: xCol }, yaxis: { ...baseLayout.yaxis, title: yCol } }
        };
      }

      case 'pie':
      case 'donut': {
        const labelCol = columns[0];
        const bestValueCol = getBestValueColumn(columns, rows);
        const useCount = shouldUseRowCount(bestValueCol);

        const aggMap = new Map<string, number>();
        rows.forEach((row: any) => {
          const key = String(row[labelCol]);
          const val = useCount ? 1 : (Number(row[bestValueCol!]) || 0);
          aggMap.set(key, (aggMap.get(key) || 0) + val);
        });

        const labels = Array.from(aggMap.keys());
        const values = Array.from(aggMap.values());

        return {
          plotData: [{
            type: 'pie',
            labels: labels,
            values: values,
            hole: selectedChartType === 'donut' ? 0.4 : 0,
            marker: { colors: ['#00F0FF', '#FF0055', '#00FF88', '#FFD700', '#FF6B6B', '#4ECDC4'] },
            textfont: { color: '#000' },
            textinfo: 'label+percent',
            hoverinfo: 'label+value+percent'
          }],
          layout: { ...baseLayout, title: `${selectedChartType === 'donut' ? 'Donut' : 'Pie'} Chart (${useCount ? 'Count' : bestValueCol})` }
        };
      }

      case 'line': {
        const xCol = columns[0];
        const yCol = columns[1];
        return {
          plotData: [{
            type: 'scatter',
            mode: 'lines',
            x: getColumn(xCol),
            y: getColumn(yCol),
            line: { color: themeColors.primary, width: 2 }
          }],
          layout: { ...baseLayout, title: 'Line Chart', xaxis: { ...baseLayout.xaxis, title: xCol }, yaxis: { ...baseLayout.yaxis, title: yCol } }
        };
      }

      case 'scatter': {
        const xCol = columns[0];
        const yCol = columns[1];
        return {
          plotData: [{
            type: 'scatter',
            mode: 'markers',
            x: getColumn(xCol),
            y: getColumn(yCol),
            marker: { color: themeColors.primary, size: 8, line: { color: '#fff', width: 0.5 } }
          }],
          layout: { ...baseLayout, title: 'Scatter Plot', xaxis: { ...baseLayout.xaxis, title: xCol }, yaxis: { ...baseLayout.yaxis, title: yCol } }
        };
      }

      case 'area': {
        const xCol = columns[0];
        const yCol = columns[1];
        return {
          plotData: [{
            type: 'scatter',
            mode: 'lines',
            fill: 'tozeroy',
            x: getColumn(xCol),
            y: getColumn(yCol),
            fillcolor: isDark ? 'rgba(0, 240, 255, 0.3)' : 'rgba(59, 130, 246, 0.3)',
            line: { color: themeColors.primary, width: 2 }
          }],
          layout: { ...baseLayout, title: 'Area Chart', xaxis: { ...baseLayout.xaxis, title: xCol }, yaxis: { ...baseLayout.yaxis, title: yCol } }
        };
      }

      // ===== STATISTICAL CHARTS =====
      case 'box': {
        const yCol = columns.find((col: string) => typeof rows[0][col] === 'number') || columns[0];
        return {
          plotData: [{
            type: 'box',
            y: getColumn(yCol),
            marker: { color: themeColors.primary },
            line: { color: themeColors.primary }
          }],
          layout: { ...baseLayout, title: 'Box Plot', yaxis: { ...baseLayout.yaxis, title: yCol } }
        };
      }

      case 'violin': {
        const yCol = columns.find((col: string) => typeof rows[0][col] === 'number') || columns[0];
        return {
          plotData: [{
            type: 'violin',
            y: getColumn(yCol),
            marker: { color: themeColors.primary },
            line: { color: themeColors.primary }
          }],
          layout: { ...baseLayout, title: 'Violin Plot', yaxis: { ...baseLayout.yaxis, title: yCol } }
        };
      }

      case 'histogram': {
        const xCol = columns.find((col: string) => typeof rows[0][col] === 'number') || columns[0];
        return {
          plotData: [{
            type: 'histogram',
            x: getColumn(xCol),
            marker: { color: themeColors.primary, line: { color: '#fff', width: 0.5 } }
          }],
          layout: { ...baseLayout, title: 'Histogram', xaxis: { ...baseLayout.xaxis, title: xCol }, yaxis: { ...baseLayout.yaxis, title: 'Frequency' } }
        };
      }

      case 'heatmap': {
        const numericCols = columns.filter((col: string) => typeof rows[0][col] === 'number');
        const matrix = numericCols.map((col1: string) =>
          numericCols.map((col2: string) => {
            const data1 = getColumn(col1);
            const data2 = getColumn(col2);
            const mean1 = data1.reduce((a: number, b: number) => a + b, 0) / data1.length;
            const mean2 = data2.reduce((a: number, b: number) => a + b, 0) / data2.length;
            const num = data1.reduce((sum: number, val: number, i: number) => sum + (val - mean1) * (data2[i] - mean2), 0);
            const den1 = Math.sqrt(data1.reduce((sum: number, val: number) => sum + Math.pow(val - mean1, 2), 0));
            const den2 = Math.sqrt(data2.reduce((sum: number, val: number) => sum + Math.pow(val - mean2, 2), 0));
            return num / (den1 * den2);
          })
        );
        return {
          plotData: [{
            type: 'heatmap',
            z: matrix,
            x: numericCols,
            y: numericCols,
            colorscale: isDark ? [[0, '#020408'], [0.5, '#00F0FF'], [1, '#FF0055']] : 'Viridis',
            showscale: true
          }],
          layout: { ...baseLayout, title: 'Correlation Heatmap' }
        };
      }

      case 'contour': {
        const xCol = columns[0];
        const yCol = columns[1];
        const zCol = columns[2] || columns[1];
        return {
          plotData: [{
            type: 'contour',
            x: getColumn(xCol),
            y: getColumn(yCol),
            z: getColumn(zCol),
            colorscale: [[0, '#020408'], [0.5, '#00F0FF'], [1, '#FF0055']],
            contours: { coloring: 'heatmap' }
          }],
          layout: { ...baseLayout, title: 'Contour Plot', xaxis: { ...baseLayout.xaxis, title: xCol }, yaxis: { ...baseLayout.yaxis, title: yCol } }
        };
      }

      // ===== FINANCIAL CHARTS =====
      case 'waterfall': {
        const xCol = columns[0];
        const yCol = columns[1];
        return {
          plotData: [{
            type: 'waterfall',
            x: getColumn(xCol),
            y: getColumn(yCol),
            connector: { line: { color: themeColors.primary } },
            increasing: { marker: { color: isDark ? '#00FF88' : '#10b981' } },
            decreasing: { marker: { color: isDark ? '#FF0055' : '#ef4444' } },
            totals: { marker: { color: isDark ? '#FFD700' : '#f59e0b' } }
          }],
          layout: { ...baseLayout, title: 'Waterfall Chart', xaxis: { ...baseLayout.xaxis, title: xCol }, yaxis: { ...baseLayout.yaxis, title: yCol } }
        };
      }

      case 'funnel': {
        const xCol = columns[0];
        const yCol = columns[1];
        return {
          plotData: [{
            type: 'funnel',
            y: getColumn(xCol),
            x: getColumn(yCol),
            marker: { color: themeColors.primary }
          }],
          layout: { ...baseLayout, title: 'Funnel Chart' }
        };
      }

      // ===== 3D CHARTS =====
      case 'scatter3d': {
        const xCol = columns[0];
        const yCol = columns[1];
        const zCol = columns[2] || columns[1];
        return {
          plotData: [{
            type: 'scatter3d',
            mode: 'markers',
            x: getColumn(xCol),
            y: getColumn(yCol),
            z: getColumn(zCol),
            marker: { color: themeColors.primary, size: 5, line: { color: '#fff', width: 0.5 } }
          }],
          layout: {
            ...baseLayout,
            title: '3D Scatter Plot',
            scene: {
              xaxis: { title: xCol, gridcolor: themeColors.grid },
              yaxis: { title: yCol, gridcolor: themeColors.grid },
              zaxis: { title: zCol, gridcolor: themeColors.grid },
              bgcolor: 'transparent'
            }
          }
        };
      }

      case 'surface': {
        const xCol = columns[0];
        const yCol = columns[1];
        const zCol = columns[2] || columns[1];
        return {
          plotData: [{
            type: 'surface',
            x: getColumn(xCol),
            y: getColumn(yCol),
            z: [getColumn(zCol)],
            colorscale: [[0, '#020408'], [0.5, '#00F0FF'], [1, '#FF0055']]
          }],
          layout: {
            ...baseLayout,
            title: '3D Surface Plot',
            scene: {
              xaxis: { title: xCol, gridcolor: 'rgba(0, 240, 255, 0.2)' },
              yaxis: { title: yCol, gridcolor: 'rgba(0, 240, 255, 0.2)' },
              zaxis: { title: zCol, gridcolor: 'rgba(0, 240, 255, 0.2)' },
              bgcolor: 'rgba(2, 4, 8, 0.5)'
            }
          }
        };
      }

      // ===== HIERARCHICAL CHARTS =====
      case 'sunburst': {
        const categoricalCols = columns.filter(col => typeof rows[0][col] === 'string');
        const bestValueCol = getBestValueColumn(columns, rows);
        const useCount = shouldUseRowCount(bestValueCol);

        const getValue = (row: any) => useCount ? 1 : (Number(row[bestValueCol!]) || 1);

        if (categoricalCols.length >= 2) {
          const labels: string[] = ['Total'];
          const parents: string[] = [''];
          const values: number[] = [rows.reduce((sum, row) => sum + getValue(row), 0)];

          const level1Map = new Map<string, number>();
          rows.forEach(row => {
            const key = String(row[categoricalCols[0]]);
            level1Map.set(key, (level1Map.get(key) || 0) + getValue(row));
          });

          level1Map.forEach((value, key) => {
            labels.push(key);
            parents.push('Total');
            values.push(value);
          });

          rows.forEach(row => {
            const parent = String(row[categoricalCols[0]]);
            const child = String(row[categoricalCols[1]]);
            const label = `${parent} - ${child}`;
            const value = getValue(row);
            if (!labels.includes(label)) {
              labels.push(label);
              parents.push(parent);
              values.push(value);
            }
          });

          return {
            plotData: [{
              type: 'sunburst',
              labels: labels,
              parents: parents,
              values: values,
              marker: { colors: ['#00F0FF', '#FF0055', '#00FF88', '#FFD700', '#FF6B6B', '#4ECDC4'] },
              textfont: { color: '#000' },
              branchvalues: 'total'
            }],
            layout: { ...baseLayout, title: `Sunburst Chart (${useCount ? 'Count' : bestValueCol})` }
          };
        } else {
          const labelCol = categoricalCols[0] || columns[0];
          return {
            plotData: [{
              type: 'sunburst',
              labels: getColumn(labelCol),
              parents: Array(rows.length).fill(''),
              values: rows.map(getValue),
              marker: { colors: ['#00F0FF', '#FF0055', '#00FF88', '#FFD700', '#FF6B6B', '#4ECDC4'] },
              textfont: { color: '#000' }
            }],
            layout: { ...baseLayout, title: `Sunburst Chart (${useCount ? 'Count' : bestValueCol})` }
          };
        }
      }

      case 'treemap': {
        const categoricalCols = columns.filter(col => typeof rows[0][col] === 'string');
        const bestValueCol = getBestValueColumn(columns, rows);
        const useCount = shouldUseRowCount(bestValueCol);

        const getValue = (row: any) => useCount ? 1 : (Number(row[bestValueCol!]) || 1);

        if (categoricalCols.length >= 2) {
          const labels: string[] = ['Total'];
          const parents: string[] = [''];
          const values: number[] = [rows.reduce((sum, row) => sum + getValue(row), 0)];

          const level1Map = new Map<string, number>();
          rows.forEach(row => {
            const key = String(row[categoricalCols[0]]);
            level1Map.set(key, (level1Map.get(key) || 0) + getValue(row));
          });

          level1Map.forEach((value, key) => {
            labels.push(key);
            parents.push('Total');
            values.push(value);
          });

          rows.forEach(row => {
            const parent = String(row[categoricalCols[0]]);
            const child = String(row[categoricalCols[1]]);
            const label = `${parent} - ${child}`;
            const value = getValue(row);
            if (!labels.includes(label)) {
              labels.push(label);
              parents.push(parent);
              values.push(value);
            }
          });

          return {
            plotData: [{
              type: 'treemap',
              labels: labels,
              parents: parents,
              values: values,
              marker: { colors: ['#00F0FF', '#FF0055', '#00FF88', '#FFD700', '#FF6B6B', '#4ECDC4'] },
              textfont: { color: '#000' },
              branchvalues: 'total'
            }],
            layout: { ...baseLayout, title: `Treemap (${useCount ? 'Count' : bestValueCol})` }
          };
        } else {
          const labelCol = categoricalCols[0] || columns[0];
          return {
            plotData: [{
              type: 'treemap',
              labels: getColumn(labelCol),
              parents: Array(rows.length).fill(''),
              values: rows.map(getValue),
              marker: { colors: ['#00F0FF', '#FF0055', '#00FF88', '#FFD700', '#FF6B6B', '#4ECDC4'] },
              textfont: { color: '#000' }
            }],
            layout: { ...baseLayout, title: `Treemap (${useCount ? 'Count' : bestValueCol})` }
          };
        }
      }

      case 'sankey': {
        const sourceCol = columns[0];
        const targetCol = columns[1];
        const valueCol = columns[2] || columns[1];
        return {
          plotData: [{
            type: 'sankey',
            node: {
              label: [...new Set([...getColumn(sourceCol), ...getColumn(targetCol)])],
              color: themeColors.primary,
              pad: 15,
              thickness: 20,
              line: { color: '#fff', width: 0.5 }
            },
            link: {
              source: getColumn(sourceCol).map((s: string) => [...new Set([...getColumn(sourceCol), ...getColumn(targetCol)])].indexOf(s)),
              target: getColumn(targetCol).map((t: string) => [...new Set([...getColumn(sourceCol), ...getColumn(targetCol)])].indexOf(t)),
              value: getColumn(valueCol),
              color: isDark ? 'rgba(0, 240, 255, 0.4)' : 'rgba(59, 130, 246, 0.4)'
            }
          }],
          layout: { ...baseLayout, title: 'Sankey Diagram' }
        };
      }

      // ===== SPECIALIZED CHARTS =====
      case 'indicator': {
        const bestValueCol = getBestValueColumn(columns, rows);
        const useCount = shouldUseRowCount(bestValueCol);

        // Helper to check if we should average or sum
        const IS_AVG_KEYWORD = ['avg', 'average', 'rate', 'percent', 'score', 'min', 'max', 'mean', 'median'];
        const shouldAverage = bestValueCol && IS_AVG_KEYWORD.some(kw => bestValueCol.toLowerCase().includes(kw));

        let value = 0;
        let prefix = "";

        if (useCount) {
          value = rows.length;
          prefix = "Total Count";
        } else {
          // Calculate Sum first
          const sum = rows.reduce((a: number, r: any) => a + (Number(r[bestValueCol!]) || 0), 0);

          if (shouldAverage && rows.length > 0) {
            value = sum / rows.length;
            prefix = `Avg ${bestValueCol}`;
          } else {
            value = sum;
            prefix = `Total ${bestValueCol}`;
          }
        }

        return {
          plotData: [{
            type: 'indicator',
            mode: 'number',
            value: value,
            domain: { x: [0, 1], y: [0, 1] },
            title: { text: prefix, font: { color: '#00F0FF' } },
            number: { font: { color: '#00F0FF', size: 60 }, valueformat: shouldAverage ? ".1f" : "d" }
          }],
          layout: { ...baseLayout, title: 'KPI Indicator' }
        };
      }

      case 'gauge': {
        const bestValueCol = getBestValueColumn(columns, rows);
        const useCount = shouldUseRowCount(bestValueCol);

        let value = 0;
        let axisRange = 100;

        if (useCount) {
          value = rows.length;
          axisRange = value * 1.5;
        } else {
          const values = getColumn(bestValueCol!);
          value = values.reduce((a: number, b: number) => a + b, 0) / values.length;
          axisRange = Math.max(...values);
        }

        return {
          plotData: [{
            type: 'indicator',
            mode: 'gauge+number',
            value: value,
            gauge: {
              axis: { range: [null, axisRange], tickcolor: '#00F0FF' },
              bar: { color: '#00F0FF' },
              bgcolor: 'rgba(2, 4, 8, 0.5)',
              borderwidth: 2,
              bordercolor: '#00F0FF',
              steps: [
                { range: [0, axisRange * 0.5], color: 'rgba(0, 240, 255, 0.2)' },
                { range: [axisRange * 0.5, axisRange], color: 'rgba(0, 240, 255, 0.4)' }
              ]
            },
            title: { text: useCount ? 'Count' : `Avg ${bestValueCol}`, font: { color: '#00F0FF' } }
          }],
          layout: { ...baseLayout, title: 'Gauge Chart' }
        };
      }

      case 'parcoords': {
        const numericCols = columns.filter((col: string) => typeof rows[0][col] === 'number');
        const dimensions = numericCols.map((col: string) => ({
          label: col,
          values: getColumn(col)
        }));
        return {
          plotData: [{
            type: 'parcoords',
            line: { color: '#00F0FF', colorscale: [[0, '#020408'], [0.5, '#00F0FF'], [1, '#FF0055']] },
            dimensions: dimensions
          }],
          layout: { ...baseLayout, title: 'Parallel Coordinates' }
        };
      }

      case 'splom': {
        const numericCols = columns.filter((col: string) => typeof rows[0][col] === 'number').slice(0, 4);
        const dimensions = numericCols.map((col: string) => ({
          label: col,
          values: getColumn(col)
        }));
        return {
          plotData: [{
            type: 'splom',
            dimensions: dimensions,
            marker: { color: '#00F0FF', size: 5, line: { color: '#fff', width: 0.5 } }
          }],
          layout: { ...baseLayout, title: 'Scatter Plot Matrix (SPLOM)' }
        };
      }

      // ===== MAPS =====
      case 'choropleth':
      case 'map': {
        const locationCol = columns.find((col: string) => col.toLowerCase().includes('state')) || columns[0];
        const bestValueCol = getBestValueColumn(columns, rows);
        const useCount = shouldUseRowCount(bestValueCol);

        const stateMap = new Map<string, number>();
        rows.forEach((row: any) => {
          const loc = row[locationCol];
          const val = useCount ? 1 : (Number(row[bestValueCol!]) || 0);
          stateMap.set(loc, (stateMap.get(loc) || 0) + val);
        });

        const locations = Array.from(stateMap.keys());
        const z = Array.from(stateMap.values());

        return {
          plotData: [{
            type: 'choropleth',
            locationmode: 'USA-states',
            locations: locations,
            z: z,
            colorscale: isDark ? [[0, '#020408'], [0.5, '#00F0FF'], [1, '#FF0055']] : 'Blues',
            colorbar: { title: useCount ? 'Count' : bestValueCol, tickfont: { color: themeColors.text } },
            marker: { line: { color: themeColors.primary, width: 1 } }
          }],
          layout: {
            ...baseLayout,
            title: `USA Choropleth Map (${useCount ? 'Patient Count' : bestValueCol})`,
            geo: {
              scope: 'usa',
              projection: { type: 'albers usa' },
              showlakes: true,
              lakecolor: isDark ? 'rgba(0, 240, 255, 0.1)' : 'rgba(59, 130, 246, 0.1)',
              bgcolor: themeColors.bgPlot
            }
          }
        };
      }

      case 'scattergeo': {
        const locationCol = columns.find((col: string) => col.toLowerCase().includes('state')) || columns[0];
        const bestValueCol = getBestValueColumn(columns, rows);
        const useCount = shouldUseRowCount(bestValueCol);

        const stateMap = new Map<string, number>();
        rows.forEach((row: any) => {
          const loc = row[locationCol];
          const val = useCount ? 1 : (Number(row[bestValueCol!]) || 0);
          stateMap.set(loc, (stateMap.get(loc) || 0) + val);
        });

        const locations = Array.from(stateMap.keys());
        const sizes = Array.from(stateMap.values());

        const maxSize = Math.max(...sizes);
        const markerSizes = sizes.map(s => (s / maxSize) * 30 + 5);

        return {
          plotData: [{
            type: 'scattergeo',
            locationmode: 'USA-states',
            locations: locations,
            text: sizes.map((v, i) => `${locations[i]}: ${v}`),
            marker: { size: markerSizes, color: '#00F0FF', line: { color: '#fff', width: 1 } }
          }],
          layout: {
            ...baseLayout,
            title: `Scatter Geo Map (${useCount ? 'Patient Count' : bestValueCol})`,
            geo: {
              scope: 'usa',
              projection: { type: 'albers usa' },
              showlakes: true,
              lakecolor: 'rgba(0, 240, 255, 0.1)',
              bgcolor: 'rgba(2, 4, 8, 0.5)'
            }
          }
        };
      }

      // ===== TABLE (Fallback) =====
      case 'table':
      default: {
        // Theme-aware colors
        const headerFill = isDark ? 'rgba(0, 240, 255, 0.2)' : '#f3f4f6';
        const headerFontColor = isDark ? '#E0F7FA' : '#1f2937';
        const cellFill = isDark
          ? ['rgba(2, 4, 8, 0.5)', 'rgba(0, 240, 255, 0.05)']
          : ['#ffffff', '#f9fafb'];
        const cellFontColor = isDark ? '#E0F7FA' : '#374151';
        const lineColor = isDark ? '#00F0FF' : '#e5e7eb';

        return {
          plotData: [{
            type: 'table',
            header: {
              values: columns,
              align: 'center',
              line: { width: 1, color: lineColor },
              fill: { color: headerFill },
              font: { family: isDark ? 'Rajdhani' : 'Inter', size: 14, color: headerFontColor }
            },
            cells: {
              values: columns.map((col: string) => getColumn(col)),
              align: 'center',
              line: { color: isDark ? 'rgba(0, 240, 255, 0.1)' : '#e5e7eb', width: 1 },
              fill: { color: cellFill },
              font: { family: isDark ? 'Rajdhani' : 'Inter', size: 12, color: cellFontColor }
            }
          }],
          layout: { ...baseLayout, title: 'Data Table' }
        };
      }
    }
  }, [data, selectedChartType]);

  if (!plotData || plotData.length === 0) {
    return (
      <div className="text-center text-[#00F0FF] p-4 border border-[#00F0FF]/30 rounded">
        No data available for visualization
      </div>
    );
  }

  return (
    <div className="w-full space-y-4">
      {/* Chart Type Selector */}
      {compatibleChartTypes.length > 1 && (
        <div className={`flex flex-wrap gap-1.5 p-2 border rounded backdrop-blur-sm ${isDark
          ? 'bg-[#020408]/60 border-[#00F0FF]/20'
          : 'bg-white/60 border-gray-200'
          }`}>
          <span className={`text-[10px] font-bold uppercase tracking-wider mr-2 self-center ${isDark ? 'text-[#00F0FF]/70' : 'text-gray-500'
            }`}>
            Visualization:
          </span>
          {compatibleChartTypes.map((chartType) => (
            <button
              key={chartType}
              onClick={() => setSelectedChartType(chartType)}
              className={`
                px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider
                transition-all duration-200
                ${selectedChartType === chartType
                  ? isDark
                    ? 'bg-[#00F0FF] text-[#020408] shadow-[0_0_10px_rgba(0,240,255,0.5)]'
                    : 'bg-blue-500 text-white shadow-sm'
                  : isDark
                    ? 'bg-[#020408]/80 text-[#00F0FF]/70 border border-[#00F0FF]/30 hover:border-[#00F0FF] hover:text-[#00F0FF]'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-blue-300 hover:text-blue-500'
                }
              `}
            >
              {chartType}
            </button>
          ))}
        </div>
      )}

      {/* Chart Display */}
      <Plot
        key={theme} // Force re-render on theme change
        data={plotData}
        layout={{
          ...layout,
          autosize: true,
          height: 500,
          modebar: {
            bgcolor: 'transparent',
          }
        }}
        config={{
          displayModeBar: true,
          displaylogo: false,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          toImageButtonOptions: {
            format: 'png',
            filename: 'chart',
            height: 800,
            width: 1200,
            scale: 2
          }
        }}
        style={{ width: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
};

export default PlotlyVisualizer;
