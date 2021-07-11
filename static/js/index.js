if (getDarkCookie() == 'true') {
	document.getElementsByClassName('navbar')[0].classList.remove("navbar-light");
	document.getElementsByClassName('navbar')[0].classList.add("navbar-dark");
}

/* Renderiza a barra de navegação (popular / novas perguntas) */
new_html = `
<ul class="nav nav-tabs" id="tabs">
	<li class="nav-item">
		<span class="nav-link bg-main-tab" id="popular">Popular</span>
	</li>
	<li class="nav-item">
		<span class="nav-link bg-main-tab" id="news">Novas perguntas</span>
	</li>
</ul>
`;
main = document.getElementsByTagName("main")[0];
main.innerHTML = new_html + main.innerHTML;

/* Renderiza as questões recentes. */
recent_questions_list = document.getElementById("n_questions-list");

for (let index in recent_questions) {
	
	question = recent_questions[index];
	
	new_html = `
	<li class="list-group-item bg-main">
		<div class="card-body">
			<h2 class="question-title">
				<a href="/question/`+question["id"]+`">
					`+question["text"]+`
				</a>
			</h2>`;

	if (question["description"] != "") {
		
		if (question["description"].length > 300) {
			/* Mostrar mais e mostrar menos. */
			new_html += "<p><span>" + question["description"].slice(0, 300) + '<font onclick="$(this).toggle(0); $(this.parentElement.nextElementSibling).toggle(0);" style="cursor: pointer; color: #007bff">... Mostrar mais</font></span><span style="display: none">' + question["description"].slice(300) + ' <font onclick="$(this.parentElement).toggle(0); $(this.parentElement.previousElementSibling.getElementsByTagName(`font`)[0]).toggle(0);" style="cursor: pointer; color: #007bff">Mostrar menos</font></span></p>';
		} else {
			new_html += "<p class='description'>" + question["description"].replaceAll("\n", "<br>") + "</p>";
		}
	}

	new_html += `
		<small class="text-muted">
			<span>respostas: <span class="response-counter" data-iddapergunta="`+question["id"]+`">`+question["total_answers"]+`</span></span>
			<span>&nbsp;&middot;&nbsp;</span>
			<span>perguntado `+question['pub_date']+`</span>
		</small>
		<hr>
	`;

	if (question["user_response"] != "null") {
		/* Caso o usuário logado tenha respondido a pergunta, renderiza a resposta. */
		new_html += `
			<div class="user-response" data-iddapergunta="`+question["id"]+`">
			<p>
				<span>Sua resposta:</span><br>
				`+question["user_response"]+`
			</p>
		`;
	} else {
		/* Caso o usuário logado não tenha respondido a pergunta, renderiza o formulário para responder. */
		new_html += `
			<div class="user-response" data-iddapergunta="`+question["id"]+`">
				<div>
					<button class="btn btn-outline-primary btn-sm" onclick="$(this).toggle(0); $(this.parentElement.nextElementSibling).toggle(0);">
						<i class="fas fa-share"></i>
						responder
					</button>
				</div>
				
				<div style="display: none">
					<form onsubmit="return enviar_resposta_pergunta(this);">
						<input name="csrfmiddlewaretoken" type="hidden" value="`+csrf_token+`">
						<input name="question_id" type="hidden" value="`+question["id"]+`">
						<textarea onclick="$(this).css('height', '120px');" name="text" maxlength="5000" class="form-control form-control-sm" placeholder="Sua resposta" required></textarea>
						<button name="submit_btn" type="submit" class="btn btn-outline-primary btn-sm">
							<i class="far fa-paper-plane"></i>
							Enviar
						</button>
					</form>
				</div>
			</div>
		`;
	}

	new_html += `
		</div>
	</li>
`;
	recent_questions_list.innerHTML += new_html;
}


/* Renderiza as questões populares. */
popular_questions_list = document.getElementById("p_questions-list");

