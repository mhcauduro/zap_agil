\# 🤖 Zap Ágil



\*\*Zap Ágil\*\* é uma poderosa ferramenta de automação para envio de mensagens personalizadas via WhatsApp Web, com suporte a anexos, campanhas agendadas, gravações de áudio e relatórios detalhados. Sua interface acessível é construída com \*\*wxPython\*\*, oferecendo controle total via mouse e atalhos de teclado.



Desenvolvido por \*\*MHC Softwares\*\*.



---



\## ⚙️ Funcionalidades



\- ✅ Envio automatizado de mensagens para contatos e grupos  

\- 📁 Suporte a listas de contatos em `.txt` ou `.xlsx`  

\- 🗑️ Agendamento de campanhas por data e hora  

\- 📎 Anexos: documentos, imagens e áudios  

\- 🎙️ Gravação de áudio dentro da própria interface  

\- 📊 Relatórios de entrega no formato CSV  

\- 🔄 Reconexão automática ao recarregar o WhatsApp Web  

\- ♿ Interface totalmente acessível e navegável por teclado (wxPython)  

\- 🧠 Detecção de números inválidos e mensagens de erro  

\- ⚖️ Registro interno de logs e notificações visuais



---



\## 🔧 Como Funciona



\### 🪀 Visão Geral



Zap Ágil automatiza o envio de mensagens no WhatsApp via controle do navegador com Selenium, além de gerenciar gravações, arquivos e agendamento com bibliotecas Python robustas.



\### 📢 Núcleo de Mensagens



\- Usa Selenium e `webdriver-manager` para interagir com o WhatsApp Web  

\- Envia mensagens individualmente, seja digitado ou via mídia/áudio  

\- Detecta números inválidos e registra nos relatórios



\### ⏰ Agendador



\- Utiliza `APScheduler` para controle preciso da data e hora  

\- Suporta tarefas únicas ou recorrentes



\### 💾 Importação de Contatos



\- Aceita arquivos `.txt` e `.xlsx` com `openpyxl`  

\- Permite adicionar ou editar contatos manualmente pela interface



\### 🎧 Áudio



\- Grava áudios com `sounddevice` e salva no formato OGG/Opus com `soundfile`  

\- Reprodução com suporte a pausar e continuar



\### 📈 Relatórios



\- Todos os envios, status e erros são registrados  

\- Exportação para CSV com timestamps e agrupamento por campanha



\### 📝 Configurações e Modelos



\- Modelos de mensagem editáveis e com variáveis como `@Nome`, `@DataVencimento`  

\- Configurações são armazenadas automaticamente



---



\## 🌐 Acessibilidade e UX



\- Interface criada com `wxPython`  

\- Navegação completa pelo teclado (Tab, Alt, setas)  

\- Atalhos para todas as funções (Ctrl+N, Ctrl+D etc.)  

\- Dicas (tooltips) em todos os botões  

\- Compatível com leitores de tela



---



\## 📂 Estrutura do Projeto



```

zap\_agil\_master/

├── zap\_agil/              # Código principal da aplicação

├── tests/                 # Testes (pytest)

├── assets/                # Ícones, documentos, arquivos estáticos

├── .vscode/               # Configurações e tarefas de desenvolvimento

├── zap\_agil.pyw           # Inicializador da aplicação

├── zap\_agil.spec          # Configuração do PyInstaller

├── requirements.txt

├── dev-requirements.txt

├── pyproject.toml

└── README.md

```



---



\## 🚀 Primeiros Passos



1\. \*\*Clone o repositório\*\*



```bash

git clone https://github.com/seu-usuario/zap-agil.git

cd zap-agil/zap\_agil\_master

```



2\. \*\*Crie o ambiente virtual\*\*



```bash

python -m venv .venv

```



\- \*\*Windows:\*\*  

&nbsp; `.venv\\Scripts\\activate`



\- \*\*macOS/Linux:\*\*  

&nbsp; `source .venv/bin/activate`



3\. \*\*Instale as dependências\*\*



```bash

pip install -r requirements.txt

```



\- Para desenvolvimento:



```bash

pip install -r dev-requirements.txt

```



4\. \*\*Execute a aplicação\*\*



```bash

python zap\_agil/zap\_agil.pyw

```



---



\## 🦞 Dicas de Uso (Teclado e Mouse)



\### Navegação



\- `Ctrl+Tab`: alternar abas  

\- `Alt`: ativar barra de menus



\### Atalhos Globais



\- `Ctrl+Q`: sair da aplicação  

\- `Ctrl+M`: minimizar para a bandeja  

\- `Ctrl+T`: abrir modelos  

\- `Ctrl+A`: agendar campanhas  

\- `Ctrl+R`: ver relatórios  

\- `Ctrl+G`: configurações  

\- `Ctrl+N`: ler notícias  

\- `Ctrl+D`: ler dicas de uso



\### Envio de Mensagens



\- Digitar contato: pressione Enter  

\- Adição manual: preencher + `Ctrl+Enter`  

\- Remover contato: selecionar + Delete  

\- Carregar lista: clique ou `Ctrl+B`



\### Mensagem e Anexos



\- Use variáveis como `@Nome`, `@DataVencimento`  

\- Anexar documento: `Ctrl+D`  

\- Anexar mídia: `Ctrl+I`  

\- Anexar áudio: `Ctrl+A`  

\- Gravar: ● Gravar → clique para parar  

\- Reproduzir/Pausar: ▶ / ❚❚



\### Modelos



\- Novo: `Ctrl+N`  

\- Salvar: `Ctrl+S`  

\- Excluir: `Ctrl+D`  

\- Anexar: `Ctrl+B`  

\- Remover: `Ctrl+R`  

\- Fechar: `Esc`



\### Relatórios



\- Exportar CSV: `Ctrl+E`  

\- Excluir: `Ctrl+D`  

\- Fechar: `Esc`



\### Agendador



\- Novo: `Ctrl+N`  

\- Duplicar: `Ctrl+P`  

\- Excluir: `Ctrl+D`  

\- Salvar: `Ctrl+S`  

\- Fechar: `Esc`



\### Usuários de Mouse



\- Passe o mouse para visualizar dicas  

\- Campos obrigatórios são destacados  

\- Menus oferecem acesso total às funções



\### Usuários de Teclado



\- Navegação com Tab, Shift+Tab, setas  

\- Use `Alt` para acessar menus  

\- Use `Enter` para confirmar diálogos



---



\## ✅ Recomendações



\- Sempre revise sua lista de contatos antes de enviar  

\- Use modelos para campanhas frequentes  

\- Monitore relatórios para acompanhar entregas  

\- Veja \*\*Ajuda > Dicas de Uso\*\* para mais informações



---



\## 📚 Para Desenvolvedores



\### Lint e Formatação



```bash

ruff check .

ruff check . --fix

```



\- Ou no VS Code:  

&nbsp; `Ctrl+Shift+P → Executar Tarefa → lint`



\### Testes



```bash

pytest

```



\### Geração do Executável (.exe)



```bash

pyinstaller zap\_agil.spec

```



> O executável será salvo em `dist/zap\_agil/`



---



\*\*Divirta-se!\*\*  

\_MHC Softwares\_

```



