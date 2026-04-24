import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/apiClient";
import { Sparkles, Check, X } from "lucide-react";
import toast from "react-hot-toast";

export default function RecommendationsPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["recommendations"],
    queryFn: () => api.listRecommendations().then(r => r.data.results),
  });

  const accept = useMutation({
    mutationFn: (id: string) => api.acceptRecommendation(id),
    onSuccess: () => { qc.invalidateQueries({queryKey:["recommendations"]}); toast.success("Added to your plan!"); },
  });
  const dismiss = useMutation({
    mutationFn: (id: string) => api.dismissRecommendation(id),
    onSuccess: () => qc.invalidateQueries({queryKey:["recommendations"]}),
  });

  const priorityStyles: Record<string, string> = {
    high: "text-red-600 bg-red-50 dark:bg-red-900/10",
    medium: "text-amber-600 bg-amber-50 dark:bg-amber-900/10",
    low: "text-green-600 bg-green-50 dark:bg-green-900/10",
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-2 mb-6">
        <Sparkles size={20} className="text-amber-500" />
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">For You</h1>
      </div>
      {isLoading ? (
        <div className="space-y-3">{[1,2,3].map(i=><div key={i} className="h-24 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse"/>)}</div>
      ) : data?.length === 0 ? (
        <div className="text-center py-20 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-2xl">
          <Sparkles size={40} className="text-gray-300 mx-auto mb-3"/>
          <p className="text-gray-400 text-sm">Recommendations appear after a few conversations.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {data?.map((rec: any) => (
            <div key={rec.id} className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-5">
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-gray-900 dark:text-gray-100 text-sm">{rec.title}</h3>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${priorityStyles[rec.priority]||""}`}>{rec.priority}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 capitalize">{rec.category}</span>
                  </div>
                  <p className="text-sm text-gray-500 leading-relaxed">{rec.description}</p>
                  {rec.status === "pending" && (
                    <div className="flex gap-2 mt-3">
                      <button onClick={() => accept.mutate(rec.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-xs font-medium hover:bg-green-100 transition-colors">
                        <Check size={12} /> Accept
                      </button>
                      <button onClick={() => dismiss.mutate(rec.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-500 text-xs font-medium hover:bg-gray-100 transition-colors">
                        <X size={12} /> Dismiss
                      </button>
                    </div>
                  )}
                  {rec.status !== "pending" && (
                    <span className="inline-block mt-2 text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-400 capitalize">{rec.status}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
