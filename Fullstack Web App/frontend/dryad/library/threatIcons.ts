import { FaCircle, FaFireAlt, FaMicrophone, FaTree, FaTruck } from "react-icons/fa";
import type { IconType } from "react-icons";
import { TbEngineFilled } from "react-icons/tb";
import { GiFireAxe, GiHandSaw } from "react-icons/gi";
import { FaGun } from "react-icons/fa6";

type ThreatName = "Chainsaw" | "Vehicles" | "Treefall" | "Generator" | "Handsaw" | "Fire" | "Gun Shot" | "Wood Chopping";

export default function getThreatIcon(name: string): IconType {
    const validNames: ThreatName[] = [
        "Chainsaw", "Vehicles", "Treefall", "Generator", "Handsaw", "Fire", "Gun Shot", "Wood Chopping"
    ];

    const mapping: Record<ThreatName, IconType> = {
        Chainsaw: FaMicrophone,
        Vehicles: FaTruck,
        Treefall: FaTree,
        Generator: TbEngineFilled,
        Handsaw : GiHandSaw,
        Fire : FaFireAlt,
        "Gun Shot" : FaGun,
        "Wood Chopping" : GiFireAxe 
    };

    if (validNames.includes(name as ThreatName)) {
        return mapping[name as ThreatName];
    }

    return FaCircle;
}