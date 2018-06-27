function init_map() {
    window.oncontextmenu = function() { return false };

    var map = L.map('map').setView([51.505, -0.09], 16);

    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var position = null;
    var buttonPressed = false;

    function locationFound(position) {
        map.setView([position.coords.latitude, position.coords.longitude]);
    }

    function updateLocation(lat, lng) {
        if (position != null) {
            map.removeLayer(position);
        }
        position = L.circle([lat, lng], 5);
        map.addLayer(position);
        data = {
            'lat': lat,
            'lon': lng,
        };
        $.get("/send_position/"+encodeURIComponent(JSON.stringify(data)), function(data) {
            updateLocation(data.location.lat, data.location.lng)
        }, "json" );
    }

    function move(c) {
        if (position == null) { return; }

        pos = position.getLatLng();
        if (c == 'w') { pos.lat += 0.0001 }
        if (c == 'a') { pos.lng -= 0.0001 }
        if (c == 's') { pos.lat -= 0.0001 }
        if (c == 'd') { pos.lng += 0.0001 }
        if (c == 'q') { pos.lat += 0.0001; pos.lng -= 0.0001 }
        if (c == 'e') { pos.lat += 0.0001; pos.lng += 0.0001 }
        if (c == 'z') { pos.lat -= 0.0001; pos.lng -= 0.0001 }
        if (c == 'x') { pos.lat -= 0.0001 }
        if (c == 'c') { pos.lat -= 0.0001; pos.lng += 0.0001 }
        position.setLatLng(pos);
        data = {
            'lat': pos.lat,
            'lon': pos.lng,
        };
        $.get("/send_position/"+encodeURIComponent(JSON.stringify(data)), function(data) {
            updateLocation(data.location.lat, data.location.lng)
        }, "json" );
    }

    function onMousemove(e) {
        if (buttonPressed) {
            updateLocation(e.latlng.lat, e.latlng.lng);
        }
    }

    function onClick(e) {
        updateLocation(e.latlng.lat, e.latlng.lng);
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(locationFound, function() {});
    }

    map.on('mousemove', onMousemove);
    map.on('click', onClick);

    $(document).mousedown(function(e){
        if (e.which == 3) { 
            buttonPressed = true; 
            e.preventDefault();
        }
    });

    $(document).mouseup(function(e){
        if (e.which == 3 || e.which == 1) { buttonPressed = false; }
    });

    $("#map").keypress(function(e) {
        c = String.fromCharCode(e.which);
        move(c)
    })
}

$(document).ready(init_map)
