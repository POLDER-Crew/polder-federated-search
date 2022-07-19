import $ from "jquery";
import proj4 from "proj4";
import L from "leaflet";
import "proj4leaflet";

proj4.defs([
    [
        "EPSG:3573",
        "+proj=laea +lat_0=90 +lon_0=-100 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs",
    ],
    [
        "EPSG:3031",
        "+proj=laea +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs",
    ],
]);

const baseOptions = {};

$(document).ready(function () {
    var extent = L.Projection.Mercator.R * Math.PI;
    var resolutions = [];
    for (var zoom = 0; zoom <= 18; zoom++) {
      resolutions.push((extent - -extent) / 256 / Math.pow(2, zoom));
    }
    var arcticMap = L.map(
        "map--arctic",
        $.extend(baseOptions, {
            crs: new L.Proj.CRS(
                "EPSG:3573",
                "+proj=laea +lat_0=90 +lon_0=-100 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs",
                {
                    minZoom: 0,
                    maxZoom: 18,
                    tms: false,
                    origin: [-extent, extent],
                    resolutions: resolutions,
                    bounds: L.bounds(
                        L.point(-extent, extent),
                        L.point(extent, -extent)
                    ),
                    // default centre when this map is loaded
                    center: [90, 0],
                    // default zoom level
                    zoom: 4,
                    continuousWorld: false,
 }
            ),
        })
    ).setView([90, 0], 4);

    var antarcticMap = L.map(
        "map--antarctic",
        $.extend(baseOptions, {
            crs: new L.Proj.CRS(
                "EPSG:3031",
                "+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs",
                {
                    origin: [-4194304, 4194304],
                    bounds: L.bounds(
                        L.point([-4194304, -4194304]),
                        L.point([4194304, 4194304])
                    ),
                    resolutions: [
                        16384.0, 8192.0, 4096.0, 2048.0, 1024.0, 512.0, 256.0,
                    ],
                }
            ),
        })
    );

    L.tileLayer("//{s}.tiles.arcticconnect.ca/osm_3573/{z}/{x}/{y}.png", {
        noWrap: true,
        // map attribution text for tiles and/or data
        attribution:
                        'Map &copy; <a href="http://arcticconnect.ca">ArcticConnect</a>. Data &copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',

    }).addTo(
        arcticMap
    );
    L.tileLayer(
        "//gibs-{s}.earthdata.nasa.gov/wmts/epsg3031/best/BlueMarble_ShadedRelief_Bathymetry/default/2020-12-01/EPSG3031_500m/{z}/{y}/{x}.jpg"
    ).addTo(antarcticMap);
});
