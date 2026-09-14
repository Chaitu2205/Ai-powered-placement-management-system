import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV_ITEMS = {
  student: [
    { to: '/student', label: 'Dashboard', end: true },
    { to: '/student/profile', label: 'Profile' },
    { to: '/student/jobs', label: 'Browse Jobs' },
    { to: '/student/applications', label: 'My Applications' },
    { to: '/student/interview-practice', label: 'Interview Practice' },
    { to: '/student/notifications', label: 'Notifications' },
  ],
  recruiter: [
    { to: '/recruiter', label: 'Dashboard', end: true },
    { to: '/recruiter/profile', label: 'Profile' },
    { to: '/recruiter/company', label: 'Company' },
    { to: '/recruiter/jobs', label: 'Jobs' },
    { to: '/recruiter/drives', label: 'Placement Drives' },
  ],
  admin: [
    { to: '/admin', label: 'Dashboard', end: true },
    { to: '/admin/students', label: 'Students' },
    { to: '/admin/recruiters', label: 'Recruiters' },
    { to: '/admin/companies', label: 'Companies' },
    { to: '/admin/jobs', label: 'Jobs' },
    { to: '/admin/drives', label: 'Placement Drives' },
    { to: '/admin/applications', label: 'Applications' },
    { to: '/admin/audit-logs', label: 'Audit Logs' },
  ],
};

export default function Sidebar() {
  const { user } = useAuth();
  const items = NAV_ITEMS[user?.role] || [];

  return (
    <aside className="hidden w-60 shrink-0 border-r border-gray-200 bg-white md:block">
      <div className="p-4 text-lg font-bold text-brand-700">PlacementOS</div>
      <nav className="flex flex-col gap-1 px-3">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium ${
                isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
