---
name: Pastel Terminal
colors:
  surface: '#FFFFFF'
  surface-dim: '#dbdad6'
  surface-bright: '#faf9f5'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f4f0'
  surface-container: '#efeeea'
  surface-container-high: '#e9e8e4'
  surface-container-highest: '#e3e2df'
  on-surface: '#1b1c1a'
  on-surface-variant: '#49454e'
  inverse-surface: '#2f312e'
  inverse-on-surface: '#f2f1ed'
  outline: '#7a757f'
  outline-variant: '#cac4cf'
  surface-tint: '#645787'
  primary: '#645787'
  on-primary: '#ffffff'
  primary-container: '#d4c4fb'
  on-primary-container: '#5c4f7e'
  inverse-primary: '#cebef5'
  secondary: '#296956'
  on-secondary: '#ffffff'
  secondary-container: '#acedd5'
  on-secondary-container: '#2e6d5a'
  tertiary: '#745752'
  on-tertiary: '#ffffff'
  tertiary-container: '#eac4bd'
  on-tertiary-container: '#6c504b'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e9ddff'
  primary-fixed-dim: '#cebef5'
  on-primary-fixed: '#20133f'
  on-primary-fixed-variant: '#4c3f6d'
  secondary-fixed: '#aff0d8'
  secondary-fixed-dim: '#93d3bc'
  on-secondary-fixed: '#002118'
  on-secondary-fixed-variant: '#06513f'
  tertiary-fixed: '#ffdad4'
  tertiary-fixed-dim: '#e3beb7'
  on-tertiary-fixed: '#2b1612'
  on-tertiary-fixed-variant: '#5b403b'
  background: '#faf9f5'
  on-background: '#1b1c1a'
  surface-variant: '#e3e2df'
  text-primary: '#2D3142'
  text-muted: '#8C92AC'
  border-subtle: '#E2E5F1'
typography:
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.3'
  body-md:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  data-lg:
    fontFamily: IBM Plex Mono
    fontSize: 16px
    fontWeight: '500'
    lineHeight: '1.4'
  data-md:
    fontFamily: IBM Plex Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.4'
  caption:
    fontFamily: IBM Plex Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.2'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  grid-gutter: 16px
  panel-padding: 16px
  stack-xs: 4px
  stack-sm: 8px
  stack-md: 12px
  stack-lg: 24px
---

## Brand & Style
The brand personality is **Calmly Analytical**. It reimagines the high-density environment of a financial terminal through a "Soft Terminal" lens—professional, data-rich, and precise, yet approachable. The design style is a hybrid of **Minimalism** and **Modern Corporate**, utilizing a "grid-locked" philosophy that prioritizes information density and scannability. 

The aesthetic is characterized by sharp 1px borders, a complete absence of shadows, and the functional use of pastel washes to categorize data sentiment. It avoids the aggressive visual noise of traditional trading platforms in favor of a clean, "Notion-meets-Bloomberg" clarity.

## Colors
The palette utilizes a warm neutral base (`#FDFCF8`) to reduce eye strain during long research sessions. Color is used functionally rather than decoratively:
- **Primary (Lavender):** Denotes interactivity, active states, and focus.
- **Secondary (Mint):** Represents positive trends, growth, and upward movement.
- **Tertiary (Peach):** Represents negative trends, challenges, and warnings.
- **Surface:** Pure white is reserved for grid panels and cards to create a clear "layer" above the warm canvas.
- **Text:** Deep Slate is used for high-contrast readability, while Cool Gray handles metadata and secondary labels.

## Typography
The system employs a strict "Interface vs. Data" typographic split. 
- **Space Grotesk** is the "Interface" font, used for structural elements, headers, and prose to provide a modern, geometric feel.
- **IBM Plex Mono** is the "Data" font, reserved for all tabular data, stock tickers, financial metrics, and timestamps. This ensures numerical alignment and a technical, terminal-like precision.

All headings use tighter letter-spacing for a professional, compact appearance. Line heights are kept lean to support high information density.

## Layout & Spacing
The layout follows a **Fixed 12-Column Grid** system, drawing inspiration from high-density data dashboards. 
- **Desktop:** 12 columns with 16px gutters. Layouts are typically split into an 8-column main area (charts/ledger) and a 4-column sidebar (earnings/news).
- **Tablet:** 8 columns, reflowing sidebar content below the main span.
- **Mobile:** Single column with reduced margins (12px).

Internal spacing is governed by a strict 4px baseline. Panels and cards should use a consistent 16px internal padding to maintain the "grid-locked" aesthetic. Dividers are strictly 1px solid lines to separate list items without adding significant vertical bulk.

## Elevation & Depth
This design system uses a **Flat Layering** model. Depth is achieved exclusively through color fills and 1px borders; **no drop shadows are permitted**.

- **Level 0 (Canvas):** The warm background (`#FDFCF8`).
- **Level 1 (Panels):** White surface cards (`#FFFFFF`) with a 1px border (`#E2E5F1`).
- **Level 2 (Active/Overlays):** Interactive highlights use Lavender fills. Tooltips use a solid Lavender background to pop against the white panels.
- **State Indicators:** Positive/Negative states use Mint and Peach washes at 10-20% opacity to highlight specific grid cells or regions.

## Shapes
The shape language is **Technical and Sharp**. A minimal 2px radius is applied to all UI elements—panels, buttons, and status pills—giving them a "nearly sharp" appearance that feels precise and engineering-focused.

Interactive elements (buttons) and semantic pills (percentage changes) should never be fully rounded; they must maintain the 2px corner radius to stay consistent with the grid-locked aesthetic.

## Components
- **Buttons:** 2px radius, solid 1px border. Primary buttons use Lavender background; secondary buttons use a white background with a Slate text and border.
- **Data Tables (Ledger):** High density. Use alternating row colors (White and Warm Canvas). Borders should only be horizontal.
- **Status Pills:** Used for +/- changes. 2px radius. Positive uses Mint background; Negative uses Peach background. Text remains Deep Slate for readability.
- **Input Fields:** 1px border (`#E2E5F1`), 2px radius. On focus, the border changes to Lavender.
- **News Feed:** List items separated by 1px bottom borders. Hovering a headline triggers a Lavender underline transition.
- **Technical Indicators:** Use IBM Plex Mono characters (`+` and `-`) as custom bullets for bull/bear cases instead of graphical icons.
- **Charts:** Line charts use a 2px Mint stroke with a vertical crosshair appearing on hover. Hover tooltips are solid Lavender boxes.