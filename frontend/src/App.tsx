// ─────────────────────────────────────────────────────────────────────────────
//  AIU Frontend — Main App Entry
//  React 18 + React Router v6 + React Query + Zustand
// ─────────────────────────────────────────────────────────────────────────────

import React, { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { useAuthStore } from "./store/authStore";
import AppLayout from "./components/layout/AppLayout";
import AuthLayout from "./components/layout/AuthLayout";
import LoadingSpinner from "./components/ui/LoadingSpinner";

// Lazy-load pages for code splitting
const LoginPage           = lazy(() => import("./pages/auth/LoginPage"));
const RegisterPage        = lazy(() => import("./pages/auth/RegisterPage"));
const DashboardPage       = lazy(() => import("./pages/DashboardPage"));
const ChatPage            = lazy(() => import("./pages/ChatPage"));
const GoalsPage           = lazy(() => import("./pages/GoalsPage"));
const InsightsPage        = lazy(() => import("./pages/InsightsPage"));
const RecommendationsPage = lazy(() => import("./pages/RecommendationsPage"));
const ProfilePage         = lazy(() => import("./pages/ProfilePage"));

// Configure React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,    // 5 minutes
      gcTime: 1000 * 60 * 30,      // 30 minutes
      retry: (failureCount, error: any) => {
        if (error?.response?.status === 401) return false;
        if (error?.response?.status === 403) return false;
        return failureCount < 2;
      },
      refetchOnWindowFocus: false,
    },
  },
});

// Route guard
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<LoadingSpinner fullScreen />}>
          <Routes>
            {/* Public routes */}
            <Route element={<AuthLayout />}>
              <Route
                path="/login"
                element={<PublicRoute><LoginPage /></PublicRoute>}
              />
              <Route
                path="/register"
                element={<PublicRoute><RegisterPage /></PublicRoute>}
              />
            </Route>

            {/* Protected app routes */}
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/chat/:conversationId" element={<ChatPage />} />
              <Route path="/goals" element={<GoalsPage />} />
              <Route path="/insights" element={<InsightsPage />} />
              <Route path="/recommendations" element={<RecommendationsPage />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: "var(--color-bg)",
            color: "var(--color-text)",
            border: "1px solid var(--color-border)",
            borderRadius: "10px",
            fontSize: "14px",
          },
        }}
      />
    </QueryClientProvider>
  );
}
