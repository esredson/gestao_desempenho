import argparse, datetime, json, random, requests, urllib3
from bs4 import BeautifulSoup

CAMPO_GRUPO_GESTOR = 'og_group_ref[und][0][default]'
CAMPO_UNIDADE_PRINCIPAL = 'field_er_jf2_mr_ativ_servidor[und]'
CAMPO_UNIDADE_ORGANIZACIONAL = 'field_er_unidade_organizacional[und]'
CAMPO_SERVIDOR = 'field_jf2_gd_servidor_uo[und]'
CAMPO_ATIVIDADE = 'field_er_gd_ativid_uo_servidor[und]'
CAMPO_ANO = 'field_er_gd_ano_monitoramento[und]'
CAMPO_MES = 'field_er_gd_mes_monitoramento[und]'
CAMPO_QUINZENA = 'field_er_gd_quinzena_monitora[und]'
CAMPO_QUANTIDADE = 'field_gd_quant_ativid_monitora[und][0][value]'
CAMPO_TOKEN = 'form_token'
CAMPO_ID_FORM = 'form_build_id',
CAMPO_RESUMO = 'field_gd_detalhe_ativid_monitora[und][0][summary]'
CAMPO_DETALHAMENTO = 'field_gd_detalhe_ativid_monitora[und][0][value]'
CAMPO_FORMATO = 'field_gd_detalhe_ativid_monitora[und][0][format]'

def echo(*texto):
   print('\n\n', *texto, '\n\n')

def obter_args():
   ano_atual = datetime.datetime.now().year
   ano_anterior = ano_atual - 1

   parser = argparse.ArgumentParser()

   parser.add_argument(
      '--ano', 
      choices=[ano_atual, ano_anterior], 
      type=int,
      help='Informe o --ano',
      required=True)
   parser.add_argument(
      '--mes', choices=['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'], 
      type=str,
      help='Informe o --mes (apenas as 3 primeiras letras, minúsculas)',
      required=True)
   parser.add_argument(
      '--quinzena', 
      choices=[1, 2], 
      type=int,
      help='Informe a --quinzena',
      required=True)
   parser.add_argument(
      '--total_horas', 
      type=int,
      help='Informe o --total_horas da quinzena. Normalmente são 7 por dia. Faça a conta.',
      required=True
   )
   parser.add_argument(
      '--efetivar', 
      action='store_true',
      help='Informe --efetivar para executar os posts',
   )

   args = parser.parse_args()
   return args

def obter_props_do_json():
   with open('props.json', 'r', encoding='utf-8') as file:
      props = json.load(file)
   return props

def obter_atividades_realizadas_do_json():
   with open('atividades_realizadas.json', 'r', encoding='utf-8') as file:
      atividades_realizadas = json.load(file)
   return atividades_realizadas

def fazer_logon(sessao, props):
   url = props['url_base'] + '/user'
   payload = {
      'name': props['matricula'],
      'pass': props['senha'],
      'form_id': 'user_login',
      'op': 'Entrar',
   }
   res = sessao.post(url, data=payload, allow_redirects=True, verify=False)
   assert res.status_code == 200, "Logon não retornou 200"
   assert "autenticado com sucesso via Siga" in res.text, "Logon não foi bem sucedido"

   echo('Logon efetuado com sucesso')


def obter_id_servidor(sessao, props, id_unidade_organizacional):
   url = props['url_base']+'/ddf/update/field_er_unidade_organizacional/node/jf2_gd_matriz_resp_monitoramento/NULL'

   params = {
      'field_er_unidade_organizacional': id_unidade_organizacional
   }

   res = sessao.get(url, params=params, verify=False)
   assert res.status_code == 200, "Consulta aos servidores não retornou 200"

   servidores_as_html = res.json()[1]['data']
   soup = BeautifulSoup(servidores_as_html, 'html.parser')
   servidor = soup.find(
      'option', string='  '+props['coordenadoria']+'  -  '+props['matricula']+'  -  '+props['nome']+' '
   )
   assert servidor is not None, "Servidor não encontrado"

   id_servidor = servidor['value']
   
   echo('Servidor: ', id_servidor)

   return id_servidor


