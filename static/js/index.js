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
			var response_counter = document.getElementById('response-counter-' + form.question_id.value);
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


/*
 * Renderiza as questões recentes. */

var questoes_recentes = document.getElementById("lista_de_questoes_recentes");

for (var index = 0; index < 20; ++index) {
questoes_recentes.innerHTML += '<li class="list-group-item bg-main questao" data-id="'+recent_questions[index].id+'">' +
																'<div class="card-body">' +
																	'<div class="flexbox">' +
																		'<h2 class="question-title fg-1">' +
																			'<a href="/question/'+recent_questions[index].id+'">' +
																				recent_questions[index].text +
																			'</a>' +
																		'</h2>' +
																		(user_status != "anonymous" ? '<a class="clickable" href="javascript:void(0);" data-toggle="modal" data-target="#question-modal" onclick=\'select_user("'+recent_questions[index].creator+'");\'><i class="fas fa-ellipsis-h"></i></a>' : '') +
																	'</div>' +
																	(recent_questions[index].description != '' ? '<p class="description">'+recent_questions[index].description+'</p>' : '') +
																	'<small class="text-muted">' +
																		'<span>respostas: <span id="response-counter-'+recent_questions[index].id+'">'+recent_questions[index].total_answers+'</span></span>' +
																		'<span>&nbsp;&middot;&nbsp;</span>' +
																		'<span>perguntado '+recent_questions[index].pub_date+' por </span>' +
																		'<a href="/user/'+recent_questions[index].creator+'">'+recent_questions[index].creator+'</a>' +
																	'</small>' +
																	'<hr>' +
																	(user_status == "anonymous" ? '<p>Faça <a href="/signin?redirect=/question/'+recent_questions[index].id+'">login</a> ou <a href="/signup?redirect=/question/'+recent_questions[index].id+'">crie uma conta</a> para responder essa pergunta.</p>' : '') +
																	(recent_questions[index].user_answer != 'False' ? '<div class="user-response" data-iddapergunta="'+recent_questions[index].id+'"><p><b>Sua resposta:</b><br>'+recent_questions[index].user_answer+'</p></div>' : '<div class="user-response" data-iddapergunta="'+recent_questions[index].id+'">'+
																	'<div>' +
																	
																	(user_status != "anonymous" ?
																	
																		'<button class="btn btn-outline-primary btn-sm" onclick="$(this).toggle(0); $(this.parentElement.parentElement.nextElementSibling).toggle(0);">' +
																			'<i class="fas fa-share"></i>' +
																			' responder' : '') +
																		'</button>' +
																	'</div></div>' +
																	'<div style="display: none">' +
																		'<form onsubmit="return enviar_resposta_pergunta(this);">' +
																			'<input type="hidden" name="csrfmiddlewaretoken" value="'+csrf_token+'">' +
																			'<input type="hidden" name="from" value="index">' +
																			'<input name="question_id" type="hidden" value="'+recent_questions[index].id+'">' +
																			'<textarea onclick=\'$(this).css("height", "120px");\' name="text" maxlength="5000" class="form-control form-control-sm" placeholder="Sua resposta" required></textarea>' +
																			'<button name="submit_btn" type="submit" class="btn btn-outline-primary btn-sm">' +
																			'<i class="far fa-paper-plane"></i>' +
																			' Enviar' +
																			'</button>' +
																		'</form>' +
																		'</div>') +
																'</div>' +
															'</li>';
}




/* Renderiza as questões populares. */
var questoes_populares = document.getElementById("lista_de_questoes_populares");

for (var index = 0; index < 20; ++index) {
questoes_populares.innerHTML += '<li class="list-group-item bg-main questao" data-id="'+popular_questions[index].id+'">' +
																'<div class="card-body">' +
																	'<div class="flexbox">' +
																		'<h2 class="question-title fg-1">' +
																			'<a href="/question/'+popular_questions[index].id+'">' +
																				popular_questions[index].text +
																			'</a>' +
																		'</h2>' +
																		(user_status != "anonymous" ? '<a class="clickable" href="javascript:void(0);" data-toggle="modal" data-target="#question-modal" onclick=\'select_user("'+popular_questions[index].creator+'");\'><i class="fas fa-ellipsis-h"></i></a>' : '') +
																	'</div>' +
																	(popular_questions[index].description != '' ? '<p class="description">'+popular_questions[index].description+'</p>' : '') +
																	'<small class="text-muted">' +
																		'<span>respostas: <span id="response-counter-'+popular_questions[index].id+'">'+popular_questions[index].total_answers+'</span></span>' +
																		'<span>&nbsp;&middot;&nbsp;</span>' +
																		'<span>perguntado '+popular_questions[index].pub_date+' por </span>' +
																		'<a href="/user/'+popular_questions[index].creator+'">'+popular_questions[index].creator+'</a>' +
																	'</small>' +
																	'<hr>' +
																	(user_status == "anonymous" ? '<p>Faça <a href="/signin?redirect=/question/'+popular_questions[index].id+'">login</a> ou <a href="/signup?redirect=/question/'+popular_questions[index].id+'">crie uma conta</a> para responder essa pergunta.</p>' : '') +
																	(popular_questions[index].user_answer != 'False' ? '<div class="user-response" data-iddapergunta="'+popular_questions[index].id+'"><p><b>Sua resposta:</b><br>'+popular_questions[index].user_answer+'</p></div>' : '<div class="user-response" data-iddapergunta="'+popular_questions[index].id+'">'+
																	'<div>' +
																	
																	(user_status != "anonymous" ?
																	
																		'<button class="btn btn-outline-primary btn-sm" onclick="$(this).toggle(0); $(this.parentElement.parentElement.nextElementSibling).toggle(0);">' +
																			'<i class="fas fa-share"></i>' +
																			' responder' : '') +
																		'</button>' +
																	'</div></div>' +
																	'<div style="display: none">' +
																		'<form onsubmit="return enviar_resposta_pergunta(this);">' +
																			'<input type="hidden" name="csrfmiddlewaretoken" value="'+csrf_token+'">' +
																			'<input type="hidden" name="from" value="index">' +
																			'<input name="question_id" type="hidden" value="'+popular_questions[index].id+'">' +
																			'<textarea onclick=\'$(this).css("height", "120px");\' name="text" maxlength="5000" class="form-control form-control-sm" placeholder="Sua resposta" required></textarea>' +
																			'<button name="submit_btn" type="submit" class="btn btn-outline-primary btn-sm">' +
																			'<i class="far fa-paper-plane"></i>' +
																			' Enviar' +
																			'</button>' +
																		'</form>' +
																		'</div>') +
																'</div>' +
															'</li>';
}
