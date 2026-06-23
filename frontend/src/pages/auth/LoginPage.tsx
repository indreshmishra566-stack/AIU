import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import toast from "react-hot-toast";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err: any) {
      toast.error(err?.message || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">Welcome back</h2>
      <p className="text-sm text-gray-500 mb-6">Your AI has been waiting</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com" required
            className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 text-gray-900 dark:text-gray-100" />
        </div>
        <div>
          <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder="••••••••••••" required
            className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 text-gray-900 dark:text-gray-100" />
        </div>
        <button type="submit" disabled={loading}
          className="w-full py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-medium text-sm transition-colors disabled:opacity-50">
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="text-center text-sm text-gray-500 mt-4">
        No account? <Link to="/register" className="text-violet-600 hover:underline">Create one</Link>
      </p>
    </div>
  );
}
