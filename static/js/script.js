// global variables
let zoom = 17;
let map, rectangle, globalLat, globalLon, requestAddress, lang, resultGlobal;
let checker;
lang = 'RU'

// класс с информацией о результатах анализа
var info, globalPoly, request, geocoder;
let checkTime = 10000;
var jstsGeometry = new jsts.geom.GeometryFactory();

$('document').ready(function (result) {


    globalLat = 55.7531979;
    globalLon = 37.618598;


    map = initMap(globalLat, globalLon, zoom);
    map.setMapTypeId('hybrid');
    setDrawingTools(map);
    map.addListener('zoom_changed', function () {
        $('.gmnoprint:eq(2)').css({
            'margin-left': '18px'
        })
    })

    geocoder = new google.maps.Geocoder();
    // Inputs for geocoding
    setGeoCoder(map, 'pac-input');
    initializeInputAddress('#pac-input', '#search_container');

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

    // init button for request
    sentRequest('#submitBtn');


    get_requests();
    setInterval(function () {
        get_requests()
    }, 20000);


    request = new userRequest();
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



function get_requests() {
    $.post('/archive', function (result) {
        insertRequesstList(result)
    })
}
//
//$.getJSON( "/ready", function( data ) {
//  var items = [];
//  console.log(data)
//});


function check_results(locationName) {
    $.ajax({
        type: "POST",
        async: false,
        url: '/check',
        data: {
            'location': locationName
        },
        dataType: 'json',
        timeout: 0
    }).done(function (result) {
        console.log("check complete", result)
        if (result.status == 200 && result.responseText == 'wait') {
            console.log('second CHECK not ready 10 s');
        } else if (result.hasOwnProperty("paths")) {
            resultGlobal = result;
            clearInterval(checker);
            showResults(resultGlobal);
        }
    }).fail(function (error) {
        showErrorMessage(error)
    });
    // $.post('/check/location:' + locationName).done().fail()
}

function makePost(coords, classes, locationName) {
    $('#loader').css({
        display: 'block'
    });
    $('#preloader').css({
        display: 'block'
    });

    if ($("#welcome")) {
        $("#welcome").remove()
    }
    if ($("#result")) {
        $("#result").css({
            display: 'none'
        });
    }
    $('#submitBtn').addClass('disabled');
    console.log(locationName);

    $.ajax({
        type: "POST",
        async: false,
        url: '/analyze',
        dataType: 'json',
        timeout: 0,
        data: {
            values: JSON.stringify({
                'arrayOfCoords': coords,
                'location': locationName,
                'classes': classes
            })
        },
        complete: function (answer) {
            console.log(answer)
            if (answer.responseText == 'wait') {
                console.log(answer.responseText);


                checker = setInterval(function () {
                        check_results(request.locationName);
                        console.log('check ', request.locationName);
                    },
                    checkTime);
                console.log('interval 10 first post');

            }
        }

    }).done(function (answer) {
        showResults(answer);
    })
}


function showResults(result_from_server) {

    let locationName = result_from_server['location'];
    let requests = result_from_server['requests'];
    let pathsOfClasses = result_from_server["paths"];
    
    $('#loader').css({
        display: 'none'
    });
    $('#preloader').css({
        display: 'none'
    });
    $("#map_overlay").css({
        "overflow-y": "scroll"
    })

    if (!$('#result').length) {
        $.ajax({
            type: "POST",
            async: false,
            url: "/results",
            success: function (resultHtml) {
                $('#map_overlay').append($(resultHtml))
            }
        })
    } else {
        $("#result").css({
            display: 'block'
        });
    }
    $('#loader').css({
        display: 'none'
    });
    $('#submitBtn').removeClass('disabled');


    drawResult(map, pathsOfClasses);
    if (userArea){
        userArea.setMap(null);
            new google.maps.Polygon({
            paths: userArea.getPaths(),
            fillOpacity: 0,
            strokeColor: "red",
            strokeOpacity: 0.6,
            map: map
        })
    } 
    insertRequesstList(result_from_server['requests']);

    // form links for share
    var url_share = new String(window.location.origin)+"/ready/location="+locationName;
    console.log(url_share);

    //    share_text = ""

    ///////////////////////////////////////
     
    $('.button.facebook').parent().attr('href', 'https://www.facebook.com/sharer/sharer.php?u=' + url_share)
    $('.button.twitter').parent().attr('href', 'http://twitter.com/share?text=LandPober web-site&url='+ url_share +'&hashtags=LandProber' )
    $('#vk').html(VK.Share.button({
        url: url_share
    }, {
        type: 'custom',
        text: '<button class="ui circular vk icon button"> <i class="vk icon"></i></button>'
    }))
}

function showErrorMessage(error) {
    console.log("check failed", error);
    $(".message.negative").removeClass("hidden");
    $(".message.negative .button").click(function () {
        document.location = "/"
    })
}



function drawResult(map, paths) {
    console.log(paths);
    classProp = {
        'trees': {
            color: "#3CA0D0",
            css_color: "trees_color",
            header: "Деревья",
            icon: "tree",
        },
        'cars': {
            color: "#FFFA00",
            css_color: "cars_color",
            header: "Автомобили",
            icon: "car",
        },
        'garage': {
            color: "#FF5A40",
            css_color: "garage_color",
            header: "Гаражи",
            icon: "cube",
        },
        'buildings': {
            color: "purple",
            css_color: "purple",
            header: "Здания",
            icon: "building"
        }
    }
    let blockNameWithResults = "#result .segment"
    $(blockNameWithResults).empty()

    let pathsOfClasses = paths;
    let centerOfUserArea = paths.center;
    delete pathsOfClasses.center;
    
    // let jstsUserSelectedArea = request.getJstsPoly();
    for (className in pathsOfClasses) {
        //let copyUserAreaForUnion = jstsUserSelectedArea;
        let pathClass = [];
        let countOfAreas = 0;
        let commonArea = 0;

        pathsOfClasses[className].forEach(function (contour) {
            pathClass.push(contour.map(function (val) {
                    return {
                        "lat": val[0],
                        "lng": val[1]
                    }
            }))
        })
        if (pathClass.length) {

            var classPaths = new google.maps.Polygon({
                paths: pathClass,
                fillColor: classProp[className].color,
                fillOpacity: 0.23,
                strokeColor: classProp[className].color,
                strokeOpacity: 0.7,
                map: map
            })
            // console.log(classPaths)
            classPaths.getPaths().getArray().forEach(function (path) {
                commonArea += google.maps.geometry.spherical.computeArea(path)
            })
            countOfAreas = classPaths.getPaths().getArray().length;
            
            $(blockNameWithResults).append(
            $('<div class="ui '+classProp[className].css_color+' ribbon label"><i class="' + classProp[className].icon + ' icon"></i>' + classProp[className].header + '</div>')).append($('<div class="ui list"><div class="item">\
                Общая площадь найденных объектов: ' + commonArea.toFixed(2) + ' m<sup><small>2</small></sup></div>\
                <div class="item">Всего найденных территорий: ' + countOfAreas + '</div></div>'))
        }

        


        map.setCenter(new google.maps.LatLng(centerOfUserArea[0], centerOfUserArea[1]));
    } //class
}

function fromJstsCoordinatesToGoogle(jstsCoords) {
    let googleCoordinates = []
    for (let latlng in jstsCoords) {
        googleCoordinates.push(new google.maps.LatLng(jstsCoords[latlng].x, jstsCoords[latlng].y))
    }
    googleCoordinates.push(googleCoordinates[0])
    return googleCoordinates
}


function drawIntersectionArea(map, polygon) {
    var coords = polygon.getCoordinates().map(function (coord) {
        return {
            lat: coord.x,
            lng: coord.y
        };
    });
    coords.push(coords[0])
    var intersectionArea = new google.maps.Polygon({
        paths: coords,
        strokeColor: '#00FF00',
        strokeOpacity: 0.8,
        strokeWeight: 4,
        fillColor: '#00FF00',
        fillOpacity: 0.35
    });
    intersectionArea.setMap(map);
}



function createJstsPolygon(geometryFactory, polygon) {
    var path = polygon.getPath();
    var coordinates = path.getArray().map(function name(coord) {
        return new jsts.geom.Coordinate(coord.lat(), coord.lng());
    });
    coordinates.push(coordinates[0]);
    var shell = geometryFactory.createLinearRing(coordinates);
    return geometryFactory.createPolygon(shell);
}



// insert info to result block
function insertInfo(info, lang) {
    $('#information').empty();

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
    if (window.location.href.includes('share')) {
        path_img = '../' + path_img;
    }
    //
    $('#information').append($('<div class="ui grid middle aligned"></div>'))

    $('#information .ui.grid').append($('<div class="row"> \
                               <div class="three wide column"> <img src="' + path_img + 'grid.png"></div>' +
        '<div class="thirteen wide column"><p>' + dictionary[1][lng] + info.squareArea.toFixed(2) + ' m<sup><small>2</small></sup></p></div>\
                                      </div>'))

    //$('#information').append($('<div class="one wide column"> <img src="'+path_img+'grid.png"></div>' + '<div class="four wide column><p>' + dictionary[1][lng] + //area.toFixed(2) + ' m<sup><small>2</small></sup></p></div>'))
    //

    $('#information .ui.grid').append($('<div class="row">\
                    <div class="three wide column"> <img src="' + path_img + 'frames.png"></div>' + '<div class="thirteen wide column"><p>' + dictionary[2][lng] + areaCount + '</p></div>\
                                        </div>'))

    //$('#information .ui.grid').append($());

    $('#information .ui.grid').append($('<div class="row"> \
                               <div class="three wide column"> <img src="' + path_img + 'forest.png"></div>' +
        '<div class="thirteen wide column"><p>' + dictionary[3][lng] +
        (info.areaOfObjects).toFixed(2) +
        ' m<sup><small>2</small></sup> </p> </div></div>'));
    //
    info.setAbin((info.areaOfObjects / info.squareArea).toFixed(2));
    var abinText;
    if (info.Abin < 0.1) {
        abinText = Abin[0][lng];
    } else if (info.Abin >= 0.1 && info.Abin < 0.6) {
        abinText = Abin[1][lng];
    } else {
        abinText = Abin[2][lng];
    }


    $('#information .ui.grid').append($('<div class="row"> \
                               <div class="three wide column"> <img src="' + path_img + 'quality.png"></div>' +
        '<div class="thirteen wide column"><p>' + dictionary[4][lng] +
        info.Abin + ' (Abin) - ' + abinText + '</p></div></div>'));
    //    //

    $('#information .ui.grid').append($('<div class="row"> \
                               <div class="three wide column"> <img src="' + path_img + 'tree.png"></div>' +
        '<div class="thirteen wide column"><p>' + dictionary[5][lng] +
        Math.round(info.areaOfObjects / 20) + '</p></div></div>'))
    //
    //    $('#information .ui.grid').append($('<div class="row"> \
    //                               <div class="three wide column"> <img src="'+path_img+'tree-silhouette.png"></div>' + 
    //                                '<div class="thirteen wide column"><p>' + dictionary[6][lng] + '</p></div></div>'))
}



function insertRequesstList(list) {
    $('#requests .row').remove();
    $('#archive').empty()
    if (list.length > 0){
        for (el in list) {

            $('#archive').append($(
                '<div class="ui basic button row" value=" ' + list[el][0] + ' "> ' +
                '<div class="column">' + list[el][0] + '</div> </div>'))
        }
        $('#archive .button').click(function () {
            var request_val = this.getAttribute('value').slice(1, -1);
            console.log(request_val)
            $.post({
                url: '/ready',
                data: {
                    'location': request_val
                }
            }).done(function (result) {
                showResults(result)
            }).fail()
        })
    }
    else{
        $('#archive').append($("<div class='column'>Cписок запросов пуст</div>"))
    }
}



//function getPixelCoordinates(latLng, zoom) {
//    var scale = 1 << zoom;
//    var worldCoordinate = project(latLng);
//    var pixelCoordinate = new google.maps.Point(
//        Math.floor(worldCoordinate.x * scale),
//        Math.floor(worldCoordinate.y * scale));
//}

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



function initMap(latitude, longitude, zoom) {
    var location = {
        lat: Number(latitude),
        lng: Number(longitude)
    };
    var map = new google.maps.Map(
        document.getElementById('map'), {
            zoom: zoom,
            center: location
        });
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


    autocomplete.addListener('place_changed', function () {

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
            //удаляем квадрат из предыдущ. поиска
            if (rectangle) {
                rectangle.setMap(null);
            }

            map.setZoom(zoom);
            map.setCenter(results[0].geometry.location);
            window.requestAddress = results['0'].formatted_address
            lat = results[0].geometry.location.lat();
            lng = results[0].geometry.location.lng();

        });
    });
}

