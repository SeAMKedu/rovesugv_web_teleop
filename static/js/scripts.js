//----------------------------------------------------------------------------
// General
//----------------------------------------------------------------------------
function setTheme(theme) {
    document.documentElement.setAttribute("data-bs-theme", theme);
};

async function sleep(time_ms) {
    await new Promise(resolve => setTimeout(resolve, time_ms));
}


//----------------------------------------------------------------------------
// SocketIO
//----------------------------------------------------------------------------
const connIcon = document.getElementById("connIcon");
const connStatus = document.getElementById("connStatus");
const alertPlaceholder = document.getElementById("alertPlaceholder");
const appendAlert = (message, type) => {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = [
        `<div class="alert alert-${type} alert-dismissible" role="alert">`,
        `   <div>${message}</div>`,
        '   <button type="button" class="btn-close" id="alertClose" data-bs-dismiss="alert" aria-label="Close"></button>',
        '</div>'
    ].join("");
    alertPlaceholder.append(wrapper);
};

let socketio = io();

socketio.on("alert", function(alertMessage) {
    console.log(alertMessage);
    appendAlert(alertMessage.msg, alertMessage.type);
});

socketio.on("connection", function(msg) {
    connIcon.classList.remove("fa-link-slash");
    connIcon.classList.add("fa-link");
    connStatus.classList.add("active");
    const alertClose = document.getElementById("alertClose");
    if (alertClose) {
        alertClose.click();
    }
    socketio.on("disconnect", function() {
        connIcon.classList.remove("fa-link");
        connIcon.classList.add("fa-link-slash");
        connStatus.classList.remove("active");
        //appendAlert("Connection to server lost", "danger");
    });
});


//----------------------------------------------------------------------------
// Leaflet
//----------------------------------------------------------------------------
let mapZoom = 17;
let roverLat = 62.789252;
let roverLon = 22.821627;

let map = L.map("map", {}).setView([roverLat, roverLon], 17);

let roverArrow = L.polyline([
    [roverLat, roverLon],
    [roverLat - 0.000001, roverLon - 0.000002]
]).arrowheads().addTo(map);

let roverIcon = L.icon({
    iconUrl: "/static/img/rover.png",
    iconSize: [30, 30],
});

let roverMarker = L.marker(
    [roverLat, roverLon], 
    {icon: roverIcon}
).addTo(map);

let navIconStart = L.icon({
    iconUrl: "/static/img/navStart.png",
    iconSize: [34, 34]
});

let navIconGoal = L.icon({
    iconUrl: "/static/img/navGoal.png",
    iconSize: [36, 35]
});

let navIconLayer = L.layerGroup();
let navWaypoints = L.polyline([]);
let plannedPath = L.polyline([], {color: "red"});

L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

function clearMap() {
    navIconLayer.clearLayers();
    navWaypoints.remove();
};

function showNavIcon(latitude, longitude, navIcon) {
    let location = L.latLng(latitude, longitude);
    L.marker(location, {icon: navIcon}).addTo(navIconLayer);
};

map.addLayer(navIconLayer);

map.on("click", function(event) {
    if (isNavActive) {
        return;
    }
    if (navSelect.value === "mapPoint") {
        clearMap();
        showNavIcon(roverLat, roverLon, navIconStart);
        showNavIcon(event.latlng.lat, event.latlng.lng, navIconGoal);
        navGoal = {
            goal: "mapPoint",
            latitude: event.latlng.lat,
            longitude: event.latlng.lng,
            yaw: yawToRadians()
        };
    }
});

//----------------------------------------------------------------------------
// Navigation
//----------------------------------------------------------------------------
const yawArrow = document.getElementById("yawArrow");
const yawInput = document.getElementById("yawInput");
const yawOutput = document.getElementById("yawOutput");
const navSelect = document.getElementById("navSelect");
const navResetBtn = document.getElementById("navResetBtn");
const navStartBtn = document.getElementById("navStartBtn");
const navStatus = document.getElementById("navStatus");
const navNavTime = document.getElementById("navNavTime");
const navTimeRem = document.getElementById("navTimeRem");
const navDistRem = document.getElementById("navDistRem");
const navNumRecs = document.getElementById("navNumRecs");
let isNavActive;
let navGoal = {};

yawOutput.textContent = yawInput.value;

