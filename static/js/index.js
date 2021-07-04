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


function hide_form_buttons(form) {
	form.getElementsByClassName('form-button')[0].style.display = 'none'
	form.getElementsByClassName('form-button')[1].style.display = 'none'
	return false
}

function show_form_buttons(form) {
	form.getElementsByClassName('form-button')[0].style.display = 'inline'
	form.getElementsByClassName('form-button')[1].style.display = 'inline'
	return false
}

function make_answer(qid) {
	form = document.getElementById('form-' + qid);
	div = form.parentElement;
	modal = document.getElementById('modal-' + qid);
	
	form.style.display = 'none';
	modal.style.display = 'block';
	
	$.ajax({
		url: '/save_answer',
		type: 'post',
		data: $('#form-' + qid).serialize(),
		complete: function() {
			modal.style.display = 'none';
			div.innerHTML += '<span style="display: block"><b>Sua resposta:</b></span> ' + form.text.value;
		},
	});
}


function show_or_hide_response_form(form) {
	$(form).toggle(200);
}


function send_response_to_popular_question(form) {
	form.parentElement.style.display = 'none';
	form.parentElement.parentElement.getElementsByClassName('p-q-loading-icon')[0].style.display = 'block';
	
	$.ajax({
		url: '/save_answer',
		type: 'post',
		data: $(form).serialize(),
		complete: function() {
			form.parentElement.parentElement.getElementsByClassName('p-q-loading-icon')[0].style.display = 'none';
			
			html = `
<div class="p-q-user-answer"> <!-- popular question user answer -->
	<hr>
	<label>
		Sua resposta:
	</label>
	<p>
		` + form.text.value + `
	</p>
</div>
`
			
			form.parentElement.parentElement.innerHTML += html;
		}
	});
}
