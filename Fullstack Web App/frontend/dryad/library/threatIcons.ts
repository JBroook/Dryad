import { FaCircle, FaMicrophone, FaTree, FaTruck } from "react-icons/fa";
import type { IconType } from "react-icons";
import { TbEngineFilled } from "react-icons/tb";

type ThreatName = "Chainsaw" | "Vehicles" | "Treefall" | "Generator";

export default function getThreatIcon(name: string): IconType {
    const validNames: ThreatName[] = [
        "Chainsaw", "Vehicles", "Treefall", "Generator"
    ];

    const mapping: Record<ThreatName, IconType> = {
        Chainsaw: FaMicrophone,
        Vehicles: FaTruck,
        Treefall: FaTree,
        Generator: TbEngineFilled
    };

    if (validNames.includes(name as ThreatName)) {
        return mapping[name as ThreatName];
    }

    return FaCircle;
}