function setTheme(theme) {
    const collection = document.getElementsByClassName('container');
    collection[0].setAttribute('data-bs-theme', theme);
};


//===================================================================
// Leaflet
//===================================================================
var geoPointLat = 62.789252;
var geoPointLon = 22.821627;
var defaultZoom = 19;

var map = L.map('map', {
    center: [geoPointLat, geoPointLon],
    zoom: defaultZoom
});

map.setView([geoPointLat, geoPointLon], defaultZoom);

// Custom icon for the marker
var roverIcon = L.icon({
    iconUrl: '/static/img/rover.png',
    shadowUrl: '/static/img/shadow.png',
    iconSize: [30, 30],
    shadowSize: [30, 30],
    iconAnchor: [15, 15],
    shadowAnchor: [15, 15],
    popupAnchor: [-5, -75]
});

// Custom marker
var marker = L.marker([geoPointLat, geoPointLon], {icon: roverIcon});

// Arrow that shows the orientation of the rover
var arrow = L.polyline([
    [geoPointLat, geoPointLon],
    [62.78925199996589, 22.82172496665635]
]).arrowheads();
arrow.addTo(map);

// Polyline that shows the planned path of the rover during navigation
var plannedPath = L.polyline([]);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);


// Set the location of the marker on the map
function setMarkerLocation(geoPoint) {
    marker.setLatLng([geoPoint.lat, geoPoint.lon]).addTo(map);
};


// Draw the arrow that shows the orientation of the rover
function drawArrow(msg) {
    arrow.remove();
    arrow = L.polyline([
        [msg.lat, msg.lon], 
        [msg.arrow_tip.lat, msg.arrow_tip.lon]
    ]).arrowheads();
    arrow.addTo(map);
};


//===================================================================
// SocketIO
//===================================================================
var socketio = io();

// Connection message from the server
socketio.on('connection', function(msg) {
    const iconElem = document.getElementById('sioConnIcon');
    const spanElem = document.getElementById('sioConnColor');
    iconElem.classList.remove('fa-link-slash');
    iconElem.classList.add('fa-link');
    spanElem.style['color'] = 'green';
    socketio.on('disconnect', function() {
        iconElem.classList.remove('fa-link');
        iconElem.classList.add('fa-link-slash');
        spanElem.style['color'] = 'crimson';
    });
});

// Location of the rover
socketio.on('navsatfix', function(msg) {
    document.getElementById('locationLat').innerHTML = msg.lat;
    document.getElementById('locationLon').innerHTML = msg.lon;
    document.getElementById('locationAlt').innerHTML = msg.alt;
    geoPointLat = msg.lat;
    geoPointLon = msg.lon;
    setMarkerLocation(msg);
    drawArrow(msg);
});