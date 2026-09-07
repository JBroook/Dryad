import { Device } from "@/app/home/project/page";
import { capitalizeFirstLetter } from "@/lib/general";
import getThreatIcon from "@/lib/threatIcons";
import { FaMicrophone } from "react-icons/fa6";

interface DevicePopupProps {
    device : Device;
}

export default function DevicePopup(props : DevicePopupProps) {
    // const date = new Date(props.incident.timestamp);
    // const formalDateTime = date.toLocaleString("en-US");
    // const Icon = getThreatIcon(props.incident.threatClass.name)

    return (
    <>
        <div className="w-64 rounded-xl bg-base-300 p-4 shadow-2xl text-xs text-base-content">

            <div className="flex items-center justify-between pb-2 mb-3">
                <div className="flex items-center gap-2 text-base-content">
                    <FaMicrophone className="text-base"/>
                    <span className="font-semibold text-sm">{props.device.name}</span>
                </div>
            </div>

            {/* <div className="mb-3">
                <div className="flex justify-between text-[11px] mb-1">
                    <span>Confidence</span>
                    <span className="font-mono font-bold">{props.incident.confidence}%</span>
                </div>
                <progress className="progress progress-primary w-full mt-2" value={props.incident.confidence} max="100"></progress>
            </div>

            <div className="space-y-1.5">
                <div className="flex justify-between">
                <span>Detected:</span>
                <span>{formalDateTime}</span>
                </div>
                <div className="flex justify-between items-center">
                <span>Status:</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium">
                    {capitalizeFirstLetter(props.incident.status)}
                </span>
                </div>
            </div> */}
        </div>
    </>);
}