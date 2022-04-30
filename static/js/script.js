// global variables
let zoom = 15;
let map, globalLat, globalLon, requestAddress, resultGlobal;
let checker;

// класс с информацией о результатах анализа
var globalPoly, request, geocoder;
let checkTime = 10000;

$('document').ready(function (result) {
    globalLat = 55.7531979;
    globalLon = 37.618598;

    // ИНИЦИАЛИЗАЦИЯ КАРТЫ
    map = initMap(globalLat, globalLon, zoom);
    map.setMapTypeId('hybrid');
    setDrawingTools(map);
    map.addListener('zoom_changed', function () {
        $('.gmnoprint:eq(2)').css({
            'margin-left': '18px'
        })
    })

    geocoder = new google.maps.Geocoder();
    // ФОРМА ПОИСКА МЕСТ ОТ ГУГЛ
    setGeoCoder(map, 'pac-input');
    initializeInputAddress('#pac-input', '#search_container');


    // ЗАПРОС НА ОБРАБОТКУ ТЕРРТИРИИ
    sentRequest('#submitBtn');

    get_requests();
    setInterval(function () {
        get_requests()
    }, 20000);
    request = new userRequest();

    // ИНИЦИАЛИЗАЦИЯ КНОПОК И ФОРМ
    $('#login_btn').click(function () {
        menuToggle("#login_content");
    });
    $('#regist_btn').click(function () {
        menuToggle("#regist_content");
    });
    $('#about').click(function () {
        menuToggle("#about_content");
    });
    $('#profile').click(function () {
        menuToggle("#profile_content");
    });

    postForm("/login", "#login_form", "#login_post");
    postForm("/registration", "#regist_form", "#regist_post");

});

//____________ _______ВЕРХНЕЕ МЕНЮ_________ ___________

// _______ ПЕРЕКЛЮЧЕНИЕ МЕЖДУ ОКНАМИ ДЛЯ ПОЛЬЗОВАТЕЛЯ _________
function menuToggle(divId) {
    var menuContent = ["#login_content", "#regist_content", "#about_content", "#profile_content"];
    menuContent.forEach(function (block) {
        if (divId != block) {
            $(block).attr("style", "display: none !important");
        }
    })
    $(divId).transition('scale')
}
// _______ ПОКАЗАТЬ МЕНЮ _________                
$("#menu_show").click(function () {
    $("#map_overlay").transition('slide left')
    $('#menu_show i').toggleClass("vertically flipped");
    $(this).transition('pulse')
    var header = $("#header_menu");
    header.transition('slide down');
    if (header.hasClass("visible")) {
        menuToggle("none");
        $("#map").css({
            filter: ""
        })
        $("#header_menu .item").removeClass('active');
    }
})

// _______ НАЖАТИЕ ЭЛ-ТОВ МЕНЮ _________ 
$("#profile, #about, #regist_btn, #login_btn").click(function () {
    $(this).toggleClass('active');
    if ($(this).hasClass("active")) {
        $("#map").css({
            filter: "blur(5px) grayscale(100%)"
        })
        $("#header_menu .item").removeClass('active');
        $(this).addClass('active');
    } else {
        $("#map").css({
            filter: ""
        });
    }
})

//ШАБЛОН ОТПРАВКИ ФОРМЫ
function postForm(url, formId, buttonId) {
    $(buttonId).click(function () {
        $.post({
            url: url,
            data: $(formId).serialize()
        }).done(function (response) {
            if (response.type == "message") {
                let text;
                if (response.text.length > 1) {
                    text = "<ul>"
                    response.text.forEach(function (subMessage) {
                        text += "<li>" + subMessage + "</li>";
                    })
                    text += "</ul>"
                } else {
                    text = response.text[0];
                }
                if ($(formId).parent().children('.message').length) {
                    $(formId).parent().children('.message').empty();
                    $(formId).parent().children('.message').append($(text));
                } else {
                    $(formId).parent().append($("<div class='ui orange tiny message'>" + text + "</div>"))
                }
            } else {
                history.go("/");
            }
        })
    })
}



