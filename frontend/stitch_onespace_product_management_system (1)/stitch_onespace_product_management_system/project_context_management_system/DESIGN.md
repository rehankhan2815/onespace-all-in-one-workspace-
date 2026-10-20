---
name: Project Context Management System
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0edec'
  surface-container-high: '#ebe7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1c1b1b'
  on-surface-variant: '#464555'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#7e3000'
  on-tertiary: '#ffffff'
  tertiary-container: '#a44100'
  on-tertiary-container: '#ffd2be'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2f00'
  background: '#fcf9f8'
  on-background: '#1c1b1b'
  surface-variant: '#e5e2e1'
typography:
  display-lg:
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
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
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
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base-unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin: 24px
---

## Brand & Style

The design system is engineered for deep focus and cognitive clarity, specifically tailored for students managing complex academic projects. The aesthetic sits at the intersection of **Minimalism** and **Corporate Modern**, prioritizing information density without sacrificing breathing room.

The visual language is characterized by:
- **Pragmatic Precision:** Every element has a functional purpose, utilizing a structural grid to anchor content.
- **Calm Productivity:** A neutral foundation with purposeful hits of indigo to guide the user's eye to primary actions.
- **Interface Transparency:** Using subtle depth and borders rather than heavy decoration to define the workspace.

## Colors

The palette is anchored by a high-contrast neutral scale to ensure legibility across long study sessions. 

- **Primary Indigo:** Reserved for high-intent actions (Create, Submit) and active navigational states.
- **Surface Strategy:** In Light Mode, use white surfaces against an off-white background to create subtle elevation. In Dark Mode, use tiered greys to prevent "pure black" eye strain.
- **Semantic Accents:** Status colors (Red, Yellow, Green) should be used sparingly in badges or small indicators to denote project priority and health.

## Typography

This design system utilizes **Inter** exclusively to maintain a systematic, utilitarian feel. 

- **Scale:** A tight scale ensures that even data-heavy project dashboards remain readable.
- **Hierarchy:** Use `label-caps` in a muted secondary color for sidebar category headers and metadata labels to distinguish them from interactive body text.
- **Weight:** Reserve bold weights for page titles and card headers to establish clear entry points for the eye.

## Layout & Spacing

The system follows a **12-column fluid grid** based on standard Bootstrap conventions. 

- **Sidebar:** A persistent 240px-280px sidebar on desktop, collapsing to a bottom-bar or hamburger menu on mobile.
- **Main Content:** Padded with `lg` (24px) margins to provide separation from the navigation.
- **Gutter Logic:** A consistent 24px gutter between card-based panels ensures a clean, breathable vertical and horizontal rhythm.
- **Alignment:** All components should align to a 4px baseline grid to maintain visual rigor.

## Elevation & Depth

Depth is used sparingly to signify interactivity and layering. 

- **Base Layer:** The application background (`bg-base`) is the lowest point.
- **Surface Layer:** Cards and panels use `bg-surface`. In light mode, these are defined by a 1px border or an extremely soft ambient shadow (0px 4px 12px rgba(0,0,0,0.05)).
- **Active State:** Modals and dropdowns sit on the highest tier, utilizing a more pronounced shadow (0px 10px 30px rgba(0,0,0,0.15)) to isolate them from the workspace.
- **Dark Mode Adjustment:** In dark mode, shadows are less visible; use subtle border-color increases to define depth instead of heavy shadows.

## Shapes

The shape language is "Rounded" to soften the professional tone and make the tool feel more accessible to students. 

- **Default:** 8px (`rounded-md`) for standard buttons, input fields, and small cards.
- **Large:** 12-16px (`rounded-lg/xl`) for main content containers and dashboard widgets.
- **Interactive Elements:** Buttons and inputs should share the same corner radius to create a unified form language.

## Components

### Buttons
Primary buttons use the indigo fill with white text. Secondary buttons use a ghost style (border only) or a subtle grey fill. Height should be standardized at 36px for compact views and 44px for primary actions.

### Cards & Panels
The foundational unit of the workspace. Cards must have a 1px border (`border` token). Headers within cards should use `headline-sm` with a bottom border to separate the title from the content area.

### Chips & Badges
- **Status Chips:** Low-contrast background fills (e.g., light green background with dark green text) for "Todo," "In Progress," and "Done."
- **Priority Pills:** Small, 20px height capsules with high-contrast indicator dots for High, Medium, and Low.

### Input Fields
Inputs feature a 1px border that shifts to the primary indigo color on focus. Use `body-md` for input text and `label-sm` for field labels placed above the input.

### Sidebar Navigation
Use a subtle hover state (background-color shift) for nav items. The active state should be marked by a primary indigo vertical bar on the left edge of the item and a change in text weight.