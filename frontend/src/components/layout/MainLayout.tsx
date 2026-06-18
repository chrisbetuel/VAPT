import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import { useUIStore } from "@/stores/uiStore";
import { useAuthStore } from "@/stores/authStore";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function MainLayout() {
  const sidebar = useUIStore((s) => s.sidebar);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  useWebSocket(isAuthenticated);

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main
          className={`flex-1 overflow-y-auto p-6 transition-all ${
            sidebar === "collapsed" ? "ml-16" : "ml-64"
          }`}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
