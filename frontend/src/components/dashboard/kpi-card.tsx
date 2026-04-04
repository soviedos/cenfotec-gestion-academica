"use client";

import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";

interface KpiCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  trend?: { value: number; label: string };
  className?: string;
}

export function KpiCard({
  label,
  value,
  icon: Icon,
  description,
  trend,
  className,
}: KpiCardProps) {
  return (
    <Card className={cn("relative overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardDescription className="text-sm font-medium">
          {label}
        </CardDescription>
        <Icon className="size-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold tracking-tight">{value}</div>
        {(description || trend) && (
          <p className="mt-1 text-xs text-muted-foreground">
            {trend && (
              <span
                className={cn(
                  "mr-1 font-medium",
                  trend.value >= 0 ? "text-emerald-600" : "text-red-500",
                )}
              >
                {trend.value >= 0 ? "+" : ""}
                {trend.value}%
              </span>
            )}
            {trend?.label ?? description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
