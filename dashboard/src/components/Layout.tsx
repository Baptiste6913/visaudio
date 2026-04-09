import { Link, Outlet, useLocation } from "react-router-dom";
import RoleSwitcher from "./RoleSwitcher";

export default function Layout() {
  const { pathname } = useLocation();

  const navLinkClass = (to: string) =>
    [
      "px-3 py-1.5 rounded text-sm font-medium transition-colors",
      pathname === to
        ? "bg-brand-600 text-white"
        : "text-gray-600 hover:text-brand-600",
    ].join(" ");

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-6">
              <span className="text-xl font-bold text-brand-600 whitespace-nowrap">
                Visaudio Optique Analytics
              </span>
              <nav className="flex items-center gap-1">
                <Link to="/" className={navLinkClass("/")}>
                  Tableau de bord
                </Link>
                <Link
                  to="/simulation"
                  className={navLinkClass("/simulation")}
                >
                  Simulation
                </Link>
              </nav>
            </div>
            <RoleSwitcher />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>
    </div>
  );
}
