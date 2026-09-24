<!-- FONTE:
  - "Escopo", "O que é / plano", "Cobrança", "Domínio", "Adesão", "Cancelamento",
    "Dados cadastrais / renomear e-mail", "Acesso / senha", "Duas etapas (2FA)",
    "Envio de e-mails", "Edição do site", "Suporte técnico / Outlook", "Limitações",
    "Contato" => derivados dos zips (conversas-oncorretor.zip + MENSAGENS-IA.zip).
  - Fatos-âncora (forma de cobrança = desconto na conta comissão da SUSEP principal;
    ausência de cartão/PIX; termos do domínio) => âncoras do contrato, confirmados nos zips.
  - Regras de comportamento do atendimento (não oferecer atendente humano, não pedir
    dados sensíveis) => ANSWER_PROMPT_SYSTEM de prompt.py (aplicadas pelo system prompt,
    reproduzidas aqui só como referência de escopo).
  NOTA: nada nesta KB foi inventado. Todo fato tem origem em um trecho literal das fontes.
  Onde as fontes são silenciosas (ex.: cartão, PIX, app próprio), a KB permanece silenciosa
  de propósito — perguntas sobre esses itens têm gabarito MODO C.
-->

# Base de conhecimento — OnCorretor

## O que é o OnCorretor
- O OnCorretor é uma plataforma digital exclusiva para corretores parceiros da Porto Seguro.
- O plano do OnCorretor contempla 1 website mais 10 contas de e-mail personalizadas com 5GB de armazenamento para cada conta, além de suporte técnico.
- Exemplos de sites feitos com o OnCorretor: roseoliveiracorretora.com.br, venturelliseguros.com.br, schiavibr.com, hga.com.br e jawscor.com.br.

## Cobrança e pagamento da mensalidade
- O valor da mensalidade do OnCorretor é de R$ 52,50.
- A mensalidade é paga por desconto direto na conta comissão da SUSEP principal (comissão Porto Seguro).
- Não é possível pagar a mensalidade por nenhuma outra forma além do desconto direto da SUSEP Porto.
- Em caso de inadimplência, o acerto da mensalidade é tratado com a Porto por meio do gestor comercial.
- Não é possível desmembrar a mensalidade da comissão nem pagá-la à parte.

## Domínio
- No OnCorretor é um domínio por adesão; não é possível atrelar mais de um domínio à mesma adesão.
- Se o corretor não tiver um domínio, o OnCorretor faz o registro e o valor é descontado da SUSEP Porto; se já tiver um domínio, ele pode ser utilizado.
- A renovação do domínio pode ser feita por outras formas de pagamento diretamente na registro.br.
- Quando um domínio fica congelado por pendências em aberto no período de renovação, o OnCorretor pode enviar QR Code ou boleto para a renovação, válida por até 1 ano.

## Adesão / contratação
- A adesão ao OnCorretor pode ser feita no site https://oncorretor.com.br/planos.html, selecionando o plano e clicando em "Quero Contratar".
- As edições e melhorias do site dentro dos modelos disponíveis estão inclusas no valor da mensalidade.

## Cancelamento
- Para cancelar, o corretor deve enviar um e-mail para atendimento@oncorretor.com.br informando: Susep, Domínio, CPF/CNPJ de cadastro e Motivo do cancelamento.

## Dados cadastrais e renomear conta de e-mail
- A mudança do e-mail cadastral deve ser solicitada por e-mail para atendimento@oncorretor.com.br, informando SUSEP, Domínio, CNPJ/CPF de cadastro e o e-mail novo.
- Para renomear uma conta de e-mail, é necessário enviar solicitação por e-mail para atendimento@oncorretor.com.br informando o usuário atual, o novo nome, a susep Porto, o CNPJ de cadastro e o domínio.
- Ao renomear uma conta de e-mail, a senha continua sendo a mesma.
- Ao renomear a conta, o endereço antigo deixa de existir e os e-mails enviados a ele não serão mais recebidos.

## Acesso, webmail e senha
- O acesso ao webmail é feito pelo endereço webmail seguido do domínio do corretor (ex.: webmail.seudominio.com.br).
- O acesso ao painel gerenciador de e-mails é feito pelo endereço painel seguido do domínio, com o usuário gerenciador@seudominio.
- Para trocar a senha, basta clicar em "Esqueceu a senha"; um link de redefinição é enviado ao e-mail secundário cadastrado.
- O OnCorretor não tem acesso à senha atual do corretor; só é possível enviar o link para redefinição de senha.
- A nova senha precisa ter no mínimo 8 caracteres; possuir ao menos 3 tipos de caracteres diferentes (maiúsculo, minúsculo, numerais e/ou caracteres especiais); não possuir informações relacionadas ao seu e-mail; não possuir números sequenciais; não possuir letras sequenciais do início do alfabeto; não possuir anos próximos ao corrente junto com informações pessoais.

## Autenticação em duas etapas (2FA)
- A autenticação em duas etapas usa o código gerado em aplicativos como Google Authenticator, Microsoft Authenticator, Authy ou semelhante.
- O código da autenticação em duas etapas é atualizado a cada 30 segundos.

## Envio de e-mails e bloqueios
- Há um limite de envio de e-mails por minuto/hora.
- Quando uma conta é bloqueada por suspeita de envio de spam, a orientação é trocar a senha e passar o antivírus; se o bloqueio persistir, o OnCorretor solicita o desbloqueio ao provedor.
- A configuração das contas de e-mail no celular Android segue o manual em https://ajuda.oncorretor.com.br/index.php/Android.

## Edição do site
- Após a contratação, as edições do site podem ser solicitadas pelo WhatsApp do OnCorretor.
- No site do corretor é possível adicionar logos de outras seguradoras parceiras.
- As dimensões mínimas das imagens de fundo do site são: imagem de fundo 1200px x 470px; imagem de fundo média 720px x 480px; imagem de fundo pequena 540px x 550px (cada uma para um dispositivo).

## Suporte técnico e Outlook
- O OnCorretor auxilia apenas na configuração de conta no Outlook; o suporte de plataforma é apenas ao webmail.
- Erros nas operações realizadas pelo próprio Outlook não são de responsabilidade do OnCorretor.
- Sites que não foram feitos pelo OnCorretor não têm suporte do OnCorretor; nesses casos é necessário verificar com o suporte do provedor.

## Limitações (o que o OnCorretor não faz)
- O OnCorretor trabalha apenas com contas de e-mail e com o site; não trabalha com redes sociais.
- O site não vem com material de marketing da Porto e o OnCorretor não tem acesso nem auxilia na ferramenta PromoDigital da Porto.
- Não é possível integrar API de compra no site; o visitante consegue apenas cotar, não comprar diretamente, e não há página de "obrigado" que contabilize a venda.
- Assuntos como capital de giro e outros temas comerciais da corretora devem ser verificados junto à Porto Seguro; não são tratados pelo OnCorretor.

## Canais de contato
- Site: www.oncorretor.com.br
- Telefone: 0800 771 5505
- WhatsApp: (011) 99714-9631
- E-mail: atendimento@oncorretor.com.br

## Comportamento do atendimento (referência de escopo — aplicado pelo sistema)
- O atendimento nunca oferece transferência para atendente humano.
- O atendimento nunca solicita dados sensíveis (CPF, RG, SUSEP, senhas etc.).