for (let index in popular_questions) {
	
	question = popular_questions[index];
	
	new_html = `
	<li class="list-group-item bg-main">
		<div class="card-body">
			<h2 class="question-title">
				<a href="/question/`+question["id"]+`">
					`+question["text"]+`
				</a>
			</h2>`;

	if (question["description"] != "") {
		
		if (question["description"].length > 300) {
			/* Mostrar mais e mostrar menos. */
			new_html += "<p><span>" + question["description"].slice(0, 300) + '<font onclick="$(this).toggle(0); $(this.parentElement.nextElementSibling).toggle(0);" style="cursor: pointer; color: #007bff">... Mostrar mais</font></span><span style="display: none">' + question["description"].slice(300) + ' <font onclick="$(this.parentElement).toggle(0); $(this.parentElement.previousElementSibling.getElementsByTagName(`font`)[0]).toggle(0);" style="cursor: pointer; color: #007bff">Mostrar menos</font></span></p>';
		} else {
			new_html += "<p class='description'>" + question["description"].replaceAll("\n", "<br>") + "</p>";
		}
	}

	new_html += `
		<small class="text-muted">
			<span>respostas: <span class="response-counter" data-iddapergunta="`+question["id"]+`">`+question["total_answers"]+`</span></span>
			<span>&nbsp;&middot;&nbsp;</span>
			<span>perguntado `+question['pub_date']+`</span>
		</small>
		<hr>
	`;

	if (question["user_response"] != "null") {
		/* Caso o usuário logado tenha respondido a pergunta, renderiza a resposta. */
		new_html += `
			<div class="user-response" data-iddapergunta="`+question["id"]+`">
			<p>
				<span>Sua resposta:</span><br>
				`+question["user_response"]+`
			</p>
		`;
	} else {
		/* Caso o usuário logado não tenha respondido a pergunta, renderiza o formulário para responder. */
		new_html += `
			<div class="user-response" data-iddapergunta="`+question["id"]+`">
				<div>
					<button class="btn btn-outline-primary btn-sm" onclick="$(this).toggle(0); $(this.parentElement.nextElementSibling).toggle(0);">
						<i class="fas fa-share"></i>
						responder
					</button>
				</div>
				
				<div style="display: none">
					<form onsubmit="return enviar_resposta_pergunta(this);">
						<input name="csrfmiddlewaretoken" type="hidden" value="`+csrf_token+`">
						<input name="question_id" type="hidden" value="`+question["id"]+`">
						<textarea onclick="$(this).css('height', '120px');" name="text" maxlength="5000" class="form-control form-control-sm" placeholder="Sua resposta" required></textarea>
						<button name="submit_btn" type="submit" class="btn btn-outline-primary btn-sm">
							<i class="far fa-paper-plane"></i>
							Enviar
						</button>
					</form>
				</div>
			</div>
		`;
	}

	new_html += `
		</div>
	</li>
`;
	popular_questions_list.innerHTML += new_html;
}


popular = document.getElementById('popular');
news = document.getElementById('news');
logo = document.getElementById('logo');

p_tab = document.getElementById('p_questions');
n_tab = document.getElementById('n_questions');

if (window.location.href.indexOf('news') == -1) {
	popular.classList.add('active');
	logo.href = '/popular';
	p_tab.style.display = 'block';
	n_tab.style.display = 'none';
} else {
	news.classList.add('active');
	logo.href = '/news';
	p_tab.style.display = 'none';
	n_tab.style.display = 'block';
}


// controlando cliques em <li> da <ul> de ID = tabs
popular.onclick = function () {
	popular.classList.add('active');
	news.classList.remove('active');
	window.history.pushState("object or string", "Title", "/popular");
	logo.href = '/popular';
	p_tab.style.display = 'block';
	n_tab.style.display = 'none';
}

news.onclick = function () {
	news.classList.add('active');
	popular.classList.remove('active');
	window.history.pushState("object or string", "Title", "/news");
	logo.href = '/news';
	p_tab.style.display = 'none';
	n_tab.style.display = 'block';
}


function enviar_resposta_pergunta(form) {
	
	form.style.opacity = 0.5;
	form.submit_btn.disabled = true;
	
	$.ajax({
		url: '/save_answer',
		type: 'post',
		data: $(form).serialize(),
		complete: function() {
			for (let key in document.getElementsByClassName('user-response')) {
				if (document.getElementsByClassName('user-response')[key].dataset['iddapergunta'] == form.question_id.value) {
					
					/* Aumenta o total de likes no contador de likes da pergunta. */
					all_response_counter = document.getElementsByClassName('response-counter');
					for (let index in all_response_counter) {
						try {
							if (all_response_counter[index].dataset['iddapergunta'] == form.question_id.value) {
								all_response_counter[index].innerText = Number(all_response_counter[index].innerText) + 1;
								break;
							}
						} catch (e) {
						}
					}
					
					new_html = `
<p>
	<span>Sua resposta:</span><br>
		`+form.text.value+`
</p>
`;
					document.getElementsByClassName('user-response')[key].innerHTML = new_html;
				}
			}
		}
	});
	
	return false;
}


/* Linkify */
$('.description').linkify({
	target: "_blank"
});
