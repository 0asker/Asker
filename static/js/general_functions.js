/*
 * ░██╗░░░░░░░██╗░█████╗░██████╗░███╗░░██╗██╗███╗░░██╗░██████╗░
 * ░██║░░██╗░░██║██╔══██╗██╔══██╗████╗░██║██║████╗░██║██╔════╝░
 * ░╚██╗████╗██╔╝███████║██████╔╝██╔██╗██║██║██╔██╗██║██║░░██╗░
 * ░░████╔═████║░██╔══██║██╔══██╗██║╚████║██║██║╚████║██║░░╚██╗
 * ░░╚██╔╝░╚██╔╝░██║░░██║██║░░██║██║░╚███║██║██║░╚███║╚██████╔╝
 * ░░░╚═╝░░░╚═╝░░╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░╚══╝╚═╝╚═╝░░╚══╝░╚═════╝░
 * 
 * Sempre que este arquivo for atualizado, atualizar a versão dele em TODOS os templates.
 * Por exemplo:
 *  de:   /static/js/general_functions.js?version=1
 *  para: /static/js/general_functions.js?version=2
 */

function veracity_test(user_points, MINIMUM_POINTS_FOR_POSTING_IMAGES) {
	if (user_points < MINIMUM_POINTS_FOR_POSTING_IMAGES) {
		alert('Você precisa de pelo menos ' + MINIMUM_POINTS_FOR_POSTING_IMAGES + ' pontos para postar imagens.');
		return false;
	}
	return true;
}
