# -*- coding: utf-8 -*-
#
# sathub/comum/util.py
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

import json
import os
import random
import sys
import psutil

from satcfe import BibliotecaSAT
from satcfe import ClienteSATLocal
from satcfe.base import FuncoesSAT
from ..integrador.base import FuncoesVFPE

from .config import PROJECT_ROOT
from .config import conf

from ..comum.config import basicConfig
from logging import critical


NUM_SESSAO_MIN = 100000
NUM_SESSAO_MAX = 999999

NUM_CAIXA_MIN = 0
NUM_CAIXA_MAX = 999

NUM_CAIXAS_MAX = (NUM_CAIXA_MAX - NUM_CAIXA_MIN) + 1

NUM_POR_FAIXA = int((NUM_SESSAO_MAX - NUM_SESSAO_MIN) / NUM_CAIXAS_MAX)


def faixa_numeracao(numero_caixa):
    """
    Retorna a faixa de numeração de sessão para o número do caixa.

    .. sourcecode:: python

        >>> a, b = faixa_numeracao(0) # caixa 0
        >>> NUM_SESSAO_MIN <= a <= NUM_SESSAO_MAX
        True
        >>> NUM_SESSAO_MIN <= b <= NUM_SESSAO_MAX
        True

        >>> x, y = faixa_numeracao(999) # caixa 999
        >>> NUM_SESSAO_MIN <= x <= NUM_SESSAO_MAX
        True
        >>> NUM_SESSAO_MIN <= y <= NUM_SESSAO_MAX
        True

    """
    _num_caixa = numero_caixa + 1
    n_min = ((_num_caixa * NUM_POR_FAIXA) + NUM_SESSAO_MIN) - NUM_POR_FAIXA
    n_max = (_num_caixa * NUM_POR_FAIXA) + NUM_SESSAO_MIN
    if _num_caixa > 1:
        n_min += 1
    return n_min, n_max


class NumeradorSessaoPorCaixa(object):
    """
    Um numerador de sessões persistente, gravando os números gerados em
    arquivos no formato JSON.

    Para evitar problemas de concorrência no acesso ao arquivo e para anular a
    possibilidade de números de sessão conflitantes entre os caixa, cada
    caixa terá o seu próprio arquivo de númeração de sessão e sua própria
    faixa de numeração, usando o seguinte esquema:

    A ER SAT deixa claro, no atributo B14 (``numeroCaixa``) que são possíveis
    caixas númerados entre 0 e 999, o que dá a possibilidade de 1000 caixas.

    Os números de sessão devem ser números de 6 dígitos, o que dá um limite
    entre 100000 e 999999. Assim, 999999-100000 dá 899999 que, se dividido
    por 1000 (caixas) dá uma faixa de cerca de 899:

    .. sourcecode:: python

        >>> 999999 - 100000
        899999
        >>> 899999 / 1000
        899

    Assim, cada caixa terá a sua própria faixa de numeração de sessão, o que
    torna impossível conflitos de número de sessão. Além disso, cada caixa
    terá um arquivo próprio, onde os números gerados serão persistidos,
    garantindo que os últimos 100 números gerados para aquele caixa não serão
    repetidos.

    +-------+-----------------------------+
    | Caixa | Faixa de Números de Sessão  |
    +=======+=============================+
    |   0   | 100000 a 100899             |
    +-------+-----------------------------+
    |   1   | 100900 a 101798             |
    +-------+-----------------------------+
    |                 ...                 |
    +-------+-----------------------------+
    |  999  | 998102 a 999000             |
    +-------+-----------------------------+

    """

    def __init__(self, tamanho=100, numero_caixa=1):
        super(NumeradorSessaoPorCaixa, self).__init__()
        self._memoria = []
        self._ultimas_vendas = []
        self._tamanho = tamanho
        self._numero_caixa = numero_caixa

        # Certifica se o número do caixa está entre o mínimo e o máximo
        assert NUM_CAIXA_MIN <= self._numero_caixa <= NUM_CAIXA_MAX, \
            f'Numero do caixa fora da faixa (0..999): {self._numero_caixa}'

        # Define arquivo em variável e carrega dados do json de sessões
        self._arquivo_json = self._file_exists(
            f'sessoes-cx-{self._numero_caixa}.json')

        self._carregar_memoria()

        # Define arquivo em variável e carrega dados do json da ultima venda
        self._ultimas_vendas_json = self._file_exists(
            f'ultima-venda-cx-{self._numero_caixa}.json')

        self._recuperar_dados_venda()

        # Define arquivo em variável e carrega dados do json dos últimos erros
        self._ultimos_erros_json = self._file_exists('ultimos-erros.json')

    def __call__(self, *args, **kwargs):
        while True:
            numero = random.randint(*faixa_numeracao(self._numero_caixa))
            if numero not in self._memoria:
                self._memoria.append(numero)
                if len(self._memoria) > self._tamanho:
                    self._memoria.pop(0)
                break
        self._escrever_memoria()
        return numero

    def _file_exists(self, file):
        return os.path.join(PROJECT_ROOT, file)

    def _carregar_memoria(self):
        self._memoria[:] = []
        if os.path.exists(self._arquivo_json):
            with open(self._arquivo_json) as file:
                self._memoria = json.load(file)

        assert isinstance(self._memoria, list), \
            "Memoria de numeracao de sessao deve ser um objeto 'list'; "\
            f"obtido {self._memoria}"

    def _recuperar_dados_venda(self):
        self._ultimas_vendas = []
        if os.path.exists(self._ultimas_vendas_json):
            with open(self._ultimas_vendas_json) as file:
                try:
                    self._ultimas_vendas = json.load(file)
                except ValueError:
                    pass
                except AttributeError:
                    self._ultimas_vendas = []

    def arquivo_em_execucao(self, arquivo):
        for proc in psutil.process_iter(['open_files']):
            proc_files = proc.info['open_files']
            if proc_files:
                for x in proc_files:
                    if x.mode == 'w' and arquivo in x.path:
                        return True
        return False

    def _escrever_memoria(self):
        count = 3
        while count:
            if self.arquivo_em_execucao(self._arquivo_json):
                critical('erro de IO na escrita do arquivo json de SESSÕES')
                count -= 1
                continue

            with open(self._arquivo_json, 'w') as file:
                json.dump(self._memoria, file)

    def _escrever_dados(self, entrada, arquivo_json, tamanho, tipo=False):
        variavel = [self._ultimas_vendas if tipo == 'VENDA' else []]
        if os.path.exists(arquivo_json):
            with open(arquivo_json) as file_r:
                try:
                    lista_dict = json.load(file_r)
                    if len(lista_dict) == tamanho:
                        lista_dict.pop(0)
                    if tipo == 'ERROR':
                        variavel = lista_dict
                except ValueError:
                    pass
                except AttributeError:
                    variavel = []

        count = 3
        while count:
            if self.arquivo_em_execucao(arquivo_json):
                critical(f'erro de IO na escrita do arquivo json de {tipo}')
                count -= 1
                continue

            with open(arquivo_json, 'w') as file_w:
                if tipo == 'ERROR':
                    variavel.append(entrada)
                json.dump(variavel, file_w, indent=4)
                if tipo == 'ERROR':
                    del variavel
                break

    def _escrever_dados_venda(self, entrada):
        self._escrever_dados(entrada, self._ultimas_vendas_json, 20, 'VENDA')

    def _escrever_dados_erro(self, entrada):
        self._escrever_dados(entrada, self._ultimos_erros_json, 1000, 'ERROR')


