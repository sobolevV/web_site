// global variables
var zoom = 19.8
var map, map2, rectangeMap1, globalLat, globalLon, cropSize, requestAddress, lang, resultGlobal, Area
lang = 'RU'
resultGlobal = ''
cropSize = 25

$('document').ready(function(){
//console.log("document ready");
var h = $(window).height();
var w = $(window).width();
// console.log('h=',h,'w=',w)

$("html, body").animate({scrollTop: 0 }, 100);
// try get geolocation
//submit btn start
if( $('#submitBtn').length ){
    var lng = 48.707067
    var lat = 44.5169033
    if (navigator.geolocation){
        navigator.geolocation.getCurrentPosition(function(position){
            lat = position.coords.latitude;
            lng = position.coords.longitude;
        })
    }

    // Поэтому меняются местами lat и lng
//    window.globalLat = lng
//    window.globalLon = lat

    // Init Google map
    var location = {lat: Number(lng), lng: Number(lat)};
    map = new google.maps.Map(
          document.getElementById('map'), {zoom: 18, center: location});
    map.setMapTypeId('hybrid');

    // init button for request
    sentRequest('#submitBtn');
    // scroll
    $('#checkBtn').click(function(){
    var scr = $("#mapWrapper").offset().top + $('body').scrollTop()
        $("html, body").animate({scrollTop: scr}, 1200);
    })

    $("#pac-input").css({display: 'none'});
    //$("#menu").append()

    // Inputs for geocoding
    setGeoCoder(window.map, 'pac-input-bottom', false);
    setGeoCoder(window.map, 'pac-input-top', false);
    // set inputs for different blocks

    initializeInputAddress('#pac-input-bottom', '#menu');
    initializeInputAddress('#pac-input-top', '#topInput');
    ////////////
    console.log('nuuu')
}
    //$("#pac-input").remove();


//submit button end------------------------------------------------
    // set text for footer
    $("#rights").text("© "+(new Date()).getFullYear()+" ALL RIGHTHS RESERVED, " )
    $('#rights').append($('<a style="color: grey;" href="/</a>'))

     var headerSize = 100;
     // animation header
     $('body').scroll(function() {
          if ( document.body.scrollTop >= headerSize ) {
               $('header').addClass('opacity');
               $('#logo').addClass('heart');
            }
            else {
                $('header').removeClass('opacity');
                $('#logo').removeClass('heart');
            }
    });
    // language change
    $('.lng').click(function(){
        if (window.lang != $(this).attr('id')){
                window.lang = $(this).attr('id')
            //функция, которая заменяет все
            changeLanguage(window.lang);
        }
    })
    $('#RU').addClass('lang-text')
    /////init different functions
    slideBtn();
    slideInfo();
    initButtons();
});

function initButtons(){
    //slide menu
    $('#btn_container > .btn').click(function(){
        if( $("#menu").css("display") == "none" ){
            $("#menu").css({display: 'block'});
        }
    //    check - if btn active -> check menu
        if ($(this).hasClass('color_btn')){
            if ( $('#menu').hasClass('hide') ){
                $('#menu').removeClass('hide');
                $('#menu').slideDown( 'slow' );
                $('#menu').addClass('show')
            }
            else{
                $('#menu').removeClass('show');
                $('#menu').slideUp( 'slow' );
                $('#menu').addClass('hide')
                $(this).removeClass('color_btn')
            }
        }
        else{
            $('#btn_container > .btn').removeClass('color_btn')
            $(this).addClass('color_btn')
            $('#menu').removeClass('hide');
            $('#menu').addClass('show')
            $("#menu > div").css({display: "none"});
            $('#menu').children().eq($(this).index()).css({display: "block"});
        }

    })
}
// set inputs for different blocks
function initializeInputAddress(id, parentId){
    var addressInputElement = $(id);
    $('.pac-container').css({display: 'none'})
    addressInputElement.on('focus', function () {
         var pacContainer = $('.pac-container');
         $(parentId).append(pacContainer);
         if (id == '#pac-input-top'){pacContainer.removeClass('test-pac'); pacContainer.css({top: '40px!important'})}
         else {pacContainer.addClass('test-pac')} //css({top: '143px!important;'})}
    })
    addressInputElement.focusout(function(){
        var pacContainer = $('.pac-container');//.remove();
        pacContainer.removeClass('test-pac')
        pacContainer.css({display: 'none'})
    })
}

