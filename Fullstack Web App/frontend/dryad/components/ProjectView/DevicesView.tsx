"use client"

import GlowButton from "../GlowButton";
import DeviceCard from "../DeviceCard";
import { Device } from "@/app/home/project/page";
import { FaPlus } from "react-icons/fa";
import { ReactEventHandler, SubmitEventHandler, useEffect, useState } from "react";
import { IoIosWarning, IoMdWifi } from "react-icons/io";
import { RxCross2 } from "react-icons/rx";
import { IoCopy } from "react-icons/io5";
import { apiFetch } from "@/library/api";
import { copyTextToClipboard } from "@/library/general";
import { FaCheck } from "react-icons/fa6";
import { useRouter } from "next/navigation";
import { useToast } from "../ToastProvider";

interface DevicesViewProps {
    projectID : string | null;
    devices : Device[];
    setDevices : React.Dispatch<React.SetStateAction<Device[]>>
    canManage: boolean;
}


export default function DevicesView(props: DevicesViewProps) {
    const { showToast } = useToast();
    const [removeDeviceIndex, setRemoveDeviceIndex] = useState(-1);
    const [deviceCode, setDeviceCode] = useState<string>("");
    const [polling, setPolling] = useState<boolean>(false);
    const [connectionState, setConnectionState] = useState<"available" | "claimed" | "expired">("available");
    const [newDeviceName, setNewDeviceName] = useState("");
    const [newDeviceID, setNewDeviceID] = useState<number>(-1)

    const onlineDevices = props.devices.reduce(
        (count, device) => count + (device.status==="online" ? 1 : 0),
        0
    )

    const offlineDevices = props.devices.reduce(
        (count, device) => count + (device.status==="offline" ? 1 : 0),
        0
    )
    
    const closeModal = (id : string) => {
        const modal = document.getElementById(id) as HTMLDialogElement;
        modal.close();

        if (id === "deviceModal") {
            setPolling(false);
        }
    }

    const openDeviceModal = () => {
        const modal = document.getElementById('deviceModal') as HTMLDialogElement;
        modal.showModal();

        apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/connection_code`, {
            method : "POST"
        })
        .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
        })
        .then((data)=>{
            setDeviceCode(data.code);
            showToast(data.message ?? "Device connection code created.");
        })
        .then(()=>setPolling(true))
        .catch((error) => {
            console.error("Device connection code creation failed:", error);
            showToast("Unable to create a device connection code.", "error");
            closeModal("deviceModal");
        });
    }

    const openRemoveModal = (id : number)=>{
        const modal = document.getElementById('deleteModal') as HTMLDialogElement;
        setRemoveDeviceIndex(id);
        modal.showModal();
    }

    const renameDevice = async (id : number, newName : string) => {
        try {
            const response = await apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/devices/${id}/`, {
                method: "PATCH",
                body: JSON.stringify({ name: newName }),
            });
            if (!response.ok) throw new Error(await response.text());
            const data = await response.json();
            props.setDevices((devices) => devices.map((device) =>
                device.id === id ? { ...device, name: newName } : device
            ));
            setNewDeviceName("");
            showToast(data.message ?? "Device renamed successfully.");
        } catch (error) {
            console.error("Device rename failed:", error);
            showToast("Unable to rename this device.", "error");
        }
    }

    const removeDevice = async (id : number) => {
        try {
            const response = await apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/devices/${id}/`, {
                method: "DELETE",
            });
            if (!response.ok) throw new Error(await response.text());
            const data = await response.json();
            props.setDevices((devices) => devices.filter((device) => device.id !== id));
            showToast(data.message ?? "Device removed successfully.");
            closeModal("deleteModal");
        } catch (error) {
            console.error("Device removal failed:", error);
            showToast("Unable to remove this device.", "error");
        }
    }

    const toggleDevice = async (id : number) => {
        const device = props.devices.find((item) => item.id === id);
        if (!device) return;
        const newStatus = device.status === "online" ? "offline" : "online";
        try {
            const response = await apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/devices/${id}/`, {
                method: "PATCH",
                body: JSON.stringify({ status: newStatus }),
            });
            if (!response.ok) throw new Error(await response.text());
            const data = await response.json();
            props.setDevices((devices) => devices.map((item) =>
                item.id === id ? { ...item, status: newStatus } : item
            ));
            showToast(data.message ?? `Device set ${newStatus}.`);
        } catch (error) {
            console.error("Device status update failed:", error);
            showToast("Unable to update the device status.", "error");
        }
    }

    const changeNewDeviceName = (e : React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();

        closeModal("deviceModal")
        if(newDeviceName!==""){
            renameDevice(newDeviceID, newDeviceName);
        }
        setConnectionState("available");
    }

    const resetPolling = () => {
        setConnectionState("available");
        openDeviceModal();
    }

    const router = useRouter();

    useEffect(() => {
        if (!polling || !deviceCode) return;

        let cancelled = false;
        let timeoutId: ReturnType<typeof setTimeout>;

        const checkStatus = async () => {
            try {
                const response = await apiFetch(
                    `http://127.0.0.1:8000/api/devices/connect?code=${deviceCode}`
                );

                if (!response.ok) {
                    throw new Error(await response.text());
                }

                const data = await response.json();

                console.log(data.status);

                if (cancelled) return;

                if (data.status !== "available") {
                    setPolling(false);

                    if(data.status==="claimed"){
                        props.setDevices([...props.devices,
                            {
                                ...data.device,
                                lastSeen : data.device.last_seen
                            }
                        ])
                        setConnectionState(data.status);
                        setNewDeviceID(data.device.id);
                        showToast("Device connected successfully.");
                    }else if(data.status==="expired"){
                        setConnectionState(data.status);
                    }
                    return;
                }

                timeoutId = setTimeout(checkStatus, 1000);
            } catch (error) {
                console.error("Polling failed:", error);

                if (!cancelled) {
                    timeoutId = setTimeout(checkStatus, 1000);
                }
            }
        };

        checkStatus();

        return () => {
            cancelled = true;
            clearTimeout(timeoutId);
        };
    }, [polling, deviceCode]);

    const deviceModalContent = () => {
        if(connectionState==="available"){
            return (<>
            <p className="pt-4 text-base text-secondary-content">
                Power on your device and enter the following code to pair it to this project.
            </p>

            <div className="rounded-xl bg-base-300 flex flex-col gap-4 py-6 mt-4 items-center">
                <p className="font-semibold text-secondary-content text-sm">ENTER CODE</p>
                {deviceCode!=="" &&
                    <h1 className="font-mono text-accent text-4xl">{deviceCode}</h1>
                }
                <button className="btn btn-base-100 text-secondary-content"
                onClick={()=>copyTextToClipboard(deviceCode)}>
                    <IoCopy />
                    Copy Code
                </button>
            </div>

            <div className="bg-warning/15 flex flex-row items-center text-warning mt-4 p-2 rounded-xl px-4">
                This code is valid for 5 minutes
            </div>
            </>)
        }else if(connectionState==="claimed"){
            return (<>
                <div className="w-full max-w-md space-y-6">
                    <div className="flex items-center gap-3 rounded-2xl bg-primary/15 border border-primary/25 px-4 py-3.5 mt-4">
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary">
                            <FaCheck />
                        </div>
                        <span className="font-semibold text-primary">
                        Device paired successfully!
                        </span>
                    </div>

                    <p className="text-base leading-relaxed text-[#7c8c85]">
                        Code <strong className="font-bold text-white">{deviceCode}</strong> was
                        accepted. Give this device a name so you can identify it later.
                    </p>

                    <form onSubmit={changeNewDeviceName} className="space-y-6">
                        <div className="form-control w-full space-y-2">
                        <label className="label p-0">
                            <span className="label-text text-base font-medium text-[#7c8c85]">
                            Device Name <span className="text-[#55635d]">(optional)</span>
                            </span>
                        </label>
                        <input
                            type="text"
                            value={newDeviceName}
                            onChange={(e) => setNewDeviceName(e.target.value)}
                            placeholder={`Device-${deviceCode}`}
                            className="input input-bordered w-full rounded-2xl border-[#1e2924] bg-[#141b18] px-4 py-3 text-base text-[#a2b2aa] placeholder-[#4a5751] focus:border-[#22c55e] focus:outline-none"
                        />
                        </div>

                        <button
                        type="submit"
                        className="btn btn-primary w-full"
                        >
                        Confirm
                        </button>
                    </form>
                </div>
            </>);
        }else if(connectionState==="expired"){
            return (<>
            <p className="pt-4 text-base text-secondary-content mb-4">
                Your code has expired. Please try again with a different code.
            </p>
            <button className="btn btn-primary w-full"
            onClick={resetPolling}>
                Retry
            </button>
            </>);
        }
    }

    return (<>
        <dialog id="deleteModal" className="modal">
            <div className="modal-box bg-base-200 border border-white/8">
                <h3 className="font-bold text-lg">Remove Device</h3>
                <p className="pt-4 text-sm text-secondary-content">
                    This action will permanently disconnect this device from your project. 
                    To use it again, the device will need to be reconnected manually.
                </p>
                <div className="modal-action">
                <form onSubmit={(e)=>{
                        e.preventDefault()
                        removeDevice(removeDeviceIndex)}}>
                    <button type="submit" className="btn btn-error mr-2">Remove</button>
                    <button 
                    type="button"
                    onClick={()=>closeModal("deleteModal")} 
                        className="btn btn-secondary">Cancel</button>
                </form>
                </div>
            </div>
        </dialog>

        <dialog id="deviceModal" className="modal">
            <div className="modal-box bg-base-200 border border-white/8">
                <div className="flex flex-row justify-between border-b border-b-neutral pb-4">
                    <div className="flex gap-3 items-center">
                        <div className="border-accent/25 border text-accent rounded-xl text-xl bg-accent/15 p-2">
                            <IoMdWifi />
                        </div>
                        <h3 className="font-bold text-lg">Add Listening Device</h3>
                    </div>

                    <button 
                    type="button"
                    onClick={() => closeModal("deviceModal")} className="btn btn-secondary text-lg rounded-full p-3 m-0">
                        <RxCross2/>
                    </button>
                </div>
                
                {deviceModalContent()}
            </div>
        </dialog> 

        <div className="flex flex-row justify-between mx-6 mt-6">
            <h1 className="font-semibold text-lg">
                Listening Devices ({props.devices.length})
            </h1>

            <div className="flex flex-row items-center gap-4">
                <p className="text-accent">
                    {onlineDevices} online
                </p>

                <p className="text-[#6B7280]">
                    {offlineDevices} offline
                </p>

                {props.canManage && <GlowButton className="btn btn-accent" color="#4ADE80" onClick={openDeviceModal}>
                    <FaPlus />
                    Add Device
                </GlowButton>}
            </div>
        </div>

        {props.devices.length>0 ? 
        <div className="grid grid-cols-3 mx-6 mt-4 gap-4">
            {props.devices.map((device, index)=>{
                return <DeviceCard 
                device={device} 
                key={index} 
                deleteEvent={openRemoveModal}
                renameDevice={renameDevice}
                toggleDevice={toggleDevice}
                canManage={props.canManage}
                showOnMap={()=>router.push(`/home/project?pid=${props.projectID}&tab=forest_map&lat=${
                    device.location.coordinates[1]
                }&lng=${
                    device.location.coordinates[0]
                }`)}
                />
            })
            }
        </div>
        :
        <div className="w-full flex flex-col justify-center items-center text-secondary-content pt-20">
            <IoMdWifi className="text-4xl"/>
            
            <h1>No devices found</h1>
            <p className="text-sm">Add a device to start recording incidents</p>
        </div>
        }
    </>);
}