import * as React from 'react';
import { BriefcaseIcon, Home, LogIn } from 'lucide-react';

import { NavMain } from '@/js/components/nav-main';
import { NavUser } from '@/js/components/nav-user';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/js/components/ui/sidebar';
import { useAuth } from '@/js/contexts/AuthContext';

const navMain = [
  {
    title: 'Dashboard',
    url: '/',
    icon: Home,
    isActive: true,
  },
];

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { user, isAuthenticated } = useAuth();

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2 py-2 pl-1">
          <BriefcaseIcon className="h-6 w-6 shrink-0" />
          <span className="font-bold text-xl group-data-[collapsible=icon]:hidden">RecruitIQ</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navMain} />
      </SidebarContent>
      <SidebarFooter>
        {isAuthenticated && user ? (
          <NavUser
            user={{
              name: user.username || user.email.split('@')[0],
              email: user.email,
            }}
          />
        ) : (
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton size="lg" asChild>
                <a href="/login">
                  <LogIn className="h-4 w-4" />
                  <span>Login</span>
                </a>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        )}
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