def obter_ids(sessao, props, args):
   url = props['url_base']+'/node/add/jf2-gd-matriz-resp-monitoramento'

   res = sessao.get(url, verify=False)
   assert res.status_code == 200, "URL IDs básicos não retornou 200"

   soup = BeautifulSoup(res.text, 'html.parser')

   grupo_gestor = soup.find(
      'select', attrs={'name': CAMPO_GRUPO_GESTOR}
   ).find(
      'option', string=props['secretaria']+'*'
   )
   assert grupo_gestor is not None, "Grupo gestor não encontrado"

   unidade_principal = soup.find(
      'select', attrs={'name': CAMPO_UNIDADE_PRINCIPAL}
   ).find(
      'option', string='  '+props['orgao']+'  -  '+props['secretaria']+' '
   )
   assert unidade_principal is not None, "Unidade principal não encontrada"

   unidade_organizacional = soup.find(
      'select', attrs={'name': CAMPO_UNIDADE_ORGANIZACIONAL}
   ).find(
      'option', string='  '+props['orgao']+'  -  '+props['coordenadoria']+' '
   )
   assert unidade_organizacional is not None, "Unidade organizacional não encontrada"

   ano = soup.find(
      'select', attrs={'name': CAMPO_ANO}
   ).find(
      'option', string=args.ano
   )
   assert ano is not None, "Ano não encontrado"

   mes = soup.find(
      'select', attrs={'name': CAMPO_MES}
   ).find(
      'option', string='  '+args.mes+' '
   )
   assert mes is not None, "Mês não encontrado"

   quinzena = soup.find(
      'select', attrs={'name': CAMPO_QUINZENA}
   ).find(
      'option', string=str(args.quinzena)+'ª quinzena'
   )
   assert quinzena is not None, "Quinzena não encontrada"

   token = soup.find(
      'input', attrs={'name': CAMPO_TOKEN}
   )
   assert token is not None, "Token não encontrado"

   ids = {
      'grupo_gestor': grupo_gestor['value'],
      'unidade_principal': unidade_principal['value'],
      'unidade_organizacional': unidade_organizacional['value'],
      'ano': ano['value'],
      'mes': mes['value'], 
      'quinzena': quinzena['value'],
      'token': token['value']
   }

   ids['servidor'] = obter_id_servidor(sessao, props, ids['unidade_organizacional'])

   echo('IDs básicos: ', ids)
   
   return ids

def obter_atividades_do_servidor(sessao, props, id_servidor):
   url = props['url_base']+'/ddf/update/field_jf2_gd_servidor_uo/node/jf2_gd_matriz_resp_monitoramento/NULL'

   params = {
      'field_jf2_gd_servidor_uo': id_servidor
   }

   res = sessao.get(url, params=params, verify=False)
   assert res.status_code == 200, "Lista de atividades não retornou 200"

   atividades_as_html = res.json()[1]['data']
   soup = BeautifulSoup(atividades_as_html, 'html.parser')

   atividades = {}
   for opt in soup.find_all('option'):
      if opt['value'] == '_none':
         continue
      key = opt.get_text(strip=True).split(f"  -  {props['secretaria']}/{props['coordenadoria']}")[0]
      value = opt['value']

      atividades[key] = value
   
   echo('Atividades cadastradas para o servidor: ', atividades)

   return atividades

def inserir_id_nas_atividades_realizadas(atividades_cadastradas, atividades_realizadas):
   for realizada in atividades_realizadas:
      cadastrada = atividades_cadastradas[realizada['descricao']]

      realizada['id'] = cadastrada
   echo('Atividades realizadas com IDs: ', atividades_realizadas)

def sortear(pesos):
   peso_total = sum(pesos)
   assert 1 - peso_total < 0.01, "Os pesos precisam somar 1"

   pesos_acumulados = []
    
   peso_acumulado = 0
   for p in pesos:
      peso_acumulado += p
      pesos_acumulados.append(peso_acumulado)

   aleatorio_entre_0_e_1 = random.random()

   for i, peso_acumulado in enumerate(pesos_acumulados):
      if aleatorio_entre_0_e_1 <= peso_acumulado:
         return i

   raise "Erro"