function slideBtn(){
    $('#slideBtn').click(function(){
        if ( this.className == 'hide' ){
            $('#slideBtn').removeClass('hide');
            $('#panel').slideDown( "slow" );
            if (window.lang == 'RU' ){$('#slideBtn').text('Скрыть');}
            else {$('#slideBtn').text('Hide');}
            $('#slideBtn').addClass('show')
        }
        else{
            $('#slideBtn').removeClass('show');
            $('#panel').slideUp( "slow" );
            if (window.lang == 'RU' ){$('#slideBtn').text('Показать')}
            else {$('#slideBtn').text('Show')}
            $('#slideBtn').addClass('hide')
        }
    })
}

function slideInfo(){
    $('#info_slider').click(function(){
    var right_panel = $('#right_panel');
    var info_cont = $("#info_container");
        if ( info_cont.hasClass('info_hide') ){

            info_cont.removeClass('info_hide');
            right_panel.animate({ width: '35%'}, 300);
            info_cont.animate({ opacity: '1'}, 600);
            info_cont.addClass('info_show');
        }
        else{
            info_cont.removeClass('info_show');
            info_cont.animate({ opacity: '0'}, 300);
            right_panel.animate({ width: '60px'}, 600);
            info_cont.addClass('info_hide');
        }
    })
}