def memoize(fn):
    # Implementação de memoize obtida de "Thumbtack Engineering"
    # https://www.thumbtack.com/engineering/a-primer-on-python-decorators/
    stored_results = {}

    def memoized(*args):
        try:
            # try to get the cached result
            return stored_results[args]
        except KeyError:
            # nothing was cached for those args. let's fix that.
            result = stored_results[args] = fn(*args)
            return result

    return memoized


@memoize
def instanciar_numerador_sessao(numero_caixa=1):
    return NumeradorSessaoPorCaixa(numero_caixa=numero_caixa)


@memoize
def instanciar_funcoes_sat(numero_caixa):
    funcoes_sat = FuncoesSAT(BibliotecaSAT(
        conf.caminho_biblioteca,
        convencao=conf.convencao_chamada),
        codigo_ativacao=conf.codigo_ativacao,
        numerador_sessao=instanciar_numerador_sessao(numero_caixa)
    )
    return funcoes_sat


@memoize
def instanciar_funcoes_vfpe(numero_caixa,
                            chave_acesso_validador,
                            caminho=conf.caminho_integrador):
    funcoes_vfpe = FuncoesVFPE(
        caminho,
        chave_acesso_validador=chave_acesso_validador,
        numerador_sessao=instanciar_numerador_sessao(numero_caixa)
    )
    return funcoes_vfpe


@memoize
def instanciar_cliente_local(numero_caixa):
    cliente = ClienteSATLocal(BibliotecaSAT(
        conf.caminho_biblioteca,
        convencao=conf.convencao_chamada),
        codigo_ativacao=conf.codigo_ativacao,
        numerador_sessao=instanciar_numerador_sessao(numero_caixa))
    return cliente


def hexdump(data):
    def _cut(sequence, size):
        for i in xrange(0, len(sequence), size):
            yield sequence[i:i+size]
    _hex = lambda seq: ['{0:02x}'.format(b) for b in seq]
    _chr = lambda seq: [chr(b) if 32 <= b <= 126 else '.' for b in seq]
    raw_data = map(ord, data)
    hexpanel = [' '.join(line) for line in _cut(_hex(raw_data), 16)]
    chrpanel = [''.join(line) for line in _cut(_chr(raw_data), 16)]
    hexpanel[-1] = hexpanel[-1] + (chr(32) * (47 - len(hexpanel[-1])))
    chrpanel[-1] = chrpanel[-1] + (chr(32) * (16 - len(chrpanel[-1])))
    return '\n'.join('%s  %s' % (h, c) for h, c in zip(hexpanel, chrpanel))


@memoize
def instanciar_impressora(tipo_conexao, modelo, string_conexao):

    # TODO importar a impressora correta do tipo correto
    if tipo_conexao == 'file':
        from escpos import FileConnection as Connection
    elif tipo_conexao == 'serial':
        from escpos.serial import SerialConnection as Connection
    elif tipo_conexao == 'rede':
        from escpos.network import NetworkConnection as Connection
    elif tipo_conexao == 'usb':
        raise NotImplementedError

    if modelo == 'elgini9':
        from escpos import FileConnection as Connection
        from escpos.impl.elgin import ElginI9 as Printer
        string_conexao = '/dev/usb/lp1'

    else:
        from escpos.impl.unknown import CB55C as Printer

    conn = Connection(string_conexao)
    impressora = Printer(conn)
    impressora.init()
    return impressora
