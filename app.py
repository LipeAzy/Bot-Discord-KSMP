import discord
from discord.ext import commands
from discord import ui, app_commands
import os
from dotenv import load_dotenv
from datetime import datetime
from discord.ext import commands, tasks
from datetime import datetime, timezone
from mcstatus import JavaServer
import json
import base64
from io import BytesIO
import aiohttp
import random
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from comandos import setup_commands

load_dotenv()

# Configurações Globais
CURRENT_USER = "LipeAzy"
CURRENT_TIME = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree  # Para facilitar o uso dos comandos de barra

setup_commands(tree)

# Configurações do Servidor
STATUS_CONFIG_FILE = "status_config.json"

# Status rotativo para o bot (agora usando status customizado)
BOT_STATUS_MESSAGES = [
    lambda data: f"👥 {data['players_online']} jogadores online",
    lambda data: f"🎮 {data.get('server_ip', 'IP não configurado')}:{data.get('server_port', 'Porta não configurada')}"
]

status_config = {
    "channel_id": None,
    "message_id": None,
    "server_ip": None,
    "server_port": None,
    "server_online_since": None  # Novo campo para guardar o timestamp do uptime
}

# Adicionar após as outras constantes de ID
CANAL_STATUS_ADICIONAL = 1370669650559373322
PRODUCAO_ROLE_ID = 1371248255954063392
CANAL_LOG_VILAS = 1370693091102556262  # Canal para logs de vilas

def load_status_config():
    global status_config
    try:
        if os.path.exists(STATUS_CONFIG_FILE):
            with open(STATUS_CONFIG_FILE, 'r') as f:
                status_config = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar configuração: {e}")

def save_status_config():
    try:
        with open(STATUS_CONFIG_FILE, 'w') as f:
            json.dump(status_config, f)
    except Exception as e:
        print(f"Erro ao salvar configuração: {e}")

def get_server_ip_port():
    ip = status_config.get("server_ip")
    port = status_config.get("server_port")
    if not ip or not port:
        raise ValueError("Servidor Minecraft não configurado. Use /configurar_servidor.")
    return ip, int(port)

async def get_server_status():
    """Função para obter o status do servidor Minecraft"""
    try:
        ip, port = get_server_ip_port()
        server = JavaServer(ip, port)
        status = await server.async_status()
        
        # Tentar obter TPS via query
        try:
            query = await server.async_query()
            tps = "20.0"
        except:
            tps = "20.0"  # Valor padrão se não conseguir consultar
        
        return {
            'online': True,
            'players_online': status.players.online,
            'players_max': status.players.max,
            'version': status.version.name,
            'latency': round(status.latency, 1),
            'tps': tps,
            'players_list': get_players_list(status),
            'server_ip': ip,
            'server_port': port
        }
    except Exception as e:
        print(f"Erro ao obter status do servidor: {e}")
        return {
            'online': False,
            'players_online': 0,
            'players_max': 0,
            'version': 'Desconhecida',
            'latency': 0,
            'tps': 'N/A',
            'players_list': [],
            'server_ip': status_config.get('server_ip', 'Não configurado'),
            'server_port': status_config.get('server_port', 'Não configurado')
        }

def get_players_list(status):
    """Obtém lista de jogadores online"""
    try:
        if hasattr(status.players, 'sample') and status.players.sample:
            return [player.name for player in status.players.sample]
        return []
    except:
        return []

def create_status_embed(status):
    """Cria a embed com as informações do servidor no estilo customizado, com uptime real"""
    current_time = datetime.now(timezone.utc)
    ip = status.get('server_ip', 'Não configurado')
    version = status.get('version', 'Desconhecida')
    jogadores_online = status.get('players_online', 0)
    aberto = status.get('online', False)
    # Cálculo de tempo aberto real
    aberto_ha = "Indisponível"
    if aberto and status_config.get('server_online_since'):
        try:
            dt_inicio = datetime.fromisoformat(status_config['server_online_since'])
            delta = current_time - dt_inicio
            horas, resto = divmod(int(delta.total_seconds()), 3600)
            minutos, segundos = divmod(resto, 60)
            aberto_ha = f"há {horas}h {minutos}m {segundos}s"
        except Exception:
            aberto_ha = "há alguns minutos"
    if aberto:
        footer_text = f"Aberto {aberto_ha} • Hoje às {current_time.strftime('%H:%M')}"
        desc = f"<a:terra_animada:1374676051833393213> **Junte-se ao nossos {jogadores_online} jogadores!**"
        color = 0xf96d18
        thumb_url = "https://message.style/cdn/images/606911dd55630ab368fb8cb9015d832e924726d4815543670b6a84489bb396b8.png"
    else:
        footer_text = f"Servidor indisponível • Hoje às {current_time.strftime('%H:%M')}"
        desc = "<a:terra_animada:1374676051833393213> **Servidor offline ou indisponível!**"
        color = 0x808080
        thumb_url = "https://message.style/cdn/images/606911dd55630ab368fb8cb9015d832e924726d4815543670b6a84489bb396b8.png"
    embed = discord.Embed(
        title="<:letra_K:1374675650517925889> |  KRIZ SMP",
        description=desc,
        color=color,
    )
    embed.set_footer(text=footer_text)
    embed.set_thumbnail(url=thumb_url)
    embed.add_field(
        name="IP:",
        value=f"```{ip}```\nVersão: **{version}**\n",
        inline=False
    )
    return embed

