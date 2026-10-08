"use client"

import NotificationOption from "@/components/NotificationOption";
import ThemeButton from "@/components/ThemeButton";
import { useTheme } from "next-themes";
import { BsFillLightningChargeFill } from "react-icons/bs";
import { MdEmail, MdOutlineDarkMode, MdOutlineLightMode } from "react-icons/md";

export default function Settings() {
  const {theme, setTheme} = useTheme();
  
  return (<>
    <div className="w-full py-5 pl-8 border-b-white/8 border-b border-b-width-[2px] flex flex-row items-center justify-between ">
      <div>
        <h1 className="font-bold text-2xl">
          Settings
        </h1>
        <p className="text-sm text-secondary-content">
          Configure system-wide preferences
        </p>
      </div>
    </div>

    <div className="mx-8 mt-6">
      <h1 className="font-semibold text-lg">Appearance</h1>
      <p className="text-secondary-content text-sm">Customize how Dryad looks on your device</p>

      <div className="card bg-base-200 rounded-2xl border border-white/8 mt-4">
        <div className="card-body">
          <h2 className="card-title text-base">Theme</h2>

          <div className="flex gap-4">
            <ThemeButton
              name="Light"
              icon={MdOutlineLightMode}
              colorOne="#EAF4EE"
              colorTwo="#F7FAF8"
              colorThree="#1F7A4C"
              onClick={() => setTheme("mytheme-light")}
              active={theme==="mytheme-light"}
            />
            <ThemeButton
              name="Dark"
              icon={MdOutlineDarkMode}
              colorOne="#18231D"
              colorTwo="#121A15"
              colorThree="#22C55E"
              onClick={() => setTheme("mytheme-dark")}
              active={theme==="mytheme-dark"}
            />
          </div>
        </div>
      </div>

      <h1 className="font-semibold text-lg mt-6">Notifications</h1>
      <p className="text-secondary-content text-sm">Control how and when you receive incident alerts</p>

      <div className="card bg-base-200 rounded-2xl border border-white/8 mt-4">
        <div className="card-body">
          <NotificationOption 
            title="Email Alerts"
            description="Receive incidents via email"
            icon={MdEmail}
            state={true}
            onChange={()=>{}}
          />
          <div className="divider"></div>
          <NotificationOption 
            title="Critical Incidents Only"
            description="Suppress medium and low severity alerts"
            icon={BsFillLightningChargeFill}
            state={true}
            onChange={()=>{}}
          />
        </div>
      </div>
    </div>
  </>);
}
