import React from 'react';
import { UserRole } from '../types/meeting';
import { Briefcase, Code, GraduationCap, SlidersHorizontal, Sparkles } from 'lucide-react';

interface HeaderProps {
  meetingId: string;
  selectedRole: UserRole;
  onSelectRole: (role: UserRole) => void;
}

export const Header: React.FC<HeaderProps> = ({ meetingId, selectedRole, onSelectRole }) => {
  const roles: { role: UserRole; label: string; icon: React.ReactNode }[] = [
    { role: 'MANAGER', label: 'Manager', icon: <Briefcase size={14} /> },
    { role: 'DEVELOPER', label: 'Developer', icon: <Code size={14} /> },
    { role: 'INTERN', label: 'Intern', icon: <GraduationCap size={14} /> },
    { role: 'DEFAULT', label: 'Default', icon: <SlidersHorizontal size={14} /> },
  ];

  return (
    <header className="header">
      <div className="header-left">
        <div className="brand-icon">
          <Sparkles size={24} />
        </div>
        <div className="title-area">
          <h1>
            Meeting Intelligence System
            {meetingId && <span className="meeting-pill">Meeting: {meetingId}</span>}
          </h1>
          <p className="header-subtitle">
            Post-Extraction Intelligence & Multi-Perspective Presentation Layer
          </p>
        </div>
      </div>

      <div className="role-switcher" role="group" aria-label="Role Perspective">
        {roles.map(({ role, label, icon }) => (
          <button
            key={role}
            className={`role-btn ${selectedRole === role ? 'active' : ''}`}
            onClick={() => onSelectRole(role)}
            title={`Switch to ${label} view`}
          >
            {icon}
            {label}
          </button>
        ))}
      </div>
    </header>
  );
};
