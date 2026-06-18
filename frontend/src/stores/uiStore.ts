import { create } from "zustand";

type Theme = "light" | "dark" | "system";
type SidebarState = "expanded" | "collapsed";

interface UIState {
  theme: Theme;
  sidebar: SidebarState;
  isMobileMenuOpen: boolean;
  setTheme: (theme: Theme) => void;
  toggleSidebar: () => void;
  setMobileMenuOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>()((set, get) => ({
  theme: "dark",
  sidebar: "expanded",
  isMobileMenuOpen: false,

  setTheme: (theme) => set({ theme }),
  toggleSidebar: () =>
    set({
      sidebar: get().sidebar === "expanded" ? "collapsed" : "expanded",
    }),
  setMobileMenuOpen: (open) => set({ isMobileMenuOpen: open }),
}));
