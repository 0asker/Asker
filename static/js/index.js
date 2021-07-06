popular = document.getElementById('popular')
news = document.getElementById('news')
logo = document.getElementById('logo')

p_tab = document.getElementById('p_questions')
n_tab = document.getElementById('n_questions')

if (window.location.href.indexOf('news') == -1) {
	popular.classList.add('active')
	logo.href = '/popular'
	p_tab.style.display = 'block'
	n_tab.style.display = 'none'
} else {
	news.classList.add('active')
	logo.href = '/news'
	p_tab.style.display = 'none'
	n_tab.style.display = 'block'
}


// controlando cliques em <li> da <ul> de ID = tabs
popular.onclick = function () {
	popular.classList.add('active')
	news.classList.remove('active')
	window.history.pushState("object or string", "Title", "/popular");
	logo.href = '/popular'
	p_tab.style.display = 'block'
	n_tab.style.display = 'none'
}

news.onclick = function () {
	news.classList.add('active')
	popular.classList.remove('active')
	window.history.pushState("object or string", "Title", "/news");
	logo.href = '/news'
	p_tab.style.display = 'none'
	n_tab.style.display = 'block'
}


function enviar_resposta_pergunta_aba_recentes(form) {
	
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
						} catch {
						}
					}
					
					new_html = `
<hr>
<p>
	<font color="black">Sua resposta:</font><br>
		`+form.text.value+`
</p>
`
					document.getElementsByClassName('user-response')[key].innerHTML = new_html;
				}
			}
		}
	});
	
	return false;
}
