import $ from "jquery";
import proj4 from "proj4";
import { applyStyle, stylefunction } from "ol-mapbox-style";
import GeoJSON from "ol/format/GeoJSON";
import Map from "ol/Map";
import OSM, { ATTRIBUTION } from "ol/source/OSM";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import VectorTileLayer from "ol/layer/VectorTile";
import VectorTileSource from "ol/source/VectorTile";
import View from "ol/View";
import MVT from "ol/format/MVT";
import Attribution from "ol/control/Attribution";
import { get as getProjection, fromLonLat } from "ol/proj";
import { Circle, Text, Fill, Stroke, Style } from "ol/style";
import { containsExtent } from "ol/extent";
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

fetch("/static/maps/style.json").then(function (response) {
    response.json().then(function (glStyle) {
        stylefunction(antarcticLayer, glStyle, "openmaptiles");
    });
});

// these two layers are just to put some labels on Antarctica to make
// the map more usable
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
            maxResolution: 20000,
            style: function (feature) {
                return new Style({
                    text: new Text({
                        text: feature.get("name"),
                        fill: new Fill({ color: "#222" }),
                        stroke: new Stroke({
                            color: "rgba(255,255,255,0.6)",
                            width: 1,
                        }),
                    }),
                });
            },
        });
    });
});

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
            style: function (feature) {
                return new Style({
                    text: new Text({
                        text: feature.get("name"),
                        fill: new Fill({ color: "#ac46ac" }),
                        stroke: new Stroke({
                            color: "rgba(255,255,255,0.6)",
                            width: 3,
                        }),
                    }),
                });
            },
        });
    });
});

// Search results styles
const accentWarm = "#e66b3d"; // see _constants.scss
const strokeWidth = 2;
const resultStroke = new Stroke({ color: accentWarm, width: strokeWidth });
const resultFill = new Fill({
    color: "rgba(230, 107, 61, 0.1)",
});
const image = new Circle({
    radius: 5,
    fill: resultFill,
    stroke: resultStroke,
});

const styles = {
    Point: new Style({
        image: image,
    }),
    LineString: new Style({
        stroke: resultStroke,
    }),
    MultiLineString: new Style({
        stroke: resultStroke,
    }),
    MultiPoint: new Style({
        image: image,
    }),
    MultiPolygon: new Style({
        stroke: resultStroke,
        fill: resultFill,
    }),
    Polygon: new Style({
        stroke: resultStroke,
        fill: resultFill,
    }),
    GeometryCollection: new Style({
        stroke: resultStroke,
        fill: resultFill,
        image: image,
    }),
    Circle: new Style({
        stroke: resultStroke,
        fill: resultFill,
    }),
};

const resultStyle = function (feature) {
    return styles[feature.getGeometry().getType()];
};

// A layer for the search results, on each map
let arcticResultsSource = new VectorSource({});
let arcticResultsLayer = new VectorLayer({
    declutter: true,
    source: arcticResultsSource,
    style: resultStyle,
});

let antarcticResultsSource = new VectorSource({});
let antarcticResultsLayer = new VectorLayer({
    declutter: true,
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
        const anchor = $("#" + feature.getId());
        $("html,body").animate({ scrollTop: anchor.offset().top }, "slow");
    }
};

export function initializeMaps() {
    arcticResultsSource.clear(true);
    antarcticResultsSource.clear(true);

    $(".map__container").removeClass("hidden");

    if (!arcticMap) {
        arcticMap = new Map(
            $.extend(baseOptions, {
                target: "map--arctic",
                view: arcticView,
                layers: [arcticLayer, arcticResultsLayer],
            })
        );

        arcticMap.on("click", function (evt) {
            displayResult(arcticMap, evt.pixel);
        });
    }

    if (!antarcticMap) {
        antarcticMap = new Map(
            $.extend(baseOptions, {
                target: "map--antarctic",
                view: antarcticView,
                layers: [
                    antarcticLayer,
                    antarcticCountriesLayer,
                    antarcticPlacesLayer,
                    antarcticResultsLayer,
                ],
            })
        );
        antarcticMap.on("click", function (evt) {
            displayResult(antarcticMap, evt.pixel);
        });
    }
}

export function addSearchResult(geometry, id) {
    const arcticFeature = new GeoJSON().readFeature(geometry, {
        dataProjection: getProjection("ESPG:4326"),
        featureProjection: arcticProjection,
    });

    arcticFeature.setId(id);
    if (
        containsExtent(
            [-arcticExtent, -arcticExtent, arcticExtent, arcticExtent],
            arcticFeature.getGeometry().getExtent()
        )
    ) {
        arcticResultsSource.addFeature(arcticFeature);
    }

    const antarcticFeature = new GeoJSON().readFeature(geometry, {
        dataProjection: getProjection("ESPG:4326"),
        featureProjection: antarcticProjection,
    });

    antarcticFeature.setId(id);
    if (
        containsExtent(
            [
                -antarcticExtent,
                -antarcticExtent,
                antarcticExtent,
                antarcticExtent,
            ],
            antarcticFeature.getGeometry().getExtent()
        )
    ) {
        antarcticResultsSource.addFeature(antarcticFeature);
    }
}