// set inputs for different blocks
function initializeInputAddress(id, parentId) {
    var addressInputElement = $(id);
    //$('.pac-container').css({display: 'none'})
    addressInputElement.on('focus', function () {
        var pacContainer = $('.pac-container');
        $(parentId).append(pacContainer);
    })
}


//____________ _______ ЗАПРОСЫ ПО ОБРАБОТКЕ ТЕРРИТОРИИ _________ ___________

//____________ ПОЛУЧИТЬ АРХИВ ЗАПРОСОВ _______ 
function get_requests() {
    $.post('/archive', function (result) {
        insertRequesstList(result)
    })
}

//____________ ПРОВЕРИТЬ ОБРАБОТАН ЛИ РЕЗУЛЬТАТ _______
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
}

//____________ ОТПРАВИТЬ НОВЫЙ ЗАПРОС _______
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

//_______ ВСТАВКА АРХИВА ЗАПРОСОВ _____
function insertRequesstList(list) {
    $('#requests .row').remove();
    $('#archive').empty()
    if (list.length > 0) {
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
    } else {
        $('#archive').append($("<div class='column'>Cписок запросов пуст</div>"))
    }
}

//____________ ________ ОТРИСОВКА И ИНФОРМАЦИЯ О РЕЗУЛЬТАТАХ _______ _______

//____________ ПОКАЗАТЬ РЕЗУЛЬТАТ _______
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

    //_______ ОТОБРАЗИТЬ ПОЛИГОНЫ _____
    drawResult(map, pathsOfClasses);
    if (userArea) {
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


    var url_share = new String(window.location.origin) + "/ready/location=" + locationName;
    console.log(url_share);

    //_______ ССЫЛКИ  _____
    $('.button.facebook').parent().attr('href', 'https://www.facebook.com/sharer/sharer.php?u=' + url_share)
    $('.button.twitter').parent().attr('href', 'http://twitter.com/share?text=LandPober web-site&url=' + url_share + '&hashtags=LandProber')
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
    $("#map").css({
        filter: "blur(5px) grayscale(100%)"
    })

    $(".message.negative .button").click(function () {
        document.location = "/"
    })
}

// ______ ЗАКРЫТИЕ БОКОВОГО СООБЩЕНИЯ _________
$('#user_popup_inform .close').on('click', function() {
    $(this)
      .closest('.message')
      .transition('browse right')
    ;
  })
;

