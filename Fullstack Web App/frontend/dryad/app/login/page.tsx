"use client"

import HollowCard from "@/components/HollowCard";
import { IoMdWifi } from "react-icons/io";
import { FiShield } from "react-icons/fi";
import { BsTree } from "react-icons/bs";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useToast } from "@/components/ToastProvider";

const registerSchema = z
  .object({
    firstName: z
      .string()
      .min(1, "First name is required"),

    lastName: z
      .string()
      .min(1, "Last name is required"),

    email: z
      .email("Please enter a valid email address"),

    password: z
      .string()
      .min(8, "Password must be at least 8 characters"),

    retypePassword: z
      .string()
      .min(1, "Please retype your password"),
  })
  .refine((data) => data.password === data.retypePassword, {
    message: "Passwords must match",
    path: ["retypePassword"],
  });

type RegisterForm = z.infer<typeof registerSchema>;

export default function Login() {
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [isLogin, setIsLogin] = useState<boolean>(true);


  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    mode: "onBlur",
  });

  const router = useRouter();
  const { showToast } = useToast();

  const handleLogin: React.SubmitEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    setSubmitted(true);
    
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    const res = await fetch(`${API_URL}/login/`, {
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
    showToast("Welcome back!")
  }

  const handleRegister = async (data: RegisterForm) => {
    setSubmitted(true);
    const API_URL = process.env.NEXT_PUBLIC_API_URL;
    const res = await fetch(`${API_URL}/register/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        first_name : data.firstName,
        last_name : data.lastName,
        email : data.email,
        password : data.password,
      }),
    });

    if (!res.ok) {
      const backendErrors = await res.json();

      for (const [field, messages] of Object.entries(backendErrors)) {
        if (field in data) {
          setError(field as keyof RegisterForm, {
            type: "server",
            message: Array.isArray(messages)
              ? messages.join(" ")
              : String(messages),
          });
        }
      }
      return;
    }

    const responseData = await res.json();
    showToast(responseData.message ?? "Account created successfully.");
    router.push(`/login/verify?email=${data.email}`)
  };

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
      <HollowCard className="h-fit w-full max-w-xl overflow-y-auto p-5 md:h-2/3 md:w-[60%] md:p-8">
        <h1 className="text-3xl font-bold text-base-content">
          {isLogin ? "Welcome back" : "Create an account"}
        </h1>
        <p className="text-secondary-content text-md mt-2 mb-4">
          {isLogin ? "Sign into your monitoring dashboard" : "Start protecting forests today"}
          </p>

        <div role="tablist" className="tabs tabs-box bg-base-200 w-full border border-base-300">
          <a role="tab" className={`tab flex-1 ${isLogin ? "text-accent bg-base-300 tab-active" : "text-secondary-content"}`}
          onClick={()=>setIsLogin(true)}>
            Sign in
          </a>
          <a role="tab" className={`tab flex-1 ${!isLogin ? "text-accent bg-base-300 tab-active" : "text-secondary-content"}`}
          onClick={()=>setIsLogin(false)}>
            Register
          </a>
        </div>

        {isLogin ?
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
              href="/login/forgot-password"
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
          :
          <form
            className="flex flex-col max-w-md mx-auto space-y-4"
            onSubmit={handleSubmit(handleRegister)}
          >
            <fieldset className="fieldset">
              <legend className="fieldset-legend font-medium text-secondary-content">
                First Name
              </legend>

              <input
                type="text"
                className={`input w-full bg-base-200 text-base-content ${
                  errors.firstName ? "input-error" : "border-base-300"
                }`}
                placeholder="Jane"
                {...register("firstName")}
              />

              {errors.firstName && (
                <p className="text-error text-sm mt-1">
                  {errors.firstName.message}
                </p>
              )}
            </fieldset>

            <fieldset className="fieldset">
              <legend className="fieldset-legend font-medium text-secondary-content">
                Last Name
              </legend>

              <input
                type="text"
                className={`input w-full bg-base-200 text-base-content ${
                  errors.lastName ? "input-error" : "border-base-300"
                }`}
                placeholder="Smith"
                {...register("lastName")}
              />

              {errors.lastName && (
                <p className="text-error text-sm mt-1">
                  {errors.lastName.message}
                </p>
              )}
            </fieldset>

            <fieldset className="fieldset">
              <legend className="fieldset-legend font-medium text-secondary-content">
                Email Address
              </legend>

              <input
                type="email"
                className={`input w-full bg-base-200 text-base-content ${
                  errors.email ? "input-error" : "border-base-300"
                }`}
                placeholder="you@organization.org"
                {...register("email")}
              />

              {errors.email && (
                <p className="text-error text-sm mt-1">
                  {errors.email.message}
                </p>
              )}
            </fieldset>

            <fieldset className="fieldset">
              <legend className="fieldset-legend font-medium text-secondary-content">
                Password
              </legend>

              <input
                type="password"
                className={`input w-full bg-base-200 text-base-content ${
                  errors.password ? "input-error" : "border-base-300"
                }`}
                placeholder="••••••••"
                {...register("password")}
              />

              {errors.password && (
                <p className="text-error text-sm mt-1">
                  {errors.password.message}
                </p>
              )}
            </fieldset>

            <fieldset className="fieldset">
              <legend className="fieldset-legend font-medium text-secondary-content">
                Retype Password
              </legend>

              <input
                type="password"
                className={`input w-full bg-base-200 text-base-content ${
                  errors.retypePassword ? "input-error" : "border-base-300"
                }`}
                placeholder="••••••••"
                {...register("retypePassword")}
              />

              {errors.retypePassword && (
                <p className="text-error text-sm mt-1">
                  {errors.retypePassword.message}
                </p>
              )}
            </fieldset>

            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="loading loading-spinner" />
              ) : (
                "Register"
              )}
            </button>
          </form>
        }
      </HollowCard>
    </div>
  </div>
  );
}
