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
const pixel_ratio = parseInt(window.devicePixelRatio) || 1;
const arcticExtent = L.Projection.Mercator.R * Math.PI;
const antarcticExtent = 12367396.2185; // To the Equator

function getResolutions(extent, maxZoom, tileSize) {
    var resolutions = [];
    for (var zoom = 0; zoom <= maxZoom; zoom++) {
        resolutions.push((extent - -extent) / tileSize / Math.pow(2, zoom));
    }
    return resolutions;
}

$(document).ready(function () {
    var arcticMap = L.map(
        "map--arctic",
        $.extend(baseOptions, {
            crs: new L.Proj.CRS(
                "EPSG:3573",
                "+proj=laea +lat_0=90 +lon_0=-100 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs",
                {
                    origin: [-arcticExtent, arcticExtent],
                    resolutions: getResolutions(arcticExtent, 18, 256),
                    bounds: L.bounds(
                        L.point(-arcticExtent, arcticExtent),
                        L.point(arcticExtent, -arcticExtent)
                    ),
                    center: [90, 0],
                    zoom: 4,
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
                    origin: [-antarcticExtent, antarcticExtent],
                    bounds: L.bounds(
                        L.point([-antarcticExtent, -antarcticExtent]),
                        L.point([antarcticExtent, antarcticExtent])
                    ),
                    resolutions: getResolutions(antarcticExtent, 16, 512),
                    center: [-90, 0],
                    zoom: 4,
                }
            ),
        })
    ).setView([-90, 0], 4);

    L.tileLayer("//{s}.tiles.arcticconnect.ca/osm_3573/{z}/{x}/{y}.png", {
        minZoom: 0,
        maxZoom: 18,
        noWrap: true,
        // map attribution text for tiles and/or data
        attribution:
            'Map &copy; <a href="http://arcticconnect.ca">ArcticConnect</a>. Data &copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(arcticMap);

    L.tileLayer(
        "https://tile.gbif.org/3031/omt/{z}/{x}/{y}@{r}x.png?style=gbif-classic".replace(
            "{r}",
            pixel_ratio
        ),
        { tileSize: 512 }
    ).addTo(antarcticMap);
});
