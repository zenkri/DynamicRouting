let map, geocoder, positionMarker, destMarker, DESTINATION, ROUTE;

function initMap() {

  map = L.map('map').setView([51.505, -0.09], 13);

  L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  // Create marker to simulate current position of the bike
  var myIcon = L.icon({
    iconUrl: 'marker.png',
    iconSize: [48, 48],
    iconAnchor: [24, 24]
  });

  let marker_options = {
    icon: myIcon,
    rotationAngle: 0
  };
  positionMarker = L.marker([50.5, 30.5], marker_options).addTo(map);

  // HERE for geocoding
  const options = {
    // No payment info, if you take it, do what you want ;-)
    app_id: 'iGrkm2eWsMPxtak51DvP',
    app_code: 'ZstERggksSlagIeBdYr11g'
  }

  geocoder = L.Control.Geocoder.here(options);
}

function geocode(input) {

  if (geocoder) {
    geocoder.geocode(input, (result) => {
      // Update in frontend
      $("#geocode-preview").empty();

      if (result.length === 0) return;
      for (let i = 0; i < 3; i++) {

        let li = document.createElement("LI");
        li.classList.add('listItem');

        if (result[i] != undefined) {

          result = result[i];

          li.innerHTML = result.name;
          li.addEventListener('click', function () {

            $('#marker_select').innerHTML = 'Change marker';
            let pos = new L.latLng(result.center.lat, result.center.lng);

            map.setView(pos, 16);

            if (destMarker === undefined) {
              destMarker = L.marker(map.getCenter());
            }
            destMarker.setLatLng(pos).addTo(map);
            DESTINATION = result;

            //L.marker(pos).addTo(map);

          })
          $("#geocode-preview").append(li);
        }
      }
    });
  }

}

function updateMarker(location, bearing) {

  positionMarker.setLatLng(location);
  positionMarker.setRotationAngle(bearing);
  map.setView(location, 20);

}

function generateRoute(start, dest) {

  start = start.lng + ',' + start.lat
  dest = dest.lng + ',' + dest.lat

  const body = {
    "coordinates": [
      [8.681495, 49.41461],
      [8.686507, 49.41943],
      [8.687872, 49.420318]
    ],
    "elevation": "true",
    "extra_info": ["surface"]
  };



  jQuery.ajax({
      url: "https://api.openrouteservice.org/v2/directions/cycling-electric/",
      type: "GET",
      data: {
        // No payment info, if you take it, do what you want ;-)
        "api_key": "5b3ce3597851110001cf624832a8bcb522f2464c9e4167d598d4bc15",
        "start": start,
        "end": dest
      },
    })
    .done(function (data, textStatus, jqXHR) {
      // console.log("HTTP Request Succeeded: " + jqXHR.status);
      // console.log(data);

      ROUTE = L.geoJSON(data.features[0].geometry).addTo(map);
      map.fitBounds(ROUTE.getBounds());

      // $('#overlay').animate({
      //   right: '-44vh'
      // })
      // $('#chevron-left').show();
      // $('#chevron-right').hide();

      // Now lets check if dis is doable!

      // Init Call to our API to validate the route

      is_doable = false;

      if (!is_doable) {
        // Init routing call again, now with proposed stop
        $('#insufficient_power').show();
        // $('#spinner').hide();



        closestStation = L.geoJSON(altRoute.closest_station)
        altRoute = L.geoJSON(altRoute.features[0]);

        console.log(closestStation);
        console.log(altRoute);


      } else {
        $('#sufficient_power').show();
        $('#spinner').hide();
      }




    })
    .fail(function (jqXHR, textStatus, errorThrown) {
      console.log("HTTP Request Failed");
    })
    .always(function () {

    });


}