// set name of userArea
function backGeoCode(lat, lng) {
    geocoder.geocode({
        'location': new google.maps.LatLng(lat, lng)
    }, function (results, status) {
        if (status == 'OK') {
            if (results[1]) {
                request.locationName = results[1].formatted_address;
                console.log(results);
                // return placeName;
            }
        } else {
            request.locationName = "Неизвестный адрес " + Math.round(Math.random() * 100);
        }
    });
}



function num2deg(xtile, ytile, zoom) {
    var n = Math.pow(2.0, zoom)
    var lon_deg = xtile / n * 360.0 - 180.0
    var lat_rad = Math.atan(Math.sinh(Math.PI * (1 - 2 * ytile / n)))
    var lat_deg = 180.0 * (lat_rad / Math.PI)
    return [lat_deg, lon_deg]
}


//function mapResizeEvent() {
//    $('#show_hide_btn').css({
//        display: 'block',
//        transition: '0.5s'
//    })
//    $('#show_hide_btn').css({
//        'margin-right': $('#right_sidebar').width()
//    });
//    $(window).resize(function () {
//        if ($('#right_sidebar').hasClass('visible')) {
//            $('#show_hide_btn').css({
//                'margin-right': $('#right_sidebar').width()
//            });
//            $('.gm-style').css({
//                width: 100 - ($('#right_sidebar').width() / $('#map').width() * 100) + '%'
//            })
//        }
//    })
//
//    $('#show_hide_btn').click(function () {
//        if ($('#right_sidebar').hasClass('visible')) {
//            $('.gm-style').css({
//                width: '100%'
//            });
//
//            $('#right_sidebar').removeClass('visible');
//
//            $('#show_hide_btn').css({
//                'margin-right': 0
//            });
//            $('#show_hide_btn  i').removeClass('right');
//            $('#show_hide_btn  i').addClass('left');
//        } else {
//            $('.gm-style').css({
//                width: 100 - Math.round(($('#right_sidebar').width() / $('#map').width()) * 100) + '%'
//            });
//            $('#right_sidebar').addClass('visible');
//
//            $('#show_hide_btn').css({
//                'margin-right': $('#right_sidebar').width()
//            });
//            $('#show_hide_btn  i').removeClass('left');
//            $('#show_hide_btn  i').addClass('right');
//        }
//    })
//
//}