//_______ НАРИСОВАТЬ ПОЛИГОНЫ НА КАРТЕ _____ (ПЕРЕНЕСТИ НА СЕРВЕР)
function drawResult(map, paths) {
    console.log(paths);
    classProp = {
        'trees': {
            color: ["#29b710"],
            css_color: "trees_color",
            header: "Деревья",
            icon: "tree",
        },
        'cars': {
            color: ["#FFFA00"],
            css_color: "cars_color",
            header: "Автомобили",
            icon: "car",
        },
        'garage': {
            color: ["#FF5A40"],
            css_color: "garage_color",
            header: "Гаражи",
            icon: "cube",
        },
        'buildings': {
            color: ["#f4425f", "#b128fc", "#fc28f4"],
            css_color: "purple",
            header: "Здания",
            icon: "building"
        },
        'water': {
            color: ["#ffa42d"],
            css_color: "purple",
            icon: "tint"
        },
        'rails':{
            color: ["#02ffd0"],
            css_color: "purple",
            icon: "pallet"
        }
    }
    let blockNameWithResults = "#result .segment"
    $(blockNameWithResults).empty()

    let pathsOfClasses = paths;
    let centerOfUserArea = paths.center;
    delete pathsOfClasses.center;

    
    //_______ ОТРИСОВКА ПОЛИГОНОВ _____
    for (className in pathsOfClasses) {
        let subClassIndex = 0;
        // для каждого подтипа объектов
        for (subClass in pathsOfClasses[className]){
            let oneTypeObjesctsPath = [];
            let countOfAreas = 0;
            let commonArea = 0;
            // для каждого контура
            pathsOfClasses[className][subClass].forEach(function (contour) {
                let oneContour = []
                // переводим в массив для google Polygon
                oneContour.push(contour.map(function (val) {
                    return {
                        "lat": val[0],
                        "lng": val[1]
                    }
                }))
                countOfAreas += 1;
                oneTypeObjesctsPath.push(oneContour[0]);
            })// subClass - forEach(contour)
            
            // если контур может быть полигоном
            if (oneTypeObjesctsPath.length) {
                

                // отображаем контур
                var contourPoly = new google.maps.Polygon({
                    paths: oneTypeObjesctsPath,
                    fillColor: classProp[className].color[subClassIndex],
                    fillOpacity: 0.23,
                    strokeColor: classProp[className].color[subClassIndex],
                    strokeOpacity: 0.7,
                    map: map
                })
                commonArea += google.maps.geometry.spherical.computeArea(contourPoly.getPath());
                
                //_______ ТЕКСТОВЫЙ РЕЗУЛЬТАТ _____
                var classDescription = $(blockNameWithResults).append($('<div class="ui ribbon label"><i class="' + classProp[className].icon + ' icon"></i>' + subClass + '</div>').css({"background": classProp[className].color[subClassIndex]}));
                // $(classDescription).css({"background": classProp[className].color[subClassIndex]})
                
                $(classDescription).append($('<div class="ui list"><div class="item">\
                Общая площадь найденных объектов: ' + commonArea.toFixed(2) + ' m<sup><small>2</small></sup></div>\
                <div class="item">Всего найденных территорий: ' + countOfAreas + '</div></div>'))
                
            }// if length  
            
            subClassIndex += 1;
        }
    } //class
    
    map.setCenter(new google.maps.LatLng(centerOfUserArea[0], centerOfUserArea[1]));
}


