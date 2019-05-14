COBI.init('token');

// Make clock appear in upper right corner
COBI.app.clockVisible.write(false);
// Also listen to standard controller events
COBI.devkit.overrideThumbControllerMapping.write(true);

// Disable Reordering in Experience
var inEditMode = (COBI.parameters.context() == COBI.context.offRideSettings || COBI.parameters.context() == COBI.context.onRideSettings);

// Initiate Map
$(function() { 
  initMap();
 
  COBI.mobile.location.subscribe(function(location){
    let loc = new L.latLng([location.coordinate.latitude, location.coordinate.longitude])
    LOCATION = location
    updateMarker(loc, location.bearing);
  });


  /**
   * 
   * Click-Listeners for several stuff
   */

  $('#chevron-left').on('click', () => {

    $('#overlay').animate({right:0})
    $('#chevron-left').hide();
    $('#chevron-right').show();

  })

  $('#chevron-right').on('click', () => {

    $('#overlay').animate({right:'-44vh'})
    $('#chevron-left').show();
    $('#chevron-right').hide();

  })


  $('#marker_select').on('click', () => {

    $('#marker_select').hide();

    $('#map').css('z-index', '0');
    $('.leaflet-control-container').css('display','inline')
    
    console.log(destMarker);

    if(destMarker === undefined){
      destMarker = new L.marker(map.getCenter()).addTo(map);
    }

    map.on('move', function () {
      destMarker.setLatLng(map.getCenter());
    });

  })
  
  // Contact API of the boys here
  $('#check_route').on('click', () => {

    map.off('move');

    if(DESTINATION === undefined){
      alert('Not yet ready, sorry');
      return;
    }

    $('#map').css('z-index', '-2');
    $('.leaflet-control-container').css('display','none')

    $('#marker_select').hide();
    $('#form-stacked-text').hide();
    $('#geocode-preview').hide();
    
    $('#destination_text').text(DESTINATION.name);
    $('#destination_text').show();
    $('#spinner').show();
    

    generateRoute(positionMarker.getLatLng(), destMarker.getLatLng());

    console.log('gonna check some routes');


  })


  

  $("#form-stacked-text").on("keyup", (e) => {
    if(e.target.value.length < 3){
      $("#geocode-preview").empty();
      return;
    }
  
    if(e.target.value.length === 0){
      $("#geocode-preview").empty();
    }
    geocode(e.target.value);
  
  });
});






// Define id, name, events, formatting functions, units and default value for each item
var definitions = [
  {
    id: 'speed',
    name: 'Speed',
    subscribe: COBI.rideService.speed.subscribe,
    unsubscribe: COBI.rideService.speed.unsubscribe,
    formatter: formatSpeedDot1,
    unit: 'km/h',
    defaultValue: '-'
  },
  {
    id: 'average_speed',
    name: 'Avg Speed',
    subscribe: COBI.tourService.averageSpeed.subscribe,
    unsubscribe: COBI.tourService.averageSpeed.unsubscribe,
    formatter: formatSpeedDot1,
    unit: 'Ø km/h',
    defaultValue: '-'
  },
  {
    id: 'user_power',
    name: 'User Power',
    subscribe: COBI.rideService.userPower.subscribe,
    unsubscribe: COBI.rideService.userPower.unsubscribe,
    formatter: formatInt,
    unit: 'watts',
    defaultValue: '-'
  },
  {
    id: 'cadence',
    name: 'Cadence',
    subscribe: COBI.rideService.cadence.subscribe,
    unsubscribe: COBI.rideService.cadence.unsubscribe,
    formatter: formatInt,
    unit: 'rpm',
    defaultValue: '-'
  },
  {
    id: 'distance',
    name: 'Distance',
    subscribe: COBI.tourService.ridingDistance.subscribe,
    unsubscribe: COBI.tourService.ridingDistance.unsubscribe,
    formatter: formatDistanceDot1,
    unit: 'km total',
    defaultValue: '-'
  },
  {
    id: 'calories',
    name: 'Calories',
    subscribe: COBI.tourService.calories.subscribe,
    unsubscribe: COBI.tourService.calories.unsubscribe,
    formatter: formatInt,
    unit: 'kcal',
    defaultValue: '-'
  },
  {
    id: 'ascent',
    name: 'Ascent',
    subscribe: COBI.tourService.ascent.subscribe,
    unsubscribe: COBI.tourService.ascent.unsubscribe,
    formatter: formatInt,
    unit: 'm',
    defaultValue: '-'
  },
  {
    id: 'heart_rate',
    name: 'Heart Rate',
    subscribe: COBI.rideService.heartRate.subscribe,
    unsubscribe: COBI.rideService.heartRate.unsubscribe,
    formatter: formatInt,
    unit: 'bpm',
    defaultValue: '-'
  },
  {
    id: 'duration',
    name: 'Duration',
    subscribe: COBI.tourService.ridingDuration.subscribe,
    unsubscribe: COBI.tourService.ridingDuration.unsubscribe,
    formatter: formatMins,
    unit: 'min',
    defaultValue: '-'
  }
];
