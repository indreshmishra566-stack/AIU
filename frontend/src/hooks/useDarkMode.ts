// ─────────────────────────────────────────────────────────────────────────────
//  AIU — useDarkMode hook
//  Manages dark/light theme with system preference detection and localStorage.
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useEffect, useCallback } from "react";

type Theme = "light" | "dark" | "system";

function getSystemPreference(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function getStoredTheme(): Theme {
  return (localStorage.getItem("aiu-theme") as Theme) ?? "system";
}

function applyTheme(theme: Theme) {
  const resolved = theme === "system" ? getSystemPreference() : theme;
  document.documentElement.classList.toggle("dark", resolved === "dark");
}

export function useDarkMode() {
  const [theme, setThemeState] = useState<Theme>(getStoredTheme);

  // Apply on mount
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  // Listen for system preference changes
  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => applyTheme("system");
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    localStorage.setItem("aiu-theme", next);
    setThemeState(next);
    applyTheme(next);
  }, []);

  const toggle = useCallback(() => {
    const current = theme === "system" ? getSystemPreference() : theme;
    setTheme(current === "dark" ? "light" : "dark");
  }, [theme, setTheme]);

  const isDark =
    theme === "dark" || (theme === "system" && getSystemPreference() === "dark");

  return { theme, isDark, setTheme, toggle };
}
