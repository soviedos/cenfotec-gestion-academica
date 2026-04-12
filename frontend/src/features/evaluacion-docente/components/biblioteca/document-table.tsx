"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Loader2, Library } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Documento } from "@/features/evaluacion-docente/types";
import { getColumns } from "./columns";

interface DocumentTableProps {
  data: Documento[];
  isLoading: boolean;
  isEmpty: boolean;
  sortBy: string;
  sortOrder: string;
  onSort: (field: string) => void;
  onDelete?: (id: string) => void;
}

export function DocumentTable({
  data,
  isLoading,
  isEmpty,
  sortBy,
  sortOrder,
  onSort,
  onDelete,
}: DocumentTableProps) {
  const columns = getColumns(sortBy, sortOrder, onSort, onDelete);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div
      className="rounded-lg border bg-card"
      role="region"
      aria-label="Tabla de documentos"
    >
      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id} className="hover:bg-transparent">
              {headerGroup.headers.map((header) => (
                <TableHead
                  key={header.id}
                  style={{
                    width:
                      header.getSize() !== 150 ? header.getSize() : undefined,
                  }}
                >
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-40">
                <div className="flex flex-col items-center justify-center gap-2">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    Cargando documentos...
                  </span>
                </div>
              </TableCell>
            </TableRow>
          ) : isEmpty ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-40">
                <div className="flex flex-col items-center justify-center gap-2">
                  <Library className="h-8 w-8 text-muted-foreground/40" />
                  <span className="text-sm text-muted-foreground">
                    No se encontraron documentos
                  </span>
                </div>
              </TableCell>
            </TableRow>
          ) : (
            table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
