import { useState } from "react";
import { FaDownload, FaRegClock, FaRegUser } from "react-icons/fa6";
import { IoIosArrowDown, IoIosArrowUp } from "react-icons/io";
import { TbMapRoute } from "react-icons/tb";
import type { RoutinePatrol } from "./ProjectView/PatrolsView";
import { capitalizeFirstLetter, timeAgo } from "@/library/general";
import GlowButton from "./GlowButton";
import { FiExternalLink } from "react-icons/fi";
import { apiFetch } from "@/library/api";

interface RoutinePatrolCardProps {
    patrol: RoutinePatrol;
}

export default function RoutinePatrolCard({ patrol }: RoutinePatrolCardProps) {
    const [isOpen, setIsOpen] = useState(false);
    const createdAt = new Date(patrol.created_at);
    const createdBy = patrol.created_by?.user;
    const coordinates = patrol.path.coordinates;
    const [isExporting, setIsExporting] = useState(false);
    const [exportError, setExportError] = useState("");

    const exportGPX = async () => {
        setIsExporting(true);
        setExportError("");
        try {
            const response = await apiFetch(
                `projects/${patrol.project.id}/routine_patrols/${patrol.id}/export/`
            );
            if (!response.ok) {
                throw new Error(await response.text());
            }

            const gpxFile = await response.blob();
            const downloadUrl = URL.createObjectURL(gpxFile);
            const link = document.createElement("a");
            link.href = downloadUrl;
            link.download = `routine-patrol-${patrol.id}.gpx`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
        } catch (error) {
            setExportError(
                error instanceof Error ? error.message : "Unable to export this patrol."
            );
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="collapse rounded-2xl w-full border border-2 border-white/5 px-2 bg-base-200 mb-4">
            <input
                type="checkbox"
                className="p-0"
                checked={isOpen}
                onChange={(event) => setIsOpen(event.target.checked)}
            />

            <div className="collapse-title flex flex-row items-center pr-2 md:pr-4">
                <div className="my-1 ml-1 h-full min-h-12 w-1 rounded-xs bg-emerald-500 md:ml-2" />
                <div className="ml-2 rounded-xl border border-emerald-500/10 bg-emerald-500/10 p-2 md:ml-4 md:p-3">
                    <TbMapRoute className="text-xl text-emerald-500" />
                </div>

                <div className="ml-2 min-w-0 flex-1 md:ml-4">
                    <h1 className="font-semibold mb-1">{patrol.name}</h1>
                    <div className="flex flex-wrap items-center text-secondary-content text-xs md:flex-row md:text-sm">
                        <TbMapRoute className="mr-1" />
                        <p className="mr-3">{capitalizeFirstLetter(patrol.frequency)}</p>
                        <FaRegClock className="mr-1" />
                        <p>Starts {new Date(`${patrol.start_date}T00:00:00`).toLocaleDateString()}</p>
                    </div>
                </div>

                <div className="ml-auto flex shrink-0 flex-row items-center">
                    {isOpen
                        ? <IoIosArrowUp className="text-2xl text-secondary-content ml-4" />
                        : <IoIosArrowDown className="text-2xl text-secondary-content ml-4" />}
                </div>
            </div>

            <div className="collapse-content w-full">
                <h1 className="font-semibold text-secondary-content text-sm">PATROL DETAILS</h1>
                <div className="mt-4 flex w-full flex-col gap-2 md:flex-row">
                    <div className="flex-1 rounded-xl bg-base-300 p-4 md:mr-2">
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

                    <div className="flex-1 rounded-xl bg-secondary p-4">
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
                    {coordinates.length >= 2 && (
                        <GlowButton
                            className="btn btn-secondary"
                            color="#60A5FA"
                            onClick={exportGPX}
                            disabled={isExporting}
                        >
                            <FaDownload />
                            {isExporting ? "Exporting..." : "Export"}
                            <FiExternalLink />
                        </GlowButton>
                    )}
                </div>
                {exportError && <p role="alert" className="text-error text-sm mt-2">{exportError}</p>}
            </div>
        </div>
    );
}
