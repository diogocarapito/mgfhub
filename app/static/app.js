// toggles das barras laterais (nav global e painel do IDE), com estado
// persistido em localStorage para sobreviver a navegação e reloads
(function () {
    function ligarToggle(botaoId, alvoClasse, chave) {
        var botao = document.getElementById(botaoId);
        if (!botao) return;

        if (localStorage.getItem(chave) === "1") {
            document.body.classList.add(alvoClasse);
        }

        botao.addEventListener("click", function () {
            var recolhida = document.body.classList.toggle(alvoClasse);
            localStorage.setItem(chave, recolhida ? "1" : "0");
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        ligarToggle("toggle-nav", "nav-recolhida", "mgfhub-nav-recolhida");
        ligarToggle("toggle-aside", "aside-recolhido", "mgfhub-aside-recolhido");
    });
})();
