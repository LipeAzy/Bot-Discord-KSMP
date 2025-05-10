import discord
from discord.ext import commands
from discord import ui
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

load_dotenv()

# Configurações Globais
CURRENT_USER = "LipeAzy"
CURRENT_TIME = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configurações do Servidor
MINECRAFT_SERVER_IP = "enx-cirion-48.enx.host"
MINECRAFT_SERVER_PORT = 10047
STATUS_CONFIG_FILE = "status_config.json"

# Status rotativo para o bot (agora usando status customizado)
BOT_STATUS_MESSAGES = [
    lambda data: f"👥 {data['players_online']} jogadores online",
    lambda data: f"🎮 {MINECRAFT_SERVER_IP}:{MINECRAFT_SERVER_PORT}",
    lambda data: f"⚡ TPS: {data['tps']}"
]

status_config = {
    "channel_id": None,
    "message_id": None
}

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

async def get_server_status():
    """Função para obter o status do servidor Minecraft"""
    try:
        server = JavaServer(MINECRAFT_SERVER_IP, MINECRAFT_SERVER_PORT)
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
            'players_list': get_players_list(status)
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
            'players_list': []
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
    """Cria a embed com as informações do servidor"""
    current_time = datetime.now(timezone.utc)
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    if status['online']:
        embed = discord.Embed(
            title="🟢 Servidor Online",
            color=discord.Color.green(),
            timestamp=current_time
        )
        
        embed.add_field(
            name="👥 Jogadores Online",
            value=f"{status['players_online']}/{status['players_max']}",
            inline=True
        )
        
        embed.add_field(
            name="🌐 Servidor",
            value=f"`{MINECRAFT_SERVER_IP}:{MINECRAFT_SERVER_PORT}`",
            inline=True
        )
        
        embed.add_field(
            name="⚡ TPS",
            value=f"{status['tps']}",
            inline=True
        )
        
        embed.add_field(
            name="📊 Latência",
            value=f"{status['latency']}ms",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Versão",
            value=status['version'],
            inline=True
        )
        
        embed.add_field(
            name="⏰ Horário UTC",
            value=f"`{formatted_time}`",
            inline=True
        )

        if status['players_list']:
            players_text = '\n'.join(status['players_list'][:10])
            if len(status['players_list']) > 10:
                players_text += f"\n... e mais {len(status['players_list']) - 10} jogadores"
            embed.add_field(
                name="🎮 Jogadores Online",
                value=f"```\n{players_text}\n```",
                inline=False
            )
        
        footer_text = f"Última atualização por {CURRENT_USER}"
    else:
        embed = discord.Embed(
            title="🔴 Servidor Offline",
            description="O servidor está temporariamente indisponível.",
            color=discord.Color.red(),
            timestamp=current_time
        )
        
        embed.add_field(
            name="🌐 Servidor",
            value=f"`{MINECRAFT_SERVER_IP}:{MINECRAFT_SERVER_PORT}`",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Horário UTC",
            value=f"`{formatted_time}`",
            inline=True
        )
        
        footer_text = f"Tentando reconectar... • {CURRENT_USER}"
    
    embed.set_footer(text=footer_text)
    return embed

@tasks.loop(minutes=2)
async def update_server_status():
    """Atualiza o status do servidor a cada 2 minutos"""
    if not status_config["channel_id"] or not status_config["message_id"]:
        return

    try:
        channel = bot.get_channel(status_config["channel_id"])
        if not channel:
            return

        status = await get_server_status()
        embed = create_status_embed(status)

        try:
            message = await channel.fetch_message(status_config["message_id"])
            await message.edit(embed=embed)
        except discord.NotFound:
            message = await channel.send(embed=embed)
            status_config["message_id"] = message.id
            save_status_config()
    except Exception as e:
        print(f"Erro ao atualizar status: {e}")

@tasks.loop(minutes=2)
async def update_bot_status():
    """Atualiza o status do bot"""
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

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_status(ctx):
    """Configura a mensagem de status inicial"""
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
    
    message = await ctx.send(embed=embed)
    
    status_config["channel_id"] = ctx.channel.id
    status_config["message_id"] = message.id
    save_status_config()
    
    await ctx.send("✅ Status configurado com sucesso!", delete_after=5)

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está online!')
    print(f'ID do Bot: {bot.user.id}')
    print(f'Current Date and Time (UTC): {CURRENT_TIME}')
    print(f'Current User\'s Login: {CURRENT_USER}')
    print('='*30)
    
    load_status_config()
    
    if not update_server_status.is_running():
        update_server_status.start()
    if not update_bot_status.is_running():
        update_bot_status.start()
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

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está online!')
    print(f'ID do Bot: {bot.user.id}')
    print('='*30)
    bot.add_view(BotaoRegistro())

@bot.event
async def on_member_join(member):
    cargo = member.guild.get_role(CARGO_NAO_REGISTRADO)
    if cargo:
        await member.add_roles(cargo)
        print(f"Cargo 'Não Registrado' adicionado para {member.name}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_registro(ctx):
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
    
    await ctx.send(embed=embed, view=BotaoRegistro())

bot.run(os.getenv('DISCORD_TOKEN'))