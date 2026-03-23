const ROBOT_NAMESPACE = "myPanther";


// Sleep for given amount of milliseconds
async function sleep(time_ms) {
    await new Promise(resolve => setTimeout(resolve, time_ms));
}

// Set the theme of the web page
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

// Custom icons of the map markers
var iconRover = L.icon({
    iconUrl: '/static/img/rover.png',
    shadowUrl: '/static/img/shadow.png',
    iconSize: [30, 30],
    shadowSize: [30, 30],
    iconAnchor: [15, 15],
    shadowAnchor: [15, 15],
    popupAnchor: [-5, -75]
});

var iconNavTarget = L.icon({
    iconUrl: '/static/img/goal.png',
    iconSize: [25, 41],
    iconAnchor: [10, 40],
    popupAnchor: [0, 0],
    shadowUrl: '',
    shadowSize: [0, 0],
    shadowAnchor: [0, 0]
});

// Custom marker for the rover
var roverMarker = L.marker([geoPointLat, geoPointLon], {icon: iconRover});

var goalMarkerGroup = L.layerGroup();
map.addLayer(goalMarkerGroup);

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


// Draw an arrow that shows the orientation of the rover
function drawArrow(msg) {
    arrow.remove();
    arrow = L.polyline([
        [msg.lat, msg.lon], 
        [msg.arrow_tip.lat, msg.arrow_tip.lon]
    ]).arrowheads();
    arrow.addTo(map);
};


// Set the center of the map view
function setMapView() {
    map.setView([geoPointLat, geoPointLon], defaultZoom);
};


// Set the location of the marker on the map
function setRoverLocation(geoPoint) {
    roverMarker.setLatLng([geoPoint.lat, geoPoint.lon]).addTo(map);
};


//===================================================================
// SocketIO
//===================================================================
var socketio = io();

// Show the battery information of the rover
socketio.on('battery_state', function(msg) {
    document.getElementById('batteryCharge').innerHTML = msg.charge;
    document.getElementById('batteryPercentage').innerHTML = msg.percentage;
    document.getElementById('batteryVoltage').innerHTML = msg.voltage;
});

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

// Show the location information of the rover
socketio.on('navsatfix', function(msg) {
    document.getElementById('locationLat').innerHTML = msg.lat;
    document.getElementById('locationLon').innerHTML = msg.lon;
    document.getElementById('locationAlt').innerHTML = msg.alt;
    geoPointLat = msg.lat;
    geoPointLon = msg.lon;
    setRoverLocation(msg);
    drawArrow(msg);
});

// Show the feedback of the navigation task
socketio.on('nav_feedback', function(msg) {
    document.getElementById('navTimeRem').innerHTML = msg.estimated_time_remainging;
    document.getElementById('navDistRem').innerHTML = msg.distance_remaining;
    document.getElementById('navNavTime').innerHTML = msg.navigation_time;
    document.getElementById('navNumRecs').innerHTML = msg.number_of_recoveries;
});

// Show the planned path of the navigation task
socketio.on('nav_path', function(msg) {
    plannedPath.remove();
    plannedPath = L.polyline(msg.path, {color: 'green'});
    plannedPath.addTo(map);
});

// Show the result of the navigation task
socketio.on('nav_result', function(msg) {
    document.getElementById('navStatus').innerHTML = msg;
    onNavResult();
});

async function onNavResult() {
    await sleep(5000);
    plannedPath.remove();
    goalMarkerGroup.clearLayers();
    resetNavFeedback();
};

// Send a command velocity message to the server
function driveRobot(direction) {
    const controlSwitch = document.getElementById('switchManualControl');
    const radioSimulation = document.getElementById('radioSimulation');
    if(controlSwitch.checked) {
        let env = radioSimulation.checked ? "simulation" : ROBOT_NAMESPACE;
        let data = {
            env: env,
            direction: direction
        };
        socketio.emit('drive_robot', data);
    }
};

// Navigation
const navTargets = {
    automotiveLab: {
        lat: 62.790967500,
        lon: 22.821647222,
        yaw: 0.0
    },
    manufacturingLab: {
        lat: 62.789319444,
        lon: 22.821791111,
        yaw: 0.7853981633974483,
    },
    roboticsLab: {
        lat: 62.789201667,
        lon: 22.822063056,
        yaw: -0.7853981633974483,
    },
};
let navStatus = 'PENDING';
let navTarget = {};

function setNavGoal(target) {
    goalMarkerGroup.clearLayers();
    if (navStatus !== 'PENDING' || target === 'mapClick') {
        return
    }
    navTarget = navTargets[target];
    
    L.marker(
        L.latLng(navTarget.lat, navTarget.lon),
        {'icon': iconNavTarget},
    ).addTo(goalMarkerGroup);
};

// Start a navigation task
function navStart() {
    if (navStatus === 'ACTIVE') {
        return;
    }
    navStatus = 'ACTICE';
    document.getElementById('navStatus').innerHTML = navStatus;
    const controlSwitch = document.getElementById('switchManualControl');
    const navTargetDD = document.getElementById('inputNavTarget');
    const startNavButton = document.getElementById('navStart');
    controlSwitch.disabled = true;
    startNavButton.disabled = true;
    socketio.emit('nav_start', navTarget);
};

// Cancel the navigation task
function navCancel() {
    socketio.emit('nav_cancel', 'stop');
};

// 
map.on('click', function(event) {
    const navTargetDD = document.getElementById('inputNavTarget');
    if (navTargetDD.value === 'mapClick' && navStatus === 'PENDING') {
        navTarget = {
            lat: event.latlng.lat,
            lon: event.latlng.lng,
            yaw: 0.0
        }
        goalMarkerGroup.clearLayers();
        L.marker(
            L.latLng(event.latlng.lat, event.latlng.lng),
            {'icon': iconNavTarget},
        ).addTo(goalMarkerGroup);
    }
});

function resetNavFeedback() {
    document.getElementById('navStatus').innerHTML = 'PENDING';
    document.getElementById('navTimeRem').innerHTML = 0.0;
    document.getElementById('navDistRem').innerHTML = 0.0;
    document.getElementById('navNavTime').innerHTML = 0.0;
    document.getElementById('navNumRecs').innerHTML = 0;
    document.getElementById('switchManualControl').disabled = false;
    document.getElementById('navStart').disabled = false;
};

resetNavFeedback();