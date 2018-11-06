// global variables
var zoom = 19.8;
var map, rectangeMap1, globalLat, globalLon, cropSize, requestAddress, lang, resultGlobal, Area
var checker
lang = 'RU'
resultGlobal = ''
cropSize = 25

$('document').ready(function () {
    var lng, lat;
    lng = 48.707067;
    lat = 44.5169033;

    window.map = initMap(lat, lng);
    window.map.setMapTypeId('hybrid');
    // init button for request
    sentRequest('#submitBtn');

    // Inputs for geocoding
    setGeoCoder(window.map, 'pac-input');
    //setGeoCoder(window.map, 'pac-input-top', false);
    // set inputs for different blocks

    initializeInputAddress('#pac-input', '#search_container');
    ////////////
    //submit button end------------------------------------------------

    // language change
    $('.lng').click(function () {
        if (window.lang != $(this).attr('id')) {
            $('.lng').removeClass('active');
            window.lang = $(this).attr('id')
            $(this).addClass('active');
            //функция, которая заменяет все
            changeLanguage(window.lang);
        }
    })
    $('#RU').addClass('lang-text')
    /////init different functions
    //slideBtn();
    //slideInfo();
    //initButtons();
    $(".ui.sidebar.right").sidebar({
        'context': '#map'
    });
    $('#requests').css({
        display: 'none'
    });
    //$('.ui.sidebar.right').sidebar({context: '#map'})


    $('#request_menu').click(function () {
        if ($('#requests').css('display') == "block") {
            $('#requests').toggle('toggle');
        }
        $('#search_container').toggle('toggle');
    })

    $('#request_list').click(function () {
        if ($('#search_container').css('display') == "block") {
            $('#search_container').toggle('toggle');
        }
        $('#requests').toggle('toggle');
        //$('#search_container').transition('fade down');
    })

    get_requests();
    setInterval(get_requests(), 20000);

});

// set inputs for different blocks
function initializeInputAddress(id, parentId) {
    var addressInputElement = $(id);
    //$('.pac-container').css({display: 'none'})
    addressInputElement.on('focus', function () {
        var pacContainer = $('.pac-container');
        $(parentId).append(pacContainer);
    })
}


function sentRequest(buttonId) {
    $(buttonId).click(function () {

        if (Number(window.globalLat) && Number(window.globalLon)) {
            // get coords
            var lat = window.globalLat
            var lon = window.globalLon
            var location, bounds
            var destination = $(window).height()

            // if it first request by user

            $('#right_sidebar').addClass('visible');
            //$('#right_sidebar').toggle('visible');
            $('#right_loader').dimmer('show');

            //$('.container').css({display: 'flex'});

            //post coordinates to server
            if (!window.requestAddress) { // if dont have a geoloc coords
                window.requestAddress = "Неизвестный адрес"
            }
            $.post('/main', {
                'lat': window.globalLat,
                'lon': window.globalLon,
                'address': window.requestAddress
            }, function (result) {

                if (result == 'wait') {
                    //maske checker
                    setTimeout(check_results(window.globalLat, window.globalLon), 5000);
                } else {
                    //write results from RESULT
                    show_results(result)
                    $('#right_loader').dimmer('hide');
                    //console.log('checker ready')
                }
                //console.log('posted')
                //$("body").animate({scrollTop: $("#mapResultWrapper").offset().top + $('body').scrollTop()}, 1200);
            }).fail(function () {
                $.post('/error', {
                    'descr': 'Невозможно выполнить запрос<br> Can\'t make request to server'
                })
            });
        } else {
            alert('Вы не выбрали место');
            //console.log(window.globalLat, window.globalLon);
        }
        //sheck lat lon end
    })
}

function get_requests() {
    $.post('/request_list', function (result) {
        insertRequesstList(result)
    })
}

