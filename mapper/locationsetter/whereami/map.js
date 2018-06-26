function init_map() {
    var map = L.map('map').setView([51.505, -0.09], 16);

    L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var position = null;

    function updateLocation(lat, lng) {
        if (position != null) {
            map.removeLayer(position);
        }
        position = L.circle([lat, lng], 5);
        map.addLayer(position);
        map.setView([lat, lng]);
    }

    function update() {
        $.get("/getpos", function(data) {
            updateLocation(data.location.lat, data.location.lng)
        }, "json" );
    }

    setInterval(update, 500);
}

$(document).ready(init_map)
