"use client"

import L from 'leaflet';
import { Ref, RefObject, useEffect, useRef, useState } from 'react';
import { FeatureGroup, MapContainer, TileLayer, useMap } from 'react-leaflet'
import type { LatLng, FeatureGroup as LeafletFeatureGroup } from "leaflet";
import { EditControl } from 'react-leaflet-draw';
import type { GeoJSON as GeoJSONType} from 'geojson';
import { GeoJSON } from "react-leaflet";
import * as turf from "@turf/turf";

import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import 'leaflet/dist/leaflet.css';

interface ForestMapProps {
    searchValue : string;
    latitude : number;
    longitude : number;
    handleArea : (area : GeoJSONType, surfaceArea : number, center : LatLng) => void;
    drawingEnabled : boolean;
    drawnItemsReference : RefObject<LeafletFeatureGroup | null>;
    geoJSON : GeoJSONType | null;
    editEnabled : boolean;
    gridCells? : any;
    gridOpacity? : number;
}

export default function ForestMap({
    gridOpacity = 0.5,
    ...props
}: ForestMapProps) {
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

            // Center/zoom map around the loaded shape
            const bounds = featureGroup.getBounds();

            if (bounds.isValid()) {
                map.fitBounds(bounds, {
                    padding: [30, 30],
                });
            }
        }, [geoJSON, featureGroupRef, map]);

        return null;
    }

    const handleRegionCreation = (e : L.DrawEvents.Created) => {
        const polygon = e.layer;

        if ('getLatLngs' in polygon && typeof polygon.getLatLngs === 'function') {
            const geoJSON = polygon.toGeoJSON();

            const geoJsonLayer = L.geoJSON(geoJSON);
            const center = geoJsonLayer.getBounds().getCenter();

            const areaKMSquare = Math.round(turf.area(geoJSON)/1_000_000);

            props.handleArea(geoJSON, areaKMSquare, center);
        }
    }

    const handleRegionEdit = (e : L.DrawEvents.Edited) => {
        e.layers.eachLayer((layer) => {
            if (layer instanceof L.Polygon) {
                const geoJSON = layer.toGeoJSON();

                const geoJsonLayer = L.geoJSON(geoJSON);
                const center = geoJsonLayer.getBounds().getCenter();

                const areaKMSquare = Math.round(turf.area(geoJSON)/1_000_000);

                props.handleArea(geoJSON, areaKMSquare, center);
            }
        });
    }

    return ( 
    <div className="map w-full h-[500px] rounded-md overflow-hidden z-0">
        <MapContainer 
            center={position} 
            zoom={6} 
            scrollWheelZoom={true}>

            <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <MapController
                location={{
                    lat: props.latitude,
                    lon: props.longitude
                }}
                hasGeoJSON={props.geoJSON !== null}
            />

            {props.gridCells && (
                <GeoJSON
                    data={props.gridCells}
                    style={{
                        color: "red",
                        opacity : gridOpacity,
                        weight: 2,
                        fillColor: "yellow",
                        fillOpacity: gridOpacity,
                    }}
                />
            )}

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
                        edit :  props.editEnabled,
                        remove : props.editEnabled
                    }}
                    onCreated={handleRegionCreation}
                    onEdited={handleRegionEdit}
                />
            </FeatureGroup>
        </MapContainer>
    </div>);
}