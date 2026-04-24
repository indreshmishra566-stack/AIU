import React from "react";
import { Outlet } from "react-router-dom";
import { Brain } from "lucide-react";

export default function AuthLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 to-gray-50 dark:from-gray-950 dark:to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-2xl bg-violet-600 flex items-center justify-center">
            <Brain size={20} className="text-white" />
          </div>
          <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">AIU</span>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8 shadow-sm">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
