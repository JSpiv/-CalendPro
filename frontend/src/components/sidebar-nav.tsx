"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";

const navItems = [
  { label: "Tasks", href: "/" },
  { label: "Calendar", href: "/calendar" },
  { label: "Log", href: "/log" },
  { label: "Account", href: "/account" },
] as const;

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SidebarNav() {
  const pathname = usePathname();
  const { data: session } = useSession();

  return (
    <aside className="w-64 shrink-0 border-r border-black/10 bg-white/60 backdrop-blur dark:border-white/10 dark:bg-white/5">
      <div className="flex h-full min-h-screen flex-col">
        <div className="px-5 py-5 flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold tracking-tight">CalendPro</div>
            <div className="text-xs text-black/60 dark:text-white/60">
              {session?.user?.name || "Navigation"}
            </div>
          </div>
          {session && (
            <button
              onClick={() => signOut()}
              className="text-[10px] uppercase tracking-wider font-bold opacity-50 hover:opacity-100 transition"
            >
              Out
            </button>
          )}
        </div>

        <nav className="flex flex-col gap-1 px-3">
          {navItems.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={[
                  "rounded-lg px-3 py-2 text-sm transition",
                  active
                    ? "bg-black/10 text-black dark:bg-white/10 dark:text-white"
                    : "text-black/70 hover:bg-black/5 hover:text-black dark:text-white/70 dark:hover:bg-white/5 dark:hover:text-white",
                ].join(" ")}
              >
                {item.label}
              </Link>
            );
          })}
          {!session && (
            <Link
              href="/login"
              className={[
                "rounded-lg px-3 py-2 text-sm transition text-black/70 hover:bg-black/5 hover:text-black dark:text-white/70 dark:hover:bg-white/5 dark:hover:text-white",
                isActive(pathname, "/login") ? "bg-black/10 text-black dark:bg-white/10 dark:text-white" : ""
              ].join(" ")}
            >
              Sign In
            </Link>
          )}
        </nav>

        <div className="mt-auto px-5 py-4 text-xs text-black/50 dark:text-white/50">
          © {new Date().getFullYear()} CalendPro
        </div>
      </div>
    </aside>
  );
}
