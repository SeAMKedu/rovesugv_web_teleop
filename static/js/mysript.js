var framiLat = 62.789247014369300;
var framiLon = 22.821891903877262;
var numMarkers = 0;

var map = L.map('map').setView([framiLat, framiLon], 17);
var markerGroup = L.layerGroup();
map.addLayer(markerGroup);


var iconNavTarget = L.icon({
    iconUrl: '/static/marker-icon-goal.png',
    iconSize: [25, 41],
    iconAnchor: [10, 40],
    popupAnchor: [0, 0],
    shadowUrl: '',
    shadowSize: [0, 0],
    shadowAnchor: [0, 0]
});

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

map.on('click', function(event) {
    numMarkers = numMarkers + 1;
    if (numMarkers > 1) {
        return;
    }
    var marker = new L.marker(
        L.latLng(event.latlng.lat, event.latlng.lng),
        {'icon': iconNavTarget},
    ).addTo(markerGroup);
});

function removeMarkers() {
    markerGroup.clearLayers();
    numMarkers = 0;
};