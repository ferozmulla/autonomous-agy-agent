import React from 'react';

/**
 * Header — Fixed top navigation bar.
 *
 * Displays "PASTEL TERMINAL" branding, "DASHBOARD" nav link, and user avatar.
 * Matches the fixed header from code.html. Static — no props needed.
 */
export default function Header() {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        {/* Left: Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-stack-lg)', minWidth: 'max-content' }}>
          <span className="app-header-brand">PASTEL TERMINAL</span>
        </div>

        {/* Center: Navigation */}
        <nav className="app-header-nav" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-stack-lg)', height: '100%' }}>
          <a href="#" aria-current="page">DASHBOARD</a>
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
