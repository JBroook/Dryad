"use client";

import L from "leaflet";
import { useEffect } from "react";
import type { RefObject } from "react";
import {
    FeatureGroup,
    MapContainer,
    Marker,
    Popup,
    TileLayer,
    useMap,
    GeoJSON,
} from "react-leaflet";
import type { FeatureGroup as LeafletFeatureGroup } from "leaflet";
import { EditControl } from "react-leaflet-draw";
import type { GeoJSON as GeoJSONType } from "geojson";
import "leaflet/dist/leaflet.css";
import "leaflet-draw/dist/leaflet.draw.css";

import { Device, IncidentType } from "@/app/home/project/page";
import getThreatIcon from "@/library/threatIcons";
import { renderToStaticMarkup } from "react-dom/server";
import IncidentPopup from "./IncidentPopup";
import { FaMicrophone } from "react-icons/fa6";
import DevicePopup from "./DevicePopup";

interface PatrolCreationMapProps {
    drawingEnabled: boolean;
    geoJSON: GeoJSONType | null;
    gridCells?: any;
    gridOpacity?: number;
    drawnItemsReference: RefObject<LeafletFeatureGroup | null>;
    incidents: IncidentType[];
    devices: Device[];
    pathCoordinates: [number, number][];
    handlePath: (coordinates: [number, number][]) => void;
}

export default function PatrolCreationMap({
    gridOpacity = 0.5,
    ...props
}: PatrolCreationMapProps) {
    useEffect(() => {
        const featureGroup = props.drawnItemsReference.current;

        if (!featureGroup) {
            return;
        }

        const drawnPathLayers: L.Polyline[] = [];
        featureGroup.eachLayer((layer) => {
            if (layer instanceof L.Polyline && !(layer instanceof L.Polygon)) {
                drawnPathLayers.push(layer);
            }
        });
        drawnPathLayers.forEach((layer) => featureGroup.removeLayer(layer));

        if (props.pathCoordinates.length >= 2) {
            featureGroup.addLayer(L.polyline(props.pathCoordinates));
        }
    }, [props.drawnItemsReference, props.pathCoordinates]);

    function GeoJSONLoader({
        geoJSON,
        featureGroupRef,
    }: {
        geoJSON: GeoJSONType | null;
        featureGroupRef: RefObject<LeafletFeatureGroup | null>;
    }) {
        const map = useMap();

        useEffect(() => {
            const featureGroup = featureGroupRef.current;

            if (!featureGroup) {
                return;
            }

            // Clear previously loaded geometry.
            featureGroup.clearLayers();

            if (!geoJSON) {
                return;
            }

            const geoJsonLayer = L.geoJSON(geoJSON);

            geoJsonLayer.eachLayer((layer) => {
                featureGroup.addLayer(layer);
            });

            // Fit the map to the loaded geometry.
            const bounds = featureGroup.getBounds();

            if (bounds.isValid()) {
                map.fitBounds(bounds, {
                    padding: [30, 30],
                });
            }
        }, [geoJSON, featureGroupRef, map]);

        return null;
    }

    // Called when a user finishes drawing a shape.
    function handleCreated(e: L.DrawEvents.Created) {
        if (e.layerType !== "polyline") {
            return;
        }

        const line = e.layer as L.Polyline;
        const points = line.getLatLngs() as L.LatLng[];

        // Leaflet coordinate order: [latitude, longitude].
        const coordinates: [number, number][] = points.map(
            (point) => [point.lat, point.lng]
        );

        // Send the completed path to the parent component.
        props.handlePath(coordinates);
    }

    const getRiskColor = (risk: number) => {
        if (risk >= 0.8) return "#d73027";
        if (risk >= 0.6) return "#fc8d59";
        if (risk >= 0.4) return "#fee08b";
        if (risk >= 0.2) return "#d9ef8b";
        return "#91cf60";
    };

    return (
        <div className="map w-full h-[500px] rounded-md overflow-hidden z-0">
            <MapContainer
                center={[52.51, 13.38]}
                zoom={6}
                scrollWheelZoom={true}
                className="w-full h-full"
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {/* Risk grid */}
                {props.gridCells && (
                    <GeoJSON
                        data={props.gridCells}
                        style={(feature) => {
                            const risk = Number(
                                feature?.properties?.risk_score ?? 0
                            );

                            return {
                                color: "#555",
                                weight: 1,
                                opacity: gridOpacity,
                                fillColor: getRiskColor(risk),
                                fillOpacity: gridOpacity * risk,
                            };
                        }}
                    />
                )}

                {/* Incident markers */}
                {props.incidents?.map(
                    (incident: IncidentType, index: number) => {
                        const Icon = getThreatIcon(
                            incident.threatClass.name
                        );

                        const incidentIcon = L.divIcon({
                            className: "",
                            html: renderToStaticMarkup(
                                <div className="p-2 bg-[#F59E0B] rounded-full">
                                    <Icon className="text-base-content text-base" />
                                </div>
                            ),
                            iconSize: [32, 32],
                            iconAnchor: [16, 16],
                        });

                        return (
                            <Marker
                                key={index}
                                position={[
                                    incident.coordinates.lng,
                                    incident.coordinates.lat,
                                ]}
                                icon={incidentIcon}
                            >
                                <Popup className="pb-4 incident-popup">
                                    <IncidentPopup incident={incident} />
                                </Popup>
                            </Marker>
                        );
                    }
                )}

                {/* Device markers */}
                {props.devices?.map(
                    (device: Device, index: number) => {
                        const deviceIcon = L.divIcon({
                            className: "",
                            html: renderToStaticMarkup(
                                <div className="p-2 bg-white rounded-full">
                                    <FaMicrophone className="text-accent text-base" />
                                </div>
                            ),
                            iconSize: [32, 32],
                            iconAnchor: [16, 16],
                        });

                        return (
                            <Marker
                                key={index}
                                position={[
                                    device.location.coordinates[1],
                                    device.location.coordinates[0],
                                ]}
                                icon={deviceIcon}
                            >
                                <Popup className="pb-4 incident-popup">
                                    <DevicePopup device={device} />
                                </Popup>
                            </Marker>
                        );
                    }
                )}

                {/* Drawing controls and loaded GeoJSON */}
                <FeatureGroup ref={props.drawnItemsReference}>
                    <GeoJSONLoader
                        geoJSON={props.geoJSON}
                        featureGroupRef={props.drawnItemsReference}
                    />

                    <EditControl
                        position="topright"
                        onCreated={handleCreated}
                        draw={{
                            rectangle: false,
                            polygon: false,
                            polyline: props.drawingEnabled,
                            circle: false,
                            marker: false,
                            circlemarker: false,
                        }}
                        edit={{
                            edit: false,
                            remove: false,
                        }}
                    />
                </FeatureGroup>
            </MapContainer>
        </div>
    );
}