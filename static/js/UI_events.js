// добавить обработку кнопки на закрытие инф. сообщения




// нажатие на кнопку выбора класса
$("#list_of_classes > button").click(function(){
		$(this).toggleClass("active");
		$(this).children('i').toggleClass("purple");
	request.toggleClass($(this).val())
})


// нажате на кнопку запроса результатов
function sentRequest(buttonId) {
    $(buttonId).click(function () {

    // вместо долготы и широты проверяем полигон
        if (request.getArea() && request.getClasses().length > 0) {
            $(this).toggleClass('disabled');
            
           
            makePost(request.getNormalizeAreaArray(), request.getClasses(), request.locationName);
            
        } else {
            if (!request.getArea()){
                alert('Вы не выделили место');    
            }
            else{
                alert('Вы не выбрали нужные объекты');
            }
            
        }
        //sheck lat lon end
    })
}