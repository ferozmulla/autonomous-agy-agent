import React from 'react';

/**
 * TickerChart — Left panel (6 columns).
 *
 * Displays company ticker, full name, industry, stock price, trend percentage
 * (with mint/peach pill), and an SVG line chart.
 *
 * @param {Object} props
 * @param {string} props.ticker - Stock ticker symbol (e.g., "AAPL").
 * @param {string} props.companyName - Full company name (e.g., "Apple Inc.").
 * @param {string} props.industry - Industry label (e.g., "Consumer Electronics").
 * @param {string} props.price - Current stock price (e.g., "$184.22").
 * @param {string} props.trendPercent - Trend percentage (e.g., "+4.2%").
 * @param {string} props.trendDirection - "up" or "down".
 * @param {string} props.chartPath - SVG path data for the line chart.
 */
export default function TickerChart({
  ticker,
  companyName,
  industry,
  price,
  trendPercent,
  trendDirection,
  chartPath,
}) {
  const isPositive = trendDirection === 'up';
  const pillClass = isPositive ? 'trend-pill--positive' : 'trend-pill--negative';
  const arrowIcon = isPositive ? 'arrow_upward' : 'arrow_downward';

  // Default chart path if none provided
  const defaultPath = 'M0,180 L100,150 L200,160 L300,120 L400,140 L500,80 L600,100 L700,40 L800,20';
  const linePath = chartPath || defaultPath;
  const fillPath = `${linePath} L800,200 L0,200 Z`;

  return (
    <div className="panel ticker-panel">
      {/* Header: Ticker + Price */}
      <div className="ticker-header">
        <div>
          <h1 className="ticker-symbol">{ticker}</h1>
          <p className="ticker-subtitle">
            {companyName} - {industry}
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <h2 className="ticker-price">{price}</h2>
          <div className={`trend-pill ${pillClass}`}>
            <span className="material-symbols-outlined">{arrowIcon}</span>
            <span>{trendPercent}</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="chart-container">
        <svg preserveAspectRatio="none" viewBox="0 0 800 200">
          <path className="chart-line" d={linePath} />
          <path className="chart-fill" d={fillPath} />
        </svg>
        <div className="chart-gridlines">
          <div className="chart-gridline" />
          <div className="chart-gridline" />
          <div className="chart-gridline" />
          <div className="chart-gridline" />
        </div>
      </div>

      {/* Date labels */}
      <div className="chart-dates">
        <span className="chart-date">10/01</span>
        <span className="chart-date">10/08</span>
        <span className="chart-date">10/15</span>
        <span className="chart-date">10/22</span>
        <span className="chart-date">10/31</span>
      </div>
    </div>
  );
}
