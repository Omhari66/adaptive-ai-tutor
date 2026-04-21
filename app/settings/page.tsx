"use client";

import { useState, useEffect } from "react";
import { Settings, User, Bell, Shield, Moon, Sun, Monitor, Save } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("profile");
  const [theme, setTheme] = useState("system");
  const [isSaving, setIsSaving] = useState(false);

  // Load initial theme from storage
  useEffect(() => {
    const current = localStorage.getItem('app_theme') || 'system';
    setTheme(current);
  }, []);

  // Apply preview theme immediately
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else if (theme === 'light') {
      root.classList.add('light');
      root.classList.remove('dark');
    } else {
      root.classList.remove('dark', 'light');
    }
  }, [theme]);

  // Revert back to saved theme if unmounted without saving
  useEffect(() => {
    return () => {
      const current = localStorage.getItem('app_theme') || 'system';
      const root = document.documentElement;
      if (current === 'dark') {
        root.classList.add('dark');
        root.classList.remove('light');
      } else if (current === 'light') {
        root.classList.add('light');
        root.classList.remove('dark');
      } else {
        root.classList.remove('dark', 'light');
      }
    };
  }, []);

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      localStorage.setItem('app_theme', theme);
      alert("Settings saved successfully!");
    }, 800);
  };

  return (
    <div className="p-8 max-w-5xl mx-auto w-full">
      <header className="mb-10">
        <h1 className="text-3xl font-bold text-[var(--color-foreground)] tracking-tight">Settings</h1>
        <p className="text-[var(--color-muted-foreground)] text-sm mt-1">Manage your account preferences and application settings.</p>
      </header>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Settings Navigation */}
        <aside className="w-full md:w-64 shrink-0">
          <nav className="flex flex-col space-y-1">
            <button 
              onClick={() => setActiveTab("profile")}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${activeTab === 'profile' ? 'bg-[var(--color-sidebar-hover)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-foreground)]'}`}
            >
              <User className="w-4 h-4" />
              Profile
            </button>
            <button 
              onClick={() => setActiveTab("appearance")}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${activeTab === 'appearance' ? 'bg-[var(--color-sidebar-hover)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-foreground)]'}`}
            >
              <Moon className="w-4 h-4" />
              Appearance
            </button>
            <button 
              onClick={() => setActiveTab("notifications")}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${activeTab === 'notifications' ? 'bg-[var(--color-sidebar-hover)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-foreground)]'}`}
            >
              <Bell className="w-4 h-4" />
              Notifications
            </button>
            <button 
              onClick={() => setActiveTab("security")}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors ${activeTab === 'security' ? 'bg-[var(--color-sidebar-hover)] text-[var(--color-foreground)]' : 'text-[var(--color-muted-foreground)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-foreground)]'}`}
            >
              <Shield className="w-4 h-4" />
              Security
            </button>
          </nav>
        </aside>

        {/* Settings Content */}
        <div className="flex-1">
          <div className="bg-[var(--color-card)] border border-[var(--color-border)] rounded-2xl p-6 md:p-8 shadow-sm">
            
            {activeTab === "profile" && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-1">Profile Information</h2>
                  <p className="text-sm text-[var(--color-muted-foreground)]">Update your account's profile information and email address.</p>
                </div>
                
                <div className="space-y-4 max-w-md">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-[var(--color-foreground)]">Name</label>
                    <input 
                      type="text" 
                      defaultValue="Student User"
                      className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-4 py-2.5 outline-none focus:border-[var(--color-primary)] transition-colors"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-[var(--color-foreground)]">Email</label>
                    <input 
                      type="email" 
                      defaultValue="student@example.com"
                      className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-4 py-2.5 outline-none focus:border-[var(--color-primary)] transition-colors"
                    />
                  </div>
                </div>
              </div>
            )}

            {activeTab === "appearance" && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-1">Appearance</h2>
                  <p className="text-sm text-[var(--color-muted-foreground)]">Customize how the Study Assistant looks on your device.</p>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl">
                  <button 
                    onClick={() => setTheme("light")}
                    className={`flex flex-col items-center gap-3 p-4 border rounded-xl transition-all ${theme === 'light' ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5' : 'border-[var(--color-border)] hover:border-[var(--color-muted-foreground)]'}`}
                  >
                    <div className="p-3 bg-amber-50 text-amber-500 rounded-full">
                      <Sun className="w-6 h-6" />
                    </div>
                    <span className="font-medium">Light</span>
                  </button>
                  <button 
                    onClick={() => setTheme("dark")}
                    className={`flex flex-col items-center gap-3 p-4 border rounded-xl transition-all ${theme === 'dark' ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5' : 'border-[var(--color-border)] hover:border-[var(--color-muted-foreground)]'}`}
                  >
                    <div className="p-3 bg-indigo-50 text-indigo-500 rounded-full">
                      <Moon className="w-6 h-6" />
                    </div>
                    <span className="font-medium">Dark</span>
                  </button>
                  <button 
                    onClick={() => setTheme("system")}
                    className={`flex flex-col items-center gap-3 p-4 border rounded-xl transition-all ${theme === 'system' ? 'border-[var(--color-primary)] bg-[var(--color-primary)]/5' : 'border-[var(--color-border)] hover:border-[var(--color-muted-foreground)]'}`}
                  >
                    <div className="p-3 bg-slate-50 text-slate-500 rounded-full">
                      <Monitor className="w-6 h-6" />
                    </div>
                    <span className="font-medium">System</span>
                  </button>
                </div>
              </div>
            )}

            {activeTab === "notifications" && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-1">Notifications</h2>
                  <p className="text-sm text-[var(--color-muted-foreground)]">Choose what updates you want to receive.</p>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 border border-[var(--color-border)] rounded-xl">
                    <div>
                      <h3 className="font-medium">Study Reminders</h3>
                      <p className="text-sm text-[var(--color-muted-foreground)]">Get notified when it's time for a scheduled study session.</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-5 h-5 accent-[var(--color-primary)] cursor-pointer" />
                  </div>
                  <div className="flex items-center justify-between p-4 border border-[var(--color-border)] rounded-xl">
                    <div>
                      <h3 className="font-medium">Document Insights</h3>
                      <p className="text-sm text-[var(--color-muted-foreground)]">Receive a summary when your document finishes processing.</p>
                    </div>
                    <input type="checkbox" defaultChecked className="w-5 h-5 accent-[var(--color-primary)] cursor-pointer" />
                  </div>
                  <div className="flex items-center justify-between p-4 border border-[var(--color-border)] rounded-xl">
                    <div>
                      <h3 className="font-medium">Weekly Report</h3>
                      <p className="text-sm text-[var(--color-muted-foreground)]">Get an overview of your progress every week.</p>
                    </div>
                    <input type="checkbox" className="w-5 h-5 accent-[var(--color-primary)] cursor-pointer" />
                  </div>
                </div>
              </div>
            )}

            {activeTab === "security" && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-semibold text-[var(--color-foreground)] mb-1">Security Settings</h2>
                  <p className="text-sm text-[var(--color-muted-foreground)]">Manage your password and security preferences.</p>
                </div>

                <div className="space-y-4 max-w-md">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-[var(--color-foreground)]">Current Password</label>
                    <input 
                      type="password" 
                      placeholder="••••••••"
                      className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-4 py-2.5 outline-none focus:border-[var(--color-primary)] transition-colors"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-[var(--color-foreground)]">New Password</label>
                    <input 
                      type="password" 
                      placeholder="••••••••"
                      className="w-full bg-[var(--color-background)] border border-[var(--color-border)] rounded-lg px-4 py-2.5 outline-none focus:border-[var(--color-primary)] transition-colors"
                    />
                  </div>
                </div>
              </div>
            )}

            <div className="mt-8 pt-6 border-t border-[var(--color-border)] flex justify-end">
              <button 
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-2 px-6 py-2.5 bg-[var(--color-primary)] text-white font-medium rounded-xl hover:bg-[var(--color-primary)]/90 transition-colors shadow-sm disabled:opacity-70"
              >
                {isSaving ? (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {isSaving ? "Saving..." : "Save Changes"}
              </button>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
