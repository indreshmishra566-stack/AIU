// ─────────────────────────────────────────────────────────────────────────────
//  AIU — ThemeToggle Component
// ─────────────────────────────────────────────────────────────────────────────

import React from "react";
import { Sun, Moon, Monitor } from "lucide-react";
import { useDarkMode } from "../../hooks/useDarkMode";
import clsx from "clsx";

export function ThemeToggle() {
  const { theme, setTheme } = useDarkMode();

  const options = [
    { value: "light",  icon: Sun,     label: "Light" },
    { value: "dark",   icon: Moon,    label: "Dark"  },
    { value: "system", icon: Monitor, label: "Auto"  },
  ] as const;

  return (
    <div className="flex items-center gap-1 p-1 rounded-xl bg-gray-100 dark:bg-gray-800">
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          title={label}
          className={clsx(
            "flex items-center justify-center w-7 h-7 rounded-lg transition-all",
            theme === value
              ? "bg-white dark:bg-gray-700 text-violet-600 dark:text-violet-400 shadow-sm"
              : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          )}
        >
          <Icon size={13} />
        </button>
      ))}
    </div>
  );
}
