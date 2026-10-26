"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

function ProjectAliasPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams.get("pid");

  useEffect(() => {
    if (!projectId) {
      router.replace("/home/projects");
      return;
    }

    router.replace(`/home/project?pid=${projectId}&tab=forest_map`);
  }, [projectId, router]);

  return null;
}

export default function ProjectAliasPage() {
  return (
    <Suspense fallback={<span className="loading loading-spinner" />}>
      <ProjectAliasPageContent />
    </Suspense>
  );
}
