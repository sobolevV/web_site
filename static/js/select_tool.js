var TILE_SIZE = 256;
var maxUserArea = 300000;
var userArea;

function clearLines(lines) {
    lines.forEach(function (line) {
        line.setMap(null);
    })
}

// google function - print latlng for events
function getCoordnates(event) {
    if (event.type == 'circle') {
        var center = event.overlay.getCenter();
        var radius = event.overlay.getRadius();
        console.log(event.overlay, center, radius);
    } else if (event.type == 'rectangle') {
        var rectBounds = event.overlay.getBounds();
        var left_top = {
            'lat': rectBounds.ma.j,
            'lon': rectBounds.fa.j
        };
        var right_bot = {
            'lat': rectBounds.ma.l,
            'lon': rectBounds.fa.l
        };
        console.log(left_top, right_bot);
    } else if (event.type == 'polygon') {
        var path = event.overlay.getPath();
        path['j'].forEach(function (LatLng, arr) {
            console.log(LatLng.lat(), LatLng.lng());
        })
    }
}

function setDrawingTools(map) {

    // options for drawing
    var drawingOptions = {
        fillColor: 'yellow',
        fillOpacity: 0.25,
        strokeWeight: 2,
        strokeColor: "yellow",
        clickable: true,
        draggable: false,
        editable: true,
        zIndex: 1
    };
    // drawing tool
    // drawingMode: google.maps.drawing.OverlayType.MARKER,
        var drawingManager = new google.maps.drawing.DrawingManager({
            drawingControl: false, // отключить инструменты
            drawingControlOptions: {
                position: google.maps.ControlPosition.LEFT_TOP,
                drawingModes: ['circle', 'polygon', 'rectangle']
            },
            rectangleOptions: drawingOptions,
            circleOptions: drawingOptions,
            polylineOptions: drawingOptions,
            polygonOptions: drawingOptions
    
        });
    //init drawing
    drawingManager.setMap(map);
    // console.log(drawingManager, $(drawingManager));
    
    // init events for new drawn areas
    google.maps.event.addListener(drawingManager, 'overlaycomplete', function (event) {
        
        console.log(event.overlay)
        google.maps.event.addListener(event.overlay, 'rightclick', function () {
            console.log(event.type + ' deleted');
            event.overlay.setMap(null);
        })
        google.maps.event.addListener(event.overlay, 'dragend', function () {
            console.log(event.type + ' dragend');
            getCoordnates(event);
        })
        //dragend
        google.maps.event.addListener(event.overlay, 'bounds_changed', function () {
            console.log(event.type + ' bounds_changed');
            getCoordnates(event);
        })
        //
        google.maps.event.addListener(event.overlay, 'heading_changed', function () {
            console.log(event.type + ' heading_changed');
            getCoordnates(event);
        })

    });

    var polyPath = [];
    var shapePath = [];

    var lines = [] // массив точек долготы и широты
    var inProcess = false;

    $('#select_tool').click(function (e) {

        if ($(this).hasClass('purple')) {
            
            map.setOptions({draggableCursor:'crosshair'});
            selectButtons('show', map);
            $(this).toggleClass('purple blue');
            $(this).text('Выключить инструмент');

            // удаляем иконки с карты
            map.setOptions({
                styles: [
                {
                  "featureType": "poi",
                  "stylers": [
                    { "visibility": "off" }
                  ]
                }
              ]
            });


            google.maps.event.addListener(map, 'click', function () {
                if (userArea) {
                    userArea.setMap(null);
                }

                shapePath = [];
                if (lines.length > 0) {
                    clearLines(lines);
                    lines = [];
                }

                map.setOptions({
                    gestureHandling: 'none'
                }) //заморозка карты

                inProcess = true;

                google.maps.event.addListener(map, 'mousemove', function (event) {
                    // console.log(event.latLng.lat(), event.latLng.lng());

                    polyPath.push(event.latLng)

                    shapePath.push(event.latLng)
                    if (shapePath.length > 2) {

                        // полигон вместо отрисовки линии
                        var shortLine = new google.maps.Polygon({
                            map: map,
                            paths: [shapePath[shapePath.length - 1], shapePath[shapePath.length - 2]],
                            geodesic: true,
                            fillColor: "#yellow",
                            fillOpacity: 0,
                            strokeColor: 'yellow',
                            strokeOpacity: 0.8,
                            strokeWeight: 4
                        });

                        // array for choosing lines
                        lines.push(shortLine);

                        // завершение полигона
                        google.maps.event.addListener(shortLine, 'click', function () {

                            map.setOptions({
                                gestureHandling: ''
                            }) //разаморозка карты
                            google.maps.event.clearListeners(map, 'mousemove');


                            userArea = new google.maps.Polygon({
                                map: map,
                                paths: polyPath,
                                strokeColor: 'yellow',
                                strokeOpacity: 0.8,
                                strokeWeight: 2,
                                fillColor: "green",
                                fillOpacity: 0.25,
                                draggable: false,
                                geodesic: true,
                            })
                            
                            request.setArea(userArea);
                            // request.getLocation
                            // console.log(window.request.getArea());
                            // polygons.push(userArea);
                            var drawnArea = google.maps.geometry.spherical.computeArea(polyPath);
                            if (drawnArea > maxUserArea) {
                                userArea.strokeColor = "red";
                                userArea.fillColor = "red";
                                $("#user_popup_inform .header").text("Слишком большая площадь выделенного участка!");
                                $("#user_popup_inform li").eq(0).text("Ваша площадь: " + Math.round(drawnArea));
                                $("#user_popup_inform li").eq(1).text("Максимальная допустимая: " + maxUserArea);
                                $("#user_popup_inform").transition('browse right');
                            } else {
                                userArea.fillColor = "green";
                                if (!$("#user_popup_inform").hasClass("hidden")){
                                    $("#user_popup_inform").transition();
                                } 
                            }

                            google.maps.event.addListener(userArea, 'rightclick', function () {
                                userArea.setMap(null);
                            })

                            clearLines(lines);
                            lines = [];
                            polyPath = [];
                            inProcess = false;
                        })
                    } // end draw

                }) // mousemove
            }) // map listener
        } // if hasClass
        else {
            selectButtons('hide', map);
            $(this).toggleClass('purple blue');
            $(this).text('Выделить область');
            map.setOptions({draggableCursor: ''});
        }
    }) // enable draw


    // сдвигаем инструменты для выделения 
    setTimeout(function () {
        $('.gmnoprint:eq(2)').css({
            'margin-left': '18px'
        })
    }, 1000)


    // отключаем рисовалку
    $('#select_tool').click(function () {
        if (!inProcess && $('#select_tool').hasClass("active")) {
            google.maps.event.clearListeners(map, 'click');
        }
    })


    $('#rm_select').click(function () {
        if (userArea) {
            if (!$("#user_popup_inform").hasClass("hidden")){
                $("#user_popup_inform").transition();
            } 
            userArea.setMap(null);
            polygons = [];
        }
    })
}

function selectButtons(typeEvent, map) {
    if (typeEvent == "show") {
        $('#rm_select').css({
            display: ''
        });

    } else {

        map.setOptions({
            styles: 'none'
        });

        $('#rm_select').css({
            display: 'none'
        });
    }
}

function project(latLng) {
    var siny = Math.sin(latLng.lat() * Math.PI / 180);

    // Truncating to 0.9999 effectively limits latitude to 89.189. This is
    // about a third of a tile past the edge of the world tile.
    siny = Math.min(Math.max(siny, -0.9999), 0.9999);

    return new google.maps.Point(
        TILE_SIZE * (0.5 + latLng.lng() / 360),
        TILE_SIZE * (0.5 - Math.log((1 + siny) / (1 - siny)) / (4 * Math.PI)));
}
