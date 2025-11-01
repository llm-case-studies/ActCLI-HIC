# ActCLI Theme Reference

This document mirrors the shared ActCLI palettes defined in the Round Table project so HIC can stay visually aligned with the broader ecosystem.

Source reference: `../ActCLI-Round-Table/docs/actcli-theme-reference.md`

## Base Palettes

| Theme | Background | Header / Footer | Sidebar | Detail Panel | Brand / Title | Hint Text | Body Text |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Ledger (F1) | `#1E2A3A` | `#0D639C` | `#213245` | `#1B2736` | `#66C2FF` | `#9FB7C8` | `#E0E0E0` |
| Analyst (F2) | `#282C34` | `#00A6A6` | `#22303A` | `#1F242B` | `#00D1D1` | `#C0C8CF` | `#F8F8F2` |
| Seminar (F3) | `#3C3C3C` | `#6A829B` | `#323232` | `#2C2C2C` | `#D4AC87` | `#D0D0D0` | `#F3F3F3` |

## Accent Guidance

- Use Ledger or Analyst as the foundation for the SPA shell (navigation, page background, typography).
- Reserve Analyst for darker shells, Ledger when subtle blues help differentiate host status panes.
- Accent buttons, live-state badges, or alerts with `#F05A28` and hover highlights with `#FFD166`.
- Keep typography body copy in a neutral sans-serif (Inter, Source Sans) and pair with a display font only for hero/section titles.
- When exporting reports back to Markdown/PDF, fall back to the base palette to maintain cross-medium cohesion.

## Implementation Notes

- Surface these colors as CSS variables (or Tailwind tokens) so the SPA can theme components consistently.
- Record any new accents or gradients you introduce so they can be fed back into the central ActCLI reference.
- For dark-mode accessibility, ensure minimum 4.5:1 contrast against the background—Ledger text already meets this target.
