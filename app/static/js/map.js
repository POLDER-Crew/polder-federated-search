import $ from "jquery";
import proj4 from "proj4";
import { applyStyle, stylefunction } from "ol-mapbox-style";
import Map from "ol/Map";
import OSM, { ATTRIBUTION } from "ol/source/OSM";
import TileArcGISRest from "ol/source";
import TileLayer from "ol/layer/Tile";
import VectorTileLayer from "ol/layer/VectorTile";
import VectorTileSource from "ol/source/VectorTile";
import View from "ol/View";
import MVT from "ol/format/MVT";
import Attribution from "ol/control/Attribution";
import { get as getProjection, fromLonLat } from "ol/proj";
import { register } from "ol/proj/proj4";

const arcticExtent = 6378137 * Math.PI; // Extent is half of the WGS84 Ellipsoid equatorial circumference.
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

let arcticProjection = getProjection("EPSG:3573");
arcticProjection.setExtent([
    -arcticExtent,
    -arcticExtent,
    arcticExtent,
    arcticExtent,
]);

let antarcticProjection = getProjection("EPSG:3031");
antarcticProjection.setExtent([
    -antarcticExtent,
    -antarcticExtent,
    antarcticExtent,
    antarcticExtent,
]);

const arcticView = new View({
    // projection: arcticProjection,
    center: fromLonLat([0, 0]),
    zoom: 2,
    minResolution: arcticExtent / 256 / Math.pow(2, 17),
    maxResolution: arcticExtent / 256,
});

const antarcticView = new View({
    projection: antarcticProjection,
    center: fromLonLat([0, -90], antarcticProjection),
    zoom: 2,
    minResolution: antarcticExtent / 128 / Math.pow(2, 15),
    maxResolution: antarcticExtent / 128,
});

const arcticLayer = new TileLayer({
    extent: [-arcticExtent, -arcticExtent, arcticExtent, arcticExtent],
    source: new OSM({
        url: "//tiles.arcticconnect.ca/osm_3573/{z}/{x}/{y}.png",
        attributions: [
            'Map &copy; <a href="http://arcticconnect.ca">ArcticConnect</a>.',
            "Data " + ATTRIBUTION,
        ],
        // projection: arcticProjection,
        maxZoom: 18,
        wrapX: false,
    }),
});

const antarcticLayer = new VectorTileLayer({
    extent: [
        -antarcticExtent,
        -antarcticExtent,
        antarcticExtent,
        antarcticExtent,
    ],
    source: new VectorTileSource({
        projection: antarcticProjection,
        format: new MVT(),
        url: "https://tile.gbif.org/3031/omt/{z}/{x}/{y}.pbf",
        tilePixelRatio: 8,
        attributions: [
            '© <a href="https://www.openmaptiles.org/copyright">OpenMapTiles</a>.',
            ATTRIBUTION,
        ],
    }),
});

fetch('/static/maps/style.json').then(function(response) {
    response.json().then(function(glStyle) {
        stylefunction(antarcticLayer, glStyle, 'openmaptiles');
    })
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

    const antarcticMap = new Map(
        $.extend(baseOptions, {
            target: "map--antarctic",
            view: antarcticView,
            layers: [antarcticLayer],
        })
    );
}