class information {

    constructor() {
        this.treesCount = 0;
        this.areaCount = 0;
        this.areaOfObjects = 0;
        this.Abin = 0;
        this.squareArea = 0;
    }

    //seters
    setTreesCount(count) {
        this.treesCount = count;
    }
    setAreaCount(count) {
        this.areaCount = count;
    }
    setAreaOfObjects(area) {
        this.areaOfObjects = area;
    }
    setAbin(abin) {
        this.Abin = abin;
    }
    setSquareArea(area) {
        this.squareArea = area;
    }

    //geters
    getTreesCount() {
        return this.treesCount
    }
    getAreaCount() {
        return this.areaCount
    }
    getAreaOfObjects() {
        return this.areaOfObjects
    }
    getAbin() {
        return this.Abin
    }
    getSquareArea() {
        return this.squareArea
    }

}


class userRequest {
    constructor() {
        this.classList = [];
        this.area;
        this.locationName;
    }

    toggleClass(className) {
        if (this.classList.indexOf(className) > -1) {
            this.classList.splice(this.classList.indexOf(className), 1)
        } else {
            this.classList.push(className);
        }
        return this.classList;
    }



    setArea(newArea) {
        this.area = newArea;
        this.setLocationName();
        return this.area;
    }

    setLocationName() {
        if (this.area) {
            let lat = 0,
                lng = 0;
            let normalArray = this.getNormalizeAreaArray();
            normalArray.forEach(function (LatLng) {
                lat += LatLng[0];
                lng += LatLng[1];
            })
            lat /= normalArray.length;
            lng /= normalArray.length;

            backGeoCode(lat, lng);
            //            console.log(this.locationName);
            // this.locationName = // Math.round(Math.random() * 100)
            //return this.locationName;
        }
    }

    getNormalizeAreaArray() {
        let normalArray = [];
        this.area.getPath().j.forEach(function (LatLng) {
            normalArray.push([LatLng.lat(), LatLng.lng()])
        })
        return normalArray;
    }

    getArea() {
        return this.area;
    }

    getClasses() {
        return this.classList;
    }

    getJstsPoly() {
        return createJstsPolygon(jstsGeometry, this.area)
    }

}
