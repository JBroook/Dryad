"use client"

import L from 'leaflet';
import { Ref, RefObject, useEffect, useRef, useState } from 'react';
import { FeatureGroup, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import type { LatLng, FeatureGroup as LeafletFeatureGroup } from "leaflet";
import { EditControl } from 'react-leaflet-draw';
import type { GeoJSON as GeoJSONType} from 'geojson';
import { GeoJSON } from "react-leaflet";

import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet/dist/leaflet.css';
import { Device, IncidentType } from '@/app/home/project/page';
import getThreatIcon from '@/lib/threatIcons';
import { renderToStaticMarkup } from 'react-dom/server';
import IncidentPopup from './IncidentPopup';
import { FaMicrophone } from 'react-icons/fa6';
import DevicePopup from './DevicePopup';
import MapLegend from './MapLegend';

interface ForestMapFullProps {
    latitude : number | null;
    longitude : number | null;
    drawingEnabled : boolean;
    geoJSON : GeoJSONType | null;
    gridCells? : any;
    gridOpacity? : number;
    drawnItemsReference : RefObject<LeafletFeatureGroup | null>;
    incidents : IncidentType[];
    enableIncidents : boolean;
    devices : Device[];
    enableDevices : boolean;
}

export default function ForestMapFull({
    gridOpacity = 0.5,
    ...props
}: ForestMapFullProps) {
    const position = L.latLng(52.51, 13.38);

    function MapController({
        location,
        hasGeoJSON,
    }: {
        location: { lat: number; lon: number } | null;
        hasGeoJSON: boolean;
    }) {
        const map = useMap();

        useEffect(() => {
            if (location && !hasGeoJSON) {
                map.setView(
                    [location.lat, location.lon],
                    13
                );
            }
        }, [location, hasGeoJSON, map]);

        return null;
    }

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

            // Remove previously loaded geometry
            featureGroup.clearLayers();

            if (!geoJSON) {
                return;
            }

            const geoJsonLayer = L.geoJSON(geoJSON);

            geoJsonLayer.eachLayer((layer) => {
                featureGroup.addLayer(layer);
            });


            // Center to lat and lng if provided
            if (props.latitude!=null && props.longitude!=null){
                map.setView(
                    [props.latitude, props.longitude],
                    16
                );
            }else{
                // Center/zoom map around the loaded shape
                const bounds = featureGroup.getBounds();

                if (bounds.isValid()) {
                    map.fitBounds(bounds, {
                        padding: [30, 30],
                    });
                }
            }

        }, [geoJSON, featureGroupRef, map]);

        return null;
    }

    const getRiskColor = (risk: number) => {
        if (risk >= 0.8) return "#d73027"; // very high
        if (risk >= 0.6) return "#fc8d59"; // high
        if (risk >= 0.4) return "#fee08b"; // medium
        if (risk >= 0.2) return "#d9ef8b"; // low
        return "#91cf60";                  // very low
    };

    return ( 
    <div className="map w-full h-[500px] rounded-md overflow-hidden z-0">
        <MapContainer 
            zoom={6} 
            scrollWheelZoom={true}>

            <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* <MapController
                location={{
                    lat: props.latitude,
                    lon: props.longitude
                }}
                hasGeoJSON={props.geoJSON !== null}
            /> */}

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
                            fillOpacity: gridOpacity*risk,
                        };
                    }}
                />
            )}


            {props.enableIncidents && props.incidents?.map((incident : IncidentType, index)=>{
                const Icon = getThreatIcon(incident.threatClass.name);

                const incidentIcon = L.divIcon({
                    className: "",
                    html: renderToStaticMarkup(
                        <div className='p-2 bg-warning rounded-full'>
                            <Icon className="text-base-content text-base"/>
                        </div>
                    ),
                    iconSize: [32, 32],
                    iconAnchor: [16, 16],
                });

                return (<Marker
                        key={index}
                        position={[incident.coordinates.lng, incident.coordinates.lat]}
                        icon={incidentIcon}
                    >
                        <Popup className='pb-4 incident-popup'>
                            <IncidentPopup incident={incident}/>
                        </Popup>
                    </Marker>)
                })
            }

            {props.enableDevices && props.devices?.map((device : Device, index)=>{

                const incidentIcon = L.divIcon({
                    className: "",
                    html: renderToStaticMarkup(
                        <div className='p-2 bg-white rounded-full'>
                            <FaMicrophone className="text-accent text-base"/>
                        </div>
                    ),
                    iconSize: [32, 32],
                    iconAnchor: [16, 16],
                });

                return (<Marker
                        key={index}
                        position={[device.location.coordinates[1], device.location.coordinates[0]]}
                        icon={incidentIcon}
                    >
                        <Popup className='pb-4 incident-popup'>
                            <DevicePopup device={device}/>
                        </Popup>
                    </Marker>)
                })
            }

            <FeatureGroup ref={props.drawnItemsReference}>
                <GeoJSONLoader
                    geoJSON={props.geoJSON}
                    featureGroupRef={props.drawnItemsReference}
                />

                <EditControl
                    position="topright"
                    draw={{
                        rectangle: props.drawingEnabled,
                        polygon: props.drawingEnabled,
                        circle: false,
                        marker: false,
                        polyline: false,
                        circlemarker: false,
                    }}
                    edit={{
                        edit :  false,
                        remove : false
                    }}
                />
            </FeatureGroup>

            <MapLegend
                showRiskHeatmap={!!props.gridCells && gridOpacity > 0}
                showIncidents={props.enableIncidents}
                showDevices={props.enableDevices}
            />
        </MapContainer>
    </div>);
}