function check_results(lat, lon) {
    $.post('/check/lat:' + lat + '_lon:' + lon, function (result) {
        if (result != 'wait') {
            console.log('ready result', result);
            window.resultGlobal = result;
            clearTimeout(window.checker);
            show_results(result);
            $('#right_sidebar').toggle('visible');
            $('#right_loader').dimmer('hide');
        } else {
            window.checker = setTimeout(check_results(window.globalLat, window.globalLon), 5000);
        }
    })

}

function show_results(result_from_server) {
    var lat = Number(result_from_server['lat'])
    var lng = Number(result_from_server['lon'])
    var location = {
        lat: Number(lat),
        lng: Number(lng)
    };
    window.resultGlobal = result_from_server
    // form links for share
    var url_share = window.location.href + 'share/lat:' + lat + '_lon:' + lng + "&ln=" + window.lang;
    var google_share = '<a href="https://plus.google.com/share?url={' + url_share + '}" onclick="shareGoogle()"><img src="https://www.gstatic.com/images/icons/gplus-32.png" alt="Share on Google+"/></a>'

    drawResult(window.map, result_from_server); //Возвращает площадь 1 маленького квадрата
    //window.Area = area;

    insertInfo(result_from_server, window.Area, window.lang);
    insertRequesstList(result_from_server['requests']);
    //    share_text = ""
    //    if (window.lang == 'RU'){share_text = '<p>Поделиться</p>'} else{share_text = '<p>Share</p>'}
    $('#links_container').append($("<div id='vk' class='ui column'></div>" +
        "<div id='google' class='ui column'></div>" +
        "<div id='facebook' class='ui column'><a href='https://www.facebook.com/sharer/sharer.php?u=" + url_share + " target='_blank'><img src='static/css/icons/facebook.png'></a></div>"))
    $('#vk').html(VK.Share.button({
        url: url_share
    }, {
        type: 'custom',
        text: "<img src='static/css/icons/vk.png'>"
    }))
    $('#google').html(google_share)
    //    $('#share').css('justify-content: center');

}

