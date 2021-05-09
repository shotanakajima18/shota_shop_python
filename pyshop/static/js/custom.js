$(function(){
    localStorage.clear()
  $("#followbtn").on('click',function(){
      var user_id = $(this).attr('attr-user-id');
      $.ajax({
          type : 'POST',
          url :'/user/'+user_id+'/follow',
          data : null,
          contentType:'application/json'
      }).done(function(data){
        $(this).removeClass("btn-success");
        $(this).addClass("btn-primary");
        $(this).text("Following");
        console.log(data);
    });
  });


});