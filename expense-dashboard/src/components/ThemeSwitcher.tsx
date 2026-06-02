import { themes, type ThemeName } from '../lib/useTheme';

interface ThemeSwitcherProps {
  value: ThemeName;
  onChange: (theme: ThemeName) => void;
}

export function ThemeSwitcher({ value, onChange }: ThemeSwitcherProps) {
  return (
    <div
      role="group"
      aria-label="Theme switcher"
      style={{ display: 'inline-flex', borderRadius: 999, border: '1px solid var(--rule)', overflow: 'hidden' }}
    >
      {themes.map((theme) => (
        <button
          key={theme}
          type="button"
          onClick={() => onChange(theme)}
          style={{
            border: 'none',
            textTransform: 'capitalize',
            padding: '7px 10px',
            cursor: 'pointer',
            fontSize: 12,
            background: value === theme ? 'var(--accent)' : 'transparent',
            color: value === theme ? 'var(--bg)' : 'var(--ink-2)',
          }}
        >
          {theme}
        </button>
      ))}
    </div>
  );
}
