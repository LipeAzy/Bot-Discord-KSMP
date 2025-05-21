# Bot-Discord-KSMP

Este bot foi desenvolvido para o **servidor de Minecraft SMP Privado Kriz SMP**, um ambiente exclusivo para amigos, com foco em diversão, Roleplay (RP), eventos MDOS e integração entre os membros. O servidor não possui fins lucrativos e é criado e gerenciado pelo grupo de amigos **Lunatics**.

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
- **Bot de Música Completo:**  
  Toque músicas e playlists do YouTube, links do Spotify (busca no YouTube), controle de fila, loop (playlist/música), aleatório (shuffle), pular, parar, pausar, retomar e voltar música, tudo com mensagens em embed. O bot começa a tocar a primeira música da playlist imediatamente, sem esperar carregar toda a lista, garantindo resposta rápida mesmo em máquinas lentas.

---

## 📜 Comandos de Barra (Slash Commands)

| Comando                   | Permissão Necessária | Função                                                                 |
|---------------------------|---------------------|------------------------------------------------------------------------|
| `/setup_status`           | Administrador       | Configura a mensagem de status do servidor Minecraft no canal atual     |
| `/setup_registro`         | Administrador       | Envia embed com botão para iniciar o registro dos membros               |
| `/criar_vila <nome>`      | Administrador       | Cria uma vila (categoria, canais e cargo exclusivos)                    |
| `/deletar_vila <nome>`    | Administrador       | Deleta uma vila (remove categoria, canais e cargo)                      |
| `/tocar <link/nome>`      | Todos               | Toca música ou playlist do YouTube, Spotify (busca), ou pesquisa por nome|
| `/entrar_call` ou `/join` | Todos               | Faz o bot entrar na call do usuário                                    |
| `/loop <playlist/musica>` | Todos               | Ativa/desativa loop da playlist ou música atual                         |
| `/aleatorio`              | Todos               | Ativa/desativa modo aleatório (shuffle)                                 |
| `/pular`                  | Todos               | Pula para a próxima música da fila                                      |
| `/stop`                   | Todos               | Para a música e limpa a fila                                            |
| `/pause`                  | Todos               | Pausa a música atual                                                   |
| `/play`                   | Todos               | Retoma a música pausada                                                |
| `/voltar`                 | Todos               | Volta para a música anterior da fila                                    |

> **Observação:** Todos os comandos são feitos via barra (slash), não mais com prefixo `!`.

---

## 🎵 Funções de Música

- Toca músicas e playlists do YouTube (streaming, sem baixar arquivos)
- Aceita links do Spotify (faz busca automática no YouTube)
- Suporte a playlists (fila automática, tocando a primeira música imediatamente)
- Comandos de controle: loop (playlist/música), aleatório (shuffle), pular, parar, pausar, retomar, voltar música
- Mensagens do bot sempre em embed
- Sistema de fila inteligente, tratamento de erros e otimização para resposta rápida mesmo em hosts lentos

---

## 🚀 Instalação e Requisitos

1. **Dependências Python:**
   - Todas as dependências estão no `requirements.txt` (discord.py, python-dotenv, mcstatus, pytz, yt-dlp, requests)
   - Instale com:
     ```bash
     pip install -r requirements.txt
     ```
2. **FFmpeg:**
   - É obrigatório para o áudio funcionar.
   - Em hosts Linux (VPS, Pterodactyl, etc):
     ```bash
     sudo apt update && sudo apt install ffmpeg
     ```
   - Em hosts Windows: baixe e adicione o FFmpeg ao PATH.
   - Em hosts Pterodactyl: escolha um template de bot Python que já inclua FFmpeg (a maioria dos templates de música já vem pronto).
3. **yt-dlp:**
   - Já incluso no requirements.txt. Se der erro de extração, atualize com:
     ```bash
     pip install -U yt-dlp
     ```
4. **Variáveis de ambiente:**
   - Configure o token do Discord e outras variáveis pelo painel do host (Environment/Startup).
5. **Comando de inicialização:**
   - Normalmente:
     ```bash
     python3 app.py
     ```
     ou
     ```bash
     python app.py
     ```

---

## 📝 Observações

- O bot utiliza variáveis de ambiente para configuração de tokens e IDs.
- O sistema de registro é feito via Modal/Embed com botão interativo.
- O bot é exclusivo para uso privado, sem fins lucrativos, mantido pelo grupo **Lunatics**.
- Caso o YouTube mude a proteção e o yt-dlp apresente erro, aguarde atualização do yt-dlp.

---

> Este projeto é mantido por amigos para amigos.  
> Qualquer dúvida, procure um membro do grupo Lunatics!
