import React from 'react';

/**
 * GrowthDrivers — Bottom-left panel (6 columns).
 *
 * Displays 3 growth drivers with `+` indicators, titles, and descriptions.
 * Uses a mint-washed header.
 *
 * @param {Object} props
 * @param {Array<{title: string, description: string}>} props.drivers - Array of 3 growth drivers.
 */
export default function GrowthDrivers({ drivers }) {
  return (
    <div className="panel growth-panel">
      {/* Mint-washed header */}
      <div className="growth-header">
        <h3 className="growth-header-title">
          <span className="material-symbols-outlined">trending_up</span>
          Growth Drivers
        </h3>
      </div>

      {/* Body with gradient background */}
      <div className="growth-body">
        <ul className="growth-list">
          {drivers.map((driver, index) => (
            <li key={index} className="growth-item">
              <span className="growth-indicator">+</span>
              <div>
                <h4 className="growth-item-title">{driver.title}</h4>
                <p className="growth-item-desc">{driver.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
