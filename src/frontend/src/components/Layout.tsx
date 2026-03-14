import { Button } from "@/components/ui/button";
import { Link } from "@tanstack/react-router";
import {
  BookOpen,
  GraduationCap,
  LogIn,
  LogOut,
  Menu,
  Newspaper,
  Video,
  X,
} from "lucide-react";
import { type ReactNode, useState } from "react";
import { useInternetIdentity } from "../hooks/useInternetIdentity";

const navLinks = [
  { to: "/notes", label: "Notes", icon: BookOpen, ocid: "nav.notes.link" },
  { to: "/videos", label: "Videos", icon: Video, ocid: "nav.videos.link" },
  { to: "/blog", label: "Blog", icon: Newspaper, ocid: "nav.blog.link" },
];

export default function Layout({ children }: { children: ReactNode }) {
  const { login, clear, identity, isLoggingIn } = useInternetIdentity();
  const [mobileOpen, setMobileOpen] = useState(false);
  const isLoggedIn = !!identity;

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="sticky top-0 z-40 bg-card/95 backdrop-blur border-b border-border shadow-xs">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link
            to="/"
            data-ocid="nav.home.link"
            className="flex items-center gap-2 group"
          >
            <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center shadow-warm">
              <GraduationCap className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-display font-semibold text-lg text-foreground">
              SEN Learning Hub
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                data-ocid={link.ocid}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                activeProps={{ className: "text-primary bg-secondary" }}
              >
                <link.icon className="w-4 h-4" />
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            {isLoggedIn ? (
              <Button
                variant="outline"
                size="sm"
                onClick={clear}
                data-ocid="nav.logout.button"
                className="hidden md:flex items-center gap-1.5"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={login}
                disabled={isLoggingIn}
                data-ocid="nav.login.button"
                className="hidden md:flex items-center gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90"
              >
                <LogIn className="w-4 h-4" />
                {isLoggingIn ? "Logging in…" : "Admin Login"}
              </Button>
            )}
            <button
              type="button"
              className="md:hidden p-2 rounded-lg hover:bg-secondary transition-colors"
              onClick={() => setMobileOpen((v) => !v)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        {mobileOpen && (
          <nav className="md:hidden border-t border-border bg-card px-4 py-3 flex flex-col gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                data-ocid={link.ocid}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors"
                activeProps={{ className: "text-primary bg-secondary" }}
                onClick={() => setMobileOpen(false)}
              >
                <link.icon className="w-4 h-4" />
                {link.label}
              </Link>
            ))}
            {isLoggedIn ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  clear();
                  setMobileOpen(false);
                }}
                data-ocid="nav.logout.button"
                className="mt-2"
              >
                <LogOut className="w-4 h-4 mr-1.5" /> Logout
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={() => {
                  login();
                  setMobileOpen(false);
                }}
                disabled={isLoggingIn}
                data-ocid="nav.login.button"
                className="mt-2 bg-primary text-primary-foreground"
              >
                <LogIn className="w-4 h-4 mr-1.5" /> Admin Login
              </Button>
            )}
          </nav>
        )}
      </header>

      <main className="flex-1">{children}</main>

      <footer className="bg-primary text-primary-foreground py-8 mt-16">
        <div className="container mx-auto px-4 text-center">
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-lg bg-primary-foreground/20 flex items-center justify-center">
              <GraduationCap className="w-4 h-4" />
            </div>
            <span className="font-display font-semibold">SEN Learning Hub</span>
          </div>
          <p className="text-primary-foreground/70 text-sm">
            Empowering educators, parents, and learners with SEN resources.
          </p>
          <p className="text-primary-foreground/50 text-xs mt-4">
            © {new Date().getFullYear()}. Built with ❤️ using{" "}
            <a
              href={`https://caffeine.ai?utm_source=caffeine-footer&utm_medium=referral&utm_content=${encodeURIComponent(window.location.hostname)}`}
              className="underline hover:text-primary-foreground/80 transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              caffeine.ai
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
