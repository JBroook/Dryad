"use client"

import GlowButton from "../GlowButton";
import DeviceCard from "../DeviceCard";
import { Device } from "@/app/home/project/page";
import { FaPlus } from "react-icons/fa";
import { useState } from "react";
import { IoMdWifi } from "react-icons/io";
import { RxCross2 } from "react-icons/rx";
import { IoCopy } from "react-icons/io5";

interface DevicesViewProps {
    projectID : string | null;
    devices : Device[];
}


export default function DevicesView(props: DevicesViewProps) {
    const [onlineDevices, setOnlineDevices] = useState<number>(2)
    const [offlineDevices, setOfflineDevices] = useState<number>(0)

    
    const closeModal = (id : string) => {
        const modal = document.getElementById(id) as HTMLDialogElement;
        modal.close();
    }

    const openDeviceModal = () => {
        const modal = document.getElementById('deviceModal') as HTMLDialogElement;
        modal.showModal();
    }

    const openRemoveModal = (index : number)=>{
        const modal = document.getElementById('deleteModal') as HTMLDialogElement;
        modal.showModal();
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
                <form onSubmit={()=>{}}>
                    <button type="submit" className="btn btn-error mr-2">Remove</button>
                    <button 
                    type="button"
                    onClick={() => closeModal("deleteModal")} className="btn btn-secondary">Cancel</button>
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
                <p className="pt-4 text-base text-secondary-content">
                    Power on your device and enter the following code to pair it to this project.
                </p>

                <div className="rounded-xl bg-base-300 flex flex-col gap-4 py-6 mt-4 items-center">
                    <p className="font-semibold text-secondary-content text-sm">ENTER CODE</p>
                    <h1 className="font-mono text-accent text-4xl">P7N-L8Q</h1>
                    <button className="btn btn-base-100 text-secondary-content">
                        <IoCopy />
                        Copy Code
                    </button>
                </div>

                <div className="bg-warning/15 flex flex-row items-center text-warning mt-4 p-2 rounded-xl">
                    <span className="loading loading-spinner mr-2"/>
                    Waiting for device to connect...
                </div>
            </div>
        </dialog> 

        <div className="flex flex-row justify-between mx-6 mt-6">
            <h1 className="font-semibold text-lg">
                Listening Devices (5)
            </h1>

            <div className="flex flex-row items-center gap-4">
                <p className="text-accent">
                    {onlineDevices} online
                </p>

                <p className="text-[#6B7280]">
                    {offlineDevices} offline
                </p>

                <GlowButton className="btn btn-accent" color="#4ADE80" onClick={openDeviceModal}>
                    <FaPlus />
                    Add Device
                </GlowButton>
            </div>
        </div>

        <div className="grid grid-cols-3 mx-6 mt-4">
            {props.devices.map((device, index)=>{
                return <DeviceCard device={device} key={index} deleteEvent={openRemoveModal}/>
            })
            }
        </div>
    </>);
}