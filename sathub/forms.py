# -*- coding: utf-8 -*-
#
# sathub/forms.py
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

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import validators
from wtforms.fields import SelectField


LOCALES = ['pt_BR', 'pt']


class LoginForm(FlaskForm):

    username = StringField(u'Nome de Usuário',
                           validators=[
                               validators.DataRequired(),
                               validators.length(min=2, max=20), ])

    password = PasswordField('Senha',
                             validators=[
                                 validators.DataRequired(),
                                 validators.length(min=6, max=20), ])

    class Meta:
        locales = LOCALES


class EmptyForm(FlaskForm):
    class Meta:
        locales = LOCALES


class ConfigurarInterfaceDeRedeFrom(FlaskForm):

    tipoInter = SelectField(
        choices=(
            ('ETHE', 'ETHE'),
            # ('WIFI', 'WIFI')
        ),
        label='Tipo de interface',
        render_kw={'class': 'form-control', 'style': 'font-size:150%'}
    )
    # SSID = StringField('Nome da rede (SSID)')
    # seg = SelectField(
    #     choices=(
    #         ('NONE', 'NONE'),
    #         ('WEP', 'WEP'),
    #         ('WAP', 'WAP'),
    #         ('WPA-PERSONAL', 'WPA-PERSONAL'),
    #         ('WPA-ENTERPRISE', 'WPA-ENTERPRISE'),
    #     ),
    #     label='Seguranaça'
    # )
    # codigo = PasswordField(
    #     'Frase ou chave de acesso à rede sem fio.',
    #     validators=[
    #         validators.DataRequired(),
    #         validators.length(min=6, max=64), ]
    # )

    tipoLan = SelectField(
        choices=(
            ('IPFIX', 'IP FIXO'),
            ('DHCP', 'DHCP (Automático)')
        ),
        label='Tipo de conexão',
        render_kw={'class': 'form-control', 'style': 'font-size:150%'}
    )
    lanIP = StringField(
        'Endereço IP',
        validators=[
            validators.DataRequired(),
            validators.length(max=15)
        ],				
        render_kw={'class': 'form-control','value':'000.000.000.000', 'style': 'font-size:150%'}
    )
    lanMask = StringField('Máscara',	validators=[
        validators.DataRequired(),
        validators.length(max=15)
    ],
        render_kw={'class': 'form-control','value':'000.000.000.000', 'style': 'font-size:150%'}
    )
    lanGW = StringField('Gateway',	validators=[
        validators.DataRequired(),
        validators.length(max=15)
    ],
        render_kw={'class': 'form-control','value':'000.000.000.000','style': 'font-size:150%'})
    lanDNS1 = StringField('DNS1',	validators=[
        validators.DataRequired(),
        validators.length(max=15)
    ], render_kw={'class': 'form-control','value':'000.000.000.000','style': 'font-size:150%'})
    lanDNS2 = StringField('DNS2',	validators=[
        validators.DataRequired(),
        validators.length(max=15)
    ], render_kw={'class': 'form-control','value':'000.000.000.000','style': 'font-size:150%'})
