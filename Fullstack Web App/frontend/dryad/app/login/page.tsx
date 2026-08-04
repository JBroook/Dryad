import HollowCard from "@/components/HollowCard";
import Image from "next/image";

export default function Login() {
  return (
  <div className="w-screen h-screen bg-gradient-to-br from-[#0A1A0F] via-[#0F2A18] to-[#0A1A0F]">
    <div className="flex flex-col w-1/2 h-full pt-10 pl-10 bg-[url('/assets/login_graphic.svg')] bg-contain bg-bottom bg-no-repeat">
      <div>
        <h1 className="text-3xl font-semibold">Dryad</h1>
      </div>

      <h1 className="w-3/4 h-fit text-6xl font-semibold mt-20"> 
        Protecting forests with acoustic AI
      </h1>

      <p className="mt-5 text-lg text-[#74A385] pr-15">
        Real-time monitoring of illegal logging using AI audio analysis and risk modelling
      </p>

      <div className="grid grid-cols-3 gap-4 w-full mt-auto mb-20 pr-15">
        <HollowCard>
          <div className="p-4 w-50">
            <h1 className="font-bold text-2xl">
              2,400+
            </h1>
            <p className="text-[#74A385]"> 
              Listening Devices
            </p>
          </div>
        </HollowCard>
        <HollowCard>
          <div className="p-4">
            <h1 className="font-bold text-xl">
              2,400+
            </h1>
            <p className="text-[#74A385]"> 
              Listening Devices
            </p>
          </div>
        </HollowCard>
        <HollowCard>
          <div className="p-4">
            <h1 className="font-bold text-xl">
              2,400+
            </h1>
            <p className="text-[#74A385]"> 
              Listening Devices
            </p>
          </div>
        </HollowCard>
      </div>
    </div>
  </div>
  );
}
