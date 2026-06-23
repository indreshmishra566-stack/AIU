import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../store/authStore";
import { api } from "../services/apiClient";
import toast from "react-hot-toast";
import { User, Save } from "lucide-react";

const COACH_MODES = [
  { value: "friendly",   label: "Friendly",   desc: "Warm & supportive" },
  { value: "mentor",     label: "Mentor",     desc: "Wise & Socratic" },
  { value: "strict",     label: "Strict",     desc: "Accountability-focused" },
  { value: "analytical", label: "Analytical", desc: "Data-driven" },
];

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore();
  const [form, setForm] = useState({
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
    coach_mode: user?.profile?.coach_mode || "friendly",
    timezone: user?.profile?.timezone || "UTC",
  });

  const mutation = useMutation({
    mutationFn: (data: typeof form) => api.updateMe(data),
    onSuccess: (res) => { updateUser(res.data.data); toast.success("Profile saved!"); },
    onError: () => toast.error("Failed to save."),
  });

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-2xl bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-violet-600 font-bold text-lg">
          {user?.first_name?.[0]?.toUpperCase() || "U"}
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">{user?.first_name} {user?.last_name}</h1>
          <p className="text-sm text-gray-500">{user?.email}</p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 space-y-5">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100">Personal info</h2>
        <div className="grid grid-cols-2 gap-4">
          {["first_name","last_name"].map(f => (
            <div key={f}>
              <label className="text-sm text-gray-500 mb-1 block capitalize">{f.replace("_"," ")}</label>
              <input value={(form as any)[f]} onChange={e => setForm({...form,[f]:e.target.value})}
                className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-violet-500" />
            </div>
          ))}
        </div>

        <div>
          <label className="text-sm text-gray-500 mb-1 block">Timezone</label>
          <input value={form.timezone} onChange={e => setForm({...form,timezone:e.target.value})}
            className="w-full px-3 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-violet-500" />
        </div>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 space-y-4">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100">AI coach mode</h2>
        <div className="grid grid-cols-2 gap-3">
          {COACH_MODES.map(m => (
            <button key={m.value} onClick={() => setForm({...form,coach_mode:m.value})}
              className={`text-left p-4 rounded-xl border-2 transition-all ${form.coach_mode === m.value ? "border-violet-500 bg-violet-50 dark:bg-violet-900/20" : "border-gray-200 dark:border-gray-700 hover:border-gray-300"}`}>
              <p className="font-medium text-sm text-gray-900 dark:text-gray-100">{m.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{m.desc}</p>
            </button>
          ))}
        </div>
      </div>

      <button onClick={() => mutation.mutate(form)} disabled={mutation.isPending}
        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-medium text-sm transition-colors disabled:opacity-50">
        <Save size={16} /> {mutation.isPending ? "Saving…" : "Save changes"}
      </button>
    </div>
  );
}
