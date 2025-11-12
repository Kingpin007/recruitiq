import { AppSidebar } from '@/js/components/app-sidebar';
import { ProtectedRoute } from '@/js/components/ProtectedRoute';
import { ThemeToggle } from '@/js/components/theme-toggle';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/js/components/ui/breadcrumb';
import { Separator } from '@/js/components/ui/separator';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/js/components/ui/sidebar';

interface MainLayoutProps {
  children: React.ReactNode;
  breadcrumbs?: Array<{ label: string; href?: string }>;
}

export function MainLayout({ children, breadcrumbs }: MainLayoutProps) {
  return (
    <ProtectedRoute>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2 border-b">
            <SidebarTrigger />
            <Separator orientation="vertical" className="h-4 ml-2" />
            {breadcrumbs && breadcrumbs.length > 0 && (
              <Breadcrumb>
                <BreadcrumbList>
                  {breadcrumbs.map((crumb, index) => (
                    <div key={crumb.label}>
                      {index > 0 && <BreadcrumbSeparator />}
                      <BreadcrumbItem>
                        {crumb.href ? (
                          <BreadcrumbLink href={crumb.href}>{crumb.label}</BreadcrumbLink>
                        ) : (
                          <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                        )}
                      </BreadcrumbItem>
                    </div>
                  ))}
                </BreadcrumbList>
              </Breadcrumb>
            )}
            <div className="ml-auto">
              <ThemeToggle />
            </div>
          </header>
          <div className="flex flex-1 flex-col gap-4 py-6 pr-6">{children}</div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
