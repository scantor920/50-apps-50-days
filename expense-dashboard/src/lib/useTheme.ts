import { useEffect, useMemo, useState } from 'react';

export type ThemeName = 'light' | 'dark' | 'masters' | 'imperial' | 'terminal';

const THEME_KEY = 'expense-dashboard-theme';

export const themes: ThemeName[] = ['light', 'dark', 'masters', 'imperial', 'terminal'];

function isTheme(value: string): value is ThemeName {
  return themes.includes(value as ThemeName);
}

function getInitialTheme(): ThemeName {
  const value = localStorage.getItem(THEME_KEY);
  if (value && isTheme(value)) {
    return value;
  }
  return 'light';
}

export function useTheme() {
  const [theme, setTheme] = useState<ThemeName>(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  return useMemo(
    () => ({
      theme,
      setTheme,
      themes,
    }),
    [theme],
  );
}
