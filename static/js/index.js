if (getDarkCookie() == 'true') {
	document.getElementsByClassName('navbar')[0].classList.remove("navbar-light");
	document.getElementsByClassName('navbar')[0].classList.add("navbar-dark");
}


function enviar_resposta_pergunta(form) {
	
	form.style.opacity = 0.5;
	form.submit_btn.disabled = true;
	
	$.ajax({
		url: '/save_answer',
		type: 'post',
		data: $(form).serialize(),
		complete: function(data) {
			
			document.getElementById('response-counter-' + form.question_id.value).innerText = Number(document.getElementById('response-counter-' + form.question_id.value).innerText) + 1;
			
			form.parentElement.innerHTML = data.responseText;
		}
	});
	
	return false;
}


/* Linkify */
$('.description').linkify({
	target: "_blank"
});


/* Paginação */
var url = new URL(window.location.href);
var current_page = url.searchParams.get('page');

if (current_page == null)
	next_page = '2';
else
	next_page = Number(current_page) + 1;

document.getElementById('next_page_recent_questions').href += next_page;

var selected_user = null;

function select_user(username) {
    selected_user = username;
}

function silence_user() {
  if (!selected_user) {
    return 0;
  }
  if (confirm("Você silenciou o usuário: " + selected_user)) {
        $.ajax({
            type: 'get',
            url: '/user/' + selected_user + '/silence',
            complete: function(data) {
                location.reload();
                return false;
            }
        })
  } else {
    alert("Você cancelou a operação.");
  }
  $('#question-modal').modal('hide');
  selected_user = null;
}
