# -*- coding: utf-8 -*-
#
# satcfe/base.py
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

import collections
# import ctypes
import os
import random
import time
import xmltodict

# from ctypes import c_int
# from ctypes import c_char_p

# from satcomum import constantes
from .xml import render_xml, sanitize_response
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from time import sleep


class MonitorIntegrador(PatternMatchingEventHandler):
    patterns = ["*.xml"]

    def __init__(self, observer):
        super(MonitorIntegrador, self).__init__()
        self.observer = observer

    def process(self, event):
        """ Realiza o processamento dos arquivos criados e modificados dentro da pasta de output do integrador

        E ao ler o arquivo notifica o observador do numero identificador do arquivo e seu caminho.

        :param event:
                event_type = None

                    The type of the event as a string.

                is_directory = False

                    True if event was emitted for a directory; False otherwise.

                src_path[source]

                    Source path of the file system object that triggered this event.

        :return:
        """
        sleep(2)
        with open(event.src_path, 'r') as xml_source:
            xml_string = xml_source.read()
            parsed = xmltodict.parse(xml_string)
            self.observer.src_path = event.src_path
            self.observer.resposta = \
                parsed.get('Integrador', {}).get('Resposta', {}).get('retorno') or \
                parsed.get('Integrador', {}).get('Resposta', {}).get('IdPagamento') or \
                parsed.get('Integrador', {}).get('Resposta', {})
            if not isinstance(self.observer.resposta, dict):
                self.observer.resposta += '|' + parsed.get('Integrador', {}).get('Identificador', {}).get('Valor')
            self.observer.numero_identificador = parsed.get('Integrador', {}).get('Identificador', {}).get('Valor')

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


# class _Prototype(object):
#     def __init__(self, argtypes, restype=c_char_p):
#         self.argtypes = argtypes
#         self.restype = restype


# FUNCTION_PROTOTYPES = dict(
#         AtivarSAT=_Prototype([c_int, c_int, c_char_p, c_char_p, c_int]),
#         ComunicarCertificadoICPBRASIL=_Prototype([c_int, c_char_p, c_char_p]),
#         EnviarDadosVenda=_Prototype([c_int, c_char_p, c_char_p]),
#         CancelarUltimaVenda=_Prototype([c_int, c_char_p, c_char_p, c_char_p]),
#         ConsultarSAT=_Prototype([c_int,]),
#         TesteFimAFim=_Prototype([c_int, c_char_p, c_char_p]),
#         ConsultarStatusOperacional=_Prototype([c_int, c_char_p]),
#         ConsultarNumeroSessao=_Prototype([c_int, c_char_p, c_int]),
#         ConfigurarInterfaceDeRede=_Prototype([c_int, c_char_p, c_char_p]),
#         AssociarAssinatura=_Prototype([c_int, c_char_p, c_char_p, c_char_p]),
#         AtualizarSoftwareSAT=_Prototype([c_int, c_char_p]),
#         ExtrairLogs=_Prototype([c_int, c_char_p]),
#         BloquearSAT=_Prototype([c_int, c_char_p]),
#         DesbloquearSAT=_Prototype([c_int, c_char_p]),
#         TrocarCodigoDeAtivacao=_Prototype([c_int, c_char_p, c_int, c_char_p, c_char_p])
#     )


class NumeroSessaoMemoria(object):
    """Implementa um numerador de sessão simples, baseado em memória, não
    persistente, que irá gerar um número de sessão (seis dígitos) diferente
    entre os ``n`` últimos números de sessão gerados. Conforme a ER SAT, um
    número de sessão não poderá ser igual aos últimos ``100`` números.

    .. sourcecode:: python

        >>> numerador = NumeroSessaoMemoria(tamanho=5)
        >>> n1 = numerador()
        >>> 100000 <= n1 <= 999999
        True
        >>> n1 in numerador
        True
        >>> n2 = numerador()
        >>> n3 = numerador()
        >>> n4 = numerador()
        >>> n5 = numerador()
        >>> len(set([n1, n2, n3, n4, n5]))
        5
        >>> n6 = numerador()
        >>> n1 in numerador
        False

    """

    def __init__(self, tamanho=1):
        super(NumeroSessaoMemoria, self).__init__()
        self._tamanho = tamanho
        self._memoria = collections.deque(maxlen=tamanho)


    def __contains__(self, item):
        return item in self._memoria


    def __call__(self, *args, **kwargs):
        while True:
            numero = random.randint(100000, 999999)
            if numero not in self._memoria:
                self._memoria.append(numero)
                break
        return numero


