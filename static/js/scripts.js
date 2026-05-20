//----------------------------------------------------------------------------
// General
//----------------------------------------------------------------------------
function setTheme(theme) {
    document.documentElement.setAttribute("data-bs-theme", theme);
};

async function sleep(time_ms) {
    await new Promise(resolve => setTimeout(resolve, time_ms));
};


//----------------------------------------------------------------------------
// SocketIO
//----------------------------------------------------------------------------
const connIcon = document.getElementById("connIcon");
const connStatus = document.getElementById("connStatus");

var socketio = io();

socketio.on("connection", function(msg) {
    connIcon.classList.remove("fa-link-slash");
    connIcon.classList.remove("fa-fade");
    connIcon.classList.add("fa-link");
    connStatus.classList.add("active");

    console.log(msg);
    isNavActive = msg.navigation.is_active;
    roverLat = msg.rover.latitude;
    roverLon = msg.rover.longitude;
    roverMarker.setLatLng([roverLat, roverLon]);
    map.setView([roverLat, roverLon], 19);

    if (isNavActive) {
        navStatus.innerHTML = "ACTIVE";
        navSelect.disabled = true;
        yawInput.disabled = true;
        navResetBtn.disabled = true;
        navStartBtn.disabled = true;
        teleopSwitch.disabled = true;
        disableTeleop(true);
        showNavMarker(
            msg.navigation.start_location.latitude, 
            msg.navigation.start_location.longitude, 
            navStartIcon
        );
        showNavMarker(
            msg.navigation.goal_pose.latitude, 
            msg.navigation.goal_pose.longitude, 
            navGoalIcon
        );
    } else {
        teleopSwitch.disabled = false;
    }

    socketio.on("disconnect", function() {
        connIcon.classList.remove("fa-link");
        connIcon.classList.add("fa-link-slash");
        connIcon.classList.add("fa-fade");
        connStatus.classList.remove("active");
    });
});


//----------------------------------------------------------------------------
// Alerts
//----------------------------------------------------------------------------
const alertPlaceholder = document.getElementById("alertPlaceholder");
const showAlert = (alertType, alertMessage) => {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = [
        `<div class="alert alert-${alertType} alert-dismissible" role="alert">`,
        `   <div>${alertMessage}</div>`,
        '   <button type="button" class="btn-close" id="alertClose" data-bs-dismiss="alert" aria-label="Close"></button>',
        '</div>'
    ].join("");
    alertPlaceholder.append(wrapper);
};

socketio.on("alert", function(msg) {
    showAlert(msg.type, msg.message);
});


//----------------------------------------------------------------------------
// Emergency Stop
//----------------------------------------------------------------------------
const eStopButton = document.getElementById("eStopButton");


function e_stop(message) {
    socketio.emit("e_stop", message);
};


//----------------------------------------------------------------------------
// Map
//----------------------------------------------------------------------------
var map = L.map("map", {});

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

var navStartIcon = L.icon({
    iconUrl: "/static/img/navStart.png",
    iconSize: [34, 34]
});

var navGoalIcon = L.icon({
    iconUrl: "/static/img/navGoal.png",
    iconSize: [36, 35]
});

var navMarkerLayer = L.layerGroup();
map.addLayer(navMarkerLayer);

var navWaypoints = L.polyline([], {color: "green"}).arrowheads({
    frequency: "50px",
    size: "10px"
}).addTo(map);

var plannedPath = L.polyline([], {color: "red"});


function clearMap() {
    navMarkerLayer.clearLayers();
    navWaypoints.remove();
    plannedPath.remove();
};


function showNavMarker(latitude, longitude, navIcon) {
    let markerLocation = L.latLng(latitude, longitude);
    L.marker(markerLocation, {icon: navIcon}).addTo(navMarkerLayer);
};

// Rover
var roverLat = 0.0;
var roverLon = 0.0;

