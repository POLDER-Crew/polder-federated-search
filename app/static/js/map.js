import $ from "jquery";
import proj4 from "proj4";
import { applyStyle, stylefunction } from "ol-mapbox-style";

import {Attribution, defaults as defaultControls} from 'ol/control';
import {toStringHDMS} from 'ol/coordinate';
import { containsExtent } from "ol/extent";
import GeoJSON from "ol/format/GeoJSON";
import MVT from "ol/format/MVT";
import {defaults as defaultInteractions} from 'ol/interaction/defaults';
import Select from 'ol/interaction/Select';
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorTileLayer from "ol/layer/VectorTile";
import Map from "ol/Map";
import Overlay from 'ol/Overlay';
import { get as getProjection, fromLonLat, toLonLat } from "ol/proj";
import { register } from "ol/proj/proj4";
import OSM, { ATTRIBUTION } from "ol/source/OSM";
import VectorSource from "ol/source/Vector";
import VectorTileSource from "ol/source/VectorTile";
import { Circle, Text, Fill, Stroke, Style } from "ol/style";
import View from "ol/View";

const pixel_ratio = parseInt(window.devicePixelRatio) || 1;

// PROJECTIONS: If you are using default map projections, you don't need any of this stuff.
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

// Set up the map projections for standard polar views. If you're using Mercator,
// you can delete these.
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

// Polar projections; if you're sticking to Mercator, you don't need these.
let arcticProjection = getProjection("EPSG:3573");
arcticProjection.setExtent(arcticExtentBoundary);

let antarcticProjection = getProjection("EPSG:3031");
antarcticProjection.setExtent(antarcticExtentBoundary);


// EXTRA PLACES: Places and countries styles for the antarctic map.
// If your map tiles include all the place names you want already, you don't need these.
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

// SEARCH RESULTS: customize these styles to match your colors and preferences
const accentWarm = "#e66b3d"; // see _constants.scss
const lightBlue = "#0092ad"; // see _constants.scss
const resultStroke = new Stroke({ color: accentWarm, width: 2 });
const selectedResultStroke = new Stroke({ color: lightBlue, width: 2 });
const resultFill = new Fill({
    color: "rgba(230, 107, 61, 0.1)",
});
const selectedResultFill = new Fill({
    color: "rgba(255, 255, 255, 0.4)",
});

const image = new Circle({
    radius: 5,
    fill: resultFill,
    stroke: resultStroke,
});

const selectedImage = new Circle({
    radius: 5,
    fill: selectedResultFill,
    stroke: selectedResultStroke,
});

const resultStyle = function (feature) {
    return new Style({
        stroke: resultStroke,
        fill: resultFill,
        image: image,
    });
};

const selectedResultStyle = function (feature) {
    return new Style({
        stroke: selectedResultStroke,
        fill: selectedResultFill,
        image: selectedImage,
    });
};

// You only need this function if you are using a non-standard projection.
// The extent, tileSize, and maximum zoom level are pieces of information that
// should be documented with a tilesource.
function getMinResolution(extent, tileSize, maxZoom) {
    return extent / (tileSize / 2) / Math.pow(2, maxZoom);
}

// VIEWS: if you have one map, you only need one view.

// This tileset does not work correctly when you specify a projection for some reason,
// even though it uses a non-standard projection.
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
// If your map alrady looks how you want it to, you don't need this block.
fetch("/static/maps/style.json").then(function (response) {
    response.json().then(function (glStyle) {
        stylefunction(antarcticLayer, glStyle, "openmaptiles");
    });
});

// EXTRA PLACES:
// If your map already has all the place names you want on it, you don't need this part.
// These two layers are just to put some labels on Antarctica to make
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

// LAYERS:
// A layer for the search results, on each map. You definitely need this
// part (although if you only have one map, you only need one of them)
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

let $popupContainer;
let $popupContent;
let $popupCloser;

const overlay = new Overlay({
  autoPan: {
    animation: {
      duration: 250,
    },
  },
});

