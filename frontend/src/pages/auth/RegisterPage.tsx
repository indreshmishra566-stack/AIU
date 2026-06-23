import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import toast from "react-hot-toast";

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
  });

  const [loading, setLoading] = useState(false);
  const { register } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await register({
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
      });

      navigate("/dashboard");
      toast.success("Welcome to AIU!");
    } catch (err: any) {
      toast.error(err?.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  const field = (
    key: keyof typeof form,
    label: string,
    type = "text",
    placeholder = ""
  ) => (
    <div>
      <label className="text-sm text-gray-600 dark:text-gray-400 mb-1 block">
        {label}
      </label>

      <input
        type={type}
        value={form[key]}
        onChange={(e) =>
          setForm({ ...form, [key]: e.target.value })
        }
        placeholder={placeholder}
        required
        className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 text-gray-900 dark:text-gray-100"
      />
    </div>
  );

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">
        Create your AI
      </h2>

      <p className="text-sm text-gray-500 mb-6">
        Build an AI version of you
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {field("first_name", "First name", "text", "Alex")}
          {field("last_name", "Last name", "text", "Smith")}
        </div>

        {field("email", "Email", "email", "alex@example.com")}
        {field("password", "Password (12+ chars)", "password", "••••••••••••")}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-medium text-sm transition-colors disabled:opacity-50"
        >
          {loading ? "Creating…" : "Create account"}
        </button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-4">
        Already have one?{" "}
        <Link
          to="/login"
          className="text-violet-600 hover:underline"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}