var roverArrow = L.polyline([
    [roverLat, roverLon],
    [roverLat - 0.000001, roverLon - 0.000002]
]).arrowheads().addTo(map);

var roverIcon = L.icon({
    iconUrl: "/static/img/rover.png",
    iconSize: [30, 30],
});

var roverMarker = L.marker(
    [roverLat, roverLon], 
    {icon: roverIcon}
).addTo(map);


//----------------------------------------------------------------------------
// Navigation
//----------------------------------------------------------------------------
const navSelect = document.getElementById("navSelect");

const yawArrow = document.getElementById("yawArrow");
const yawInput = document.getElementById("yawInput");
const yawOutput = document.getElementById("yawOutput");

const navResetBtn = document.getElementById("navResetBtn");
const navStartBtn = document.getElementById("navStartBtn");

const navStatus = document.getElementById("navStatus");
const navNavTime = document.getElementById("navNavTime");
const navTimeRem = document.getElementById("navTimeRem");
const navDistRem = document.getElementById("navDistRem");
const navNumRecs = document.getElementById("navNumRecs");

var isNavActive = false;
var navGoal = {};

yawOutput.textContent = `${yawInput.value}°`;


yawInput.addEventListener("input", function() {
    yawArrow.style.transform = `rotate(${-this.value}deg)`;
    yawOutput.textContent = `${this.value}°`;
    navGoal.yaw = yawToRadians();
});


function yawToRadians() {
    return parseInt(yawInput.value) * Math.PI / 180;
};


map.on("click", function(event) {
    if (isNavActive) {
        showAlert("warning", "Navigation is running");
        return;
    }
    if (navSelect.value === "mapPoint") {
        clearMap();
        showNavMarker(roverLat, roverLon, navStartIcon);
        showNavMarker(event.latlng.lat, event.latlng.lng, navGoalIcon);
        navGoal = {
            goal: navSelect.value,
            latitude: event.latlng.lat,
            longitude: event.latlng.lng,
            yaw: yawToRadians(),
            startLat: roverLat,
            startLon: roverLon
        };
    }
});


function setNavGoal(selectedGoal) {
    clearMap();
    navGoal.goal = selectedGoal;
    if (selectedGoal === "mapPoint") {
        return;
    }
    socketio.emit("get_waypoints", selectedGoal);
};


function startNav() {
    if (isNavActive) {
        showAlert("warning", "Navigation is running");
        return;
    }
    if (Object.keys(navGoal).length === 0) {
        showAlert("danger", "No navigation goal set");
        return;
    }
    if (navSelect.value === "mapPoint") {
        navGoal.yaw = yawToRadians();
        navGoal.startLat = roverLat;
        navGoal.startLon = roverLon;
        if (!("latitude" in navGoal)) {
            showAlert("danger", "No goal point set. Please click the map.");
            return;
        }
    } else if (navSelect.value === "maptLab" || navSelect.value === "roboLab") {
        navGoal.startLat = roverLat;
        navGoal.startLon = roverLon;
    }

    isNavActive = true;
    
    navStatus.innerHTML = "ACTIVE";
    navSelect.disabled = true;
    yawInput.disabled = true;
    navResetBtn.disabled = true;
    navStartBtn.disabled = true;
    teleopSwitch.disabled = true;
    
    socketio.emit("navigation_task", {task: "start", goal: navGoal});
};


function resetNav() {
    if (isNavActive) {
        showAlert("warning", "Navigation is running");
        return;
    }
    yawArrow.style.transform = `rotate(0deg)`;
    yawInput.value = "0";
    yawOutput.textContent = `${yawInput.value}°`;

    navSelect.disabled = false;
    yawInput.disabled = false;
    navResetBtn.disabled = false;
    navStartBtn.disabled = false;

    navStatus.innerHTML = "PENDING";
    navNavTime.innerHTML = 0.0.toFixed(1);
    navTimeRem.innerHTML = 0.0.toFixed(1);
    navDistRem.innerHTML = 0.0.toFixed(1);
    navNumRecs.innerHTML = 0;

    teleopSwitch.disabled = false;

    clearMap();

    navGoal = {};
};