function sentRequest(buttonId){

    $(buttonId).click(function(){

        if ( Number(window.globalLat) &&  Number(window.globalLon))
            {
            // get coords
            var lat = window.globalLat
            var lon = window.globalLon
            var location, bounds
            var destination = $(window).height()

            // if it first request by user

                // add preloader

            $('#info').empty();
            //$('#mapResultWrapper').css({display: 'none'})

            $('.container').css({display: 'flex'});

                //post coordinates to server
                if (!window.requestAddress){ // if dont have a geoloc coords
                        window.requestAddress = "Неизвестный адрес"
                    }
                $.post('/', {'lat': window.globalLat, 'lon': window.globalLon, 'address': window.requestAddress} ,function(result){
                    var lat = Number(result['lat'])
                    var lng = Number(result['lon'])
                    var location = {lat: Number(lat), lng: Number(lng)};
                    window.resultGlobal = result
        //            if (!window.map2){ // initialize result map
        //                window.map2 = new google.maps.Map(
        //                          document.getElementById('map2'), {zoom: 17, center: location});
        //                window.map2.setMapTypeId('satellite');
        //
        //                window.map2.addListener("click", function (event) {
        //                    var latitude = event.latLng.lat();
        //                    var longitude = event.latLng.lng();
        //                    // console.log( latitude + ', ' + longitude );
        //                    // console.log('zoom = ', map2.getZoom())
        //                    latLng = new google.maps.LatLng(Number(latitude), Number(longitude));
        //                    getPixelCoordinates(latLng, zoom);
        //                    //console.log('fromLatLngToPoint', fromLatLngToPoint(latLng, map2))
        //                })
        //
        //            }
                    // form links for share
                    var url_share = window.location.href+'share/lat:'+lat+'_lon:'+lon+"&ln="+window.lang;
                    var google_share = '<a href="https://plus.google.com/share?url={'+url_share+'}" onclick="shareGoogle()"><img src="https://www.gstatic.com/images/icons/gplus-32.png" alt="Share on Google+"/></a>'

                    drawResult(window.map, result); //Возвращает площадь 1 маленького квадрата
                    //window.Area = area;
                    $('#info').empty();
                    $('#share_links').remove();
                    insertInfo(result, window.Area, window.lang);
                    insertRequesstList(result['requests']);
                    share_text = ""
                    if (window.lang == 'RU'){share_text = '<p>Поделиться</p>'} else{share_text = '<p>Share</p>'}
                    $('#info').after($("<div id='share_links'>"+share_text+"<div id='vk' class='link'>"+
                            "</div><div id='google' class='link'></div>"+
                            "<div id='facebook' class='link'><a href='https://www.facebook.com/sharer/sharer.php?u="+url_share+
                                " target='_blank'><img src='static/css/icons/facebook.png'></a></div>"+
                        "</div>"))
                    $('#vk').html(VK.Share.button({url: url_share},
                        {type: 'custom', text: "<img src='static/css/icons/vk.png'>"}))//'<img src=\"https://vk.com/images/share_32.png\" width=\"32\" height=\"32\" />'
                    $('#google').html(google_share)
                    $('#share').css('justify-content: center');

                    $('#mapResultWrapper').css({display: 'flex'});
                    //$("body").animate({scrollTop: $("#mapResultWrapper").offset().top + $('body').scrollTop()}, 1200);
                }).fail(function() {
                    $.post('/error', {'descr': 'Невозможно выполнить запрос<br> Can\'t make request to server'})
                });
            }
            else{
                alert('Вы не выбрали место')
            }
        //sheck lat lon end
    })
}
// form link for google
function shareGoogle(){
    javascript:window.open(this.href,'', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=600,width=600');
return false;
}

function drawResult(map, json){
    var lat = Number(json['lat'])
    var lng = Number(json['lon'])
    // console.log('drawRes', lat, lng)
    // var area;
    var latLng = new google.maps.LatLng(lat, lng)
    // get coords for big rectangle - area
    var boundsOfRect = getBoundsOfArea(latLng, map)
        var pixRecX = (boundsOfRect['f']['f'] - boundsOfRect['f']['b']) / (2500/cropSize)
        var pixRecY = (boundsOfRect['b']['f'] - boundsOfRect['b']['b']) / (2500/cropSize)
        // console.log('pixX', pixRecX, 'pixY', pixRecY)

                var areaPoints = [
            new google.maps.LatLng(lat, lng),
            new google.maps.LatLng(lat, lng-pixRecY),
            new google.maps.LatLng(lat-pixRecX, lng),
            new google.maps.LatLng(lat-pixRecX, lng-pixRecY)]

         //area = google.maps.geometry.spherical.computeArea(areaPoints)


//lat увеличивается снизу-вверх - ось Y значит не обнуляется в цикле
//lon увеличивается слева-направо - ось Х - значит обнуляется каждый цикл
        // draw all rectangles
        var leftTopY = lng + 50*pixRecY // не обнуляется
        for( var i = 99; i >= 0; i--){
            var leftTopX = lat - 48*pixRecX // обнуляется каждый цикл
            for( var j = 99; j >= 0 ; j--){

                bounds = {  north: leftTopX,
                    south: leftTopX - pixRecX,
                    east:  leftTopY,
                    west:  leftTopY - pixRecY
                    }
                // if result in this coord
                if (json[+(i)+':'+(j)]['delta']){
                    color = json[+(i)+':'+(j)]['color']
                    addRectangle(map, bounds, color)
                    //console.log('bounds', bounds, 'res',result[+(99-i)+':'+(99-j)])
                }
                leftTopX += pixRecX;
            }
            leftTopY -= pixRecY;
        }
        map.setZoom(18);
        map.setCenter({lat: lat, lng: lng});
        $('.container').css({display: 'none'});
        // return area;
}

// insert info to result block
function insertInfo(result, area, lang){
    // console.log('area = ', area)

    var commonObjCount = Math.pow(2500 / window.cropSize, 2) //сетка
    var oneSegmentArea = area / commonObjCount
    // console.log(commonObjCount)
    var enToRu = {'tree': 'Деревья'};
    var lng = 0;
    var Abin = [['Плохие условия', 'Bad'], ['Хорошие условия', 'Good'], ['Отличные условия', 'Exellent'] ]
    if (lang != "RU"){lng = 1;}
    var dictionary =  [['В заданном квадрате обнаружено', 'Results for the selected area'],//0
                     ['Общая площадь квадрата поиска: ','Total area of the search square: '],//1
                     ['Всего участков территории с деревьями: ','Total land plots with trees: '],//2
                  ['Площадь зеленых насаждений: ','Area of all trees: '],//3
                  ['Качество озеленения согласно нормам Всемирной организациии здравохранения: ',
                    'The quality of landscaping in accordance with the standards of the World Health Organization: '],//4
                  ['Оценочное количество деревьев: ', 'Estimated number of trees: '],//5
                  ['Одно крупное дерево выделяет столько кислорода, сколько нужно 1 человеку в сутки для дыхания.',//7
                  'One large tree gives off as much oxygen as it takes one person a day to breathe.'],
                  ['Новый запрос', 'New request'],
                  ['Последние запросы', 'Last requests' ]];
    $('#info h4').remove();
    $('#info_list').remove();
    $('#info').prepend($('<h4 style="margin: 3.5em 0.5em 0 0.5em; text-align: center;">'+dictionary[0][lng]+'</h4>'))
    $('#info h4').after($('<div id="info_list" ></div>'))
    path_img = 'static/css/icons/'
    if ( !$('#mapWrapper').length ){
        path_img = '../' + path_img;
    }
    // console.log(path_img)
    $('#info_list').append($('<p><img src="'+path_img+'grid.png">'+dictionary[1][lng]+area.toFixed(2)+ ' m<sup><small>2</small></sup></p>'))
    $('#info_list').append($('<p><img src="'+path_img+'frames.png">'+dictionary[2][lng]+ result['objects']['tree']['count']+'</p>'));
    $('#info_list').append($('<p><img src="'+path_img+'forest.png">'+dictionary[3][lng]+
            (result['objects']['tree']['count']*oneSegmentArea).toFixed(2)+ ' m<sup><small>2</small></sup></p>'));
    var abinVal = ((result['objects']['tree']['count']*oneSegmentArea)/(area)).toFixed(2)

    var abinText;

    if ( abinVal < 0.1){ abinText = Abin[0][lng];}
    else if (abinVal >= 0.1 && abinVal < 0.6){ abinText = Abin[1][lng];}
    else {abinText = Abin[2][lng];}
    $('#info_list').append($('<p><img src="'+path_img+'quality.png">'+dictionary[4][lng]+
         abinVal    + ' (Abin) - ' + abinText + '</p>'));
    $('#info_list').append($('<p><img src="'+path_img+'tree.png">'+dictionary[5][lng] +
        Math.round((result['objects']['tree']['count']*oneSegmentArea)/(10.7)) + '</p>'))
    $('#info_list').append($('<p><img src="'+path_img+'tree-silhouette.png">'+dictionary[6][lng]+'</p>'))
//    if ( !$('#newRequest').length && $('#mapWrapper').length ){
//        $('#info_list').after($("<div id='newRequest' class='btn' style='width: 100%; margin-top: 1%;'>"+dictionary[7][lng]+"</div>"))
//        $('#newRequest').click(function(){
//            $("html, body").animate({scrollTop: -1 * $("#mapContent").offset().top}, 1000);
//        })
//    }
//    $('#newRequest').text(dictionary[7][lng])
//    if (!window.location.href.includes('share')){
//        $('#newRequest').after($('<h4>'+(dictionary[8][lng])+'</h4>'));
//    }
}

function insertRequesstList(list){
    // console.log(list)
    var text;
    if (window.lang == "RU"){text = 'Последние запросы'}
    else {text = 'Last requests'}
//    if ( $('#map2').length != 0 ){
//        $('#info').append($("<div id='requests'></div>"));
        for ( el in list ){
            $('#requests').append($('<div class="request_line"><div class="request">'+list[el][0]+'</div><div class="request">'+list[el][1]+'</div></div>'))
        }
}


//изобразить квадрат на карте
function addRectangle(map, bounds, color){
// console.log('rectangle added')
var rectangle = new google.maps.Rectangle({
          strokeColor: color,
          strokeOpacity: 0.0,
          strokeWeight: 0.1,
          fillColor: color,
          fillOpacity: 0.4,
          map: map,
          bounds: bounds
        });
}

function fromLatLngToPoint(latLng, map) {
	var topRight = map.getProjection().fromLatLngToPoint(map.getBounds().getNorthEast());
	var bottomLeft = map.getProjection().fromLatLngToPoint(map.getBounds().getSouthWest());
	var scale = Math.pow(2, zoom);
	var worldPoint = map.getProjection().fromLatLngToPoint(latLng);
	return new google.maps.Point((worldPoint.x - bottomLeft.x) * scale, (worldPoint.y - topRight.y) * scale);
}

function getPixelCoordinates(latLng, zoom) {
var scale = 1 << zoom;
var worldCoordinate = project(latLng);
var pixelCoordinate = new google.maps.Point(
    Math.floor(worldCoordinate.x * scale),
    Math.floor(worldCoordinate.y * scale));
//console.log('pixels coords', pixelCoordinate)
}

function project(latLng) {
    var TILE_SIZE = 256;
        var siny = Math.sin(latLng.lat() * Math.PI / 180);
        // Truncating to 0.9999 effectively limits latitude to 89.189. This is
        // about a third of a tile past the edge of the world tile.
        siny = Math.min(Math.max(siny, -0.9999), 0.9999);
        var x = (TILE_SIZE * (0.5 + latLng.lng() / 360))
        var y = (TILE_SIZE * (0.5 - Math.log((1 + siny) / (1 - siny)) / (4 * Math.PI)))

        return new google.maps.Point(
            x,
            y );
}

function getBoundsOfArea(center, map){
    var imgSize = 1675
    var scale = Math.pow(2,zoom);

    var proj = map.getProjection();
    // console.log('map in bounds', map, 'center', center, 'proj', proj);
    var wc = proj.fromLatLngToPoint(center);
    var bounds = new google.maps.LatLngBounds();
    var sw = new google.maps.Point(((wc.x * scale) - imgSize)/ scale, ((wc.y * scale) - imgSize)/ scale);
    bounds.extend(proj.fromPointToLatLng(sw));
    var ne = new google.maps.Point(((wc.x * scale) + imgSize)/ scale, ((wc.y * scale) + imgSize)/ scale);
    bounds.extend(proj.fromPointToLatLng(ne));

    // console.log('bound of Big rectangle', bounds)
    //var rect = new google.maps.Rectangle(opts);
    return bounds
}

function inrange(min,number,max){
    if ( !isNaN(number) && (number >= min) && (number <= max) ){
        return true;
    } else {
        return false;
    };
}

function initMap(longitude, latitude) {
  var location = {lat: Number(latitude), lng: Number(longitude)};
  var map = new google.maps.Map(
      document.getElementById('map'), {zoom: zoom, center: location});
  var marker = new google.maps.Marker({position: location, map: map});
}



//Поле для ввода адреса, которое определяет координаты
function setGeoCoder(map, id, main){
    var cityCircle, lat, lng;
    var input = document.getElementById(id);

        var autocomplete = new google.maps.places.Autocomplete(
            input, {placeIdOnly: true});
        autocomplete.bindTo('bounds', map);
        //autocomplete.setFields(
        //   ['address_components', 'geometry', 'icon', 'name']);
        if (main){
            map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
            google.maps.ControlPosition
        }
        var geocoder = new google.maps.Geocoder;

        autocomplete.addListener('place_changed', function() {

            var place = autocomplete.getPlace();
            if (cityCircle){
               cityCircle.setMap(null);
            }
              if (!place.place_id) {
                return;
              }
          geocoder.geocode({'placeId': place.place_id}, function(results, status) {

                if (status !== 'OK') {
                  window.alert('Geocoder failed due to: ' + status);
                  return;
                }
                //map.setZoom(17);

                map.setCenter(results[0].geometry.location);
                 window.requestAddress = results['0'].formatted_address
                 lat = results[0].geometry.location.lat();
                 lng = results[0].geometry.location.lng();

                 // get center of tile
                 //
                 //
                 var scale = 1 << 20;
                var tileSize = 256
                var worldCoordinate = project(new google.maps.LatLng(lat, lng));
                // set lat lng to center of tile
                var tileCoordinate = new google.maps.Point(
                    Math.floor(worldCoordinate.x * scale / tileSize),
                    Math.floor(worldCoordinate.y * scale / tileSize));
                 pixels_x = worldCoordinate.x * scale
                 pixels_y = worldCoordinate.y * scale
                 pixels_x = (Number((pixels_x - pixels_x%tileSize).toFixed(0)) + 128) / scale
                 pixels_y = (Number((pixels_y - pixels_y%tileSize).toFixed(0)) + 128) / scale
                 var testCoord = new google.maps.Point(pixels_x, pixels_y)
                 lat = window.map.getProjection().fromPointToLatLng(testCoord).lat()
                 lng = window.map.getProjection().fromPointToLatLng(testCoord).lng()

//                 var marker = new google.maps.Marker({
//                   position: new google.maps.LatLng(lat, lng),
//                   map: window.map,
//                   title: 'center latlng'
//                 });
                 //
                 //
                 //
                // Set the position of the marker using the place ID and location.

                var boundsOfArea = getBoundsOfArea(new google.maps.LatLng(Number(lat), Number(lng)), window.map)

                var path = [ new google.maps.LatLng(boundsOfArea.f.f,  boundsOfArea.b.f),
                    new google.maps.LatLng(boundsOfArea.f.f,  boundsOfArea.b.b),
                ]
                var dist = Number(google.maps.geometry.spherical.computeDistanceBetween(path[0], path[1]))
                window.Area = dist * dist;
                console.log('area', window.Area)
                // bounds: boundsOfArea,
                var opts = {
                    bounds: boundsOfArea,
                    strokeOpacity: 0.8,
                    fillColor: '#A8E4A0',
                    fillOpacity: 0.1,
                    strokeColor: '#A8E4A0',
                    map: window.map,
                    editable:false
                }
                if (window.rectangeMap1){
                    window.rectangeMap1.setMap(null);
                }
                window.rectangeMap1 = new google.maps.Rectangle(opts);

                window.globalLat = lat
                window.globalLon = lng

                // console.log('coords latLng changed', window.globalLat, window.globalLon)
          });
        });
}
//
//function point2LatLng(point, map) {
//  var topRight = map.getProjection().fromLatLngToPoint(map.getBounds().getNorthEast());
//  var bottomLeft = map.getProjection().fromLatLngToPoint(map.getBounds().getSouthWest());
//  var scale = Math.pow(2, map.getZoom());
//  var worldPoint = new google.maps.Point(point.x / scale + bottomLeft.x, point.y / scale + topRight.y);
//  return map.getProjection().fromPointToLatLng(worldPoint);
//}


function changeLanguage(lang){
    $('#steps').empty();
    $('#header > h2').remove();
    $('#topInstruction').empty();
    $('#info_list').empty();
    //$('#language').empty();

    if ( lang == "RU" ){
        $('#RU').addClass('lang-text')
        $('#EN').removeClass('lang-text')
        $('#steps').append($("<h4>Шаг2. Проверьте область классификации</h4>"+
                        "<p>Если зеленая область соответствует Вашему запросу, то перейдите к следующему шагу.</p>"+
                        '<h4>Шаг3. Нажмите "Получить"</h4>'+
                        "<p>Нажмите на кнопку, если Вы выполнили все шаги.</p>"));

        $("#header > h1").after($('<h2 style="font-size: 1.8em;">Зонд космической оценки землепользования<br>(озелененность территории)</h2>'))
        $('#topInstruction').append($('<div style="    display: flex; justify-content: center;">'+
                '<h3>Космический аппарат готов к работе</h3><div class="indicator"></div></div>'+
                '<p>Для начала работы со спутником, укажите квадрат поиска - введите адрес</p>'))
        $('#submitBtn').text('ПОЛУЧИТЬ')
        $('#checkBtn').text('ПОКАЗАТЬ');
        $('#slideBtn').text('Скрыть');
        $('#share_links p').text('Поделиться ')
        $('#comment > a').text('Оставить комментарий о сайте')
    }
    else{
        $('#RU').removeClass('lang-text')
        $('#EN').addClass('lang-text')
        $('#steps').append($("<h4>Step 2. Check the classification area</h4>"+
                        "<p>If the green area matches your query, go to the next step.</p>"+
                        '<h4>Step3. Click "GET"</h4>'+
                        "<p>Click on the button if you have completed all the steps.</p>"));

        $("#header > h1").after($('<h2 style="font-size: 1.8em;">Probe for space survey of land use<br>(green spaces)</h2>'))
        $('#topInstruction').append($('<div style="    display: flex; justify-content: center;">'+
                '<h3>The spacecraft is ready for work</h3><div class="indicator"></div></div>'+
                '<p>To get started with the satellite, specify the search box - enter the address</p>'))
        $('#submitBtn').text('GET');
        $('#checkBtn').text('SHOW');
        $('#slideBtn').text('Hide');
        $('#share_links p').text('Share ')
        $('#comment > a').text('Stay comment about site')

    }

    if ( window.resultGlobal != ""){
            insertInfo(window.resultGlobal, window.Area, window.lang);
        }
}