// //_______ __________ ДОСТАТЬ ФОРМИРОВАНИЕ РЕЗУЛЬТАТА __________ _____ (ПЕРЕНЕСТИ НА СЕРВЕР)
//
//// insert info to result block
//function insertInfo(info, lang) {
//    $('#information').empty();
//
//    var enToRu = {
//        'tree': 'Деревья'
//    };
//    var lng = 0;
//    var Abin = [['Плохие условия', 'Bad'], ['Хорошие условия', 'Good'], ['Отличные условия', 'Exellent']]
//    if (lang != "RU") {
//        lng = 1;
//    }
//    var dictionary = [['В заданном квадрате обнаружено', 'Results for the selected area'], //0
//                     ['Общая площадь квадрата поиска: ', 'Total area of the search square: '], //1
//                     ['Всего участков территории с деревьями: ', 'Total land plots with trees: '], //2
//                  ['Площадь зеленых насаждений: ', 'Area of all trees: '], //3
//                  ['Качество озеленения согласно нормам Всемирной организациии здравохранения: ',
//                    'The quality of landscaping in accordance with the standards of the World Health Organization: '], //4
//                  ['Оценочное количество деревьев: ', 'Estimated number of trees: '], //5
//                  ['Одно крупное дерево выделяет столько кислорода, сколько нужно 1 человеку в сутки для дыхания.', //7
//                  'One large tree gives off as much oxygen as it takes one person a day to breathe.'],
//                  ['Новый запрос', 'New request'],
//                  ['Последние запросы', 'Last requests']];
//    //$('#information h4').remove();
//
//    $('#information').append($('<h4 class="ui header center aligned item">' + dictionary[0][lng] + '</h4>'))
//    //$('#info h4').after($('<div id="info_list" ></div>'))
//    path_img = 'static/css/icons/'
//    if (window.location.href.includes('share')) {
//        path_img = '../' + path_img;
//    }
//    //
//    $('#information').append($('<div class="ui grid middle aligned"></div>'))
//
//    $('#information .ui.grid').append($('<div class="row"> \
//                               <div class="three wide column"> <img src="' + path_img + 'grid.png"></div>' +
//        '<div class="thirteen wide column"><p>' + dictionary[1][lng] + info.squareArea.toFixed(2) + ' m<sup><small>2</small></sup></p></div>\
//                                      </div>'))
//
//    //$('#information').append($('<div class="one wide column"> <img src="'+path_img+'grid.png"></div>' + '<div class="four wide column><p>' + dictionary[1][lng] + //area.toFixed(2) + ' m<sup><small>2</small></sup></p></div>'))
//    //
//
//    $('#information .ui.grid').append($('<div class="row">\
//                    <div class="three wide column"> <img src="' + path_img + 'frames.png"></div>' + '<div class="thirteen wide column"><p>' + dictionary[2][lng] + areaCount + '</p></div>\
//                                        </div>'))
//
//    //$('#information .ui.grid').append($());
//
//    $('#information .ui.grid').append($('<div class="row"> \
//                               <div class="three wide column"> <img src="' + path_img + 'forest.png"></div>' +
//        '<div class="thirteen wide column"><p>' + dictionary[3][lng] +
//        (info.areaOfObjects).toFixed(2) +
//        ' m<sup><small>2</small></sup> </p> </div></div>'));
//    //
//    info.setAbin((info.areaOfObjects / info.squareArea).toFixed(2));
//    var abinText;
//    if (info.Abin < 0.1) {
//        abinText = Abin[0][lng];
//    } else if (info.Abin >= 0.1 && info.Abin < 0.6) {
//        abinText = Abin[1][lng];
//    } else {
//        abinText = Abin[2][lng];
//    }
//
//
//    $('#information .ui.grid').append($('<div class="row"> \
//                               <div class="three wide column"> <img src="' + path_img + 'quality.png"></div>' +
//        '<div class="thirteen wide column"><p>' + dictionary[4][lng] +
//        info.Abin + ' (Abin) - ' + abinText + '</p></div></div>'));
//    //    //
//
//    $('#information .ui.grid').append($('<div class="row"> \
//                               <div class="three wide column"> <img src="' + path_img + 'tree.png"></div>' +
//        '<div class="thirteen wide column"><p>' + dictionary[5][lng] +
//        Math.round(info.areaOfObjects / 20) + '</p></div></div>'))
//    //
//    //    $('#information .ui.grid').append($('<div class="row"> \
//    //                               <div class="three wide column"> <img src="'+path_img+'tree-silhouette.png"></div>' + 
//    //                                '<div class="thirteen wide column"><p>' + dictionary[6][lng] + '</p></div></div>'))
//}



//_______ ИНИЦИАЛИЗАЦИЯ КАРТЫ _____
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
    navigator.geolocation.getCurrentPosition(function(position){
        map.setCenter({"lat": position.coords.latitude, "lng": position.coords.longitude});   
    },
    function(Error){
        console.log(Error)
        map.setCenter({"lat": globalLat, "lng": globalLon});
    })
    return map
}



//_______ ИНИЦЦИАЛИЗАЦИЯ ПОИСКА МЕСТ ГУГЛ _____
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

            map.setZoom(zoom);
            map.setCenter(results[0].geometry.location);
            window.requestAddress = results['0'].formatted_address
            lat = results[0].geometry.location.lat();
            lng = results[0].geometry.location.lng();

        });
    });
}

//_______ ПОИСК НАЗВАНИЙ ИЗ КООР-Т ГУГЛ _____
// set name of userArea
function backGeoCode(lat, lng) {
    geocoder.geocode({
        'location': new google.maps.LatLng(lat, lng)
    }, function (results, status) {
        if (status == 'OK') {
            if (results[1]) {
                request.locationName = results[1].formatted_address.replace(/[\\/]+/g, " ");
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