"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

export default function ProjectAliasPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams.get("pid");

  useEffect(() => {
    if (!projectId) {
      router.replace("/home/projects");
      return;
    }

    router.replace(`/home/project?pid=${projectId}&tab=overview`);
  }, [projectId, router]);

  return null;
}
