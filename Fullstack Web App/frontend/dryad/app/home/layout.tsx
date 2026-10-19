"use client";

import Sidebar from "@/components/Sidebar";
import MobileNavigation from "@/components/MobileNavigation";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function HomeLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();
  const [isMobile, setIsMobile] = useState<boolean | null>(null);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 767px)");
    const updateViewport = () => setIsMobile(mediaQuery.matches);

    updateViewport();
    mediaQuery.addEventListener("change", updateViewport);
    return () => mediaQuery.removeEventListener("change", updateViewport);
  }, []);

  useEffect(() => {
    if (
      isMobile &&
      !["/home/mobile", "/home/incidents", "/home/patrols"].includes(pathname)
    ) {
      router.replace("/home/mobile");
    }
  }, [isMobile, pathname, router]);

  if (isMobile === null) {
    return null;
  }

  if (isMobile) {
    if (!["/home/mobile", "/home/incidents", "/home/patrols"].includes(pathname)) {
      return null;
    }

    return (
      <>
        <MobileNavigation />
        <main className="min-h-[calc(100dvh-4rem)] w-full min-w-0 pb-6">
          {children}
        </main>
      </>
    );
  }

  return (
    <div className="flex flex-row">
      <Sidebar />
      <main className="ml-64 min-w-0 flex-1">{children}</main>
    </div>
  );
}
