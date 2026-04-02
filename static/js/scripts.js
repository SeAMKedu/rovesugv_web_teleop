//============================================================================
// Utility functions
//============================================================================
async function sleep(time_ms) {
    await new Promise(resolve => setTimeout(resolve, time_ms));
}

// Set the theme of the web page
function setTheme(theme) {
    const collection = document.getElementsByClassName("container");
    collection[0].setAttribute("data-bs-theme", theme);
};


//===================================================================
// Leaflet
//===================================================================
var roverLat = 62.789252;
var roverLon = 22.821627;
var defaultZoom = 19;

var map = L.map("map", {
    center: [roverLat, roverLon],
    zoom: defaultZoom
});

map.setView([roverLat, roverLon], defaultZoom);

// Custom icons of the map markers
var roverIcon = L.icon({
    iconUrl: "/static/img/rover.png",
    shadowUrl: "/static/img/shadow.png",
    iconSize: [30, 30],
    shadowSize: [30, 30],
    iconAnchor: [15, 15],
    shadowAnchor: [15, 15],
    popupAnchor: [-5, -75]
});

var navTargetIcon = L.icon({
    iconUrl: "/static/img/goal.png",
    iconSize: [25, 41],
    iconAnchor: [10, 40],
    popupAnchor: [0, 0],
    shadowUrl: "",
    shadowSize: [0, 0],
    shadowAnchor: [0, 0]
});

// Custom marker for the rover
var roverMarker = L.marker([roverLat, roverLon], {icon: roverIcon});

var goalMarkerGroup = L.layerGroup();
map.addLayer(goalMarkerGroup);

