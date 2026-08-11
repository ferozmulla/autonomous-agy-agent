import React from 'react';

/**
 * MarketChallenges — Bottom-right panel (6 columns).
 *
 * Displays 3 market challenges with `-` indicators, titles, and descriptions.
 * Uses a peach-washed header.
 *
 * @param {Object} props
 * @param {Array<{title: string, description: string}>} props.challenges - Array of 3 challenges.
 */
export default function MarketChallenges({ challenges }) {
  return (
    <div className="panel challenges-panel">
      {/* Peach-washed header */}
      <div className="challenges-header">
        <h3 className="challenges-header-title">
          <span className="material-symbols-outlined">warning</span>
          Market Challenges
        </h3>
      </div>

      {/* Body with gradient background */}
      <div className="challenges-body">
        <ul className="challenges-list">
          {challenges.map((challenge, index) => (
            <li key={index} className="challenge-item">
              <span className="challenge-indicator">-</span>
              <div>
                <h4 className="challenge-item-title">{challenge.title}</h4>
                <p className="challenge-item-desc">{challenge.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
