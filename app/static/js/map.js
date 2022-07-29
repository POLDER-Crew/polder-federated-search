import $ from "jquery";
import proj4 from "proj4";
import { applyStyle, stylefunction } from "ol-mapbox-style";

import { containsExtent } from "ol/extent";
import GeoJSON from "ol/format/GeoJSON";
import MVT from "ol/format/MVT";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorTileLayer from "ol/layer/VectorTile";
import Map from "ol/Map";
import { get as getProjection, fromLonLat } from "ol/proj";
import { register } from "ol/proj/proj4";
import OSM, { ATTRIBUTION } from "ol/source/OSM";
import VectorSource from "ol/source/Vector";
import VectorTileSource from "ol/source/VectorTile";
import { Circle, Text, Fill, Stroke, Style } from "ol/style";
import View from "ol/View";

const arcticExtent = 6378137 * Math.PI; // Extent is half of the WGS84 Ellipsoid equatorial circumference.
const arcticExtentBoundary = [
    -arcticExtent,
    -arcticExtent,
    arcticExtent,
    arcticExtent,
];
const arcticTileSize = 512;
const arcticMaxZoom = 18;

const antarcticExtent = 12367396.2185; // To the Equator
const antarcticExtentBoundary = [
    -antarcticExtent,
    -antarcticExtent,
    antarcticExtent,
    antarcticExtent,
];
const antarcticTileSize = 256;
const antarcticMaxZoom = 16;

const pixel_ratio = parseInt(window.devicePixelRatio) || 1;

// Set up the map projections for standard polar views.
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
arcticProjection.setExtent(arcticExtentBoundary);

let antarcticProjection = getProjection("EPSG:3031");
antarcticProjection.setExtent(antarcticExtentBoundary);

// Places and countries styles for the antarctic map
const placesTextFill = new Fill({ color: "#222" });
const countriesTextFill = new Fill({ color: "#ac46ac" });
const placesTextStroke = new Stroke({
    color: "rgba(255,255,255,0.6)",
    width: 1,
});
const countriesTextStroke = new Stroke({
    color: "rgba(255,255,255,0.6)",
    width: 3,
});

const placesTextStyle = function (feature) {
    return new Style({
        text: new Text({
            text: feature.get("name"),
            fill: placesTextFill,
            stroke: placesTextStroke,
        }),
    });
};

const countriesTextStyle = function (feature) {
    return new Style({
        text: new Text({
            text: feature.get("name"),
            fill: countriesTextFill,
            stroke: countriesTextStroke,
        }),
    });
};

// Search results styles
const accentWarm = "#e66b3d"; // see _constants.scss
const resultStroke = new Stroke({ color: accentWarm, width: 2 });
const resultFill = new Fill({
    color: "rgba(230, 107, 61, 0.1)",
});
const highlightedResultFill = new Fill({
    color: "rgba(230, 107, 61, 0.4)",
});

const image = new Circle({
    radius: 5,
    fill: resultFill,
    stroke: resultStroke,
});

const resultStyle = function (feature) {
    return new Style({
        stroke: resultStroke,
        fill: resultFill,
        image: image,
    });
};

// The extent, tileSize, and maximum zoom level are pieces of information that
// should be documented with a tilesource.
function getMinResolution(extent, tileSize, maxZoom) {
    return extent / (tileSize / 2) / Math.pow(2, maxZoom);
}

// This tileset does not work correctly when you specify a projection for some reason.
const arcticView = new View({
    center: fromLonLat([0, 0]), // top of the globe
    zoom: 2,
    minResolution: getMinResolution(
        arcticExtent,
        arcticTileSize,
        arcticMaxZoom
    ),
    maxResolution: arcticExtent / (arcticTileSize / 2),
});

// This one needs a projection.
const antarcticView = new View({
    projection: antarcticProjection,
    center: fromLonLat([0, -90], antarcticProjection),
    zoom: 2,
    minResolution: getMinResolution(
        antarcticExtent,
        antarcticTileSize,
        antarcticMaxZoom
    ),
    maxResolution: antarcticExtent / (antarcticTileSize / 2),
});

// The main map layers and tilesets, for each
const arcticLayer = new TileLayer({
    extent: arcticExtentBoundary,
    source: new OSM({
        url: "//tiles.arcticconnect.ca/osm_3573/{z}/{x}/{y}.png",
        attributions: [
            'Map &copy; <a href="http://arcticconnect.ca">ArcticConnect</a>.',
            "Data " + ATTRIBUTION,
        ],
        maxZoom: arcticMaxZoom,
        wrapX: false,
    }),
});

