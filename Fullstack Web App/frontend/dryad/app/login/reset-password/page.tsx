"use client"

import HollowCard from "@/components/HollowCard";
import { IoMdWifi } from "react-icons/io";
import { FiShield } from "react-icons/fi";
import { BsTree } from "react-icons/bs";
import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useToast } from "@/components/ToastProvider";

const resetPasswordSchema = z
  .object({
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

type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;

export default function ForgotPassword() {
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [email, setEmail] = useState<string>("");

  const APIBase = "http://127.0.0.1:8000/api";
  // const APIBase = "http://192.168.100.7:8000/api";

  const searchParams = useSearchParams();

  const router = useRouter();
  const { showToast } = useToast();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema),
    mode: "onBlur",
  });

  const handlePasswordReset = async (data: ResetPasswordForm) => {
    setSubmitted(true);
    const res = await fetch(`${APIBase}/reset_password/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        password : data.password,
        password_confirm : data.retypePassword,
        token : searchParams.get("token")
      }),
    });

    if (!res.ok) {
      const backendErrors = await res.json();

      for (const [field, messages] of Object.entries(backendErrors)) {
        if (field in data) {
          setError(field as keyof ResetPasswordForm, {
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
    showToast(responseData.message ?? "Password reset successfully.");
    router.push(`/login`)
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
      <HollowCard className="h-fit w-full max-w-xl overflow-y-auto p-5 md:w-[60%] md:p-8">
        <h1 className="text-3xl font-bold text-base-content">
          New Password
        </h1>
        <p className="text-secondary-content text-md mt-2 mb-4">
          Enter a new password for your account
          </p>
        <form onSubmit={handleSubmit(handlePasswordReset)}>
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

          <button className="btn btn-primary w-full mt-6" disabled={submitted} type="submit">
            {submitted ?
              <span className="loading loading-spinner"></span>
              :
              "Submit"
            }
          </button>
        </form>
      </HollowCard>
    </div>
  </div>
  );
}
