// ─────────────────────────────────────────────────────────────────────────────
//  AIU — Layout Components
// ─────────────────────────────────────────────────────────────────────────────

// === AppLayout.tsx ============================================================
// File: src/components/layout/AppLayout.tsx

import React from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, MessageSquare, Target, Lightbulb,
  Sparkles, User, LogOut, Brain,
} from "lucide-react";
import { useAuthStore } from "../../store/authStore";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/dashboard",       icon: LayoutDashboard, label: "Dashboard" },
  { to: "/chat",            icon: MessageSquare,   label: "Chat" },
  { to: "/goals",           icon: Target,          label: "Goals" },
  { to: "/insights",        icon: Lightbulb,       label: "Insights" },
  { to: "/recommendations", icon: Sparkles,        label: "For You" },
  { to: "/profile",         icon: User,            label: "Profile" },
];

export default function AppLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950 overflow-hidden">

      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="hidden md:flex flex-col w-56 border-r border-gray-200
                        dark:border-gray-800 bg-white dark:bg-gray-900 shrink-0">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-4 py-5 border-b
                        border-gray-100 dark:border-gray-800">
          <div className="w-8 h-8 rounded-xl bg-violet-600 flex items-center justify-center">
            <Brain size={16} className="text-white" />
          </div>
          <span className="font-bold text-gray-900 dark:text-gray-100 text-lg tracking-tight">
            AIU
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
                  isActive
                    ? "bg-violet-50 dark:bg-violet-900/20 text-violet-700 dark:text-violet-300"
                    : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
                )
              }
            >
              <Icon size={17} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="p-3 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-3 px-2 py-2">
            <div className="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-900/40
                            flex items-center justify-center text-xs font-semibold
                            text-violet-700 dark:text-violet-300 shrink-0">
              {user?.first_name?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-900 dark:text-gray-100 truncate">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-[10px] text-gray-400 truncate">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="text-gray-400 hover:text-red-500 transition-colors p-1"
              title="Logout"
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────────────── */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>

      {/* ── Mobile bottom nav ────────────────────────────────────────────── */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900
                      border-t border-gray-200 dark:border-gray-800 flex z-50">
        {NAV_ITEMS.slice(0, 5).map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                "flex-1 flex flex-col items-center gap-1 py-3 text-[10px] font-medium transition-colors",
                isActive
                  ? "text-violet-600"
                  : "text-gray-400"
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
