//$('document').ready(function(){
//
//var lat = $('#lat').val()
//var lng = $('#lon').val()
//
//while ( Number(lat) == 0 ){
//    lat = $('#lat').val()
//    lng = $('#lon').val()
//}
//console.log('second map added lat', lat, 'lng', lng);
//
//var location = {lat: Number(lat), lng: Number(lng)};
//console.log('location', location);
//var map2 = new google.maps.Map(
//          document.getElementById('map2'), {zoom: 17, center: location});
//map2.setMapTypeId('satellite');
//
//var w = $(document).width();
//var h = $(document).height();
//
////$('.maps').addClass('two-maps');
//
//$('.maps').css({height: h});
//$("#helloMenu").css({width: w, height: Number(h/2)});
//$('.step').css({width: Number(w/3), height: Number(h/2)});
////Сделать перевод пикселей в координаты
//
//
//
//})
//
//function drawRectangles(data){
////Вызывать функцию из html файла и передавать в нее результаты
//console.log('some data', data)
//}
//
//
////Передаем координаты в пикселях и карту - где нужно рисовать
//
//
////bounds = {  north: Number(lng),
////            south: Number(lat),
////            east:  Number(lng+1),
////            west:  Number(lat+1)
////         }