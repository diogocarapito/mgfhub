// comportamentos do lado do cliente:
//  - toggle do painel lateral do IDE (estado persistido em localStorage)
//  - botão de alternância do tema claro/escuro (persistido em localStorage;
//    o tema é aplicado cedo, no <head>, para evitar flash)
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

    function ligarTema() {
        var botao = document.getElementById("tema-toggle");
        if (!botao) return;
        var etiqueta = botao.querySelector("[data-tema-label]");

        function atualizarEtiqueta() {
            var escuro = document.documentElement.dataset.theme === "dark";
            if (etiqueta) etiqueta.textContent = escuro ? "Modo claro" : "Modo escuro";
        }

        atualizarEtiqueta();

        botao.addEventListener("click", function () {
            var novo = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
            document.documentElement.dataset.theme = novo;
            localStorage.setItem("mgfhub-tema", novo);
            atualizarEtiqueta();
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        ligarToggle("toggle-aside", "aside-recolhido", "mgfhub-aside-recolhido");
        ligarTema();
    });
})();
