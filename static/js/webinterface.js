function setTheme(theme) {
    const collection = document.getElementsByClassName('container');
    collection[0].setAttribute('data-bs-theme', theme);
};


// Leaflet
var geoPointLat = 62.789252;
var geoPointLon = 22.821627;
var defaultZoom = 19;

var map = L.map('map', {
    center: [geoPointLat, geoPointLon],
    zoom: defaultZoom
});

map.setView([geoPointLat, geoPointLon], defaultZoom);

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);


// SocketIO
var socketio = io();

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