  "use client"

import StepPanel from "@/components/StepPanel";
import Link from "next/link";
import { FaArrowLeft } from "react-icons/fa";

  export default function New() {
    return (
    <div className="flex flex-col">
      <div className="fixed top-0 h-20 w-full flex flex-row items-center bg-secondary border-b border-b-white/8">
        <Link href="/home/projects" 
          className="btn text-secondary-content font-medium ml-5">
          <FaArrowLeft className="text-secondary-content"/>
          Dashboard
        </Link>

        <h1 className="ml-10">New Monitoring Project</h1>
      </div>

      <div className="flex min-h-screen mt-20">
        <div className="flex-1 min-w-0">
          main 
        </div>

        <StepPanel currentStep={1} />
      </div>
    </div>
    );
  }
