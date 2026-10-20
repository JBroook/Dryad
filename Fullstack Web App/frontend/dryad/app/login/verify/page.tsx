"use client"

import HollowCard from "@/components/HollowCard";
import { IoMdWifi } from "react-icons/io";
import { FiShield } from "react-icons/fi";
import { BsTree } from "react-icons/bs";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useToast } from "@/components/ToastProvider";

export default function Verify() {
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [code, setCode] = useState<string>("");

  const APIBase = "http://127.0.0.1:8000/api";
  // const APIBase = "http://192.168.100.7:8000/api";

  const searchParams = useSearchParams();

  const router = useRouter();
  const { showToast } = useToast();

  const handleVerification = async (e : React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();

    setSubmitted(true);
    const res = await fetch(`${APIBase}/verify_email/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email : await searchParams.get("email"),
        code : code
      }),
    });

    if (!res.ok) {
      showToast("Email verification failed.", "error");
      setSubmitted(false);
      return;
    }

    const data = await res.json();
    showToast(data.message ?? "Email verified successfully.");
    router.push(`/login`)
  }

  return (
  <div className="flex min-h-screen w-full flex-col bg-base-100 text-base-content md:h-screen md:flex-row">
    <div className="hidden flex-col bg-base-200/80 bg-[url('/assets/login_graphic.svg')] bg-contain bg-bottom bg-no-repeat pt-10 pl-10 md:flex md:h-full md:w-1/2 md:border-r md:border-base-300">
      <div>
        <h1 className="text-3xl font-semibold">Dryad</h1>
      </div>

      <h1 className="w-3/4 h-fit text-6xl font-semibold mt-20 text-base-content"> 
        Protecting forests with acoustic AI
      </h1>

      <p className="mt-5 text-lg text-secondary-content pr-15">
        Real-time monitoring of illegal logging using AI audio analysis and risk modelling
      </p>

      <div className="grid grid-cols-3 gap-4 w-full mt-auto mb-20 pr-15">
        <HollowCard>
          <div className="p-4 w-50">
            <IoMdWifi className="text-accent text-3xl mb-2"/>
            <h1 className="font-bold text-2xl">
              2,400+
            </h1>
            <p className="text-secondary-content"> 
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
            <p className="text-secondary-content"> 
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
            <p className="text-secondary-content"> 
              Incidents Caught
            </p>
          </div>
        </HollowCard>
      </div>
    </div>

    <div className="flex w-full flex-1 items-center justify-center px-4 py-8 md:h-full md:w-1/2 md:px-0 md:py-0">
      <HollowCard className="h-fit w-full max-w-xl overflow-y-auto p-5 md:w-[60%] md:p-8">
        <h1 className="text-3xl font-bold text-base-content">
          Verify your account
        </h1>
        <p className="text-secondary-content text-md mt-2 mb-4">
          Check your email for the verification code
          </p>

        <form onSubmit={handleVerification}>
          <div className="flex justify-center my-8">
            <label className="otp otp-accent otp-xl">
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              <span></span>
              
              <input 
                type="text" 
                inputMode="numeric" 
                autoComplete="one-time-code" 
                maxLength={6}
                pattern="[0-9]*" 
                required
                value={code}
                onChange={(e)=>setCode(e.target.value)}
              />
            </label>
          </div>

          <button className="btn btn-primary w-full" disabled={submitted} type="submit">
            {submitted ?
              <span className="loading loading-spinner"></span>
              :
              "Verify"
            }
          </button>
        </form>
      </HollowCard>
    </div>
  </div>
  );
}