const selectRegionHandler = function (evt) {
    let coordinate = evt.mapBrowserEvent.coordinate;
    let map = evt.mapBrowserEvent.map;

    overlay.setMap(map);
    let popupHtml = '';
    let showPopup = false;


    evt.selected.forEach(function (feature) {
        if (feature && feature.setStyle) { // sometimes you get back an ice layer or something
            showPopup = true;
            popupHtml += `<h4 class="popup-title"><a href="#${feature.get('id')}">${feature.get('name')}</a></h4>`;
        }
    });

    if(showPopup) {
        const hdms = toStringHDMS(toLonLat(coordinate));
        popupHtml += `<p><code>${hdms}</code></p>`;
        $popupContent.html(popupHtml);
        overlay.setPosition(coordinate);
    }
};

// The handler for changing the style of selected / deselected regions.
// Can't have maps share them, apparently.
const selectRegionArctic = new Select({style: selectedResultStyle, multi: true});

// The handler for showing the popup
selectRegionArctic.on('select', selectRegionHandler);

const selectRegionAntarctic = new Select({style: selectedResultStyle, multi: true});
selectRegionAntarctic.on('select', selectRegionHandler);

const $mapContainer = $(".map__container");
let $arcticScreenReaderList = $("#map__screenreader--arctic");
let $antarcticScreenReaderList = $("#map__screenreader--antarctic");

export function initializeMaps(lazy=false) {
    // Stuff for the popup that comes up when you click on the map
    $popupContainer = $('#map__popup');
    $popupCloser = $('#map__popup-closer');
    $popupContent = $('#map__popup-content');

    overlay.setElement($popupContainer[0]);

    // Prevents showing a stray overlay container on paging
    overlay.setPosition(undefined);

    // Accessibility helpers
    $arcticScreenReaderList = $("#map__screenreader--arctic");
    $antarcticScreenReaderList = $("#map__screenreader--antarctic");

    $arcticScreenReaderList.empty();
    $antarcticScreenReaderList.empty();

    arcticResultsSource.clear(true);
    antarcticResultsSource.clear(true);

    $mapContainer.removeClass("hidden");


    if (!lazy || !arcticMap) {
        arcticMap = new Map({
            target: "map--arctic",
            view: arcticView,
            overlays: [overlay],
            layers: [arcticLayer, arcticResultsLayer],
            controls: defaultControls({attribution: false}).extend(
                [new Attribution({collapsible: true})]
            ),
            interactions: defaultInteractions().extend([selectRegionArctic])
        });
    }

    if (!lazy || !antarcticMap) {
        antarcticMap = new Map({
            target: "map--antarctic",
            view: antarcticView,
            overlays: [overlay],
            layers: [
                antarcticLayer,
                antarcticCountriesLayer,
                antarcticPlacesLayer,
                antarcticResultsLayer,
            ],
            controls: defaultControls({attribution: false}).extend(
                [new Attribution({collapsible: true,})]
            ),
            interactions: defaultInteractions().extend([selectRegionAntarctic])
        });
    }

    $popupCloser.on('click', function () {
      overlay.setPosition(undefined);
      $popupCloser.blur();
      $popupContent.empty();
      return false;
    });
}

export function addSearchResult(id, result) {
    // We're adding features twice in here because there are two maps.
    // If you only have one map, you only need to do this once.
    const arcticFeature = new GeoJSON().readFeature(result.geometry, {
        // If your tileset is using the default projection, don't need the next two lines.
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
        // Can we reproject it in GeoSPARQL or something?
        arcticFeature.set("id", id);
        arcticFeature.set("name", result.name);
        arcticResultsSource.addFeature(arcticFeature);
        $arcticScreenReaderList.append(`<li>${result.name}</li>`);
    }

    const antarcticFeature = new GeoJSON().readFeature(result.geometry, {
        // If your tileset is using the default projection, don't need the next two lines.
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
        antarcticFeature.set("id", id);
        antarcticFeature.set("name", result.name);
        antarcticResultsSource.addFeature(antarcticFeature);
        $antarcticScreenReaderList.append(`<li>${result.name}</li>`);
    }
}
