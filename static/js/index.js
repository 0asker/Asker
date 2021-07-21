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



/* Scroll infinito */

function isScrolledIntoView(elem)
{
		var docViewTop = $(window).scrollTop();
		var docViewBottom = docViewTop + $(window).height();

		var elemTop = $(elem).offset().top;
		var elemBottom = elemTop + $(elem).height() / 2;

		return ((elemBottom <= docViewBottom) && (elemTop >= docViewTop));
}

pode_pegar_mais_questoes = true;
proxima_pagina_perguntas_recentes = 2; // por padrão a próxima página para pegar perguntas é 2.

window.onscroll = function() {
	if (isScrolledIntoView($("#carregamento_novas_perguntas"))) {
		if(window.getComputedStyle(document.getElementById("novas_questoes"), null).getPropertyValue("display") == "block" && pode_pegar_mais_questoes) {
			
			pode_pegar_mais_questoes = false;
			
			/* Obtem mais perguntas para a página inicial */
			
			$.ajax({
				url: "/more_questions",
				type: "get",
				data: {
					page: proxima_pagina_perguntas_recentes,
				},
				complete: function(data) {
					document.getElementById("novas_questoes").getElementsByTagName("ul")[0].innerHTML += data.responseText;
					pode_pegar_mais_questoes = true;
					proxima_pagina_perguntas_recentes++;
				}
			});
			
		}
	}
}
