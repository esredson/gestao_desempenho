

### Objetivo

Este script automatiza o processo de cadastro das tarefas realizadas pela pessoa numa quinzena. O próprio script define a quantidade de cada tarefa. Mas essa definição não é totalmente aleatória.

Primeiro, a pessoa predefine (no arquivo `atividades_realizadas.json`) quais tarefas ela sempre executa. Cada tarefa deve vir acompanhada de um peso, representando a fatia que, em média, a tarefa costuma consumir do tempo. Os pesos de todas as tarefas devem somar 1. 

Ao executar o script, a pessoa informa o ano, o mês, a quinzena e o total de horas trabalhadas na quinzena. O script então gera uma quantidade adequada para cada tarefa respeitando os peso predefinidos. Ou seja, as quantidades são sorteadas, mas as probabilidades respeitam os pesos das tarefas. Ao final, o script envia os posts para efetivar o cadastro (um post para cada tarefa).

### Pré-requisitos:

- [Git 2.31.1](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
- [Python 3.9.7](https://www.python.org/downloads/)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)
  - [Crie um ambiente virtual](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/) pra instalar essa lib, se achar melhor.
  - Para instalar: `pip install beautifulsoup4` 

### Preparação inicial

1. [Baixe este projeto pelo Git](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
2. Peça os arquivos `atividades_realizadas.json` e `props.json` já preenchidos e altere os dados.
	- As descrições no arquivo `atividades_realizadas.json` precisam existir cadastradas no site de modo exatamente igual pois a relação entre o que estiver no arquivo e as tarefas do site é feita pela descrição (isso é ruim, mas por enquanto é o jeito). 
	- Não precisam constar nesse arquivo todas as atividades que estão liberadas no site pra pessoa; apenas as que ela quer lançar. Se não souber a descrição exata das atividades no site, execute a aplicação sem o `--efetivar` (ver abaixo) que as tarefas que estiverem liberadas no site pra pessoa vão aparecer todas no output.

### Execução quinzenal:

- Execute o main.py `python ./main.py --ano 2023 --mes mai --quinzena 1 --total_horas 70`
	- Para efetuar os posts, é preciso passar também o argumento `--efetivar`. Mas é recomendável rodar antes sem esse argumento, apenas para saber se todos os asserts vão passar. Assim, a aplicação inteira executa mas sem fazer os posts.
	- Caso prefira rodar no modo debug, esses argumentos ficam na chave `args` do `.vscode/launch.json`
	- Após a execução, verifique no site se as tarefas foram cadastradas com sucesso