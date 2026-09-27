"use client";

import { useMap } from "react-leaflet";
import L from "leaflet";
import { useEffect } from "react";

interface MapLegendProps {
    showRiskHeatmap: boolean;
    showIncidents: boolean;
    showDevices: boolean;
}

export default function MapLegend({
    showRiskHeatmap,
    showIncidents,
    showDevices,
}: MapLegendProps) {
    const map = useMap();

    useEffect(() => {
        const Legend = L.Control.extend({
            onAdd: function () {
                const div = L.DomUtil.create(
                    "div",
                    "leaflet-control map-legend"
                );

                div.innerHTML = `
                    <div class="bg-base-200/95 backdrop-blur-sm rounded-lg border border-white/10 shadow-lg p-3 min-w-[180px]">
                        <div class="text-xs font-bold uppercase tracking-wider text-secondary-content mb-3">
                            Legend
                        </div>

                        ${
                            showRiskHeatmap
                                ? `
                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-4 h-4 rounded-sm" style="background:#91cf60"></div>
                                <span class="text-xs">Very Low Risk</span>
                            </div>

                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-4 h-4 rounded-sm" style="background:#d9ef8b"></div>
                                <span class="text-xs">Low Risk</span>
                            </div>

                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-4 h-4 rounded-sm" style="background:#fee08b"></div>
                                <span class="text-xs">Medium Risk</span>
                            </div>

                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-4 h-4 rounded-sm" style="background:#fc8d59"></div>
                                <span class="text-xs">High Risk</span>
                            </div>

                            <div class="flex items-center gap-2 mb-3">
                                <div class="w-4 h-4 rounded-sm" style="background:#d73027"></div>
                                <span class="text-xs">Very High Risk</span>
                            </div>
                        `
                                : ""
                        }

                        ${
                            showIncidents
                                ? `
                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-4 h-4 rounded-full bg-warning"></div>
                                <span class="text-xs">Incident</span>
                            </div>
                        `
                                : ""
                        }

                        ${
                            showDevices
                                ? `
                            <div class="flex items-center gap-2">
                                <div class="w-4 h-4 rounded-full bg-white border border-accent flex items-center justify-center">
                                    <span style="color:#4ADE80; font-size:9px;">●</span>
                                </div>
                                <span class="text-xs">Device</span>
                            </div>
                        `
                                : ""
                        }
                    </div>
                `;

                // Prevent clicks/scrolling in the legend from reaching the map
                L.DomEvent.disableClickPropagation(div);
                L.DomEvent.disableScrollPropagation(div);

                return div;
            },
        });

        const legend = new Legend({
            position: "bottomright",
        });

        legend.addTo(map);

        return () => {
            map.removeControl(legend);
        };
    }, [map, showRiskHeatmap, showIncidents, showDevices]);

    return null;
}
