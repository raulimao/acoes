'use client';

import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function TermsPage() {
    return (
        <div className="min-h-screen bg-[#0B0C15] text-gray-300 font-sans selection:bg-purple-500/30">
            <div className="max-w-4xl mx-auto px-6 py-12 md:py-20">

                <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors mb-8">
                    <ArrowLeft className="w-4 h-4" /> Voltar para Home
                </Link>

                <h1 className="text-3xl md:text-5xl font-bold text-white mb-8">Termos de Uso</h1>
                <p className="text-gray-500 mb-12">Última atualização: {new Date().toLocaleDateString('pt-BR')}</p>

                <div className="space-y-8 text-lg leading-relaxed">
                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">1. Aceitação dos Termos</h2>
                        <p>
                            Ao acessar e usar a plataforma NorteAcoes ("Serviço"), você concorda em cumprir estes Termos de Uso e todas as leis aplicáveis. Se você não concordar com algum destes termos, está proibido de usar ou acessar este site.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">2. Licença de Uso</h2>
                        <p>
                            É concedida permissão para baixar temporariamente uma cópia dos materiais (informações ou software) no site NorteAcoes, apenas para visualização transitória pessoal e não comercial. Esta é a concessão de uma licença, não uma transferência de título, e sob esta licença você não pode:
                        </p>
                        <ul className="list-disc pl-6 mt-4 space-y-2 text-gray-400">
                            <li>Modificar ou copiar os materiais;</li>
                            <li>Usar os materiais para qualquer finalidade comercial ou para exibição pública;</li>
                            <li>Tentar descompilar ou fazer engenharia reversa de qualquer software contido no site;</li>
                            <li>Remover quaisquer direitos autorais ou outras notações de propriedade dos materiais.</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">3. Isenção de Responsabilidade (Disclaimer)</h2>
                        <p>
                            Os materiais no site da NorteAcoes são fornecidos "como estão". NorteAcoes não oferece garantias, expressas ou implícitas, e, por este meio, isenta e nega todas as outras garantias, incluindo, sem limitação, garantias implícitas ou condições de comercialização, adequação a um fim específico ou não violação de propriedade intelectual.
                        </p>
                        <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg mt-4">
                            <p className="text-yellow-200 text-sm">
                                <strong>Importante:</strong> Nenhuma informação contida neste site constitui recomendação de investimento. A NorteAcoes é uma ferramenta de análise e não se responsabiliza por perdas financeiras decorrentes do uso das informações aqui contidas.
                            </p>
                        </div>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">4. Limitações</h2>
                        <p>
                            Em nenhum caso a NorteAcoes ou seus fornecedores serão responsáveis por quaisquer danos (incluindo, sem limitação, danos por perda de dados ou lucro ou devido a interrupção dos negócios) decorrentes do uso ou da incapacidade de usar os materiais em NorteAcoes.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">5. Planos e Pagamentos</h2>
                        <p>
                            O serviço oferece planos gratuitos e pagos (Premium). Ao assinar um plano pago, você concorda em pagar as taxas associadas. As assinaturas são renovadas automaticamente, a menos que sejam canceladas com pelo menos 24 horas de antecedência ao final do período atual.
                        </p>
                        <p className="mt-4">
                            Você pode gerenciar ou cancelar sua assinatura a qualquer momento através das configurações da sua conta.
                        </p>
                    </section>

                </div>

                <div className="mt-20 pt-8 border-t border-white/10 text-center text-gray-500 text-sm">
                    <p>Dúvidas? Entre em contato: suporte@norteacoes.com</p>
                </div>
            </div>
        </div>
    );
}
