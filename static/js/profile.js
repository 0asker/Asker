questions = document.getElementById("questions")
responses = document.getElementById("responses")
questions_section = document.getElementById("questions-section")
responses_section = document.getElementById("responses-section")

questions.onclick = function() {
	questions.classList.add("active")
	questions.classList.remove("disabled")
	
	responses.classList.add("disabled")
	responses.classList.remove("active")
	
	questions_section.style.display = "block"
	responses_section.style.display = "none"
}

responses.onclick = function() {
	questions.classList.add("disabled")
	questions.classList.remove("active")
	
	responses.classList.add("active")
	responses.classList.remove("disabled")
	
	questions_section.style.display = "none"
	responses_section.style.display = "block"
}


q_page = 1
function show_more_questions(button, uid) {
	questions = document.getElementById('qs')
	
	$.ajax({
		type: 'get',
		dataType: 'json',
		url: '/get_more_questions',
		data: {
			q_page: ++q_page,
			user_id: uid,
		},
		complete: function(data) {
			data = JSON.parse(data.responseText)
			
			$.each(data.questions, function(i, val) {
			        var newLi = '<li class="list-group-item bg-main"><div class="question card-body"><a href="/question/'+val.id+'">'+val.text+'</a><br><span style="color: #888; font-size: 80%;">Perguntada '+val.naturalday+'</span>';
                    if (!val.best_answer) {
                        /* val.best_answer será -1 se proibido, a qid se existir, e null se não existir */
                        newLi += '<br><span style="color: #888; font-size: 80%;">Sem melhor resposta</span>';
                    }
					newLi += '</div></li>';

				questions.innerHTML += newLi;
			})
			
			if(!data.has_next) {
				button.remove()
			}
		}
	})
}


r_page = 1
function show_more_responses(button, uid) {
	responses = document.getElementById('rs')
	
	$.ajax({
		type: 'get',
		dataType: 'json',
		url: '/get_more_responses',
		data: {
			r_page: ++r_page,
			user_id: uid,
		},
		complete: function(data) {
			data = JSON.parse(data.responseText)
			
			$.each(data.responses, function(i, val) {
			    var newLi = '<li class="list-group-item bg-main"><div class="response card-body"><a href="/question/'+val.question_id+'">'+val.question_text+'</a><br><p>';
			    if (val.best_answer) {
			        newLi += '<span class="badge badge-pill badge-primary">🏆 Melhor resposta</span> ';
			    }
			    newLi += val.text + '</p><span style="color: #888; font-size: 80%;">Perguntada por <a href="/user/'+val.creator+'">'+val.creator+'</a> '+val.naturalday+'</span></div></li>';
			    responses.innerHTML += newLi;
			})
			
			if(!data.has_next) {
				button.remove()
			}
		}
	})
}

function toggleDarkMode() {
	formbgcolor='bg-darkerish'; bgcolor='bg-dark'; textcolor='text-light';
	inactivetextcolor='text-secondary';
	document.body.style = "background: #222; color: white;";
	document.getElementsByClassName('navbar')[0].classList.add("bg-dark");
	document.getElementsByClassName('navbar')[0].classList.add("navbar-dark");
	document.getElementsByClassName('navbar')[0].classList.remove("bg-light");
	document.getElementsByClassName('navbar')[0].classList.remove("navbar-light");
	document.getElementById('tabs').classList.add("dark");

	activitytabs = document.getElementsByClassName('activity-tab')
	for (i = 0; i < activitytabs.length; i++) {
		activitytabs[i].classList.add(bgcolor);
		activitytabs[i].classList.add(inactivetextcolor);
	}
}
