# -*- coding: utf-8 -*-
#
# sathub/views.py
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
import platform

import flask

from flask import abort
from flask import flash
from flask import redirect
from flask import request
from flask import render_template
from flask import url_for


from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import current_user
from flask_login import login_user
from flask_login import login_required
from flask_login import logout_user
from satcfe import BibliotecaSAT
from satcfe import ClienteSATLocal
from satcfe.base import FuncoesSAT
from .comum.config import conf

from . import __version__ as sathub_version
from . import app
from . import executor
from . import conf as sathubconf
from .forms import AssociarAssinaturaForm, AtivarSatForm, EmptyForm
from .forms import LoginForm, ConfigurarInterfaceDeRedeFrom
from .comum.util import instanciar_funcoes_sat
from .comum.util import instanciar_numerador_sessao


FUNCOES_ABERTAS = {
        'consultarsat': dict(
                titulo=u'Consultar SAT',
                descricao=u'Testa a comunicação com o equipamento SAT',
                funcao='ConsultarSAT'),

        'consultarstatusoperacional': dict(
                titulo=u'Status Operacional',
                descricao=u'Consulta o status operacional do equipamento SAT',
                funcao='ConsultarStatusOperacional'),
    }


FUNCOES_RESTRITAS = {
        'extrairlogs': dict(
                titulo=u'Extrair Logs',
                descricao=u'Obtém os registros de log do equipamento SAT.',
                funcao='ExtrairLogs'),
        'atualizarsoftwaresat': dict(
                titulo=u'Atualizar Software',
                descricao=u'Atualização de software base.',
                funcao='AtualizarSoftwareSAT'),
        'bloquearsat': dict(
                titulo=u'Bloquear SAT',
                descricao=u'Bloqueio de equipamento.',
                funcao='BloquearSAT'),
        'desbloquearsat': dict(
                titulo=u'Desloquear SAT',
                descricao=u'Desbloqueio de equipamento.',
                funcao='DesbloquearSAT'),
    }


class User(UserMixin):

    @staticmethod
    def get(user_id):
        if sathubconf.usuario != user_id:
            return None
        user = User()
        user.id = sathubconf.usuario
        return user


    @staticmethod
    def authenticate(username, password):
        if sathubconf.usuario == username:
            if sathubconf.senha == password:
                user = User()
                user.id = sathubconf.usuario
                return user
        return None


login_manager = LoginManager()
login_manager.init_app(app)


@app.context_processor
def injetar_extrainfo():
    return dict(
            sathubconf=sathubconf,
            flask_version=flask.__version__,
            python_version=platform.python_version(),
            platform_uname=' | '.join(platform.uname()),
            produto=dict(nome='SATHub', versao=sathub_version))


@app.errorhandler(404)
def pagina_nao_encontrada(error):
    return render_template('404.html'), 404


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    return render_template('401.html'), 401


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/associarassinatura',methods=['GET','POST'])
def associar_assinatura():
    form = AssociarAssinaturaForm(request.form)
    if request.method == 'POST' and form.validate():
        # pcCodAtivacao = form.pcCodAtivacao.data
        sequencia_cnpj = form.cnpjSoftwareHouse.data + form.cnpjContribuinte.data
        assinatura_ac = form.lpcAssinaturaCnpjs.data
        numero_caixa = 1
        fsat = instanciar_funcoes_sat(numero_caixa)
        retorno = fsat.associar_assinatura(sequencia_cnpj, assinatura_ac)
        flash(f'{retorno}', 'info')
        return redirect(url_for('index'))

    return render_template('associarassinatura.html',form=form)

@app.route('/ativarsat',methods=['GET','POST'])
def ativar_sat():
    form = AtivarSatForm(request.form)
    if request.method == 'POST' and form.validate():
        tipoCertificado = int(form.tipoCertificado.data)
        codigo_ativacao = form.codAtivacao.data
        cnpjContribuinte = form.cnpjContribuinte.data
        uf = int(form.uf.data)
        numero_caixa = 1
        # def instanciar_funcoes_sat():
        #         breakpoint()
        #         funcoes_sat = FuncoesSAT(BibliotecaSAT(conf.caminho_biblioteca,
        #         convencao=conf.convencao_chamada))
        #         return funcoes_sat
        fsat = instanciar_funcoes_sat(numero_caixa)
        # numero_sessao = instanciar_numerador_sessao(numero_caixa)
        retorno = fsat.ativar_sat(tipo_certificado=tipoCertificado,cnpj=cnpjContribuinte,codigo_uf=uf)
        flash(f'{retorno}', 'info')
        return redirect(url_for('index'))

    return render_template('associarassinatura.html',form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            login_user(user)
            flash('Login realizado com sucesso.', 'success')
            return redirect(request.args.get('next') or url_for('index'))
        else:
            form.username.errors.append('athentication error')

    return render_template('login.html', form=form)

@app.route('/configurarinterfacederede',methods=['GET','POST'])
def configurar_interface_de_rede():
    form = ConfigurarInterfaceDeRedeFrom(request.form)
    if request.method == 'POST' and form.validate():
        lanIP =  f'<lanIP>{form.lanIP.data}</lanIP>' if form.lanIP.data != '000.000.000.000' else ''
        lanMask = f'<lanMask>{form.lanMask.data}</lanMask>' if form.lanIP.data != '000.000.000.000' else ''
        lanGW = f'<lanGW>{form.lanGW.data}</lanGW>' if form.lanIP.data != '000.000.000.000' else ''
        lanDNS1 = f'<lanDNS1>{form.lanDNS1.data}</lanDNS1>' if form.lanIP.data != '000.000.000.000' else ''
        lanDNS2 = f'<lanDNS2>{form.lanDNS2.data}</lanDNS2>' if form.lanIP.data != '000.000.000.000' else ''
        dados = f"<config>\
                    <tipoInter>{form.tipoInter.data}</tipoInter>\
                    <tipoLan>{form.tipoLan.data}</tipoLan>\
                    {lanIP}\
                    {lanMask}\
                    {lanGW}\
                    {lanDNS1}\
                    {lanDNS2}\
                    <proxy>0</proxy>\
                </config>"
        numero_caixa = 1
        configuracao = dados

        fsat = instanciar_funcoes_sat(numero_caixa)
        retorno = fsat.configurar_interface_de_rede(configuracao)
        flash(f'{retorno}', 'info')
        return redirect(url_for('index'))
    return render_template('configurarinterfacederede.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'Você acabou de fazer o logout.', 'info')
    return redirect(url_for('index'))


@app.route('/exec/<funcaosat>', methods=['GET', 'POST'])
def executar_funcao_sat(funcaosat):

    resultado = None

    if funcaosat in FUNCOES_RESTRITAS:
        if not current_user.is_authenticated:
            return app.login_manager.unauthorized()
        funcao = FUNCOES_RESTRITAS.get(funcaosat)
    else:
        funcao = FUNCOES_ABERTAS.get(funcaosat)
        if not funcao:
            abort(404)

    form = funcao.get('form_class', EmptyForm)(request.form)
    if request.method == 'POST' and form.validate():
        resultado = getattr(executor, funcao.get('funcao').lower())(form)

    return render_template('funcao.html',
            funcao=funcao,
            form=form,
            resultado=resultado)
