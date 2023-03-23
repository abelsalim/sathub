# -*- coding: utf-8 -*-
#
# sathub/resources/enviardadosvenda.py
#
# Copyright 2015 Base4 Sistemas Ltda ME
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging

import json

import xmltodict

from flask_restful import Resource

from ..comum.util import hexdump
from ..comum.util import instanciar_funcoes_sat
from ..comum.util import instanciar_numerador_sessao as instanciar_numerador
from ..custom import request_parser


logger = logging.getLogger('sathub.resource')

parser = request_parser()

parser.add_argument('dados_venda',
        type=str,
        required=True,
        help=u'XML contendo os dados do CF-e de venda')


class EnviarDadosVenda(Resource):


    def pega_lista(self, numero_caixa):
        with open(f'/opt/sathub/sessoes-cx-{numero_caixa}.json') as file:
            return json.load(file)


    def post(self):
        
        while True:
            args = parser.parse_args()

            numero_caixa = args['numero_caixa']
            dados_venda = args['dados_venda']
            
            # Extraindo pedido do xml
            xml = xmltodict.parse(dados_venda)
            pedido = xml['CFe']['infCFe']['infAdic']['infCpl'].split(' ')[1]

            # Resgatando dicionário com a última venda
            numerador_instanciado = instanciar_numerador(numero_caixa)
            ultimas_vendas = numerador_instanciado._ultimas_vendas
            
            # Instanciando objeto sathub
            fsat = instanciar_funcoes_sat(numero_caixa)
            
            # Consultando MFE
            consultar_sat = fsat.consultar_sat()

            if not consultar_sat:
                return 'Sem comunicação com o MFE!'

            # Verificando se o último cupom emitido é o mesmo do atual 
            if ultimas_vendas:
                for venda in ultimas_vendas:
                    dados_json, pedido_json, cupom_json = (x for x in venda.values())
                    if dados_venda == dados_json and pedido == pedido_json:
                        return f'Documento já emitido pelo {cupom_json} e Minuta {pedido_json}'

            # Envio de cupom
            retorno = fsat.enviar_dados_venda(dados_venda)

            # Obtendo retorno do cupom (Se foi emitido ou não)
            if retorno.split("|")[1] == '06000':
                numero_cupom = f'CF-e nº {int(retorno.split("|")[8][34:40])}'

                # Montando dicionário da venda atual
                ultima_venda_dict = {
                    'xml_ultima_venda': dados_venda,
                    'pedido_ultima_venda': pedido,
                    'cupom_ultima_venda': numero_cupom
                    }

                # Enviando dicionário para arquivo
                numerador_instanciado._escrever_dados_venda_json(ultima_venda_dict)

            elif retorno.split("|")[1] == '06097':
                continue
                
            break

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Retorno "EnviarDadosVenda" '
                    '(numero_caixa=%s)\n%s', numero_caixa, hexdump(retorno))

        return dict(funcao='EnviarDadosVenda', retorno=retorno)
