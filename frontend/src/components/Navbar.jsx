import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div className="text-sm text-gray-500">
        Signed in as <span className="font-medium text-gray-800">{user?.email}</span>{' '}
        <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs uppercase tracking-wide text-gray-500">
          {user?.role}
        </span>
      </div>
      <button
        onClick={handleLogout}
        className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        Log out
      </button>
    </header>
  );
}
