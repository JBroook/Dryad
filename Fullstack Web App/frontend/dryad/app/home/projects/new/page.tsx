"use client"

import StepPanel from "@/components/StepPanel";

export default function New() {
  return (
  <div className="flex flex-col">
    <div className="fixed top-0 h-16 w-full bg-primary">
    navbar
    </div>

    <div className="flex min-h-screen mt-16">
      <div className="flex-1 min-w-0">
        main content
      </div>

      <StepPanel currentStep={1} />
    </div>
  </div>
  );
}
