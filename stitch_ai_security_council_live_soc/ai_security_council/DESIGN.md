---
name: AI Security Council
colors:
  surface: '#12131c'
  surface-dim: '#12131c'
  surface-bright: '#383843'
  surface-container-lowest: '#0d0e17'
  surface-container-low: '#1a1b24'
  surface-container: '#1e1f29'
  surface-container-high: '#282933'
  surface-container-highest: '#33343e'
  on-surface: '#e3e1ef'
  on-surface-variant: '#bbc9cf'
  inverse-surface: '#e3e1ef'
  inverse-on-surface: '#2f303a'
  outline: '#859399'
  outline-variant: '#3c494e'
  surface-tint: '#4cd6ff'
  primary: '#a4e6ff'
  on-primary: '#003543'
  primary-container: '#00d1ff'
  on-primary-container: '#00566a'
  inverse-primary: '#00677f'
  secondary: '#d0bcff'
  on-secondary: '#3c0091'
  secondary-container: '#571bc1'
  on-secondary-container: '#c4abff'
  tertiary: '#96e9ff'
  on-tertiary: '#003640'
  tertiary-container: '#43d1f0'
  on-tertiary-container: '#005766'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#b7eaff'
  primary-fixed-dim: '#4cd6ff'
  on-primary-fixed: '#001f28'
  on-primary-fixed-variant: '#004e60'
  secondary-fixed: '#e9ddff'
  secondary-fixed-dim: '#d0bcff'
  on-secondary-fixed: '#23005c'
  on-secondary-fixed-variant: '#5516be'
  tertiary-fixed: '#acedff'
  tertiary-fixed-dim: '#4cd7f6'
  on-tertiary-fixed: '#001f26'
  on-tertiary-fixed-variant: '#004e5c'
  background: '#12131c'
  on-background: '#e3e1ef'
  surface-variant: '#33343e'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.5'
    letterSpacing: 0.02em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.4'
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.1em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-page: 32px
  panel-padding: 20px
  stack-sm: 8px
  stack-md: 16px
---

## Brand & Style
The design system embodies a high-fidelity, cyber-futuristic aesthetic tailored for mission-critical security operations. It evokes a sense of absolute control, technical precision, and proactive defense. The personality is "Sentinel Intelligence"—quietly observant but capable of explosive responsiveness.

The style leverages **Glassmorphism** and **Cyber-Futurism**. Interfaces are built using semi-transparent layers that suggest depth and digital complexity. Surfaces utilize backdrop blurs to maintain legibility against dynamic, deep-space backgrounds, while neon accents provide functional cues for system health and threat levels.

## Colors
The palette is rooted in a deep-space foundation to reduce eye strain during long shifts in a SOC environment. 

- **Foundation:** The core background is a rich, near-black navy.
- **Accents:** Neon blue and cyan are used for navigational elements and primary actions. Violet is reserved for AI-driven insights and sophisticated data patterns.
- **Functional:** Status colors use high-saturation pigments to ensure "Critical" alerts immediately capture the user's attention against the dark backdrop.
- **Surfaces:** Glass components use a semi-transparent base with a subtle white or primary-tinted inner glow (1px border) to define boundaries.

## Typography
The typography strategy creates a clear distinction between "Interface" and "Intelligence."

- **Inter** is the primary workhorse for navigation, headers, and descriptive text, providing high legibility at all scales.
- **JetBrains Mono** is utilized for all technical data, logs, IP addresses, and system metrics. Its monospaced nature ensures that columns of numbers align perfectly, aiding in rapid pattern recognition.
- **Scale:** Headlines on mobile should scale down by roughly 20% (e.g., `headline-lg` becomes 26px) to maintain visual hierarchy without overwhelming the viewport.

## Layout & Spacing
The layout uses a **Fluid Grid** model with high-density information architecture.

- **Grid:** A 12-column system is used for desktop. Components should snap to 4px increments (the base unit).
- **Responsive:** 
    - **Desktop:** 12 columns, 24px gutters.
    - **Tablet:** 6 columns, 16px gutters.
    - **Mobile:** 2 columns, 12px gutters.
- **Containers:** Panels are the primary containment unit. They should grow to fill space but maintain consistent internal padding (20px) to prevent data from feeling cramped despite the high information density.

## Elevation & Depth
Depth is expressed through **Glassmorphism** and luminosity rather than traditional shadows.

- **Base Layer:** The deepest background level (#0a0b14).
- **Surface Layer:** Semi-transparent panels (`surface_glass`) with a `backdrop-filter: blur(12px)`. 
- **Borders:** Instead of drop shadows, use 1px solid borders with 10-20% opacity of the primary or secondary color to define "lift."
- **Active States:** Elements in a "Critical" or "Active" state utilize an outer glow (`box-shadow: 0 0 15px rgba(0, 209, 255, 0.3)`) to simulate light emission.

## Shapes
The shape language is "Soft-Tech." While the aesthetic is futuristic, avoid aggressive sharp corners which can feel hostile. 

- **Standard Elements:** Buttons and input fields use a 4px radius (`roundedness: 1`).
- **Panels:** Larger dashboard modules use 8px (`rounded-lg`) to create a distinct container feel.
- **Status Pills:** Use fully rounded (`rounded-xl`) shapes for status indicators to contrast against the more rectangular data panels.

## Components
- **Buttons:** Primary buttons feature a subtle gradient from Cyan to Blue with a glow effect on hover. Ghost buttons use the 1px border rule.
- **Input Fields:** Dark backgrounds (0% opacity) with a 1px border that illuminates (Neon Blue) when focused. Use JetBrains Mono for input text.
- **Cards/Panels:** The core of the dashboard. Must include a `backdrop-blur`. Headers within panels should have a subtle bottom border separator.
- **Status Indicators:** Small circular "pips" that pulse for active threats. Success (Green), Warning (Yellow), and Critical (Red) must be high-contrast.
- **Data Tables:** Row-based with alternating subtle highlights. No vertical borders; use horizontal spacing and monospaced alignment.
- **Terminal/Log Viewers:** Dedicated black-out containers using `code-sm` typography with syntax highlighting for various log types (JSON, Syslog).