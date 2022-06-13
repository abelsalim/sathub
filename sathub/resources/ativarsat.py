
import logging
from satcfe import BibliotecaSAT
from satcfe import ClienteSATLocal
from satcfe.base import FuncoesSAT

from flask_restful import Resource

from ..comum.util import hexdump
from ..comum.util import instanciar_funcoes_sat
from ..custom import numero_caixa, request_parser


logger = logging.getLogger('sathub.resource')

parser = request_parser()

parser.add_argument('codigo_ativacao',
        type=str,
        required=True,
        help=u'Código de ativação')

parser.add_argument('tipo_certificado',
        type=int,
        required=True,
        help=u'Tipo de Certificado: AC-SAT ou ICP-BRASIL')

parser.add_argument('cnpj_contribuinte',
        type=str,
        required=True,
        help=u'CNPJ do contribuinte')

parser.add_argument('uf',
        type=int,
        required=True,
        help=u'Código do estado')

class AtivarSat(Resource):

    def post(self):
        args = parser.parse_args()
        numero_caixa = 1
        codigo_ativacao = args['codigo_ativacao']
        tipo_certificado = args['tipo_certificado']
        cnpj_contribuinte = args['cnpj_contribuinte']
        uf = args['uf']

        def instanciar_funcoes_sat(numero_caixa):
                funcoes_sat = FuncoesSAT(BibliotecaSAT(conf.caminho_biblioteca,
                convencao=conf.convencao_chamada),
                codigo_ativacao=conf.codigo_ativacao,
                numerador_sessao=instanciar_numerador_sessao(numero_caixa))
                return funcoes_sat

        fsat = instanciar_funcoes_sat(numero_caixa)       
        retorno = fsat.ativar_sat(tipo_certificado,codigo_ativacao,cnpj_contribuinte,uf)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Retorno "Ativar MFE" ('
                    'numero_caixa=%s, '
                    'codigo_ativacao="%s", '
                    'tipo_certificado="%s", '
                    'cnpj_contribuinte="%s",'
                    'uf="%s") \n%s',
                            numero_caixa,
                            codigo_ativacao,
                            tipo_certificado,
                            cnpj_contribuinte,
                            uf,
                            hexdump(retorno))

        return dict(funcao='AtivarSat', retorno=retorno)
