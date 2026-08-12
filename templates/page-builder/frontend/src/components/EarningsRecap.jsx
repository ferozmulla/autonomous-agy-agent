import React from 'react';

/**
 * EarningsRecap — Right panel (6 columns).
 *
 * Displays EPS (actual vs. estimate), Revenue (actual vs. estimate),
 * and Gross Margin (progress bar with target).
 *
 * @param {Object} props
 * @param {string} props.quarter - Quarter label (e.g., "Q3").
 * @param {string} props.eps - EPS actual (e.g., "$1.24").
 * @param {string} props.epsEstimate - EPS estimate (e.g., "$1.18").
 * @param {string} props.revenue - Revenue actual (e.g., "$89.5B").
 * @param {string} props.revenueEstimate - Revenue estimate (e.g., "$88.2B").
 * @param {string} props.grossMargin - Gross margin percentage (e.g., "44.3%").
 * @param {string} props.grossMarginTarget - Target percentage (e.g., "44.0%").
 */
export default function EarningsRecap({
  quarter,
  eps,
  epsEstimate,
  revenue,
  revenueEstimate,
  grossMargin,
  grossMarginTarget,
}) {
  // Extract numeric margin for the progress bar width
  const marginNum = parseFloat(grossMargin) || 0;
  const barWidth = `${Math.min(marginNum, 100)}%`;

  // Strip trailing "est" / "estimate" from estimate props to avoid "est est"
  const cleanEstimate = (val) => (val || '').replace(/\s*est(imate)?\s*$/i, '').trim();
  const cleanEps = cleanEstimate(epsEstimate);
  const cleanRev = cleanEstimate(revenueEstimate);

  return (
    <div className="panel earnings-panel">
      {/* Decorative circle */}
      <div className="earnings-decorative-circle" />

      {/* Section header */}
      <div className="section-header">
        <span className="material-symbols-outlined section-header-icon">analytics</span>
        <h3 className="section-header-title">{new Date().getFullYear()} {quarter} Earnings Recap</h3>
      </div>

      {/* Earnings data */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-stack-lg)', flexGrow: 1 }}>
        {/* EPS */}
        <div className="earnings-group">
          <p className="earnings-label">Earnings Per Share (EPS)</p>
          <div className="earnings-row">
            <span className="earnings-value">{eps}</span>
            <span className="earnings-estimate">vs {cleanEps} est</span>
          </div>
        </div>

        {/* Revenue */}
        <div className="earnings-group">
          <p className="earnings-label">Revenue</p>
          <div className="earnings-row">
            <span className="earnings-value">{revenue}</span>
            <span className="earnings-estimate">vs {cleanRev} est</span>
          </div>
        </div>

        {/* Gross Margin */}
        <div className="earnings-group" style={{ marginTop: 'auto', paddingTop: 'var(--space-stack-md)' }}>
          <p className="earnings-label">Gross Margin</p>
          <div className="margin-bar-track">
            <div className="margin-bar-fill" style={{ width: barWidth }} />
          </div>
          <div className="margin-labels">
            <span className="margin-value">{grossMargin}</span>
            <span className="margin-target">Target: {grossMarginTarget}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
