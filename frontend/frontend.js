var map = L.map('map', {center: [48.709936, 21.238923], zoom: 15}),
    realtime = L.realtime(undefined, {
        getFeatureId: function(f) { return f.id; },
        start: false
    }).addTo(map);

function update(e) {
    realtime.update(e);
}

function remove(e) {
    realtime.remove(e);
}

L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

var source = new EventSource('http://api.chab.us/buses/tail');
source.addEventListener('add', update);
source.addEventListener('change', update);
source.addEventListener('remove', remove);

realtime.on('update', function(e) {
    var popupContent = function(fId) {
            var features = e.features[fId];
            return '<h3>' + features.properties.type+ '</h3>' +
                JSON.stringify(features.properties, null, 4);
        },

        bindFeaturePopup = function(fId) {
            realtime.getLayer(fId).bindPopup(popupContent(fId));
        },
        updateFeaturePopup = function(fId) {
            realtime.getLayer(fId).getPopup().setContent(popupContent(fId));
        };

    Object.keys(e.enter).forEach(bindFeaturePopup);
    Object.keys(e.update).forEach(updateFeaturePopup);
});



var ws = new WebSocket("ws://127.0.0.1:5678/"),
    messages = document.createElement('ul');
ws.onmessage = function (event) {
    update( JSON.parse(event.data));
    // var geoJson = JSON.parse(event.data);
    // var metadata = JSON.stringify( geoJson.features);
    //
    // var messages = document.getElementsByTagName('ul')[0],
    //     message = document.createElement('li'),
    //     content = document.createTextNode(metadata);
    //
    //
    //
    // message.appendChild(content);
    // messages.appendChild(message);
};