@tasks.loop(seconds=20)
async def update_server_status():
    """Atualiza o status do servidor a cada 20 segundos"""
    try:
        status = await get_server_status()
        # Se o servidor está online e não havia timestamp, salva o início do uptime
        if status['online']:
            if not status_config.get('server_online_since'):
                status_config['server_online_since'] = datetime.now(timezone.utc).isoformat()
                save_status_config()
        else:
            # Se ficou offline, limpa o timestamp
            if status_config.get('server_online_since'):
                status_config['server_online_since'] = None
                save_status_config()
        embed = create_status_embed(status)

        # Atualizar mensagem configurada pelo setup_status
        if status_config["channel_id"] and status_config["message_id"]:
            try:
                channel = bot.get_channel(status_config["channel_id"])
                if channel:
                    try:
                        message = await channel.fetch_message(status_config["message_id"])
                        await message.edit(embed=embed)
                    except discord.NotFound:
                        # Mensagem não encontrada, envia nova e atualiza o config
                        message = await channel.send(embed=embed)
                        status_config["message_id"] = message.id
                        save_status_config()
            except Exception as e:
                print(f"Erro ao atualizar status no canal principal: {e}")

        else:
            # Se não há configuração, envia nova mensagem e salva
            channel = bot.get_channel(CANAL_STATUS_ADICIONAL)
            if channel:
                message = await channel.send(embed=embed)
                status_config["channel_id"] = channel.id
                status_config["message_id"] = message.id
                save_status_config()

        # Atualizar canal adicional (opcional, pode remover se não quiser duplicidade)
        try:
            canal_adicional = bot.get_channel(CANAL_STATUS_ADICIONAL)
            if canal_adicional:
                # Buscar última mensagem do canal
                async for message in canal_adicional.history(limit=1):
                    try:
                        await message.edit(embed=embed)
                        break
                    except:
                        await canal_adicional.send(embed=embed)
                        break
                else:
                    # Se não houver mensagens, enviar uma nova
                    await canal_adicional.send(embed=embed)
        except Exception as e:
            print(f"Erro ao atualizar status no canal adicional: {e}")

    except Exception as e:
        print(f"Erro ao atualizar status: {e}")

@tasks.loop(seconds=20)
async def update_bot_status():
    """Atualiza o status do bot a cada 20 segundos"""
    try:
        status = await get_server_status()
        if status['online']:
            status_message = random.choice(BOT_STATUS_MESSAGES)(status)
            await bot.change_presence(
                activity=discord.CustomActivity(name=status_message),
                status=discord.Status.online
            )
        else:
            await bot.change_presence(
                activity=discord.CustomActivity(name="Servidor Offline 😴"),
                status=discord.Status.dnd
            )
    except Exception as e:
        print(f"Erro ao atualizar status do bot: {e}")

# --- Comando de barra: setup_status ---
@tree.command(name="setup_status", description="Configura a mensagem de status inicial")
@app_commands.checks.has_permissions(administrator=True)
async def setup_status_slash(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)  # Defer para evitar timeout

    if status_config["channel_id"] and status_config["message_id"]:
        try:
            old_channel = bot.get_channel(status_config["channel_id"])
            if old_channel:
                try:
                    old_message = await old_channel.fetch_message(status_config["message_id"])
                    await old_message.delete()
                except discord.NotFound:
                    pass
        except Exception as e:
            print(f"Erro ao deletar mensagem antiga: {e}")

    status = await get_server_status()
    embed = create_status_embed(status)
    message = await interaction.channel.send(embed=embed)
    
    status_config["channel_id"] = interaction.channel.id
    status_config["message_id"] = message.id
    save_status_config()

    await interaction.followup.send("✅ Status configurado com sucesso!", ephemeral=True)