// form link for google
function shareGoogle() {
    javascript: window.open(this.href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=600,width=600');
    return false;
}

function drawResult(map, json) {
    var lat = Number(json['lat'])
    var lng = Number(json['lon'])
    // console.log('drawRes', lat, lng)
    // var area;
    var latLng = new google.maps.LatLng(lat, lng)
    // get coords for big rectangle - area

    var boundsOfRect = getBoundsOfArea(latLng, map)
    /////////////////////////

    ///////////////////////////////
    var pixRecX = Math.abs((boundsOfRect['l']['j'] - boundsOfRect['l']['l'])) / (100)
    var pixRecY = Math.abs((boundsOfRect['j']['j'] - boundsOfRect['j']['l'])) / (100)
    console.log(pixRecX, pixRecY)
    // console.log('pixX', pixRecX, 'pixY', pixRecY)

    var areaPoints = [
            new google.maps.LatLng(lat, lng),
            new google.maps.LatLng(lat, lng - pixRecY),
            new google.maps.LatLng(lat - pixRecX, lng),
            new google.maps.LatLng(lat - pixRecX, lng - pixRecY)]

    //area = google.maps.geometry.spherical.computeArea(areaPoints)

    //lat увеличивается снизу-вверх - ось Y значит не обнуляется в цикле
    //lon увеличивается слева-направо - ось Х - значит обнуляется каждый цикл
    // draw all rectangles
    var leftTopY = lng + 50 * pixRecY // не обнуляется
    for (var i = 99; i >= 0; i--) {
        var leftTopX = lat - 48 * pixRecX // обнуляется каждый цикл
        for (var j = 99; j >= 0; j--) {

            bounds = {
                north: leftTopX,
                south: leftTopX - pixRecX,
                east: leftTopY,
                west: leftTopY - pixRecY
            }
            // if result in this coord
            if (json[+(i) + ':' + (j)]['delta']) {
                color = json[+(i) + ':' + (j)]['color']
                addRectangle(map, bounds, color)
                //console.log('bounds', bounds, 'res',result[+(99-i)+':'+(99-j)])
            }
            leftTopX += pixRecX;
        }
        leftTopY -= pixRecY;
    }
    map.setZoom(18);
    map.setCenter({
        lat: lat,
        lng: lng
    });
    //$('.container').css({display: 'none'});
    // return area;
}

// insert info to result block
function insertInfo(result, area, lang) {
    // console.log('area = ', area)
    $('#information').empty();
    var commonObjCount = Math.pow(2500 / window.cropSize, 2) //сетка
    var oneSegmentArea = area / commonObjCount
    // console.log(commonObjCount)
    var enToRu = {
        'tree': 'Деревья'
    };
    var lng = 0;
    var Abin = [['Плохие условия', 'Bad'], ['Хорошие условия', 'Good'], ['Отличные условия', 'Exellent']]
    if (lang != "RU") {
        lng = 1;
    }
    var dictionary = [['В заданном квадрате обнаружено', 'Results for the selected area'], //0
                     ['Общая площадь квадрата поиска: ', 'Total area of the search square: '], //1
                     ['Всего участков территории с деревьями: ', 'Total land plots with trees: '], //2
                  ['Площадь зеленых насаждений: ', 'Area of all trees: '], //3
                  ['Качество озеленения согласно нормам Всемирной организациии здравохранения: ',
                    'The quality of landscaping in accordance with the standards of the World Health Organization: '], //4
                  ['Оценочное количество деревьев: ', 'Estimated number of trees: '], //5
                  ['Одно крупное дерево выделяет столько кислорода, сколько нужно 1 человеку в сутки для дыхания.', //7
                  'One large tree gives off as much oxygen as it takes one person a day to breathe.'],
                  ['Новый запрос', 'New request'],
                  ['Последние запросы', 'Last requests']];
    //$('#information h4').remove();

    $('#information').append($('<h4 class="ui header center aligned item">' + dictionary[0][lng] + '</h4>'))
    //$('#info h4').after($('<div id="info_list" ></div>'))
    path_img = 'static/css/icons/'
    //    if ( !$('#mapWrapper').length ){
    //        path_img = '../' + path_img;
    //    }
    // console.log(path_img)
    //
    $('#information').append($('<div class="ui grid middle aligned"></div>'))
    
    $('#information .ui.grid').append($('<div class="row"> \
                               <div class="three wide column"> <img src="'+path_img+'grid.png"></div>' + 
                                '<div class="thirteen wide column"><p>' + dictionary[1][lng] + area.toFixed(2) + ' m<sup><small>2</small></sup></p></div>\
                                      </div>'))
    
    //$('#information').append($('<div class="one wide column"> <img src="'+path_img+'grid.png"></div>' + '<div class="four wide column><p>' + dictionary[1][lng] + //area.toFixed(2) + ' m<sup><small>2</small></sup></p></div>'))
    //
    
    $('#information .ui.grid').append($('<div class="row">\
                    <div class="three wide column"> <img src="'+path_img+'frames.png"></div>' + '<div class="thirteen wide column"><p>' + dictionary[2][lng] + result['objects']['tree']['count'] + '</p></div>\
                                        </div>'))
    
    //$('#information .ui.grid').append($());
    
    $('#information .ui.grid').append($('<div class="row"> \
                               <div class="three wide column"> <img src="'+path_img+'forest.png"></div>' + 
                                '<div class="thirteen wide column"><p>' + dictionary[3][lng] +
                            (result['objects']['tree']['count'] * oneSegmentArea).toFixed(2) + 
                                      ' m<sup><small>2</small></sup> </p> </div></div>'));

    var abinVal = ((result['objects']['tree']['count'] * oneSegmentArea) / (area)).toFixed(2)
    var abinText;
    if (abinVal < 0.1) {
        abinText = Abin[0][lng];
    } else if (abinVal >= 0.1 && abinVal < 0.6) {
        abinText = Abin[1][lng];
    } else {
        abinText = Abin[2][lng];
    }

    //
    $('#information .ui.grid').append($('<div class="row"> \
                               <div class="three wide column"> <img src="'+path_img+'quality.png"></div>' + 
                                '<div class="thirteen wide column"><p>'+ dictionary[4][lng] +
        abinVal + ' (Abin) - ' + abinText + '</p></div></div>'));
    //
    $('#information .ui.grid').append($('<div class="row"> \
                               <div class="three wide column"> <img src="'+path_img+'tree.png"></div>' + 
                                '<div class="thirteen wide column"><p>'+ dictionary[5][lng] +
        Math.round((result['objects']['tree']['count'] * oneSegmentArea) / (10.7)) + '</p></div></div>'))
    //
    $('#information .ui.grid').append($('<div class="row"> \
                               <div class="three wide column"> <img src="'+path_img+'tree-silhouette.png"></div>' + 
                                '<div class="thirteen wide column"><p>' + dictionary[6][lng] + '</p></div></div>'))
}

function insertRequesstList(list) {
    // console.log(list)
    $('#requests row').remove();
    var text;
    if (window.lang == "RU") {
        text = 'Последние запросы'
    } else {
        text = 'Last requests'
    }
    //$('#requests').append('<h4 class="ui header item aligned center"></h4>')
    for (el in list) {
        $('#requests .two.columns').append($('<div class="row">' +
                                '<div class="column">' + list[el][0] + '</div>' +
                                '<div class="column">' + list[el][1] + '</div>' +
                                '</div>'))
    }
}


//изобразить квадрат на карте
function addRectangle(map, bounds, color) {
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
        y);
}

