import { Device } from "@/app/home/project/page";
import { capitalizeFirstLetter } from "@/lib/general";
import getThreatIcon from "@/lib/threatIcons";
import { FaMicrophone } from "react-icons/fa6";

interface DevicePopupProps {
    device : Device;
}

export default function DevicePopup(props : DevicePopupProps) {

    return (
    <>
        <div className="w-64 rounded-xl bg-base-300 p-4 shadow-2xl text-xs text-base-content">

            <div className="flex items-center justify-between pb-2 mb-3">
                <div className="flex items-center gap-2 text-base-content">
                    <FaMicrophone className="text-base"/>
                    <span className="font-semibold text-sm">{props.device.name}</span>
                </div>
            </div>
        </div>
    </>);
}