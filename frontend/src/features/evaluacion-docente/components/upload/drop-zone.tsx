"use client";

import { useCallback, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { cn } from "@/lib/utils";

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB
const ACCEPTED_TYPE = "application/pdf";

interface DropZoneProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
}

export function DropZone({ onFilesSelected, disabled }: DropZoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndEmit = useCallback(
    (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0) return;
      const valid: File[] = [];
      for (const file of Array.from(fileList)) {
        if (file.type !== ACCEPTED_TYPE) continue;
        if (file.size > MAX_FILE_SIZE) continue;
        if (file.size === 0) continue;
        valid.push(file);
      }
      if (valid.length > 0) onFilesSelected(valid);
    },
    [onFilesSelected],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      if (disabled) return;
      validateAndEmit(e.dataTransfer.files);
    },
    [disabled, validateAndEmit],
  );

  const handleDrag = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (disabled) return;
      setDragActive(e.type === "dragenter" || e.type === "dragover");
    },
    [disabled],
  );

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="Zona de carga de archivos"
      onClick={() => !disabled && inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          if (!disabled) inputRef.current?.click();
        }
      }}
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 text-center transition-colors",
        dragActive
          ? "border-primary bg-primary/5"
          : "border-muted-foreground/25 hover:border-muted-foreground/40",
        disabled && "pointer-events-none opacity-50",
      )}
    >
      <Upload
        className={cn(
          "mb-4 h-10 w-10",
          dragActive ? "text-primary" : "text-muted-foreground/50",
        )}
      />
      <p className="text-sm font-medium text-foreground">
        {dragActive
          ? "Soltar archivos aqui"
          : "Arrastra archivos PDF aqui o haz clic para seleccionar"}
      </p>
      <p className="mt-1 text-xs text-muted-foreground/70">
        Solo archivos PDF — Maximo 50 MB por archivo
      </p>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        multiple
        className="hidden"
        data-testid="file-input"
        onChange={(e) => {
          validateAndEmit(e.target.files);
          e.target.value = "";
        }}
        disabled={disabled}
      />
    </div>
  );
}
