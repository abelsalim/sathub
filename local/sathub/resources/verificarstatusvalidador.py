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

from flask.ext import restful

from ..comum.util import hexdump
from ..comum.util import instanciar_funcoes_vfpe
from ..custom import request_parser


logger = logging.getLogger('sathub.resource')

parser = request_parser()

parser.add_argument('numero_caixa',type=str,required=True)
parser.add_argument('cnpj',type=str,required=True)
parser.add_argument('id_fila',type=str,required=True)
parser.add_argument('chave_acesso_validador',type=str,required=True)
parser.add_argument('caminho_integrador',type=str,required=False)


class VerificarStatusValidador(restful.Resource):

    def post(self):
        args = parser.parse_args()

        numero_caixa = int(args['numero_caixa'])
        cnpj = args['cnpj']
        id_fila = args['id_fila']
        chave_acesso_validador = args['chave_acesso_validador']

        if args.get('caminho_integrador'):
            fvfpe = instanciar_funcoes_vfpe(
                numero_caixa, chave_acesso_validador,
                args['caminho_integrador']
            )
        else:
            fvfpe = instanciar_funcoes_vfpe(numero_caixa)
        retorno = fvfpe.verificar_status_validador(cnpj, id_fila)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Retorno "EnviarDadosVenda" '
                    '(numero_caixa=%s)\n%s', numero_caixa, hexdump(retorno))

        return dict(funcao='VerificarStatusValidador', retorno=retorno)
