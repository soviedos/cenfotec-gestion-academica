import { AuthGuard } from "@/features/auth";
import { PortalShell } from "@/components/layout";

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <PortalShell>{children}</PortalShell>
    </AuthGuard>
  );
}
