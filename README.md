Sistema de Comandas Simples
Descrição

Sistema simples e prático para gerenciamento de comandas, com geração de PDF e suporte para impressão térmica de 80mm. Ideal para bares, lanchonetes e pequenas empresas que precisam de um controle rápido e eficiente de pedidos.

O sistema permite:

Criação e gerenciamento de comandas.

Salvamento automático das comandas em PDF.

Impressão direta em impressoras térmicas de 80mm.

Pré-requisitos

Python 3.x

Bibliotecas necessárias: reportlab, pyinstaller (para gerar o executável)

Impressora térmica compatível conectada

Instalação e Execução

Clone o repositório:

git clone https://github.com/XCHICOX/Sistemas-comandas.git

cd nome_do_repositorio


Instale as dependências:

pip install -r requirements.txt


Para gerar o executável:

pyinstaller --onefile seu_arquivo_principal.py


Execute o programa:

python seu_arquivo_principal.py


ou abra o executável gerado.

Observações

Certifique-se de configurar corretamente a impressora térmica antes de usar.

O PDF é gerado automaticamente para cada comanda, permitindo arquivamento digital e fácil consulta.
