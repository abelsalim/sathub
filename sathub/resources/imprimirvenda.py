# -*- coding: utf-8 -*-
#
# sathub/resources/imprimirvenda.py
#
# Copyright 2017 KMEE INFORMATICA LTDA
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

from flask_restful import Resource
from satextrato.venda import ExtratoCFeVenda

from ..comum.util import hexdump
from ..comum.util import instanciar_impressora
from ..custom import request_parser
import base64
from io import StringIO

from satextrato import config as conf
conf.code128_quebrar = True
conf.Rodape.esquerda = 'https://www.zenirmoveis.com.br'
conf.Rodape.direita = 'T.I Grupo Zenir'
conf.Cupom.avancar_linhas = 3
conf.Cupom.exibir_nome_consumidor = True
conf.Cupom.itens_modo_condensado = True
conf.Cupom.resumido = True
logger = logging.getLogger('sathub.resource')

parser = request_parser()

parser.add_argument('dados_venda',
        type=str,
        required=True,
        help=u'XML contendo os dados do CF-e de venda')
parser.add_argument('modelo', type=str, required=True)
parser.add_argument('conexao', type=str, required=True)
parser.add_argument('site_sefaz', type=str, required=True)


class ImprimirVenda(Resource):

    def post(self):
        args = parser.parse_args()

        dados_venda = args['dados_venda']
        modelo = args['modelo']
        conexao = args['conexao']
        resumido = False
        impressora = instanciar_impressora('file', modelo, conexao)
        xml = StringIO(dados_venda)
        impressao = ExtratoCFeVenda(xml, impressora, resumido)
        impressao.imprimir()
