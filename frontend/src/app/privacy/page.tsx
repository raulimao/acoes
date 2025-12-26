'use client';

import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function PrivacyPage() {
    return (
        <div className="min-h-screen bg-[#0B0C15] text-gray-300 font-sans selection:bg-purple-500/30">
            <div className="max-w-4xl mx-auto px-6 py-12 md:py-20">

                <Link href="/" className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors mb-8">
                    <ArrowLeft className="w-4 h-4" /> Voltar para Home
                </Link>

                <h1 className="text-3xl md:text-5xl font-bold text-white mb-8">Política de Privacidade</h1>
                <p className="text-gray-500 mb-12">Última atualização: {new Date().toLocaleDateString('pt-BR')}</p>

                <div className="space-y-8 text-lg leading-relaxed">
                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">1. Informações que Coletamos</h2>
                        <p>
                            Coletamos informações que você nos fornece diretamente, como quando cria uma conta, atualiza seu perfil ou usa nossos recursos premium.
                        </p>
                        <ul className="list-disc pl-6 mt-4 space-y-2 text-gray-400">
                            <li><strong>Informações de Conta:</strong> Nome, endereço de e-mail e senha (criptografada).</li>
                            <li><strong>Informações de Pagamento:</strong> Processadas de forma segura pelo nosso parceiro Stripe. Nós <strong>não</strong> armazenamos números completos de cartão de crédito.</li>
                            <li><strong>Dados de Uso:</strong> Informações sobre como você interage com nossos serviços, como páginas visitadas e ações analisadas.</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">2. Como Usamos Suas Informações</h2>
                        <p>
                            Usamos as informações coletadas para:
                        </p>
                        <ul className="list-disc pl-6 mt-4 space-y-2 text-gray-400">
                            <li>Fornecer, manter e melhorar nossos serviços;</li>
                            <li>Processar transações e enviar avisos relacionados;</li>
                            <li>Enviar atualizações técnicas, alertas de segurança e suporte;</li>
                            <li>Responder aos seus comentários e perguntas.</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">3. Compartilhamento de Informações</h2>
                        <p>
                            Não vendemos seus dados pessoais. Podemos compartilhar informações nas seguintes circunstâncias limitadas:
                        </p>
                        <ul className="list-disc pl-6 mt-4 space-y-2 text-gray-400">
                            <li><strong>Provedores de Serviço:</strong> Com fornecedores que nos ajudam a operar o negócio (ex: Stripe para pagamentos, Supabase para banco de dados).</li>
                            <li><strong>Obrigação Legal:</strong> Se exigido por lei ou em resposta a processos legais válidos.</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">4. Seus Direitos (LGPD)</h2>
                        <p>
                            Como usuário, você tem direito a solicitar:
                        </p>
                        <ul className="list-disc pl-6 mt-4 space-y-2 text-gray-400">
                            <li>Acesso aos seus dados pessoais;</li>
                            <li>Correção de dados incompletos ou inexatos;</li>
                            <li>Exclusão de seus dados pessoais (Direito ao Esquecimento);</li>
                            <li>Revogação do consentimento.</li>
                        </ul>
                        <p className="mt-4">
                            Para exercer esses direitos, entre em contato conosco através do e-mail de suporte.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-bold text-white mb-4">5. Segurança</h2>
                        <p>
                            Adotamos medidas de segurança adequadas para proteger contra acesso não autorizado, alteração, divulgação ou destruição de suas informações pessoais.
                        </p>
                    </section>

                </div>

                <div className="mt-20 pt-8 border-t border-white/10 text-center text-gray-500 text-sm">
                    <p>Dúvidas? Entre em contato: suporte@topacoes.com</p>
                </div>
            </div>
        </div>
    );
}