function stopNav() {
    navGoal = {};
    socketio.emit("navigation_task", {task: "stop", goal: navGoal});
};


socketio.on("nav_feedback", function(msg) {
    navNavTime.innerHTML = msg.navigation_time;
    navTimeRem.innerHTML = msg.estimated_time_remaining;
    navDistRem.innerHTML = msg.distance_remaining;
    navNumRecs.innerHTML = msg.number_of_recoveries;
});


socketio.on("nav_path", function(msg) {
    plannedPath.setLatLngs(msg.path).addTo(map);;
});


async function onNavResult() {
    await sleep(5000);
    resetNav();
    const alertClose = document.getElementById("alertClose");
    if (alertClose) {
        alertClose.click();
    }
};


socketio.on("nav_result", function(msg) {
    isNavActive = false;
    navStatus.innerHTML = msg.result;
    onNavResult();
});


socketio.on("nav_status", function(msg) {
    isNavActive = msg.is_active;
});


socketio.on("nav_waypoints", function(msg) {
    let firstWaypoint = msg.waypoints[0];
    let lastWaypoint = msg.waypoints[msg.waypoints.length - 1];
    let startLatitude = 0.0;
    let startLongitude = 0.0;
    
    if (firstWaypoint === lastWaypoint) {
        startLatitude = roverLat;
        startLongitude = roverLon;
    } else {
        startLatitude = firstWaypoint[0];
        startLongitude = firstWaypoint[1];
    }
    
    navWaypoints.setLatLngs(msg.waypoints).addTo(map);
    showNavMarker(startLatitude, startLongitude, navStartIcon);
    showNavMarker(lastWaypoint[0], lastWaypoint[1], navGoalIcon);
    
    navGoal.latitude = lastWaypoint[0];
    navGoal.longitude = lastWaypoint[1];
    navGoal.yaw = lastWaypoint[2];
    navGoal.startLat = startLatitude;
    navGoal.startLon = startLongitude;
});


//----------------------------------------------------------------------------
// Teleoperation
//----------------------------------------------------------------------------
const teleopStatus = document.getElementById("teleopStatus");
const teleopSwitch = document.getElementById("teleopSwitch");

const teleopButton1 = document.getElementById("teleop1");
const teleopButton2 = document.getElementById("teleop2");
const teleopButton3 = document.getElementById("teleop3");
const teleopButton4 = document.getElementById("teleop4");
const teleopButton5 = document.getElementById("teleop5");
const teleopButton6 = document.getElementById("teleop6");
const teleopButton7 = document.getElementById("teleop7");
const teleopButton8 = document.getElementById("teleop8");
const teleopButton9 = document.getElementById("teleop9");

const teleopSpeedBtnMinus = document.getElementById("teleopSpeedBtnMinus");
const teleopSpeed = document.getElementById("teleopSpeed");
const teleopSpeedBtnPlus = document.getElementById("teleopSpeedBtnPlus");

const teleopTimeout = 500; // in milliseconds
const roverSpeedMin = 0.5;
const roverSpeedMax = 2.0;
const angularSpeed = 0.5;

var roverSpeed = 0.5;
var isTeleopEnabled = false;
var teleopTimer = null;


function disableTeleop(isDisabled) {
    let teleopButtons = [
        teleopButton1, teleopButton2, teleopButton3,
        teleopButton4, teleopButton5, teleopButton6,
        teleopButton7, teleopButton8, teleopButton9,
        teleopSpeedBtnMinus, teleopSpeedBtnPlus
    ]
    for (let i=0; i<teleopButtons.length; i++) {
        teleopButtons[i].disabled = isDisabled;
    }
};


