import $ from "jquery";
import proj4 from "proj4";
import Map from "ol/Map";
import OSM, { ATTRIBUTION } from "ol/source/OSM";
import TileLayer from "ol/layer/Tile";
import View from "ol/View";
import Attribution from "ol/control/Attribution";
import { Projection, fromLonLat } from "ol/proj";
import { register } from "ol/proj/proj4";

const arcticExtent = 6378137 * Math.PI;
const pixel_ratio = parseInt(window.devicePixelRatio) || 1;
const antarcticExtent = 12367396.2185; // To the Equator

const baseOptions = {};

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
register(proj4);

const arcticProjection = new Projection({
    code: "EPSG:3573",
    extent: [-arcticExtent, arcticExtent, arcticExtent, -arcticExtent],
});

const antarcticProjection = new Projection({
    code: "EPSG:3031",
    extent: [
        -antarcticExtent,
        -antarcticExtent,
        antarcticExtent,
        antarcticExtent,
    ],
});

function getResolutions(extent, maxZoom, tileSize) {
    var resolutions = [];
    for (var zoom = 0; zoom <= maxZoom; zoom++) {
        resolutions.push((extent - -extent) / tileSize / Math.pow(2, zoom));
    }
    return resolutions;
}

export function initializeMaps() {
    $(".map__container").removeClass("hidden");
    const arcticMap = new Map(
        $.extend(baseOptions, {
            target: "map--arctic",
            view: new View({
                projection: arcticProjection,
                center: fromLonLat([90, 0], arcticProjection),
                extent: [
                    -arcticExtent,
                    arcticExtent,
                    arcticExtent,
                    -arcticExtent,
                ],
                zoom: 3,
            }),
            layers: [
                new TileLayer({
                    source: new OSM({
                        url: "//{s}.tiles.arcticconnect.ca/osm_3573/{z}/{x}/{y}.png",
                        attribution:
                            'Map &copy; <a href="http://arcticconnect.ca">ArcticConnect</a>. Data &copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
                    }),
                    minZoom: 0,
                    maxZoom: 18,
                }),
            ],
        })
    );

    // var antarcticMap = L.map(
    //     "map--antarctic",
    //     $.extend(baseOptions, {
    //         crs: new L.Proj.CRS(
    //             "EPSG:3031",
    //             "+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs",
    //             {
    //                 origin: [-antarcticExtent, antarcticExtent],
    //                 bounds: L.bounds(
    //                     L.point([-antarcticExtent, -antarcticExtent]),
    //                     L.point([antarcticExtent, antarcticExtent])
    //                 ),
    //                 resolutions: getResolutions(antarcticExtent, 16, 512),
    //                 center: [-90, 0],
    //                 zoom: 2,
    //             }
    //         ),
    //     })
    // ).setView([-90, 0], 2);

    // L.tileLayer(
    //     "https://tile.gbif.org/3031/omt/{z}/{x}/{y}@{r}x.png?style=gbif-geyser".replace(
    //         "{r}",
    //         pixel_ratio
    //     ),
    //     { tileSize: 512 }
    // ).addTo(antarcticMap);
}