# Comando slash para configurar o servidor Minecraft
@tree.command(name="configurar_servidor", description="Configura o IP e a porta do servidor Minecraft.")
@app_commands.describe(ip="IP do servidor", porta="Porta do servidor")
@app_commands.checks.has_permissions(administrator=True)
async def configurar_servidor_slash(interaction: discord.Interaction, ip: str, porta: int):
    status_config["server_ip"] = ip
    status_config["server_port"] = porta
    save_status_config()
    await interaction.response.send_message(f"✅ Servidor configurado para `{ip}:{porta}`.", ephemeral=True)

# IDs dos cargos e canal
CARGO_NAO_REGISTRADO = 1370692084159484055
CARGO_REGISTRADO = 1370692057227858020
CANAL_REGISTROS = 1370693091102556262

class RegistroModal(ui.Modal, title='Registro do Servidor'):
    nick_minecraft = ui.TextInput(
        label='Qual seu Nick do Minecraft?',
        placeholder='Digite seu nick exatamente como é no jogo',
        required=True,
        min_length=3,
        max_length=16
    )
    
    tipo_jogador = ui.TextInput(
        label='Você será Player ou Ovo?',
        placeholder='Digite "Player" ou "Ovo"',
        required=True
    )
    
    vila = ui.TextInput(
        label='Deseja participar de uma vila?',
        placeholder='Se sim, digite o nome da vila. Se não, digite "Não"',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Pegar os cargos
        cargo_registrado = interaction.guild.get_role(CARGO_REGISTRADO)
        cargo_nao_registrado = interaction.guild.get_role(CARGO_NAO_REGISTRADO)
        
        # Atualizar os cargos do membro
        membro = interaction.user
        await membro.remove_roles(cargo_nao_registrado)
        await membro.add_roles(cargo_registrado)

        # Criar embed para o usuário
        embed_usuario = discord.Embed(
            title="✅ Registro Completado!",
            description="Seu registro foi concluído com sucesso!",
            color=discord.Color.green()
        )
        embed_usuario.add_field(name="Nick Minecraft", value=self.nick_minecraft.value, inline=False)
        embed_usuario.add_field(name="Tipo de Jogador", value=self.tipo_jogador.value, inline=False)
        embed_usuario.add_field(name="Vila", value=self.vila.value, inline=False)
        embed_usuario.set_footer(text="Bem-vindo(a) ao servidor!")

        # Criar embed para o canal de registros
        embed_registro = discord.Embed(
            title="📝 Novo Registro",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed_registro.add_field(name="Discord", value=f"{interaction.user.mention} (`{interaction.user.name}`)", inline=False)
        embed_registro.add_field(name="Nick Minecraft", value=self.nick_minecraft.value, inline=False)
        embed_registro.add_field(name="Tipo de Jogador", value=self.tipo_jogador.value, inline=False)
        embed_registro.add_field(name="Vila", value=self.vila.value, inline=False)
        embed_registro.set_footer(text=f"ID do usuário: {interaction.user.id}")
        
        if interaction.user.avatar:
            embed_registro.set_thumbnail(url=interaction.user.avatar.url)

        # Enviar mensagem para o usuário
        await interaction.response.send_message(embeds=[embed_usuario], ephemeral=True)

        # Enviar mensagem no canal de registros
        canal_registros = interaction.guild.get_channel(CANAL_REGISTROS)
        if canal_registros:
            await canal_registros.send(embeds=[embed_registro])

class BotaoRegistro(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Iniciar Registro", style=discord.ButtonStyle.green, custom_id="registro_button")
    async def registro(self, interaction: discord.Interaction, button: ui.Button):
        modal = RegistroModal()
        await interaction.response.send_modal(modal)

# --- Comando de barra: criar_vila ---
@tree.command(name="criar_vila", description="Cria uma nova vila com categoria, canais e cargo exclusivo.")
@app_commands.describe(nome_vila="Nome da vila")
@app_commands.checks.has_permissions(administrator=True)
async def criar_vila_slash(interaction: discord.Interaction, nome_vila: str):
    producao_role = interaction.guild.get_role(PRODUCAO_ROLE_ID)
    if producao_role not in interaction.user.roles:
        await interaction.response.send_message("❌ Você não tem permissão para criar vilas.", ephemeral=True)
        return

    nome_vila_formatado = nome_vila.strip().title()
    nome_cargo = f"▪︎ 𝐕𝐢𝐥𝐚 {nome_vila_formatado} ▪︎"
    nome_categoria = f"🛖 | Vila {nome_vila_formatado}"
    nome_chat = "💬┇chat"
    nome_comandos = "💻┇comandos"
    nome_voice = f"🎤┇{nome_vila_formatado}"

    cargo_vila = await interaction.guild.create_role(name=nome_cargo, mentionable=True)
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        cargo_vila: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True),
        interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
    }
    if producao_role:
        overwrites[producao_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)

    categoria = await interaction.guild.create_category(name=nome_categoria, overwrites=overwrites)
    await categoria.create_text_channel(nome_chat)
    await categoria.create_text_channel(nome_comandos)
    await categoria.create_voice_channel(nome_voice)

    categoria_referencia = interaction.guild.get_channel(1370678132515803228)
    if categoria_referencia:
        nova_posicao = categoria_referencia.position + 1
        await categoria.edit(position=nova_posicao)

    await interaction.response.send_message(f"✅ Vila criada com sucesso!\nCargo: {cargo_vila.mention}\nCategoria: {categoria.name}")

    canal_log = interaction.guild.get_channel(CANAL_LOG_VILAS)
    if canal_log:
        embed = discord.Embed(
            title="🏗️ Vila Criada",
            description=f"**Nome:** {nome_vila_formatado}\n**Cargo:** {cargo_vila.mention}\n**Categoria:** {categoria.name}\n**Responsável:** {interaction.user.mention}",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )
        await canal_log.send(embed=embed)

# --- Comando de barra: deletar_vila ---
@tree.command(name="deletar_vila", description="Deleta a vila, removendo categoria, canais e cargo.")
@app_commands.describe(nome_vila="Nome da vila")
@app_commands.checks.has_permissions(administrator=True)
async def deletar_vila_slash(interaction: discord.Interaction, nome_vila: str):
    producao_role = interaction.guild.get_role(PRODUCAO_ROLE_ID)
    if producao_role not in interaction.user.roles:
        await interaction.response.send_message("❌ Você não tem permissão para deletar vilas.", ephemeral=True)
        return

    nome_vila_formatado = nome_vila.strip().title()
    nome_cargo = f"▪︎ 𝐕𝐢𝐥𝐚 {nome_vila_formatado} ▪︎"
    nome_categoria = f"🛖 | Vila {nome_vila_formatado}"

    cargo = discord.utils.get(interaction.guild.roles, name=nome_cargo)
    if cargo:
        await cargo.delete()

    categoria = discord.utils.get(interaction.guild.categories, name=nome_categoria)
    if categoria:
        for canal in categoria.channels:
            await canal.delete()
        await categoria.delete()

    await interaction.response.send_message(f"🗑️ Vila '{nome_vila_formatado}' deletada com sucesso!")

    canal_log = interaction.guild.get_channel(CANAL_LOG_VILAS)
    if canal_log:
        embed = discord.Embed(
            title="🗑️ Vila Deletada",
            description=f"**Nome:** {nome_vila_formatado}\n**Responsável:** {interaction.user.mention}",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )
        await canal_log.send(embed=embed)

# --- Comando de barra: setup_registro ---
@tree.command(name="setup_registro", description="Envia o painel de registro no canal atual")
@app_commands.checks.has_permissions(administrator=True)
async def setup_registro_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎮 Sistema de Registro",
        description="Clique no botão abaixo para iniciar seu registro no servidor!",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📝 Processo de Registro",
        value="Você responderá algumas perguntas sobre:\n"
              "• Nick do Minecraft\n"
              "• Tipo de jogador (Player/Ovo)\n"
              "• Participação em vila",
        inline=False
    )
    embed.add_field(
        name="ℹ️ Importante",
        value="• Digite seu nick exatamente como é no jogo\n"
              "• Responda todas as perguntas com atenção\n"
              "• Após o registro, você terá acesso aos canais do servidor",
        inline=False
    )
    embed.set_footer(text="Clique no botão verde abaixo para começar!")
    
    await interaction.response.send_message(embed=embed, view=BotaoRegistro())

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está online!')
    print(f'ID do Bot: {bot.user.id}')
    print(f'Current Date and Time (UTC): {CURRENT_TIME}')
    print(f'Current User\'s Login: {CURRENT_USER}')
    print('='*30)
    
    # Carregar configurações e iniciar tasks
    load_status_config()
    bot.add_view(BotaoRegistro())
    
    if not update_server_status.is_running():
        update_server_status.start()
    if not update_bot_status.is_running():
        update_bot_status.start()
    
    # Sincronizar comandos de barra
    try:
        synced = await tree.sync()
        print(f"Comandos de barra sincronizados: {len(synced)}")
    except Exception as e:
        print(f"Erro ao sincronizar comandos de barra: {e}")

@bot.event
async def on_member_join(member):
    cargo = member.guild.get_role(CARGO_NAO_REGISTRADO)
    if cargo:
        await member.add_roles(cargo)
        print(f"Cargo 'Não Registrado' adicionado para {member.name}")

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))