class FuncoesVFPE(object):
    def __init__(self, caminho_integrador, chave_acesso_validador=None, numerador_sessao=None):
        self._caminho_integrador = self.limpa_formatacao_caminho_integrador(caminho_integrador)
        self._chave_acesso_validador = chave_acesso_validador
        self._numerador_sessao = numerador_sessao or NumeroSessaoMemoria()
        self._path = os.path.join(os.path.dirname(__file__), 'templates/')
                        
    @property
    def ref(self):
        """Uma referência para a biblioteca SAT carregada."""
        return self._libsat


    @property
    def caminho(self):
        """Caminho completo para a biblioteca SAT."""
        return self._caminho


    @property
    def convencao(self):
        """Convenção de chamada para a biblioteca SAT. Deverá ser um dos valores
        disponíveis na contante :attr:`~satcomum.constantes.CONVENCOES_CHAMADA`.
        """
        return self._convencao

    def limpa_formatacao_caminho_integrador(self, caminho):
        if caminho[0] != '/':
            caminho = '/' + caminho
        if caminho[len(caminho)-1] != '/':
            caminho = caminho + '/'

        return caminho.replace('\\', '/')

    @property
    def caminho_integrador(self):
        return self._caminho_integrador

    def gerar_numero_sessao(self):
        """Gera o número de sessão para a próxima invocação de função SAT."""
        return self._numerador_sessao()

    @property
    def chave_acesso_validador(self):
        return self._chave_acesso_validador


    # def __getattr__(self, name):
    #     if name.startswith('invocar__'):
    #         metodo_vfpe = name.replace('invocar__', '')
    #         proto = FUNCTION_PROTOTYPES[metodo_vfpe]
    #         fptr = getattr(self._biblioteca.ref, metodo_vfpe)
    #         fptr.argtypes = proto.argtypes
    #         fptr.restype = proto.restype
    #         return fptr
    #     raise AttributeError('{!r} object has no attribute {!r}'.format(
    #             self.__class__.__name__, name))

    def comando_vfpe(self, template, **kwargs):
        numero_identificador = kwargs.get(
            'numero_sessao',
            self.gerar_numero_sessao()
        )

        kwargs['numero_identificador'] = numero_identificador
        xml = render_xml(self._path, template, True, **kwargs)
        xml.write(
            str(self.caminho_integrador)+'input/' + str(numero_identificador) + '-' + template.lower(),
            xml_declaration=True,
            encoding='UTF-8'
        )

        observer = Observer()
        observer.numero_identificador = False
        observer.src_path = False
        observer.schedule(MonitorIntegrador(observer), path=str(self.caminho_integrador)+'output')
        observer.start()

        while True:
            # Analisa a pasta a cada um segundo.
            time.sleep(1)
            if str(numero_identificador) == observer.numero_identificador and observer.src_path:
                # Ao encontrar um arquivo de retorno com o mesmo numero identificador da remessa sai do loop.
                break
        observer.stop()
        observer.join()
        return observer.resposta

    def verificar_status_validador(self, cpnj, id_fila):
        """Função ``VerificarStatusValidador`` conforme ER SAT, item 6.1.14. Desbloqueio
        operacional do equipamento SAT.

        :return: Retorna *verbatim* a resposta da função SAT.
        :rtype: string
        """
        consulta = {
            'chave_acesso_validador': self._chave_acesso_validador,
            'id_fila': id_fila,
            'cnpj': cpnj,
        }

        return self.comando_vfpe('VerificarStatusValidador.xml', consulta=consulta)

    def enviar_pagamentos_armazenamento_local(self):
        """Função ``VerificarStatusValidador`` conforme ER SAT,
        item 6.1.14. Desbloqueio
        operacional do equipamento SAT.

        :return: Retorna *verbatim* a resposta da função SAT.
        :rtype: string
        """
        consulta = {
        }
        return self.comando_vfpe('EnviarPagamentosEmArmazenamentoLocal.xml',
                                 consulta=consulta)

    def enviar_pagamento(self, chave_requisicao, estabecimento, serial_pos,
                         cpnj, icms_base, vr_total_venda,
                         h_multiplos_pagamentos, h_anti_fraude,
                         cod_moeda, origem_pagemento):
        consulta = {
            'chave_acesso_validador': self._chave_acesso_validador,
            'chave_requisicao': chave_requisicao,
            'estabecimento': estabecimento,
            'serial_pos': serial_pos,
            'cpnj': cpnj,
            'icms_base': icms_base,
            'vr_total_venda': vr_total_venda,
            'h_multiplos_pagamentos': h_multiplos_pagamentos,
            'h_anti_fraude': h_anti_fraude,
            'cod_moeda': cod_moeda,
            'origem_pagemento': origem_pagemento
        }
        return self.comando_vfpe('EnviarPagamento.xml', consulta=consulta)


    def enviar_status_pagamento(self, codigo_autorizacao, bin, dono_cartao,
                                data_expiracao, instituicao_financeira, parcelas,
                                codigo_pagamento, valor_pagamento, id_fila,
                                tipo, ultimos_quatro_digitos):

        consulta = {
            'chave_acesso_validador': self._chave_acesso_validador,
            'codigo_autorizacao': codigo_autorizacao,
            'bin': bin,
            'dono_cartao':dono_cartao,
            'data_expiracao':data_expiracao,
            'instituicao_financeira':instituicao_financeira,
            'parcelas':parcelas,
            'codigo_pagamento':codigo_autorizacao,
            'valor_pagamento':valor_pagamento,
            'id_fila':id_fila,
            'tipo':tipo,
            'ultimos_quatro_digitos':ultimos_quatro_digitos
        }
        return self.comando_vfpe('EnviarStatusPagamento.xml', consulta=consulta)

    def recuperar_dados_locais_enviados(self):

        consulta = {
            'chave_acesso_validador': self._chave_acesso_validador,
        }
        return self.comando_vfpe('RecuperarDadosLocaisEnviadosParaValidadorFiscal.xml', consulta=consulta)

    def resposta_fiscal(self, id_fila, chave_acesso, nsu, numero_aprovacao,
                        bandeira, adquirente, cnpj, impressao_fiscal,
                        numero_documento):

        consulta = {
            'chave_acesso_validador': self._chave_acesso_validador,
            'id_fila': id_fila,
            'chave_acesso': chave_acesso,
            'nsu': nsu,
            'numero_aprovacao': numero_aprovacao,
            'bandeira': bandeira,
            'adquirente': adquirente,
            'cnpj': cnpj,
            'impressao_fiscal': impressao_fiscal,
            'numero_documento': numero_documento,
        }
        return self.comando_vfpe("RespostaFiscal.xml", consulta=consulta)


