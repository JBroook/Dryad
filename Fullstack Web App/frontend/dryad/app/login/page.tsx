"use client"

import HollowCard from "@/components/HollowCard";
import { IoMdWifi } from "react-icons/io";
import { FiShield } from "react-icons/fi";
import { BsTree } from "react-icons/bs";
import { useState } from "react";

export default function Login() {
  const [submitted, setSubmitted] = useState<boolean>(false);

  const handleLogin = async () => {
    setSubmitted(true);
    
  }

  return (
  <div className="flex flex-row w-screen h-screen bg-gradient-to-br from-[#0A1A0F] via-[#0F2A18] to-[#0A1A0F]">
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
            <IoMdWifi className="text-accent text-3xl mb-2"/>
            <h1 className="font-bold text-2xl">
              2,400+
            </h1>
            <p className="text-[#74A385]"> 
              Listening Devices
            </p>
          </div>
        </HollowCard>
        <HollowCard>
          <div className="p-4 w-50">
            <FiShield className="text-accent text-3xl mb-2"/>
            <h1 className="font-bold text-2xl">
              10
            </h1>
            <p className="text-[#74A385]"> 
              Forests Protected
            </p>
          </div>
        </HollowCard>
        <HollowCard>
          <div className="p-4 w-50">
            <BsTree className="text-accent text-3xl mb-2"/>
            <h1 className="font-bold text-2xl">
              1,847
            </h1>
            <p className="text-[#74A385]"> 
              Incidents Caught
            </p>
          </div>
        </HollowCard>
      </div>
    </div>

    <div className="flex w-1/2 h-full items-center justify-center">
      <HollowCard className="p-8 w-[60%] max-w-xl">
        <h1 className="text-3xl font-bold">Welcome back</h1>
        <p className="text-[#74A385] text-md mt-2 mb-4">Sign into your monitoring dashboard</p>

        <div role="tablist" className="tabs tabs-box bg-[#273F2F] w-full">
          <a role="tab" className="tab flex-1 text-accent bg-[#265335] tab-active ">
            Sign in
          </a>
          <a role="tab" className="tab flex-1 text-[#A3ADA6] ">
            Register
          </a>
        </div>

        <form className="flex flex-col max-w-md mx-auto space-y-4">
          <fieldset className="fieldset">
            <legend className="fieldset-legend font-medium text-[#A3ADA6]">Email Address</legend>
            <input
              type="email"
              className="input w-full bg-[#273F2F]"
              placeholder="you@example.com"
            />
          </fieldset>

          <fieldset className="fieldset">
            <legend className="fieldset-legend font-medium text-[#A3ADA6]">Password</legend>
            <input
              type="password"
              className="input w-full bg-[#273F2F]"
              placeholder="••••••••"
            />
          </fieldset>

          <a
            href="/forgot-password"
            className="link link-hover text-sm self-end text-accent"
          >
            Forgot password?
          </a>

          <button className="btn btn-primary w-full" disabled={submitted} onClick={handleLogin}>
            {submitted ?
              <span className="loading loading-spinner"></span>
              :
              "Sign In"
            }
          </button>
        </form>
      </HollowCard>
    </div>
  </div>
  );
}