const antarcticLayer = new VectorTileLayer({
    extent: antarcticExtentBoundary,
    source: new VectorTileSource({
        projection: antarcticProjection,
        format: new MVT(),
        url: "https://tile.gbif.org/3031/omt/{z}/{x}/{y}.pbf",
        tilePixelRatio: 8, // How do I know this? It was in the GBIF example code: https://tile.gbif.org/ui/3031/
        attributions: [
            '© <a href="https://www.openmaptiles.org/copyright">OpenMapTiles</a>.',
            ATTRIBUTION,
        ],
    }),
});

// Styles for the antarctic map. See the README in the static/maps directory for more information.
fetch("/static/maps/style.json").then(function (response) {
    response.json().then(function (glStyle) {
        stylefunction(antarcticLayer, glStyle, "openmaptiles");
    });
});

// these two layers are just to put some labels on Antarctica to make
// the map more usable.
let antarcticPlacesLayer;
let antarcticCountriesLayer;

fetch("/static/maps/places.geojson").then(function (response) {
    response.json().then(function (places) {
        const vectorSource = new VectorSource({
            features: new GeoJSON().readFeatures(places),
        });
        antarcticPlacesLayer = new VectorLayer({
            declutter: true,
            source: vectorSource,
            maxResolution: 20000, // These are detailed place names; only show them when we are zoomed in.
            style: placesTextStyle,
        });
    });
});

// Country boundaries.
fetch("/static/maps/countries.geojson").then(function (response) {
    response.json().then(function (places) {
        const vectorSource = new VectorSource({
            features: new GeoJSON().readFeatures(places, {
                dataProjection: getProjection("ESPG:4326"),
                featureProjection: antarcticProjection,
            }),
        });
        antarcticCountriesLayer = new VectorLayer({
            declutter: true,
            source: vectorSource,
            minResolution: 10000,
            style: countriesTextStyle,
        });
    });
});

// A layer for the search results, on each map
let arcticResultsSource = new VectorSource({});
let arcticResultsLayer = new VectorLayer({
    source: arcticResultsSource,
    style: resultStyle,
});

let antarcticResultsSource = new VectorSource({});
let antarcticResultsLayer = new VectorLayer({
    source: antarcticResultsSource,
    style: resultStyle,
});

let arcticMap;
let antarcticMap;

const displayResult = function (map, pixel) {
    const feature = map.forEachFeatureAtPixel(pixel, function (feature) {
        return feature;
    });
    if (feature) {
        feature.setStyle(
            new Style({
                stroke: resultStroke,
                fill: highlightedResultFill,
                image: image,
                text: new Text({
                    text: feature.get("name"),
                    fill: placesTextFill,
                    stroke: placesTextStroke,
                    padding: [5, 5, 5, 5],
                }),
            })
        );
    }
};

export function initializeMaps() {
    arcticResultsSource.clear(true);
    antarcticResultsSource.clear(true);

    $(".map__container").removeClass("hidden");

    if (!arcticMap) {
        arcticMap = new Map({
            target: "map--arctic",
            view: arcticView,
            layers: [arcticLayer, arcticResultsLayer],
        });

        arcticMap.on("click", function (evt) {
            displayResult(arcticMap, evt.pixel);
        });
    }

    if (!antarcticMap) {
        antarcticMap = new Map({
            target: "map--antarctic",
            view: antarcticView,
            layers: [
                antarcticLayer,
                antarcticCountriesLayer,
                antarcticPlacesLayer,
                antarcticResultsLayer,
            ],
        });
        antarcticMap.on("click", function (evt) {
            displayResult(antarcticMap, evt.pixel);
        });
    }
}

export function addSearchResult(name, geometry) {
    const arcticFeature = new GeoJSON().readFeature(geometry, {
        dataProjection: getProjection("ESPG:4326"),
        featureProjection: arcticProjection,
    });

    if (
        containsExtent(
            arcticExtentBoundary,
            arcticFeature.getGeometry().getExtent()
        )
    ) {
        // todo: let's set these in the geojson on the server side.
        arcticFeature.set("name", name);
        arcticResultsSource.addFeature(arcticFeature);
    }

    const antarcticFeature = new GeoJSON().readFeature(geometry, {
        dataProjection: getProjection("ESPG:4326"),
        featureProjection: antarcticProjection,
    });

    if (
        containsExtent(
            antarcticExtentBoundary,
            antarcticFeature.getGeometry().getExtent()
        )
    ) {
        // todo: let's set these in the geojson on the server side.
        antarcticFeature.set("name", name);
        antarcticResultsSource.addFeature(antarcticFeature);
    }
}
