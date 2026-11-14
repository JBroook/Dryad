"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { TbMapRoute } from "react-icons/tb";
import { IoWarningOutline } from "react-icons/io5";
import { BsTree } from "react-icons/bs";
import { logoutRequest } from "@/library/api";

const navigationItems = [
  { href: "/home/mobile", label: "Home", icon: BsTree },
  { href: "/home/incidents", label: "Incidents", icon: IoWarningOutline },
  { href: "/home/patrols", label: "Patrols", icon: TbMapRoute },
];

export default function MobileNavigation() {
  const pathname = usePathname();
  const router = useRouter();

  const logout = async () => {
    try {
      await logoutRequest();
    } catch (error) {
      console.error("Logout failed:", error);
    }
    router.replace("/login");
  };

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-base-300 bg-base-200 px-3">
      <Link href="/home/mobile" className="text-lg font-semibold">
        Dryad
      </Link>
      <nav aria-label="Mobile navigation" className="flex items-center gap-1">
        {navigationItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={pathname === href ? "page" : undefined}
            aria-label={label}
            className={`flex min-h-11 min-w-11 flex-col items-center justify-center rounded-lg px-2 text-xs ${
              pathname === href
                ? "bg-base-300 text-accent"
                : "text-secondary-content"
            }`}
          >
            <Icon className="text-lg" />
            <span>{label}</span>
          </Link>
        ))}
        <button
          type="button"
          onClick={logout}
          className="min-h-11 rounded-lg px-2 text-xs text-secondary-content"
        >
          Log out
        </button>
      </nav>
    </header>
  );
}