function getRoverSpeed(direction, linearSpeed) {
    let speeds = {
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
    return speeds[direction]
};


function setRoverSpeed(direction) {
    if (direction === -1) {
        roverSpeed = roverSpeed - 0.1;
        if (roverSpeed < roverSpeedMin) {
            roverSpeed = roverSpeedMin;
        }
    } else if (direction === 1) {
        roverSpeed = roverSpeed + 0.1;
        if (roverSpeed > roverSpeedMax) {
            roverSpeed = roverSpeedMax;
        }
    }
    teleopSpeed.value = Math.round(roverSpeed * 10) / 10;
};


function teleop(linearSpeedX, angularSpeedZ) {
    if (teleopSwitch.checked) {
        let speedValues = {
            linearX: linearSpeedX,
            angularZ: angularSpeedZ
        };
        socketio.emit("teleoperate", speedValues);
    }
};


function startTeleop(direction) {
    teleopTimer = setInterval(function() {
        let speed = getRoverSpeed(direction, roverSpeed);
        teleop(speed.linear, speed.angular);
    }, teleopTimeout);
}


async function stopTeleop() {
    clearInterval(teleopTimer);
    teleop(0.0, 0.0);
}


teleopSwitch.addEventListener("click", function() {
    if (this.checked) {
        teleopStatus.innerHTML = "ON";
        isTeleopEnabled = true;
        disableTeleop(false);
    } else {
        teleopStatus.innerHTML = "OFF";
        isTeleopEnabled = false;
        disableTeleop(true);
    }
});

// Desktop
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

// Mobile device with touch screen
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

disableTeleop(true);


//----------------------------------------------------------------------------
// Location Information
//----------------------------------------------------------------------------
const locationLat = document.getElementById("locationLat");
const locationLon = document.getElementById("locationLon");
const locationAlt = document.getElementById("locationAlt");

function setMapView() {
    map.setView([roverLat, roverLon], 19);
};

socketio.on("navsatfix", function(msg) {
    roverLat = msg.latitude;
    roverLon = msg.longitude;
    locationLat.innerHTML = msg.latitude.toFixed(9);
    locationLon.innerHTML = msg.longitude.toFixed(9);
    locationAlt.innerHTML = msg.altitude.toFixed(1);
    roverArrow.setLatLngs([[
        [roverLat, roverLon],
        [msg.arrowhead.latitude, msg.arrowhead.longitude]
    ]]).arrowheads();
    roverMarker.setLatLng([roverLat, roverLon]);
});


//----------------------------------------------------------------------------
// Telemetry
//----------------------------------------------------------------------------
const batteryPctIcon = document.getElementById("batteryPctIcon");
const batteryPct = document.getElementById("batteryPct");
const batteryCharge = document.getElementById("batteryCharge");
const batteryCapacity = document.getElementById("batteryCapacity");
const batteryTemp = document.getElementById("batteryTemp");

socketio.on("battery_state", function(msg) {
    batteryPctIcon.classList.remove(...batteryPctIcon.classList);
    batteryPctIcon.classList.add("fas");

    if (msg.percentage > 90.0) {
        batteryPctIcon.classList.add("fa-battery-full");
    } else if (msg.percentage > 75.0) {
        batteryPctIcon.classList.add("fa-battery-three-quarters");
    } else if (msg.percentage > 50.0) {
        batteryPctIcon.classList.add("fa-battery-half");
    } else if (msg.percentage > 25.0) {
        batteryPctIcon.classList.add("fa-battery-quarter");
    } else if (msg.percentage < 10.0) {
        batteryPctIcon.classList.add("fa-battery-empty");
    }

    batteryPct.innerHTML = msg.percentage.toFixed(1);
    batteryCharge.innerHTML = msg.charge.toFixed(1);
    batteryCapacity.innerHTML = msg.capacity;
    batteryTemp.innerHTML = msg.temperature.toFixed(1);
});