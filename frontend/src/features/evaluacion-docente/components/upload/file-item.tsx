"use client";

import { FileText, CheckCircle2, XCircle, Loader2, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export type FileItemStatus = "pending" | "uploading" | "success" | "error";

export interface FileItemData {
  id: string;
  file: File;
  status: FileItemStatus;
  error?: string;
}

interface FileItemProps {
  item: FileItemData;
  onRemove: (id: string) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const statusConfig: Record<
  FileItemStatus,
  { icon: typeof FileText; color: string; label: string }
> = {
  pending: {
    icon: FileText,
    color: "text-muted-foreground",
    label: "Pendiente",
  },
  uploading: {
    icon: Loader2,
    color: "text-primary",
    label: "Subiendo...",
  },
  success: {
    icon: CheckCircle2,
    color: "text-emerald-600",
    label: "Completado",
  },
  error: {
    icon: XCircle,
    color: "text-destructive",
    label: "Error",
  },
};

export function FileItem({ item, onRemove }: FileItemProps) {
  const config = statusConfig[item.status];
  const StatusIcon = config.icon;
  const canRemove = item.status !== "uploading";

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border px-4 py-3 transition-colors",
        item.status === "error" && "border-destructive/30 bg-destructive/5",
        item.status === "success" && "border-emerald-200 bg-emerald-50/50",
      )}
    >
      <StatusIcon
        className={cn(
          "h-5 w-5 shrink-0",
          config.color,
          item.status === "uploading" && "animate-spin",
        )}
      />

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{item.file.name}</p>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {formatSize(item.file.size)}
          </span>
          <span className="text-xs text-muted-foreground">·</span>
          <span className={cn("text-xs", config.color)}>{config.label}</span>
        </div>
        {item.error && (
          <p className="mt-1 text-xs text-destructive">{item.error}</p>
        )}
      </div>

      {canRemove && (
        <Button
          variant="ghost"
          size="icon-xs"
          onClick={() => onRemove(item.id)}
          aria-label={`Eliminar ${item.file.name}`}
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );
}
