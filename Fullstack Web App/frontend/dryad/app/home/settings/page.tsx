"use client"

import NotificationOption from "@/components/NotificationOption";
import ThemeButton from "@/components/ThemeButton";
import { apiFetch } from "@/library/api";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { BsFillLightningChargeFill } from "react-icons/bs";
import { FaPlus } from "react-icons/fa6";
import { MdEmail, MdOutlineDarkMode, MdOutlineLightMode } from "react-icons/md";
import { useToast } from "@/components/ToastProvider";

export default function Settings() {
  const { showToast } = useToast();
  const {theme, setTheme} = useTheme();
  const [mode, setMode] = useState<boolean>(false);
  const [emailAlerts, setEmailAlerts] = useState<boolean | null>(null);
  const [criticalIncidentsOnly, setCriticalIncidentsOnly] = useState<boolean | null>(null);

  const handleEmailSetting = async (e : React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.checked;
    try {
      const response = await apiFetch(`users/settings`, {
        method: "PATCH",
        body: JSON.stringify({ receive_emails: value }),
      });
      if (!response.ok) throw new Error(await response.text());
      setEmailAlerts(value);
      const data = await response.json();
      showToast(data.message ?? "Email alert settings saved.");
    } catch (err) {
      console.error("Email alert settings update failed:", err);
      showToast("Unable to save email alert settings.", "error");
    }
  }

  const handleCriticalIncidentsSetting = async (e : React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.checked;
    try {
      const response = await apiFetch(`users/settings`, {
        method: "PATCH",
        body: JSON.stringify({ critical_incidents_only: value }),
      });
      if (!response.ok) throw new Error(await response.text());
      setCriticalIncidentsOnly(value);
      const data = await response.json();
      showToast(data.message ?? "Incident alert settings saved.");
    } catch (err) {
      console.error("Incident alert settings update failed:", err);
      showToast("Unable to save incident alert settings.", "error");
    }
  }

  useEffect(()=>{
    setMode(theme==="mytheme-light")

    // fetch user's settings
    apiFetch(`users/settings`)
    .then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    })
    .then((data)=>{console.log(data); return data})
    .then((data)=>{
      setEmailAlerts(data.receive_emails)
      setCriticalIncidentsOnly(data.critical_incidents_only)
    })
    .catch((err) => console.error("Fetch failed:", err));
  }, [theme])
  
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

    <div className="mx-8 mt-6 mb-30">
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
              active={mode}
            />
            <ThemeButton
              name="Dark"
              icon={MdOutlineDarkMode}
              colorOne="#18231D"
              colorTwo="#121A15"
              colorThree="#22C55E"
              onClick={() => setTheme("mytheme-dark")}
              active={!mode}
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
            onChange={handleEmailSetting}
            active={emailAlerts}
          />
          <div className="divider"></div>
          <NotificationOption 
            title="Invite Emails"
            description="Receive notifications about invites to new projects"
            icon={FaPlus}
            state={true}
            onChange={handleEmailSetting}
            active={emailAlerts}
          />
          <div className="divider"></div>
          <NotificationOption 
            title="Critical Incidents Only"
            description="Only get notified for high confidence incidents"
            icon={BsFillLightningChargeFill}
            state={true}
            onChange={handleCriticalIncidentsSetting}
            active={criticalIncidentsOnly}
          />
        </div>
      </div>
    </div>
  </>);
}
