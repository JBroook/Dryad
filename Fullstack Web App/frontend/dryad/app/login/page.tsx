"use client"

import HollowCard from "@/components/HollowCard";
import { IoMdWifi } from "react-icons/io";
import { FiShield } from "react-icons/fi";
import { BsTree } from "react-icons/bs";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Login() {
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");

  const APIBase = "http://127.0.0.1:8000/api";
  // const APIBase = "http://192.168.100.7:8000/api";

  const router = useRouter();

  const handleLogin: React.SubmitEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    setSubmitted(true);
    
    const res = await fetch(`${APIBase}/login/`, {
      method: "POST",
      headers: {
        "Content-Type" : "application/json"
      },
      body: JSON.stringify({
        email,
        password
      })
    })

    if(!res.ok){
      alert("Invalid Credentials");
      setSubmitted(false);
      return;
    }

    const data = await res.json();

    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    localStorage.setItem("userID", data.user.id);

    router.push("/home/projects");
  }

  return (
  <div className="flex flex-row w-screen h-screen bg-base-100 text-base-content">
    <div className="flex flex-col w-1/2 h-full pt-10 pl-10 bg-base-200/80 bg-[url('/assets/login_graphic.svg')] bg-contain bg-bottom bg-no-repeat border-r border-base-300">
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

    <div className="flex w-1/2 h-full items-center justify-center">
      <HollowCard className="p-8 w-[60%] max-w-xl">
        <h1 className="text-3xl font-bold text-base-content">Welcome back</h1>
        <p className="text-secondary-content text-md mt-2 mb-4">Sign into your monitoring dashboard</p>

        <div role="tablist" className="tabs tabs-box bg-base-200 w-full border border-base-300">
          <a role="tab" className="tab flex-1 text-accent bg-base-300 tab-active ">
            Sign in
          </a>
          <a role="tab" className="tab flex-1 text-secondary-content ">
            Register
          </a>
        </div>

        <form className="flex flex-col max-w-md mx-auto space-y-4" onSubmit={handleLogin}>
          <fieldset className="fieldset">
            <legend className="fieldset-legend font-medium text-secondary-content">Email Address</legend>
            <input
              type="email"
              className="input w-full bg-base-200 border border-base-300 text-base-content"
              placeholder="you@example.com"
              value={email}
              onChange={(e)=>setEmail(e.target.value)}
            />
          </fieldset>

          <fieldset className="fieldset">
            <legend className="fieldset-legend font-medium text-secondary-content">Password</legend>
            <input
              type="password"
              className="input w-full bg-base-200 border border-base-300 text-base-content"
              placeholder="••••••••"
              value={password}
              onChange={(e)=>setPassword(e.target.value)}
            />
          </fieldset>

          <a
            href="/forgot-password"
            className="link link-hover text-sm self-end text-accent"
          >
            Forgot password?
          </a>

          <button className="btn btn-primary w-full" disabled={submitted}>
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
