# Bot-Discord-Emolok

Este bot foi desenvolvido para o **servidor de Minecraft SMP Privado Emolok**, um ambiente exclusivo para amigos, com foco em diversão, Roleplay (RP), eventos MDOS e integração entre os membros. O servidor não possui fins lucrativos e é criado e gerenciado pelo grupo de amigos **Lunatics**.

---

## ⚙️ Funções do Bot

- **Status do Servidor Minecraft:**  
  Atualiza automaticamente o status do servidor Minecraft em um canal do Discord, mostrando jogadores online, TPS, versão, latência e mais.
- **Sistema de Registro:**  
  Usuários podem se registrar via botão e formulário, recebendo cargos automaticamente e registrando informações no canal de registros.
- **Criação e Gerenciamento de Vilas:**  
  Comandos para criar e deletar vilas, gerando categorias, canais e cargos exclusivos para cada vila, com permissões automáticas.
- **Logs de Ações:**  
  Toda criação e exclusão de vila é registrada em um canal de logs.
- **Gerenciamento de Cargos:**  
  Automatiza a troca de cargos ao registrar e ao entrar no servidor.

---

## 📜 Comandos Disponíveis

| Comando                | Permissão Necessária | Função                                                                 |
|------------------------|---------------------|------------------------------------------------------------------------|
| `!setup_status`        | Administrador       | Configura a mensagem de status do servidor Minecraft no canal atual     |
| `!setup_registro`      | Administrador       | Envia embed com botão para iniciar o registro dos membros               |
| `!criar_vila <nome>`   | Produção/Admin      | Cria uma vila (categoria, canais e cargo exclusivos)                    |
| `!deletar_vila <nome>` | Produção/Admin      | Deleta uma vila (remove categoria, canais e cargo)                      |

---

## 📝 Observações

- O bot utiliza variáveis de ambiente para configuração de tokens e IDs.
- O sistema de registro é feito via Modal/Embed com botão interativo.
- O bot é exclusivo para uso privado, sem fins lucrativos, mantido pelo grupo **Lunatics**.

---

> Este projeto é mantido por amigos para amigos.  
> Qualquer dúvida, procure um membro do grupo Lunatics!