yawInput.addEventListener("input", function() {
    yawArrow.style.transform = `rotate(${-this.value}deg)`;
    yawOutput.textContent = this.value;
    navGoal.yaw = parseInt(yawInput.value);
});

function disableElements(isDisabled) {
    navSelect.disabled = isDisabled;
    yawInput.disabled = isDisabled;
    navResetBtn.disabled = isDisabled;
    navStartBtn.disabled = isDisabled;
    teleopSwitch.disabled = isDisabled;
};

async function onNavResult() {
    await sleep(5000);
    navStatus.innerHTML = "PENDING";

    plannedPath.remove();
    clearMap();
    disableElements(false);
    yawInput.value = 0;
    yawOutput.textContent = yawInput.value;
    navNavTime.innerHTML = 0.0;
    navTimeRem.innerHTML = 0.0;
    navDistRem.innerHTML = 0.0;
    navNumRecs.innerHTML = 0;
};

function stopNav() {
    clearMap();
    disableElements(false);
    disableTeleop(false);
    socketio.emit("stop_navigation");
};

function resetNav() {
    if (isNavActive) {
        return;
    }
    clearMap();
    let navGoal = "";
    yawInput.value = 0;
    yawArrow.style.transform = `rotate(0deg)`;
    yawOutput.textContent = yawInput.value;
};

function startNav() {
    if (isNavActive) {
        appendAlert("Navigation is already running", "danger");
        return;
    }
    disableElements(true);
    disableTeleop(true);
    navStatus.innerHTML = "ACTIVE";
    socketio.emit("start_navigation", navGoal);
};

function setNavGoal(selectedGoal) {
    clearMap();
    navGoal = {goal: selectedGoal};
    if (selectedGoal === "mapPoint") {
        navGoal.yaw = parseInt(yawInput.value);
        return;
    }
    socketio.emit("get_waypoints", selectedGoal);
};

function yawToRadians() {
    return parseInt(yawInput.value) * Math.PI / 180;
};

socketio.on("nav_feedback", function(msg) {
    navNavTime.innerHTML = msg.navigation_time;
    navTimeRem.innerHTML = msg.estimated_time_remainging;
    navDistRem.innerHTML = msg.distance_remaining;
    navNumRecs.innerHTML = msg.number_of_recoveries;
});

socketio.on("nav_path", function(msg) {
    plannedPath.setLatLngs(msg.path).addTo(map);
});

socketio.on("nav_result", function(msg) {
    navStatus.innerHTML = msg;
    onNavResult();
});

socketio.on("nav_status", function(navigation_status) {
    isNavActive = navigation_status;
});

socketio.on("nav_waypoints", function(waypoints) {
    let startPoint = waypoints[0];
    let goalPoint = waypoints[waypoints.length-1];
    navWaypoints.remove();
    navWaypoints = L.polyline(waypoints, {color: "green"}).arrowheads({
        frequency: "50px",
        size: "10px"
    }).addTo(map);
    if (startPoint === goalPoint) {
        showNavIcon(roverLat, roverLon, navIconStart);
    } else {
        showNavIcon(startPoint[0], startPoint[1], navIconStart);
    }
    showNavIcon(goalPoint[0], goalPoint[1], navIconGoal);
});

//----------------------------------------------------------------------------
// Teleop
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

let roverSpeed = 0.5;

disableTeleop(true);

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
        let data = {
            linearX: linearSpeedX,
            angularZ: angularSpeedZ
        };
        socketio.emit("teleoperate", data);
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

teleopSwitch.addEventListener("change", function() {
    if (this.checked) {
        teleopStatus.innerHTML = "ON";
        disableTeleop(false);
    } else {
        teleopStatus.innerHTML = "OFF";
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


//----------------------------------------------------------------------------
// Location
//----------------------------------------------------------------------------
const locationLat = document.getElementById("locationLat");
const locationLon = document.getElementById("locationLon");
const locationAlt = document.getElementById("locationAlt");

socketio.on("navsatfix", function(msg) {
    roverLat = msg.lat;
    roverLon = msg.lon;
    locationLat.innerHTML = msg.lat;
    locationLon.innerHTML = msg.lon;
    locationAlt.innerHTML = msg.alt;
    roverArrow.setLatLngs([[
        [roverLat, roverLon],
        [msg.arrowhead.lat, msg.arrowhead.lon]
    ]]).arrowheads().addTo(map);
    roverMarker.setLatLng([roverLat, roverLon]).addTo(map);
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