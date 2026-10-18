import { useState } from "react";
import { FaLocationArrow, FaRegClock, FaRegUser } from "react-icons/fa6";
import { IoIosArrowDown, IoIosArrowUp } from "react-icons/io";
import { TbMapRoute } from "react-icons/tb";
import type { RoutinePatrol } from "./ProjectView/PatrolsView";
import { capitalizeFirstLetter, timeAgo } from "@/library/general";
import GlowButton from "./GlowButton";
import { FiExternalLink } from "react-icons/fi";

interface RoutinePatrolCardProps {
    patrol: RoutinePatrol;
}

export default function RoutinePatrolCard({ patrol }: RoutinePatrolCardProps) {
    const [isOpen, setIsOpen] = useState(false);
    const createdAt = new Date(patrol.created_at);
    const createdBy = patrol.created_by?.user;
    const coordinates = patrol.path.coordinates;
    const waypoints = coordinates.map(([longitude, latitude]) => `${latitude},${longitude}`);
    const navigationUrl = waypoints.length >= 2
        ? `https://www.google.com/maps/dir/?api=1&${new URLSearchParams({
            origin: waypoints[0],
            destination: waypoints[waypoints.length - 1],
            ...(waypoints.length > 2
                ? { waypoints: waypoints.slice(1, -1).join("|") }
                : {}),
            travelmode: "walking",
        }).toString()}`
        : undefined;

    return (
        <div className="collapse rounded-2xl w-full border border-2 border-white/5 px-2 bg-base-200 mb-4">
            <input
                type="checkbox"
                className="p-0"
                checked={isOpen}
                onChange={(event) => setIsOpen(event.target.checked)}
            />

            <div className="collapse-title flex flex-row items-center pr-4">
                <div className="h-full min-h-12 w-1 rounded-xs ml-2 my-1 bg-emerald-500" />
                <div className="p-3 rounded-xl border ml-4 bg-emerald-500/10 border-emerald-500/10">
                    <TbMapRoute className="text-xl text-emerald-500" />
                </div>

                <div className="ml-4">
                    <h1 className="font-semibold mb-1">{patrol.name}</h1>
                    <div className="flex flex-row items-center text-secondary-content text-sm">
                        <TbMapRoute className="mr-1" />
                        <p className="mr-3">{capitalizeFirstLetter(patrol.frequency)}</p>
                        <FaRegClock className="mr-1" />
                        <p>Starts {new Date(`${patrol.start_date}T00:00:00`).toLocaleDateString()}</p>
                    </div>
                </div>

                <div className="ml-auto flex flex-row items-center">
                    {isOpen
                        ? <IoIosArrowUp className="text-2xl text-secondary-content ml-4" />
                        : <IoIosArrowDown className="text-2xl text-secondary-content ml-4" />}
                </div>
            </div>

            <div className="collapse-content w-full">
                <h1 className="font-semibold text-secondary-content text-sm">PATROL DETAILS</h1>
                <div className="w-full flex mt-4">
                    <div className="flex-1 bg-base-300 rounded-xl p-4 mr-2">
                        <div className="flex gap-2 items-center">
                            <FaRegUser className="text-xs" />
                            <p className="text-secondary-content text-sm">Created By</p>
                        </div>
                        <h1 className="font-semibold mt-1">
                            {createdBy
                                ? `${createdBy.first_name} ${createdBy.last_name}`.trim()
                                : "Unknown"}
                        </h1>
                        {patrol.created_by?.role && (
                            <p className="text-sm text-secondary-content mt-1">
                                {capitalizeFirstLetter(patrol.created_by.role)}
                            </p>
                        )}
                    </div>

                    <div className="flex-1 bg-secondary rounded-xl p-4">
                        <div className="flex gap-2 items-center">
                            <FaRegClock className="text-xs" />
                            <p className="text-secondary-content text-sm">Created At</p>
                        </div>
                        <h1 className="font-semibold mt-1">{createdAt.toLocaleString("en-US")}</h1>
                        <p className="text-sm text-secondary-content mt-1">
                            {timeAgo(patrol.created_at)}
                        </p>
                    </div>
                </div>

                <div className="flex mt-4 justify-between items-center">
                    <p className="text-secondary-content text-sm">
                        Route · {coordinates.length} waypoints
                    </p>
                    {navigationUrl && (
                        <GlowButton
                            className="btn btn-secondary"
                            color="#60A5FA"
                            onClick={() => window.open(navigationUrl, "_blank", "noopener,noreferrer")}
                        >
                            <FaLocationArrow />
                            Navigate
                            <FiExternalLink />
                        </GlowButton>
                    )}
                </div>
            </div>
        </div>
    );
}
