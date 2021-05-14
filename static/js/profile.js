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
				questions.innerHTML += '<hr><div class="question"><a href="/question/'+val.id+'">'+val.text+'</a> <span>&middot; perguntada '+val.naturalday+'</span></div><hr>'
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
				responses.innerHTML += '<hr><div class="response"><a href="/question/'+val.question_id+'">'+val.question_text+'</a><br><p>'+val.text+'</p></div><hr>'
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
