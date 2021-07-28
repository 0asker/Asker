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
			response_counter = document.getElementById('response-counter-' + form.question_id.value);
			response_counter.innerText = Number(response_counter.innerText) + 1;
			form.parentElement.innerHTML = data.responseText;
		},
	});
	
	return false;
}

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
                if (data.responseText == 'Added') {
                    location.reload();
                    return false;
                }
            }
        });
  } else {
    alert("Você cancelou a operação.");
  }
  $('#question-modal').modal('hide');
  selected_user = null;
}

function load_more() {
	$.ajax({
			url: "/more_questions",
			type: "get",
			data: {
					id_de_inicio: document.getElementById("novas_questoes").getElementsByClassName("questao")[document.getElementById("novas_questoes").getElementsByClassName("questao").length - 1].getAttribute("data-id") - 1,
			},
			complete: function(data) {
					document.getElementById("novas_questoes").getElementsByTagName("ul")[0].innerHTML += data.responseText;
			}
	});
}
