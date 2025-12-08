// @ts-nocheck
import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

interface PlotlyVisualizerProps {
  data: any;
  visualizationType: string;
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

  // Basic charts (need at least 2 columns)
  if (columns.length >= 2) {
    compatible.push('bar', 'scatter', 'area');

    // Pie/donut for categorical + numeric
    if (categoricalCols.length >= 1 && numericCols.length >= 1) {
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


const PlotlyVisualizer: React.FC<PlotlyVisualizerProps> = ({ data, visualizationType }) => {
  const [selectedChartType, setSelectedChartType] = useState<string>(visualizationType);

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

    // Dark theme layout (HUD aesthetic)
    const baseLayout: any = {
      paper_bgcolor: 'rgba(2, 4, 8, 0.8)',
      plot_bgcolor: 'rgba(2, 4, 8, 0.5)',
      font: { color: '#E0F7FA', family: 'Rajdhani, sans-serif' },
      margin: { t: 40, r: 20, b: 60, l: 60 },
      hoverlabel: {
        bgcolor: 'rgba(0, 240, 255, 0.9)',
        font: { color: '#000', size: 12 }
      },
      xaxis: {
        gridcolor: 'rgba(0, 240, 255, 0.2)',
        zerolinecolor: 'rgba(0, 240, 255, 0.3)'
      },
      yaxis: {
        gridcolor: 'rgba(0, 240, 255, 0.2)',
        zerolinecolor: 'rgba(0, 240, 255, 0.3)'
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

      case 'pie': {
        const labelCol = columns[0];
        const valueCol = columns[1];
        return {
          plotData: [{
            type: 'pie',
            labels: getColumn(labelCol),
            values: getColumn(valueCol),
            marker: { colors: ['#00F0FF', '#FF0055', '#00FF88', '#FFD700', '#FF6B6B', '#4ECDC4'] },
            textfont: { color: '#000' }
          }],
          layout: { ...baseLayout, title: 'Pie Chart' }
        };
      }

      case 'donut': {
        const labelCol = columns[0];
        const valueCol = columns[1];
        return {
          plotData: [{
            type: 'pie',
            labels: getColumn(labelCol),
            values: getColumn(valueCol),
            hole: 0.4,
            marker: { colors: ['#00F0FF', '#FF0055', '#00FF88', '#FFD700', '#FF6B6B', '#4ECDC4'] },
            textfont: { color: '#000' }
          }],
          layout: { ...baseLayout, title: 'Donut Chart' }
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
            line: { color: '#00F0FF', width: 2 }
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
            marker: { color: '#00F0FF', size: 8, line: { color: '#fff', width: 0.5 } }
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
            fillcolor: 'rgba(0, 240, 255, 0.3)',
            line: { color: '#00F0FF', width: 2 }
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
            marker: { color: '#00F0FF' },
            line: { color: '#00F0FF' }
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
            marker: { color: '#00F0FF' },
            line: { color: '#00F0FF' }
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
            marker: { color: '#00F0FF', line: { color: '#fff', width: 0.5 } }
          }],
          layout: { ...baseLayout, title: 'Histogram', xaxis: { ...baseLayout.xaxis, title: xCol }, yaxis: { ...baseLayout.yaxis, title: 'Frequency' } }
        };
      }

      case 'heatmap': {
        // Assume all numeric columns for correlation matrix
        const numericCols = columns.filter((col: string) => typeof rows[0][col] === 'number');
        const matrix = numericCols.map((col1: string) =>
          numericCols.map((col2: string) => {
            const data1 = getColumn(col1);
            const data2 = getColumn(col2);
            // Simple correlation calculation
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
            colorscale: [[0, '#020408'], [0.5, '#00F0FF'], [1, '#FF0055']],
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
            connector: { line: { color: '#00F0FF' } },
            increasing: { marker: { color: '#00FF88' } },
            decreasing: { marker: { color: '#FF0055' } },
            totals: { marker: { color: '#FFD700' } }
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
            marker: { color: '#00F0FF' }
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
            marker: { color: '#00F0FF', size: 5, line: { color: '#fff', width: 0.5 } }
          }],
          layout: {
            ...baseLayout,
            title: '3D Scatter Plot',
            scene: {
              xaxis: { title: xCol, gridcolor: 'rgba(0, 240, 255, 0.2)' },
              yaxis: { title: yCol, gridcolor: 'rgba(0, 240, 255, 0.2)' },
              zaxis: { title: zCol, gridcolor: 'rgba(0, 240, 255, 0.2)' },
              bgcolor: 'rgba(2, 4, 8, 0.5)'
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
        // Build hierarchical structure from flat data
        // If we have 2+ categorical columns, create parent-child relationships
        const categoricalCols = columns.filter(col => typeof rows[0][col] === 'string');
        const numericCol = columns.find(col => typeof rows[0][col] === 'number') || columns[columns.length - 1];

        if (categoricalCols.length >= 2) {
          // Multi-level hierarchy
          const labels: string[] = ['Total']; // Root node
          const parents: string[] = [''];
          const values: number[] = [rows.reduce((sum, row) => sum + (Number(row[numericCol]) || 1), 0)];

          // Level 1: First categorical column
          const level1Map = new Map<string, number>();
          rows.forEach(row => {
            const key = String(row[categoricalCols[0]]);
            level1Map.set(key, (level1Map.get(key) || 0) + (Number(row[numericCol]) || 1));
          });

          level1Map.forEach((value, key) => {
            labels.push(key);
            parents.push('Total');
            values.push(value);
          });

          // Level 2: Second categorical column
          rows.forEach(row => {
            const parent = String(row[categoricalCols[0]]);
            const child = String(row[categoricalCols[1]]);
            const label = `${parent} - ${child}`;
            const value = Number(row[numericCol]) || 1;

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
            layout: { ...baseLayout, title: 'Sunburst Chart' }
          };
        } else {
          // Single level - just use first column as categories
          const labelCol = categoricalCols[0] || columns[0];
          const valueCol = numericCol;
          return {
            plotData: [{
              type: 'sunburst',
              labels: getColumn(labelCol),
              parents: Array(rows.length).fill(''),
              values: getColumn(valueCol),
              marker: { colors: ['#00F0FF', '#FF0055', '#00FF88', '#FFD700', '#FF6B6B', '#4ECDC4'] },
              textfont: { color: '#000' }
            }],
            layout: { ...baseLayout, title: 'Sunburst Chart' }
          };
        }
      }

      case 'treemap': {
        // Build hierarchical structure from flat data
        const categoricalCols = columns.filter(col => typeof rows[0][col] === 'string');
        const numericCol = columns.find(col => typeof rows[0][col] === 'number') || columns[columns.length - 1];

        if (categoricalCols.length >= 2) {
          // Multi-level hierarchy
          const labels: string[] = ['Total'];
          const parents: string[] = [''];
          const values: number[] = [rows.reduce((sum, row) => sum + (Number(row[numericCol]) || 1), 0)];

          // Level 1
          const level1Map = new Map<string, number>();
          rows.forEach(row => {
            const key = String(row[categoricalCols[0]]);
            level1Map.set(key, (level1Map.get(key) || 0) + (Number(row[numericCol]) || 1));
          });

          level1Map.forEach((value, key) => {
            labels.push(key);
            parents.push('Total');
            values.push(value);
          });

          // Level 2
          rows.forEach(row => {
            const parent = String(row[categoricalCols[0]]);
            const child = String(row[categoricalCols[1]]);
            const label = `${parent} - ${child}`;
            const value = Number(row[numericCol]) || 1;

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
            layout: { ...baseLayout, title: 'Treemap' }
          };
        } else {
          // Single level
          const labelCol = categoricalCols[0] || columns[0];
          const valueCol = numericCol;
          return {
            plotData: [{
              type: 'treemap',
              labels: getColumn(labelCol),
              parents: Array(rows.length).fill(''),
              values: getColumn(valueCol),
              marker: { colors: ['#00F0FF', '#FF0055', '#00FF88', '#FFD700', '#FF6B6B', '#4ECDC4'] },
              textfont: { color: '#000' }
            }],
            layout: { ...baseLayout, title: 'Treemap' }
          };
        }
      }

      case 'sankey': {
        // Simplified Sankey - requires source, target, value
        const sourceCol = columns[0];
        const targetCol = columns[1];
        const valueCol = columns[2] || columns[1];
        return {
          plotData: [{
            type: 'sankey',
            node: {
              label: [...new Set([...getColumn(sourceCol), ...getColumn(targetCol)])],
              color: '#00F0FF',
              pad: 15,
              thickness: 20,
              line: { color: '#fff', width: 0.5 }
            },
            link: {
              source: getColumn(sourceCol).map((s: string) => [...new Set([...getColumn(sourceCol), ...getColumn(targetCol)])].indexOf(s)),
              target: getColumn(targetCol).map((t: string) => [...new Set([...getColumn(sourceCol), ...getColumn(targetCol)])].indexOf(t)),
              value: getColumn(valueCol),
              color: 'rgba(0, 240, 255, 0.4)'
            }
          }],
          layout: { ...baseLayout, title: 'Sankey Diagram' }
        };
      }

      // ===== SPECIALIZED CHARTS =====
      case 'indicator': {
        const valueCol = columns.find((col: string) => typeof rows[0][col] === 'number') || columns[0];
        const value = getColumn(valueCol).reduce((a: number, b: number) => a + b, 0);
        return {
          plotData: [{
            type: 'indicator',
            mode: 'number+delta',
            value: value,
            delta: { reference: value * 0.9 },
            domain: { x: [0, 1], y: [0, 1] },
            title: { text: valueCol, font: { color: '#00F0FF' } },
            number: { font: { color: '#00F0FF', size: 60 } }
          }],
          layout: { ...baseLayout, title: 'KPI Indicator' }
        };
      }

      case 'gauge': {
        const valueCol = columns.find((col: string) => typeof rows[0][col] === 'number') || columns[0];
        const values = getColumn(valueCol);
        const avgValue = values.reduce((a: number, b: number) => a + b, 0) / values.length;
        return {
          plotData: [{
            type: 'indicator',
            mode: 'gauge+number',
            value: avgValue,
            gauge: {
              axis: { range: [null, Math.max(...values)], tickcolor: '#00F0FF' },
              bar: { color: '#00F0FF' },
              bgcolor: 'rgba(2, 4, 8, 0.5)',
              borderwidth: 2,
              bordercolor: '#00F0FF',
              steps: [
                { range: [0, Math.max(...values) * 0.5], color: 'rgba(0, 240, 255, 0.2)' },
                { range: [Math.max(...values) * 0.5, Math.max(...values)], color: 'rgba(0, 240, 255, 0.4)' }
              ]
            },
            title: { text: valueCol, font: { color: '#00F0FF' } }
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
        const valueCol = columns[1];
        return {
          plotData: [{
            type: 'choropleth',
            locationmode: 'USA-states',
            locations: getColumn(locationCol),
            z: getColumn(valueCol),
            colorscale: [[0, '#020408'], [0.5, '#00F0FF'], [1, '#FF0055']],
            colorbar: { title: valueCol, tickfont: { color: '#E0F7FA' } },
            marker: { line: { color: '#00F0FF', width: 1 } }
          }],
          layout: {
            ...baseLayout,
            title: 'USA Choropleth Map',
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

      case 'scattergeo': {
        const locationCol = columns.find((col: string) => col.toLowerCase().includes('state')) || columns[0];
        const valueCol = columns[1];
        return {
          plotData: [{
            type: 'scattergeo',
            locationmode: 'USA-states',
            locations: getColumn(locationCol),
            text: getColumn(valueCol).map((v: any, i: number) => `${getColumn(locationCol)[i]}: ${v}`),
            marker: { size: getColumn(valueCol), color: '#00F0FF', line: { color: '#fff', width: 1 } }
          }],
          layout: {
            ...baseLayout,
            title: 'Scatter Geo Map',
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
        return {
          plotData: [{
            type: 'table',
            header: {
              values: columns,
              align: 'center',
              line: { width: 1, color: '#00F0FF' },
              fill: { color: 'rgba(0, 240, 255, 0.2)' },
              font: { family: 'Rajdhani', size: 14, color: '#E0F7FA' }
            },
            cells: {
              values: columns.map((col: string) => getColumn(col)),
              align: 'center',
              line: { color: 'rgba(0, 240, 255, 0.1)', width: 1 },
              fill: { color: ['rgba(2, 4, 8, 0.5)', 'rgba(0, 240, 255, 0.05)'] },
              font: { family: 'Rajdhani', size: 12, color: '#E0F7FA' }
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
        <div className="flex flex-wrap gap-2 p-3 bg-[#020408]/60 border border-[#00F0FF]/20 rounded backdrop-blur-sm">
          <span className="text-[#00F0FF]/70 text-sm font-rajdhani mr-2 self-center">
            Visualization:
          </span>
          {compatibleChartTypes.map((chartType) => (
            <button
              key={chartType}
              onClick={() => setSelectedChartType(chartType)}
              className={`
                px-3 py-1 rounded text-xs font-rajdhani uppercase tracking-wider
                transition-all duration-200
                ${selectedChartType === chartType
                  ? 'bg-[#00F0FF] text-[#020408] shadow-[0_0_10px_rgba(0,240,255,0.5)]'
                  : 'bg-[#020408]/80 text-[#00F0FF]/70 border border-[#00F0FF]/30 hover:border-[#00F0FF] hover:text-[#00F0FF] hover:shadow-[0_0_5px_rgba(0,240,255,0.3)]'
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
        data={plotData}
        layout={{
          ...layout,
          autosize: true,
          height: 400,
          modebar: {
            bgcolor: 'rgba(0, 240, 255, 0.1)',
            color: '#00F0FF',
            activecolor: '#FF0055'
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
