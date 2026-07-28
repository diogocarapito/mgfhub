// comportamentos do lado do cliente:
//  - botão de alternância do tema claro/escuro (persistido em localStorage;
//    o tema é aplicado cedo, no <head>, para evitar flash)
//  - zonas de upload do IDE (clique/arrastar, lista, auto-análise)
(function () {
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

    // zonas de upload do IDE: seleção acumulativa (clique ou arrastar),
    // lista dos ficheiros carregados e remoção individual
    function ligarUploads() {
        var inputs = document.querySelectorAll(".nav-upload input[type=file]");
        if (!inputs.length) return;

        // impede o browser de abrir/navegar quando se larga um ficheiro fora
        // de uma zona de upload (só ativo em páginas com upload)
        ["dragover", "drop"].forEach(function (ev) {
            window.addEventListener(ev, function (e) {
                if (!(e.target.closest && e.target.closest(".file-drop"))) e.preventDefault();
            });
        });

        inputs.forEach(function (input) {
            var campo = input.closest(".upload-campo");
            if (!campo) return;
            var form = input.closest("form.nav-upload");
            var drop = campo.querySelector('label[for="' + input.id + '"]');
            var etiqueta = drop ? drop.querySelector("[data-ficheiro-label]") : null;
            var lista = campo.querySelector(".ficheiros-lista");

            // fonte de verdade acumulada (o input nativo substitui a cada escolha)
            var acumulados = [];

            function escrever() {
                var dt = new DataTransfer();
                acumulados.forEach(function (f) { dt.items.add(f); });
                input.files = dt.files;
            }

            // re-analisa automaticamente (htmx faz POST e actualiza os gráficos)
            function submeter() {
                if (!form) return;
                if (typeof form.requestSubmit === "function") {
                    form.requestSubmit();
                } else {
                    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true }));
                }
            }

            function render() {
                var n = acumulados.length;
                if (drop) drop.classList.toggle("tem-ficheiro", n > 0);
                if (etiqueta) etiqueta.textContent = n === 0 ? "Escolher ficheiros" : "Adicionar mais";
                if (!lista) return;
                lista.innerHTML = "";
                acumulados.forEach(function (f, i) {
                    var li = document.createElement("li");

                    var nome = document.createElement("span");
                    nome.className = "ficheiro-nome";
                    nome.textContent = f.name;
                    nome.title = f.name;

                    var btn = document.createElement("button");
                    btn.type = "button";
                    btn.className = "ficheiro-remover";
                    btn.setAttribute("aria-label", "Remover " + f.name);
                    btn.textContent = "×";
                    btn.addEventListener("click", function () {
                        acumulados.splice(i, 1);
                        escrever();
                        render();
                        submeter();
                    });

                    li.appendChild(nome);
                    li.appendChild(btn);
                    lista.appendChild(li);
                });
            }

            // junta ficheiros (do picker ou de drag-and-drop), só .xlsx, sem repetir
            function adicionar(ficheiros) {
                var mudou = false;
                Array.prototype.forEach.call(ficheiros, function (f) {
                    if (!/\.xlsx$/i.test(f.name)) return;
                    var repetido = acumulados.some(function (g) {
                        return g.name === f.name && g.size === f.size;
                    });
                    if (!repetido) {
                        acumulados.push(f);
                        mudou = true;
                    }
                });
                if (mudou) {
                    escrever();
                    render();
                    submeter();
                }
            }

            input.addEventListener("change", function () {
                adicionar(input.files);
            });

            // drag-and-drop na própria zona
            if (drop) {
                ["dragenter", "dragover"].forEach(function (ev) {
                    drop.addEventListener(ev, function (e) {
                        e.preventDefault();
                        drop.classList.add("a-arrastar");
                        if (etiqueta) etiqueta.textContent = "Largar aqui";
                    });
                });
                drop.addEventListener("dragleave", function (e) {
                    if (!drop.contains(e.relatedTarget)) {
                        drop.classList.remove("a-arrastar");
                        render();
                    }
                });
                drop.addEventListener("drop", function (e) {
                    e.preventDefault();
                    drop.classList.remove("a-arrastar");
                    if (e.dataTransfer && e.dataTransfer.files) adicionar(e.dataTransfer.files);
                    render();
                });
            }
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        ligarTema();
        ligarUploads();
    });
})();