function getBoundsOfArea(center, map) {
    var imgSize = 1675
    var scale = Math.pow(2, zoom);

    var proj = map.getProjection();
    // console.log('map in bounds', map, 'center', center, 'proj', proj);
    var wc = proj.fromLatLngToPoint(center);
    var bounds = new google.maps.LatLngBounds();
    var sw = new google.maps.Point(((wc.x * scale) - imgSize) / scale, ((wc.y * scale) - imgSize) / scale);
    var point1 = new google.maps.Point(sw);
    bounds.extend(proj.fromPointToLatLng(sw));
    var ne = new google.maps.Point(((wc.x * scale) + imgSize) / scale, ((wc.y * scale) + imgSize) / scale);
    var point2 = new google.maps.Point(ne);
    bounds.extend(proj.fromPointToLatLng(ne));

    // console.log('bound of Big rectangle', bounds)
    //var rect = new google.maps.Rectangle(opts);
    return bounds
}

function inrange(min, number, max) {
    if (!isNaN(number) && (number >= min) && (number <= max)) {
        return true;
    } else {
        return false;
    };
}

function initMap(longitude, latitude) {
    var location = {
        lat: Number(latitude),
        lng: Number(longitude)
    };
    var map = new google.maps.Map(
        document.getElementById('map'), {
            zoom: 17,
            center: location
        });
    console.log("map init")
    return map
}



//Поле для ввода адреса, которое определяет координаты
function setGeoCoder(map, id, main) {
    var lat, lng;
    var input_area = document.getElementById(id);

    var autocomplete = new google.maps.places.Autocomplete(
        input_area, {
            placeIdOnly: true
        });
    autocomplete.bindTo('bounds', map);
    //autocomplete.setFields(
    //   ['address_components', 'geometry', 'icon', 'name']);
    //        if (main){
    //            map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
    //            google.maps.ControlPosition
    //        }
    var geocoder = new google.maps.Geocoder;

    autocomplete.addListener('place_changed', function () {
        console.log('listener ready')
        var place = autocomplete.getPlace();
        if (!place.place_id) {
            return;
        }
        geocoder.geocode({
            'placeId': place.place_id
        }, function (results, status) {

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
                Math.floor(worldCoordinate.y * scale / tileSize)
            );
            pixels_x = worldCoordinate.x * scale
            pixels_y = worldCoordinate.y * scale
            pixels_x = (Number((pixels_x - pixels_x % tileSize).toFixed(0)) + 128) / scale
            pixels_y = (Number((pixels_y - pixels_y % tileSize).toFixed(0)) + 128) / scale
            var testCoord = new google.maps.Point(pixels_x, pixels_y)
            lat = window.map.getProjection().fromPointToLatLng(testCoord).lat()
            lng = window.map.getProjection().fromPointToLatLng(testCoord).lng()
            console.log('changed coords', lat, lng)
            // Set the position of the marker using the place ID and location.

            var boundsOfArea = getBoundsOfArea(new google.maps.LatLng(Number(lat), Number(lng)), window.map)
            console.log('vounds = ', boundsOfArea)
            var path = [new google.maps.LatLng(boundsOfArea.j.j, boundsOfArea.l.j),
                          new google.maps.LatLng(boundsOfArea.j.l, boundsOfArea.l.l),
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
                editable: false
            }
            if (window.rectangeMap1) {
                window.rectangeMap1.setMap(null);
            }
            window.rectangeMap1 = new google.maps.Rectangle(opts);

            window.globalLat = lat
            window.globalLon = lng

            // console.log('coords latLng changed', window.globalLat, window.globalLon)
        });
    });
}


