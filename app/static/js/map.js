import $ from "jquery";
import proj4 from "proj4";
import Map from "ol/Map";
import OSM, { ATTRIBUTION } from "ol/source/OSM";
import TileLayer from "ol/layer/Tile";
import View from "ol/View";
import Attribution from "ol/control/Attribution";
import { get as getProjection, Projection, fromLonLat } from "ol/proj";
import { register } from "ol/proj/proj4";

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
        "+proj=stere +lat_0=-90 +lat_ts=-71 +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs",
    ],
]);
register(proj4);

const arcticProjection = new Projection({
    code: "EPSG:3573",
    extent: [-948.75, -543592.47, 5817.41, -3333128.95],
    units: "m",
    minZoom: 0,
    maxZoom: 18,
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

const arcticView = new View({
    projection: arcticProjection,
    center: fromLonLat([0, 90], arcticProjection),
    zoom: 3,
    maxResolution: (6378137 * Math.PI) / 512 / Math.pow(2, 18),
    minResolution: (6378137 * Math.PI) / 512 / 2,
});

const arcticLayer = new TileLayer({
    source: new OSM({
        url: "//tiles.arcticconnect.ca/osm_3573/{z}/{x}/{y}.png",
        attributions: [
            'Map &copy; <a href="http://arcticconnect.ca">ArcticConnect</a>. Data &copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors',
            ATTRIBUTION,
        ],
    }),
    // minZoom: 0,
    // maxZoom: 18,
});

export function initializeMaps() {
    $(".map__container").removeClass("hidden");
    const arcticMap = new Map(
        $.extend(baseOptions, {
            target: "map--arctic",
            view: arcticView,
            layers: [arcticLayer],
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