// Arrow that shows the orientation of the rover
var arrow = L.polyline([
    [roverLat, roverLon],
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
function setRoverOrientationArrow(msg) {
    arrow.remove();
    arrow = L.polyline([
        [msg.lat, msg.lon], 
        [msg.arrow_head.lat, msg.arrow_head.lon]
    ]).arrowheads();
    arrow.addTo(map);
};


// Set the center of the map view
function setMapView() {
    map.setView([roverLat, roverLon], defaultZoom);
};


// Set the location of the marker on the map
function setRoverMarkerLocation(geoPoint) {
    roverMarker.setLatLng([geoPoint.lat, geoPoint.lon]).addTo(map);
};


//===================================================================
// SocketIO
//===================================================================
var socketio = io();

// Show the battery information of the rover
socketio.on("battery_state", function(msg) {
    document.getElementById("batteryCharge").innerHTML = msg.charge;
    document.getElementById("batteryPercentage").innerHTML = msg.percentage;
    document.getElementById("batteryVoltage").innerHTML = msg.voltage;
});

// Connection message from the server
socketio.on("connection", function(msg) {
    const iconElem = document.getElementById("sioConnIcon");
    const spanElem = document.getElementById("sioConnColor");
    iconElem.classList.remove("fa-link-slash");
    iconElem.classList.add("fa-link");
    spanElem.style["color"] = "green";
    socketio.on("disconnect", function() {
        iconElem.classList.remove("fa-link");
        iconElem.classList.add("fa-link-slash");
        spanElem.style["color"] = "crimson";
    });
});

// Show the location information of the rover
socketio.on("navsatfix", function(msg) {
    document.getElementById("locationLat").innerHTML = msg.lat;
    document.getElementById("locationLon").innerHTML = msg.lon;
    document.getElementById("locationAlt").innerHTML = msg.alt;
    roverLat = msg.lat;
    roverLon = msg.lon;
    setRoverMarkerLocation(msg);
    setRoverOrientationArrow(msg);
});

// Show the feedback of the navigation task
socketio.on("nav_feedback", function(msg) {
    document.getElementById("navTimeRem").innerHTML = msg.estimated_time_remainging;
    document.getElementById("navDistRem").innerHTML = msg.distance_remaining;
    document.getElementById("navNavTime").innerHTML = msg.navigation_time;
    document.getElementById("navNumRecs").innerHTML = msg.number_of_recoveries;
});

// Show the planned path of the navigation task
socketio.on("nav_path", function(msg) {
    plannedPath.remove();
    plannedPath = L.polyline(msg.path, {color: "green"});
    plannedPath.addTo(map);
});

// Show the result of the navigation task
socketio.on("nav_result", function(msg) {
    document.getElementById("navStatus").innerHTML = msg;
    onNavResult();
});

async function onNavResult() {
    await sleep(5000);
    plannedPath.remove();
    goalMarkerGroup.clearLayers();
    resetNavFeedback();
};

//============================================================================
// Teleoperation
//============================================================================
const linearSpeed = 0.5;
const angularSpeed = 0.5;
const speeds = {
    forwardL: {linear: linearSpeed, angular: angularSpeed},
    forward: {linear: linearSpeed, angular: 0.0},
    forwardR: {linear: linearSpeed, angular: -angularSpeed},
    rotateL: {linear: 0.0, angular: angularSpeed},
    stop: {linear: 0.0, angular: 0.0},
    rotateR: {linear: 0.0, angular: -angularSpeed},
    backwardL: {linear: -linearSpeed, angular: -angularSpeed},
    backward: {linear: -linearSpeed, angular: 0.0},
    backwardR: {linear: -linearSpeed, angular: angularSpeed},
};

const teleopButton1 = document.getElementById("teleop1");
const teleopButton2 = document.getElementById("teleop2");
const teleopButton3 = document.getElementById("teleop3");
const teleopButton4 = document.getElementById("teleop4");
const teleopButton5 = document.getElementById("teleop5");
const teleopButton6 = document.getElementById("teleop6");
const teleopButton7 = document.getElementById("teleop7");
const teleopButton8 = document.getElementById("teleop8");
const teleopButton9 = document.getElementById("teleop9");
const teleopSwitch = document.getElementById("teleopSwitch");

const teleopTimeout = 500; // in milliseconds
let teleopTimer = null;

teleopButton1.addEventListener("mousedown", () => { startTeleop("forwardL"); });
teleopButton2.addEventListener("mousedown", () => { startTeleop("forward"); });
teleopButton3.addEventListener("mousedown", () => { startTeleop("forwardR"); });
teleopButton4.addEventListener("mousedown", () => { startTeleop("rotateL"); });
teleopButton5.addEventListener("mousedown", () => { startTeleop("stop"); });
teleopButton6.addEventListener("mousedown", () => { startTeleop("rotateR"); });
teleopButton7.addEventListener("mousedown", () => { startTeleop("backwardL"); });
teleopButton8.addEventListener("mousedown", () => { startTeleop("backward"); });
teleopButton9.addEventListener("mousedown", () => { startTeleop("backwardR"); });

teleopButton1.addEventListener("mouseup", () => { stopTeleop(); });
teleopButton2.addEventListener("mouseup", () => { stopTeleop(); });
teleopButton3.addEventListener("mouseup", () => { stopTeleop(); });
teleopButton4.addEventListener("mouseup", () => { stopTeleop(); });
teleopButton5.addEventListener("mouseup", () => { stopTeleop(); });
teleopButton6.addEventListener("mouseup", () => { stopTeleop(); });
teleopButton7.addEventListener("mouseup", () => { stopTeleop(); });
teleopButton8.addEventListener("mouseup", () => { stopTeleop(); });
teleopButton9.addEventListener("mouseup", () => { stopTeleop(); });

teleopButton1.addEventListener("touchstart", () => { startTeleop("forwardL"); });
teleopButton2.addEventListener("touchstart", () => { startTeleop("forward"); });
teleopButton3.addEventListener("touchstart", () => { startTeleop("forwardR"); });
teleopButton4.addEventListener("touchstart", () => { startTeleop("rotateL"); });
teleopButton5.addEventListener("touchstart", () => { startTeleop("stop"); });
teleopButton6.addEventListener("touchstart", () => { startTeleop("rotateR"); });
teleopButton7.addEventListener("touchstart", () => { startTeleop("backwardL"); });
teleopButton8.addEventListener("touchstart", () => { startTeleop("backward"); });
teleopButton9.addEventListener("touchstart", () => { startTeleop("backwardR"); });

teleopButton1.addEventListener("touchend", () => { stopTeleop(); });
teleopButton2.addEventListener("touchend", () => { stopTeleop(); });
teleopButton3.addEventListener("touchend", () => { stopTeleop(); });
teleopButton4.addEventListener("touchend", () => { stopTeleop(); });
teleopButton5.addEventListener("touchend", () => { stopTeleop(); });
teleopButton6.addEventListener("touchend", () => { stopTeleop(); });
teleopButton7.addEventListener("touchend", () => { stopTeleop(); });
teleopButton8.addEventListener("touchend", () => { stopTeleop(); });
teleopButton9.addEventListener("touchend", () => { stopTeleop(); });

function teleop(linearSpeedX, angularSpeedZ) {
    if (teleopSwitch.checked) {
        let data = {
            linearX: linearSpeedX,
            angularZ: angularSpeedZ
        };
        socketio.emit("teleoperate", data);
    }
};


function startTeleop(direction) {
    teleopTimer = setInterval(function() {
        teleop(speeds[direction]["linear"], speeds[direction]["angular"]);
    }, teleopTimeout);
}


async function stopTeleop() {
    clearInterval(teleopTimer);
    await sleep(teleopTimeout);
    teleop(0.0, 0.0);
}

// Navigation
let navStatus = "PENDING";
let navGoal = {};

// Set navigation goal when user clicks a point on map
map.on("click", function(event) {
    const navGoalDD = document.getElementById("inputNavGoal");
    if (navGoalDD.value === "mapClick" && navStatus === "PENDING") {
        let clickedMapPointLat = event.latlng.lat;
        let clickedMapPointLon = event.latlng.lng;
        navGoal = {
            mapClick: {
                latitude: clickedMapPointLat,
                longitude: clickedMapPointLon,
            }
        };
        goalMarkerGroup.clearLayers();
        L.marker(
            L.latLng(clickedMapPointLat, clickedMapPointLon),
            {"icon": navTargetIcon},
        ).addTo(goalMarkerGroup);
    }
});

// Set navigation goal
function setNavGoal(selectedGoal) {
    if (navStatus !== "PENDING" || selectedGoal === "mapClick") {
        return
    }
    if (selectedGoal === "mfgLab" || selectedGoal === "roboLab") {
        navGoal = {
            goal: selectedGoal
        };
    } else if (selectedGoal === "auto2robo" || selectedGoal === "robo2auto") {
        navGoal = {
            route: selectedGoal
        };
    }
};

// Start a navigation task
function navStart() {
    if (navStatus === "ACTIVE") {
        return;
    }
    disableTeleopButtons(true);
    navStatus = "ACTICE";
    document.getElementById("navStatus").innerHTML = "ACTIVE   ";
    const startNavButton = document.getElementById("navStart");
    teleopSwitch.disabled = true;
    startNavButton.disabled = true;
    socketio.emit("start_navigation", navGoal);
};

// Cancel the navigation task
function navStop() {
    socketio.emit("stop_navigation");
};

function resetNavFeedback() {
    navStatus = "PENDING";
    document.getElementById("navStatus").innerHTML = "PENDING  ";
    document.getElementById("navTimeRem").innerHTML = 0.0;
    document.getElementById("navDistRem").innerHTML = 0.0;
    document.getElementById("navNavTime").innerHTML = 0.0;
    document.getElementById("navNumRecs").innerHTML = 0;
    teleopSwitch.disabled = false;
    document.getElementById("navStart").disabled = false;
    disableTeleopButtons(true);
};


function disableTeleopButtons(isDisabled) {
    teleopButton1.disabled = isDisabled;
    teleopButton2.disabled = isDisabled;
    teleopButton3.disabled = isDisabled;
    teleopButton4.disabled = isDisabled;
    // stop button remains enabled
    teleopButton6.disabled = isDisabled;
    teleopButton7.disabled = isDisabled;
    teleopButton8.disabled = isDisabled;
    teleopButton9.disabled = isDisabled;
};

disableTeleopButtons(true);
resetNavFeedback();