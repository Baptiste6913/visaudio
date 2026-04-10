import { useRef, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import RoleSwitcher from "./RoleSwitcher";
import { uploadExcel } from "../utils/api";
import type { UploadResult } from "../types";

type UploadState =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "success"; result: UploadResult }
  | { status: "error"; message: string };

export default function Layout() {
  const { pathname } = useLocation();
  const fileRef = useRef<HTMLInputElement>(null);
  const [upload, setUpload] = useState<UploadState>({ status: "idle" });

  const navLinkClass = (to: string) =>
    [
      "px-3 py-1.5 rounded text-sm font-medium transition-colors",
      pathname === to
        ? "bg-brand-600 text-white"
        : "text-gray-600 hover:text-brand-600",
    ].join(" ");

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    // Reset input so the same file can be re-selected
    e.target.value = "";

    setUpload({ status: "uploading" });
    try {
      const result = await uploadExcel(file);
      setUpload({ status: "success", result });
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Erreur lors de l'import.";
      setUpload({ status: "error", message });
    }
  };

  const handleUploadClick = () => {
    fileRef.current?.click();
  };

  const dismissBanner = () => setUpload({ status: "idle" });

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white/90 backdrop-blur-md sticky top-0 z-50 border-b border-gray-200 shadow-sm">
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
                <Link to="/agents" className={navLinkClass("/agents")}>
                  Agents
                </Link>
                <Link
                  to="/simulation"
                  className={navLinkClass("/simulation")}
                >
                  Simulation
                </Link>
              </nav>
            </div>

            <div className="flex items-center gap-3">
              {/* Hidden file input */}
              <input
                ref={fileRef}
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={handleFileChange}
                aria-label="Sélectionner un fichier Excel"
              />

              {/* Upload button */}
              <button
                onClick={handleUploadClick}
                disabled={upload.status === "uploading"}
                className={[
                  "flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium border transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600",
                  upload.status === "uploading"
                    ? "bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed"
                    : "bg-white text-gray-600 border-gray-200 hover:border-brand-400 hover:text-brand-600",
                ].join(" ")}
                aria-busy={upload.status === "uploading"}
              >
                {upload.status === "uploading" ? (
                  <>
                    {/* Spinner */}
                    <svg
                      className="animate-spin h-3.5 w-3.5 text-gray-400"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                      />
                    </svg>
                    Import en cours…
                  </>
                ) : (
                  <>
                    {/* Upload arrow-up icon */}
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-3.5 w-3.5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M12 3v13M8 7l4-4 4 4"
                      />
                    </svg>
                    Importer un fichier Excel
                  </>
                )}
              </button>

              <RoleSwitcher />
            </div>
          </div>
        </div>

        {/* Success banner */}
        {upload.status === "success" && (
          <div
            role="status"
            aria-live="polite"
            className="bg-green-50 border-t border-green-200 px-4 sm:px-6 lg:px-8 py-2 flex items-center justify-between"
          >
            <p className="text-sm text-green-700 font-medium">
              {upload.result.message} — rechargement en cours…
            </p>
            <button
              onClick={dismissBanner}
              className="text-green-600 hover:text-green-800 text-xs ml-4"
              aria-label="Fermer"
            >
              ✕
            </button>
          </div>
        )}

        {/* Error banner */}
        {upload.status === "error" && (
          <div
            role="alert"
            className="bg-red-50 border-t border-red-200 px-4 sm:px-6 lg:px-8 py-2 flex items-center justify-between"
          >
            <p className="text-sm text-red-700 font-medium">{upload.message}</p>
            <button
              onClick={dismissBanner}
              className="text-red-600 hover:text-red-800 text-xs ml-4"
              aria-label="Fermer"
            >
              ✕
            </button>
          </div>
        )}
      </header>
      <div className="h-0.5 bg-gradient-to-r from-brand-500 via-brand-400 to-blue-400" />

      <main className="page-enter max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>
    </div>
  );
}