def sortear_ateh_atingir_qtd_horas_e_inserir_nas_atividades_realizadas(atividades_realizadas, qtd_horas_a_atingir):
   for atividade in atividades_realizadas:
      atividade['quantidade'] = 0

   pesos = [atividade['peso'] for atividade in atividades_realizadas]
   qtd_horas_atingida = 0
   while qtd_horas_atingida < qtd_horas_a_atingir:
        i = sortear(pesos)
        atividades_realizadas[i]['quantidade']+=1
        qtd_horas_atingida += atividades_realizadas[i]['horas_por_unidade']
   
   echo("Quantidade de horas atingida: "+ str(qtd_horas_atingida))
   echo('Atividades realizadas com quantidades: ', atividades_realizadas)

def obter_id_form(sessao, props):
   url = props['url_base']+'/node/add/jf2-gd-matriz-resp-monitoramento'

   res = sessao.get(url, verify=False)
   assert res.status_code == 200, "URL form_build_id não retornou 200"

   soup = BeautifulSoup(res.text, 'html.parser')

   id_form = soup.find(
      'input', attrs={'name': CAMPO_ID_FORM}
   )
   assert id_form is not None, "Grupo gestor não encontrado"
   return id_form['value']

def gerar_posts(sessao, props, args, ids, atividades_realizadas):
   url = props['url_base']+'/node/add/jf2-gd-matriz-resp-monitoramento'
   headers = {
      "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
      "accept-language": "en,pt-BR;q=0.9,pt;q=0.8,en-US;q=0.7,es;q=0.6,it;q=0.5",
      "cache-control": "max-age=0",
      "sec-ch-ua": "\"Google Chrome\";v=\"113\", \"Chromium\";v=\"113\", \"Not-A.Brand\";v=\"24\"",
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "\"Windows\"",
      "sec-fetch-dest": "document",
      "sec-fetch-mode": "navigate",
      "sec-fetch-site": "same-origin",
      "sec-fetch-user": "?1",
      "upgrade-insecure-requests": "1"
   }
   payload = {
      'form_token': ids['token'],
      'form_id': 'jf2_gd_matriz_resp_monitoramento_node_form',
      CAMPO_GRUPO_GESTOR: ids['grupo_gestor'],
      CAMPO_UNIDADE_PRINCIPAL: ids['unidade_principal'],
      CAMPO_UNIDADE_ORGANIZACIONAL: ids['unidade_organizacional'],
      CAMPO_SERVIDOR: ids['servidor'],
      CAMPO_ANO: ids['ano'],
      CAMPO_MES: ids['mes'],
      CAMPO_QUINZENA: ids['quinzena'],
      CAMPO_RESUMO: '',
      CAMPO_DETALHAMENTO: '',
      CAMPO_FORMATO: 'filtered_html',
      'op': 'Salvar',
      'changed': '',
      'additional_settings__active_tab': ''
   }

   for atividade in atividades_realizadas:
      if atividade['quantidade'] == 0:
         continue  
      payload[CAMPO_ID_FORM] = obter_id_form(sessao, props)
      payload[CAMPO_ATIVIDADE] = atividade['id']
      payload[CAMPO_QUANTIDADE] = atividade['quantidade']

      echo('Salvando atividade: ', payload)
      
      if args.efetivar:
         res = sessao.post(url, data=payload, headers=headers, allow_redirects=True, verify=False)
         assert res.status_code == 200, "Post não retornou 200"
         assert "foi criado" in res.text, "Post não foi bem sucedido"
            
def main():
   urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
   sessao = requests.Session()
   
   args = obter_args()
   props = obter_props_do_json()
   fazer_logon(sessao, props)
   ids = obter_ids(sessao, props, args)
   atividades_cadastradas = obter_atividades_do_servidor(sessao, props, ids['servidor'])
   atividades_realizadas = obter_atividades_realizadas_do_json()
   inserir_id_nas_atividades_realizadas(atividades_cadastradas, atividades_realizadas)
   sortear_ateh_atingir_qtd_horas_e_inserir_nas_atividades_realizadas(atividades_realizadas, args.total_horas)
   gerar_posts(sessao, props, args, ids, atividades_realizadas)

if __name__ == "__main__":
    main()
