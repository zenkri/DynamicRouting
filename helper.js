const fs = require('fs');

let cobi_input = require('./ebike-15min-ride.json')

let coords = []

cobi_input.forEach(element => {
  if (element.path === 'mobile/location') {

    curr = element.payload

    let myCoords = {
          lat : curr.coordinate.latitude,
          lng : curr.coordinate.longitude
    }
    
    coords.push(myCoords)
  }
});


fs.writeFileSync('coords.json', JSON.stringify(coords))


/**
 * 
 * 
 * 47.470089, 11.026281 = Start
 * 47.464454, 11.021392 = Gasthof
 * 47.446186, 11.023020 = Destination? Waxenstein
 * 
 * 
 */