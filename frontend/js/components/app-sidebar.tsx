import * as React from 'react';
import {
  BriefcaseIcon,
  FileText,
  Home,
  Settings2,
  Upload,
  Users,
} from 'lucide-react';

import { NavMain } from '@/js/components/nav-main';
import { NavUser } from '@/js/components/nav-user';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from '@/js/components/ui/sidebar';

// This is sample data.
const data = {
  user: {
    name: 'Admin User',
    email: 'admin@recruitiq.com',
    avatar: '/avatars/admin.jpg',
  },
  navMain: [
    {
      title: 'Dashboard',
      url: '/',
      icon: Home,
      isActive: true,
    },
    {
      title: 'Upload Resumes',
      url: '/upload',
      icon: Upload,
    },
    {
      title: 'Candidates',
      url: '/',
      icon: Users,
      items: [
        {
          title: 'All Candidates',
          url: '/',
        },
        {
          title: 'Pending Review',
          url: '/?status=pending',
        },
        {
          title: 'Interviews',
          url: '/?recommendation=interview',
        },
      ],
    },
    {
      title: 'Job Descriptions',
      url: '/admin/recruitment/jobdescription/',
      icon: BriefcaseIcon,
    },
    {
      title: 'Reports',
      url: '#',
      icon: FileText,
    },
    {
      title: 'Settings',
      url: '#',
      icon: Settings2,
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2 py-2 pl-1">
          <BriefcaseIcon className="h-6 w-6 shrink-0" />
          <span className="font-bold text-xl group-data-[collapsible=icon]:hidden">RecruitIQ</span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
