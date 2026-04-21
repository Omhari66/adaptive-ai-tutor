"use client";

import Sidebar from "./Sidebar";
import { ReactNode, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Menu } from "lucide-react";

export default function AppLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem("auth_token");
    const isAuthPage = pathname === "/login" || pathname === "/register";
    
    if (!token && !isAuthPage) {
      router.push("/login");
    } else {
      setIsAuthenticated(true);
    }
  }, [pathname, router]);

  // Avoid hydration mismatch by waiting for client mount
  if (!mounted) return null;

  const isAuthPage = pathname === "/login" || pathname === "/register";

  if (!isAuthenticated && !isAuthPage) return null; // Avoid flashing content before redirect
  
  if (isAuthPage) {
    return <main className="bg-[var(--color-background)] min-h-screen">{children}</main>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-background)]">
      <div className={`transition-all duration-300 ease-in-out shrink-0 relative ${isSidebarOpen ? 'w-64 border-r border-[var(--color-sidebar-border)]' : 'w-0 border-none overflow-hidden'}`}>
        <div className="w-64">
           <Sidebar />
        </div>
        {/* Collapse Button */}
        {isSidebarOpen && (
          <button 
            onClick={() => setIsSidebarOpen(false)}
            className="absolute top-3 right-3 p-1 rounded-md text-[var(--color-muted-foreground)] hover:bg-[var(--color-sidebar-hover)] hover:text-[var(--color-foreground)] transition-colors z-50"
            title="Close Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
      </div>
      <main className="flex-1 relative flex flex-col h-full min-w-0 bg-[var(--color-background)]">
        {/* Expand Button */}
        {!isSidebarOpen && (
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="absolute z-50 top-3.5 left-4 p-1.5 rounded-md text-[var(--color-muted-foreground)] hover:bg-[var(--color-muted)] hover:text-[var(--color-foreground)] transition-colors bg-[var(--color-background)]"
            title="Open Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}
        <div className="flex-1 overflow-y-auto w-full">
          {children}
        </div>
      </main>
    </div>
  );
}
