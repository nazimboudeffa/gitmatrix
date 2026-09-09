# GitMatrix — Brand Spec (Design Proposal)

## Direction: tech-utility (dark adaptation)

## OKLCh Tokens

- `--bg`:      oklch(16% 0.012 250)   — deep navy-charcoal (#1e2127)
- `--surface`: oklch(18% 0.010 250)   — panel background (#22252b)
- `--fg`:      oklch(85% 0.012 250)   — primary text (#d7dae0)
- `--muted`:   oklch(58% 0.018 250)   — secondary text (#9da5b4)
- `--border`:  oklch(26% 0.010 250)   — hairlines (#3a3f46)
- `--accent`:  oklch(72% 0.145 85)    — gold accent (#e5c07b)

## Font Stacks

- Display: `-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', system-ui, sans-serif`
- Body:    `-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', system-ui, sans-serif`
- Mono:    `'Cascadia Mono', 'JetBrains Mono', 'SF Mono', Menlo, monospace`

## Observed Rules

1. Single accent color (gold) used sparingly — active branch indicator, selected commit ring, primary CTA.
2. Graph colors are a separate 10-color palette for branch differentiation, not derived from the accent.
3. Status pills use semantic colors: green (staged), red (unstaged), orange (untracked), blue (hunk).
4. Dark chrome (toolbar, status bar) is slightly lighter than the main background.
5. Monospace is reserved for diff content, commit SHAs, and technical labels.
