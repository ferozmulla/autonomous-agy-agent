import React from 'react';

/**
 * Header — Fixed top navigation bar.
 *
 * Displays "<COMPANY_NAME> PULSE" branding, "DASHBOARD" nav link, and user avatar.
 *
 * @param {Object} props
 * @param {string} props.companyName - Company name to display (e.g., "DRAFTKINGS INC.").
 */
export default function Header({ companyName }) {
  // Extract just the core company name (drop "Inc.", "Corp.", etc.)
  const brandName = (companyName || 'COMPANY')
    .replace(/\s*(Inc\.?|Corp\.?|Ltd\.?|LLC|PLC|Co\.?|Group|Holdings?)\s*$/i, '')
    .trim()
    .toUpperCase();

  return (
    <header className="app-header">
      <div className="app-header-inner">
        {/* Left: Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-stack-lg)', minWidth: 'max-content' }}>
          <span className="app-header-brand">{brandName} PULSE</span>
        </div>

        {/* Center: Navigation */}
        <nav className="app-header-nav" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-stack-lg)', height: '100%' }}>
          <a href="#" aria-current="page">DASHBOARD</a>
          <a href="#conversational-analytics" style={{ cursor: 'pointer' }}
             onClick={(e) => {
               e.preventDefault();
               document.getElementById('conversational-analytics')?.scrollIntoView({ behavior: 'smooth' });
             }}
          >ASK PULSE</a>
        </nav>

        {/* Right: Avatar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-stack-md)' }}>
          <div className="app-header-avatar">
            <span className="material-symbols-outlined">person</span>
          </div>
        </div>
      </div>
    </header>
  );
}