function changeLanguage(lang) {
    //$('#search_container').empty();
    //$('#in').empty();
    //$('#language').empty();

    if (lang == "RU") {
        $('#requests h4').text("Список запросов");
        $('#search_container h3:nth-child(1)').text('Внимание');
        $('#search_container h3:nth-child(2)').text('Проверьте квадрат поиска');
        $('#search_container div p').text('Нажмите кнопку "Получить", если зеленая область соответствует Вашему запросу, иначе повторите запрос адреса.');
        //                        '<h4>Шаг3. Нажмите "Получить"</h4>'+
        //                        "<p>Нажмите на кнопку, если Вы выполнили все шаги.</p>"));

        //        $("#header > h1").after($('<h2 style="font-size: 1.8em;">Зонд космической оценки землепользования<br>(озелененность территории)</h2>'))
        //        $('#topInstruction').append($('<div style="    display: flex; justify-content: center;">'+
        //                '<h3>Космический аппарат готов к работе</h3><div class="indicator"></div></div>'+
        //                '<p>Для начала работы со спутником, укажите квадрат поиска - введите адрес</p>'))
        $('#submitBtn').text('ПОЛУЧИТЬ')
        $('#checkBtn').text('ПОКАЗАТЬ');
        $('#ptr').text('Санкт-Петербург');
        $('#request_menu').text('Новый запрос');
        $('#request_list').text('Архив запросов');
        //
        //$('#slideBtn').text('Скрыть');
        $('#links .header').text('Поделиться')
        $('#links .item .button a').text('Оставить комментарий о сайте')
    } else {
        $('#requests h4').text("Requests list");
        $('#search_container h3:nth-child(1)').text('Attention');
        $('#search_container h3:nth-child(2)').text('Check the classification area');
        $('#search_container > div > p').text('Click the "Get" button if the green area matches your request, otherwise repeat the address request.');
        //        $('#steps').append($("<h4>Step 2. Check the classification area</h4>"+
        //                        "<p>If the green area matches your query, go to the next step.</p>"+
        //                        '<h4>Step3. Click "GET"</h4>'+
        //                        "<p>Click on the button if you have completed all the steps.</p>"));

        //        $("#header > h1").after($('<h2 style="font-size: 1.8em;">Probe for space survey of land use<br>(green spaces)</h2>'))
        //        $('#topInstruction').append($('<div style="    display: flex; justify-content: center;">'+
        //                '<h3>The spacecraft is ready for work</h3><div class="indicator"></div></div>'+
        //                '<p>To get started with the satellite, specify the search box - enter the address</p>'))
        $('#submitBtn').text('GET');
        $('#checkBtn').text('SHOW');
        $('#ptr').text('St. Petersburg');
        $('#request_menu').text('New request');
        $('#request_list').text('Archive of requests');
        //request_list
        //$('#slideBtn').text('Hide');
        $('#links .header').text('Share')
        $('#links .item .button a').text('Stay comment about site')

    }

    if (window.resultGlobal != "") {
        insertInfo(window.resultGlobal, window.Area, window.lang);
    }
}