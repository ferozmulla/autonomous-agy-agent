import React from 'react';
import Header from './components/Header';
import TickerChart from './components/TickerChart';
import EarningsRecap from './components/EarningsRecap';
import GrowthDrivers from './components/GrowthDrivers';
import MarketChallenges from './components/MarketChallenges';
import ConversationalAnalytics from './components/ConversationalAnalytics';

/**
 * App — Main application shell.
 *
 * Contains the 12-column grid layout matching the code.html reference.
 * Props use placeholder values (e.g., "{{TICKER}}") that the Page Builder
 * agent replaces with real data from web search.
 */
export default function App() {
  /* ---------------------------------------------------------------
   * Company-specific data.
   * The Page Builder agent replaces these placeholder values with
   * real data obtained via web search.
   * --------------------------------------------------------------- */
  const companyData = {
    ticker: '{{TICKER}}',
    companyName: '{{COMPANY_NAME}}',
    industry: '{{INDUSTRY}}',
    price: '{{PRICE}}',
    trendPercent: '{{TREND_PERCENT}}',
    trendDirection: '{{TREND_DIRECTION}}', // 'up' or 'down'
    chartPath: '{{CHART_PATH}}',
    quarter: '{{QUARTER}}',
    eps: '{{EPS}}',
    epsEstimate: '{{EPS_ESTIMATE}}',
    revenue: '{{REVENUE}}',
    revenueEstimate: '{{REVENUE_ESTIMATE}}',
    grossMargin: '{{GROSS_MARGIN}}',
    grossMarginTarget: '{{GROSS_MARGIN_TARGET}}',
    growthDrivers: [
      { title: '{{GROWTH_1_TITLE}}', description: '{{GROWTH_1_DESC}}' },
      { title: '{{GROWTH_2_TITLE}}', description: '{{GROWTH_2_DESC}}' },
      { title: '{{GROWTH_3_TITLE}}', description: '{{GROWTH_3_DESC}}' },
    ],
    marketChallenges: [
      { title: '{{CHALLENGE_1_TITLE}}', description: '{{CHALLENGE_1_DESC}}' },
      { title: '{{CHALLENGE_2_TITLE}}', description: '{{CHALLENGE_2_DESC}}' },
      { title: '{{CHALLENGE_3_TITLE}}', description: '{{CHALLENGE_3_DESC}}' },
    ],
    suggestedPrompts: [
      '{{SUGGESTED_PROMPT_1}}',
      '{{SUGGESTED_PROMPT_2}}',
      '{{SUGGESTED_PROMPT_3}}',
    ],
    backendUrl: '{{CA_BACKEND_URL}}',
  };

  return (
    <>
      <Header companyName={companyData.companyName} />
      <main className="main-content">
        <div className="main-content-inner">
          {/* Row 1: Ticker Chart + Earnings Recap (6+6) */}
          <div className="dashboard-grid">
            <div className="col-6">
              <TickerChart
                ticker={companyData.ticker}
                companyName={companyData.companyName}
                industry={companyData.industry}
                price={companyData.price}
                trendPercent={companyData.trendPercent}
                trendDirection={companyData.trendDirection}
                chartPath={companyData.chartPath}
              />
            </div>
            <div className="col-6">
              <EarningsRecap
                quarter={companyData.quarter}
                eps={companyData.eps}
                epsEstimate={companyData.epsEstimate}
                revenue={companyData.revenue}
                revenueEstimate={companyData.revenueEstimate}
                grossMargin={companyData.grossMargin}
                grossMarginTarget={companyData.grossMarginTarget}
              />
            </div>
          </div>

          {/* Row 2: Growth Drivers + Market Challenges (6+6) */}
          <div className="dashboard-grid">
            <div className="col-6">
              <GrowthDrivers drivers={companyData.growthDrivers} />
            </div>
            <div className="col-6">
              <MarketChallenges challenges={companyData.marketChallenges} />
            </div>
          </div>

          {/* Row 3: Conversational Analytics (12 cols) */}
          <div id="conversational-analytics" className="dashboard-grid">
            <div className="col-12">
              <ConversationalAnalytics
                backendUrl={companyData.backendUrl}
                suggestedPrompts={companyData.suggestedPrompts}
                companyName={companyData.companyName}
              />
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
