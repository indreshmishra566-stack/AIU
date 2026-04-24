import React from "react";
import { Loader2 } from "lucide-react";
import clsx from "clsx";

export default function LoadingSpinner({ fullScreen = false }: { fullScreen?: boolean }) {
  return (
    <div className={clsx("flex items-center justify-center", fullScreen && "min-h-screen")}>
      <Loader2 size={28} className="animate-spin text-violet-500" />
    </div>
  );
}
